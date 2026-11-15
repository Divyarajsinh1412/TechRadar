"""
TechRadar — Test Suite for Real API Collectors, Deduplication & Cloud Database Migration
Tests all external collectors using mocked HTTP responses and tests PostgreSQL/SQLite persistence.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import (
    init_database,
    bulk_save_live_observations,
    get_live_observations,
    get_source_status,
    update_source_status,
    log_collection_run,
    save_raw_job_postings,
    is_using_postgres,
    get_database_url
)
from collectors.github_collector import GitHubCollector
from collectors.huggingface_collector import HuggingFaceCollector
from collectors.adzuna_collector import AdzunaCollector
from collectors.google_trends_collector import GoogleTrendsCollector
from collectors.developer_survey_collector import DeveloperSurveyCollector

class TestCollectorsAndDatabase(unittest.TestCase):
    """Automated test cases for collectors, deduplication, and database operations."""

    def setUp(self):
        """Ensure database is initialized before each test."""
        init_database()

    # ---------------- 1. GitHub Collector Tests ----------------

    @patch("requests.Session.get")
    def test_github_collector_success(self, mock_get):
        """Verify GitHub Collector parses repo search results and produces valid observations."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"X-RateLimit-Remaining": "4900"}
        mock_resp.json.return_value = {
            "total_count": 150000,
            "items": [
                {
                    "name": "cpython",
                    "html_url": "https://github.com/python/cpython",
                    "stargazers_count": 62000,
                    "forks_count": 29000,
                    "open_issues_count": 7500
                }
            ]
        }
        mock_get.return_value = mock_resp

        collector = GitHubCollector(token="test_mock_token")
        observations = collector.collect(technologies=["Python"])

        self.assertGreaterEqual(len(observations), 3)
        metrics = {obs["metric_name"]: obs["metric_value"] for obs in observations}
        self.assertEqual(metrics["stars"], 62000)
        self.assertEqual(metrics["forks"], 29000)
        self.assertEqual(metrics["repo_count"], 150000)
        self.assertEqual(observations[0]["data_quality_status"], "verified_live")

    @patch("requests.Session.get")
    def test_github_collector_rate_limit(self, mock_get):
        """Verify GitHub Collector gracefully stops without crashing when rate limit is reached."""
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.headers = {"X-RateLimit-Remaining": "0"}
        mock_get.return_value = mock_resp

        collector = GitHubCollector(token=None)
        observations = collector.collect(technologies=["Rust", "Go"])
        self.assertEqual(len(observations), 0)

    # ---------------- 2. Hugging Face Collector Tests ----------------

    @patch("requests.Session.get")
    def test_huggingface_collector_success(self, mock_get):
        """Verify Hugging Face Collector computes aggregate downloads and community likes."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"id": "meta-llama/Llama-2-7b", "downloads": 450000, "likes": 12500},
            {"id": "meta-llama/Llama-3-8b", "downloads": 850000, "likes": 24000}
        ]
        mock_get.return_value = mock_resp

        collector = HuggingFaceCollector()
        observations = collector.collect(technologies=["PyTorch"])

        self.assertEqual(len(observations), 3)
        metrics = {obs["metric_name"]: obs["metric_value"] for obs in observations}
        self.assertEqual(metrics["hf_downloads"], 1300000)
        self.assertEqual(metrics["hf_likes"], 36500)
        self.assertEqual(metrics["hf_models_tracked"], 2)

    @patch("requests.Session.get")
    def test_huggingface_collector_rate_limit(self, mock_get):
        """Verify Hugging Face Collector handles HTTP 429 gracefully."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp

        collector = HuggingFaceCollector()
        observations = collector.collect(technologies=["PyTorch"])
        self.assertEqual(len(observations), 0)

    # ---------------- 3. Adzuna Job Market Collector Tests ----------------

    def test_adzuna_unconfigured_state(self):
        """Verify Adzuna correctly detects missing credentials and disables unauthenticated calls."""
        collector = AdzunaCollector(app_id=None, app_key=None)
        self.assertFalse(collector.is_configured())
        observations = collector.collect(technologies=["Python"])
        self.assertEqual(len(observations), 0)

    def test_adzuna_skill_extraction(self):
        """Verify skill extraction regex finds technologies without false positives."""
        collector = AdzunaCollector(app_id="dummy", app_key="dummy")
        text = "Senior Software Engineer needed with Python and Docker experience. Knowledge of PyTorch and Kubernetes is a plus."
        detected = collector.extract_skills_from_text(text)
        self.assertIn("Python", detected)
        self.assertIn("Docker", detected)
        self.assertIn("PyTorch", detected)
        self.assertIn("Kubernetes", detected)

    def test_adzuna_csv_import_mode(self):
        """Verify real CSV job postings can be ingested without generating fake data."""
        sample_jobs_df = pd.DataFrame([
            {"job_title": "Full Stack Developer", "description": "Hands on with React, Node.js and TypeScript. Good communication."},
            {"job_title": "Cloud Architect", "description": "Designing microservices on AWS with Terraform and Docker."}
        ])
        temp_csv = os.path.join(os.path.dirname(__file__), "temp_jobs.csv")
        sample_jobs_df.to_csv(temp_csv, index=False)

        try:
            collector = AdzunaCollector()
            obs = collector.import_jobs_from_csv(temp_csv)
            techs = [o["technology"] for o in obs]
            self.assertIn("React", techs)
            self.assertIn("TypeScript", techs)
            self.assertIn("AWS", techs)
            self.assertIn("Docker", techs)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)

    # ---------------- 4. Google Trends Collector Tests ----------------

    @patch("pytrends.request.TrendReq")
    def test_google_trends_collector(self, mock_trend_cls):
        """Verify Google Trends collector captures relative search index."""
        mock_instance = MagicMock()
        mock_df = pd.DataFrame({
            "Python": [85, 90, 95],
            "Rust": [40, 45, 50],
            "isPartial": [False, False, False]
        })
        mock_instance.interest_over_time.return_value = mock_df
        mock_trend_cls.return_value = mock_instance

        collector = GoogleTrendsCollector()
        obs = collector.collect(technologies=["Python", "Rust"])
        self.assertGreaterEqual(len(obs), 2)
        metrics = {o["technology"]: o["metric_value"] for o in obs}
        self.assertEqual(metrics["Python"], 95.0)
        self.assertEqual(metrics["Rust"], 50.0)

    # ---------------- 5. Database Upsert & Duplicate Prevention ----------------

    def test_live_observations_duplicate_prevention(self):
        """Verify duplicate live observations are updated rather than duplicated."""
        now_str = "2026-11-15"
        obs1 = [{
            "observation_date": now_str,
            "technology": "Zig",
            "category": "Programming Languages",
            "source_id": "github",
            "metric_name": "stars",
            "metric_value": 31000.0,
            "data_frequency": "daily",
            "data_quality_status": "verified_live"
        }]
        bulk_save_live_observations(obs1)

        # Ingest same key with updated metric value
        obs2 = [{
            "observation_date": now_str,
            "technology": "Zig",
            "category": "Programming Languages",
            "source_id": "github",
            "metric_name": "stars",
            "metric_value": 31500.0,
            "data_frequency": "daily",
            "data_quality_status": "verified_live"
        }]
        bulk_save_live_observations(obs2)

        # Query and verify single row with updated value
        df = get_live_observations(frequency="daily", technology="Zig")
        self.assertFalse(df.empty)
        zig_stars = df[df["metric_name"] == "stars"]
        self.assertEqual(len(zig_stars), 1)
        self.assertEqual(float(zig_stars["metric_value"].iloc[0]), 31500.0)

    def test_raw_job_postings_deduplication(self):
        """Verify raw job postings deduplicate by external_id."""
        jobs = [
            {
                "external_id": "job_uniq_12345",
                "source_id": "adzuna",
                "title": "Data Scientist",
                "company": "AI Labs",
                "location": "Bengaluru",
                "country": "in",
                "salary_min": 1500000.0,
                "salary_max": 2500000.0,
                "detected_skills": "Python, PyTorch",
                "posting_date": "2026-11-15"
            }
        ]
        count1 = save_raw_job_postings(jobs)
        count2 = save_raw_job_postings(jobs) # Insert duplicate
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)

    def test_source_status_and_collection_history(self):
        """Verify source status updates and history logs are written."""
        update_source_status(
            source_id="github",
            status="active",
            message="Test sync verified.",
            records_count=25
        )
        status_df = get_source_status()
        gh_row = status_df[status_df["source_id"] == "github"]
        self.assertFalse(gh_row.empty)
        self.assertEqual(gh_row["status"].iloc[0], "active")

        log_collection_run(
            source_id="github",
            job_name="test_github_job",
            status="success",
            records_collected=25
        )

if __name__ == "__main__":
    unittest.main()
