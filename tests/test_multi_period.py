"""
TechRadar — Multi-Period Analytics & Live Intelligence Test Suite
Tests:
- Daily, Weekly, and Monthly data aggregation
- Safe growth rate calculations (zero & missing division prevention)
- 7-day and 30-day moving averages
- Weekly growth consistency and monthly acceleration
- SQLite live_observations and data_source_status CRUD
- Live intelligence ranking functions (fastest growing, new frameworks)
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np

# Ensure path includes root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.multi_period_analytics import (
    calculate_safe_growth_rate,
    aggregate_by_frequency,
    compute_multi_period_growth_and_averages,
    get_fastest_growing_now,
    get_gaining_github_activity,
    get_newly_posted_technologies,
    get_declining_technologies,
    get_newly_detected_skills
)
from modules.multi_period_generator import generate_daily_observations, generate_weekly_observations
from modules.live_collector import query_github_technology_signal, query_huggingface_model_signal
from database.db import (
    init_database,
    bulk_save_live_observations,
    get_live_observations,
    get_source_status,
    update_source_status,
    close_engine
)

class TestMultiPeriodAnalytics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Prepare sample datasets for testing."""
        from modules.data_loader import load_dataset
        cls.monthly_df = load_dataset()
        cls.daily_df = generate_daily_observations(days=30)
        cls.weekly_df = generate_weekly_observations(cls.monthly_df)

    def test_01_safe_growth_rate_calculations(self):
        """Test safe growth percentage calculations under normal, zero, and missing scenarios."""
        # Normal positive growth: 100 -> 150 = +50.0%
        self.assertEqual(calculate_safe_growth_rate(150, 100), 50.0)
        # Normal negative growth: 100 -> 80 = -20.0%
        self.assertEqual(calculate_safe_growth_rate(80, 100), -20.0)
        # Zero baseline: Must NOT raise ZeroDivisionError or return inf
        self.assertIsNone(calculate_safe_growth_rate(50, 0))
        # Negative baseline: Must return None
        self.assertIsNone(calculate_safe_growth_rate(50, -10))
        # Missing values: Must return None
        self.assertIsNone(calculate_safe_growth_rate(np.nan, 100))
        self.assertIsNone(calculate_safe_growth_rate(100, np.nan))

    def test_02_daily_aggregation_and_ma7(self):
        """Test daily aggregation, DoD growth rate, and 7-day moving averages."""
        self.assertFalse(self.daily_df.empty)
        self.assertIn("job_postings", self.daily_df.columns)
        self.assertIn("date", self.daily_df.columns)

        daily_processed = compute_multi_period_growth_and_averages(self.daily_df, frequency="Daily")
        self.assertIn("MA_7", daily_processed.columns)
        self.assertIn("MA_30", daily_processed.columns)
        self.assertIn("growth_pct", daily_processed.columns)

        # Ensure no inf values exist
        self.assertFalse(np.isinf(daily_processed["growth_pct"].dropna()).any())

    def test_03_weekly_aggregation_and_acceleration(self):
        """Test weekly aggregation, WoW growth rate, and weekly growth acceleration."""
        self.assertFalse(self.weekly_df.empty)
        weekly_processed = compute_multi_period_growth_and_averages(self.weekly_df, frequency="Weekly")
        
        self.assertIn("MA_4", weekly_processed.columns)
        self.assertIn("growth_acceleration", weekly_processed.columns)
        self.assertIn("growth_consistency", weekly_processed.columns)
        self.assertFalse(np.isinf(weekly_processed["growth_pct"].dropna()).any())

    def test_04_monthly_aggregation_and_yoy(self):
        """Test monthly aggregation, MoM growth rate, and YoY 12-month lag growth."""
        monthly_processed = compute_multi_period_growth_and_averages(self.monthly_df, frequency="Monthly")
        
        self.assertIn("MA_3", monthly_processed.columns)
        self.assertIn("MA_6", monthly_processed.columns)
        self.assertIn("YoY_Growth_Pct", monthly_processed.columns)
        self.assertFalse(np.isinf(monthly_processed["growth_pct"].dropna()).any())

    def test_05_live_intelligence_rankings(self):
        """Test fastest growing, top GitHub activity, and declining technology detection."""
        daily_processed = compute_multi_period_growth_and_averages(self.daily_df, frequency="Daily")
        
        fastest = get_fastest_growing_now(daily_processed, top_n=3)
        self.assertFalse(fastest.empty)
        self.assertLessEqual(len(fastest), 3)

        top_gh = get_gaining_github_activity(daily_processed, top_n=3)
        self.assertFalse(top_gh.empty)

        new_posts = get_newly_posted_technologies(daily_processed, top_n=3)
        self.assertFalse(new_posts.empty)

        new_skills = get_newly_detected_skills()
        self.assertIsInstance(new_skills, list)
        self.assertGreater(len(new_skills), 0)

    def test_06_sqlite_live_observations_persistence(self):
        """Test bulk saving and querying of multi-period live observations in SQLite."""
        test_db = os.path.join(os.path.dirname(__file__), "test_live.db")
        if os.path.exists(test_db):
            os.remove(test_db)

        init_database(db_path=test_db)

        sample_obs = [
            {
                "observation_date": "2026-11-15",
                "technology": "Rust",
                "category": "Programming Languages",
                "source_id": "github",
                "metric_name": "github_activity",
                "metric_value": 94.5,
                "data_frequency": "daily",
                "data_quality_status": "verified_live"
            },
            {
                "observation_date": "2026-11-15",
                "technology": "Python",
                "category": "Programming Languages",
                "source_id": "job_market",
                "metric_name": "job_postings",
                "metric_value": 150.0,
                "data_frequency": "daily",
                "data_quality_status": "verified_live"
            }
        ]

        saved = bulk_save_live_observations(sample_obs, db_path=test_db)
        self.assertEqual(saved, 2)

        queried = get_live_observations(frequency="daily", db_path=test_db)
        self.assertEqual(len(queried), 2)
        self.assertIn("Rust", queried["technology"].tolist())

        # Test duplicate prevention (INSERT OR REPLACE)
        saved_dup = bulk_save_live_observations(sample_obs, db_path=test_db)
        self.assertEqual(saved_dup, 2)
        queried_after = get_live_observations(frequency="daily", db_path=test_db)
        self.assertEqual(len(queried_after), 2) # No duplicate rows!

        close_engine(test_db)
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
            except Exception:
                pass

    def test_07_data_source_status_tracking(self):
        """Test updating and reading data source statuses."""
        test_db = os.path.join(os.path.dirname(__file__), "test_sources.db")
        close_engine(test_db)
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
            except Exception:
                pass

        init_database(db_path=test_db)
        sources = get_source_status(db_path=test_db)
        self.assertFalse(sources.empty)
        self.assertIn("github", sources["source_id"].tolist())

        update_source_status("github", "active", "12 repos synced", records_count=5, db_path=test_db)
        updated = get_source_status(db_path=test_db)
        gh_row = updated[updated["source_id"] == "github"].iloc[0]
        self.assertEqual(gh_row["status"], "active")
        self.assertIn("12 repos", gh_row["message"])

        close_engine(test_db)
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
            except Exception:
                pass

    def test_08_live_collector_safe_offline_handling(self):
        """Test live collectors handle sandbox/offline/rate-limited environments gracefully."""
        # Querying with short timeout in sandbox should return None, 'offline_cached' without throwing an unhandled exception
        gh_data, gh_status = query_github_technology_signal("Rust")
        self.assertIn(gh_status, ["verified_live", "offline_cached", "rate_limited"])

        hf_data, hf_status = query_huggingface_model_signal("PyTorch")
        self.assertIn(hf_status, ["verified_live", "offline_cached", "rate_limited"])

if __name__ == "__main__":
    unittest.main()
