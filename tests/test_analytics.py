"""
TechRadar — Comprehensive Unit & Analytical Test Suite
Tests all analytical modules and validates compliance with CSA4503 course concepts.
"""

import os
import unittest
import pandas as pd
import numpy as np

# Ensure path includes root
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.data_loader import load_dataset, get_dataset_metadata, standardize_columns
from modules.data_cleaning import (
    remove_duplicates,
    impute_missing_values,
    normalize_technology_names,
    convert_data_types,
    detect_iqr_outliers,
    filter_iqr_outliers
)
from modules.exploratory_analysis import get_structural_profile, get_frequency_tables
from modules.statistical_analysis import compute_detailed_descriptive_stats, get_correlation_matrix
from modules.aggregation import (
    perform_groupby_analysis,
    create_pivot_table,
    create_crosstab_analysis,
    demonstrate_hierarchical_indexing,
    demonstrate_melt_and_pivot,
    demonstrate_dataset_merging
)
from modules.time_series import (
    prepare_datetime_series,
    resample_technology_metric,
    compute_rolling_and_lags,
    demonstrate_period_arithmetic,
    demonstrate_timezone_handling
)
from modules.opportunity_analysis import calculate_opportunity_scores, get_classification_summary
from modules.report_generator import generate_pdf_report
from database.db import init_database, save_metrics_to_db, load_metrics_from_db, close_engine

class TestTechRadarAnalytics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load sample dataset once for all tests."""
        cls.df = load_dataset()

    def test_01_data_loader(self):
        """Test dataset loading, schema standardization, and metadata extraction."""
        self.assertFalse(self.df.empty, "Dataset should not be empty")
        self.assertIn("technology", self.df.columns)
        self.assertIn("category", self.df.columns)
        self.assertIn("job_postings", self.df.columns)
        
        meta = get_dataset_metadata(self.df)
        self.assertGreater(meta["rows"], 2000)
        self.assertGreaterEqual(meta["technologies_count"], 35)
        self.assertEqual(meta["categories_count"], 7)

    def test_02_data_cleaning_and_deduplication(self):
        """Test duplicate detection and removal."""
        initial_len = len(self.df)
        deduped, removed = remove_duplicates(self.df)
        self.assertLessEqual(len(deduped), initial_len)
        self.assertGreaterEqual(removed, 0)
        self.assertEqual(deduped.duplicated().sum(), 0)

    def test_03_missing_value_imputation(self):
        """Test numerical and categorical missing value imputation."""
        # Create a toy dataframe with nulls
        toy_df = pd.DataFrame({
            "salary": [100000.0, np.nan, 120000.0, 140000.0],
            "category": ["Cloud", np.nan, "Cloud", "AI"]
        })
        cleaned, logs = impute_missing_values(toy_df, numerical_strategy="median", categorical_strategy="mode")
        self.assertEqual(cleaned["salary"].isnull().sum(), 0)
        self.assertEqual(cleaned["salary"].iloc[1], 120000.0)
        self.assertEqual(cleaned["category"].isnull().sum(), 0)
        self.assertEqual(cleaned["category"].iloc[1], "Cloud")

    def test_04_string_normalization(self):
        """Test standardizing technology names (e.g. k8s -> Kubernetes, golang -> Go)."""
        toy_df = pd.DataFrame({"technology": ["k8s", "golang", "reactjs", "python", "Rust"]})
        cleaned, changes = normalize_technology_names(toy_df)
        self.assertEqual(cleaned["technology"].tolist(), ["Kubernetes", "Go", "React", "Python", "Rust"])
        self.assertEqual(changes, 4)

    def test_05_iqr_outlier_detection(self):
        """Test Interquartile Range (IQR) outlier detection and filtering."""
        outliers_df, metrics = detect_iqr_outliers(self.df, col="average_salary")
        self.assertIn("q1", metrics)
        self.assertIn("q3", metrics)
        self.assertIn("iqr", metrics)
        self.assertIn("lower_bound", metrics)
        self.assertIn("upper_bound", metrics)
        self.assertGreater(metrics["iqr"], 0)
        self.assertLess(metrics["lower_bound"], metrics["q1"])
        self.assertGreater(metrics["upper_bound"], metrics["q3"])

        # Filter outliers
        filtered = filter_iqr_outliers(self.df, col="average_salary")
        self.assertLessEqual(len(filtered), len(self.df))

    def test_06_statistical_analysis(self):
        """Test central tendency, dispersion, skewness, kurtosis, and correlation."""
        stats_table = compute_detailed_descriptive_stats(self.df)
        self.assertFalse(stats_table.empty)
        self.assertIn("Mean", stats_table.columns)
        self.assertIn("Median", stats_table.columns)
        self.assertIn("Std Dev", stats_table.columns)
        self.assertIn("Skewness", stats_table.columns)
        self.assertIn("Kurtosis", stats_table.columns)
        self.assertIn("IQR", stats_table.columns)

        corr = get_correlation_matrix(self.df, method="pearson")
        self.assertFalse(corr.empty)
        # Check diagonal values are 1.0
        for col in corr.columns:
            self.assertAlmostEqual(corr.loc[col, col], 1.0, places=3)

    def test_07_aggregation_groupby_and_pivot(self):
        """Test GroupBy split-apply-combine and pivot tables with margins."""
        # GroupBy
        grp = perform_groupby_analysis(self.df, group_cols=["category"])
        self.assertFalse(grp.empty)
        self.assertEqual(len(grp), 7)

        # Pivot Table
        pivot = create_pivot_table(self.df, index_col="category", column_col="year", value_col="job_postings", agg_func="sum", margins=True)
        self.assertFalse(pivot.empty)
        self.assertIn("Total", pivot.index)
        self.assertIn("Total", pivot.columns)

        # Crosstab
        ct = create_crosstab_analysis(self.df, row_col="category", col_col="year", normalize="all", margins=True)
        self.assertFalse(ct.empty)

        # MultiIndex
        multi, unstacked, restacked = demonstrate_hierarchical_indexing(self.df)
        self.assertFalse(multi.empty)
        self.assertFalse(unstacked.empty)

        # Melt & Pivot
        wide, long_df = demonstrate_melt_and_pivot(self.df)
        self.assertFalse(wide.empty)
        self.assertFalse(long_df.empty)

        # Merging
        merged = demonstrate_dataset_merging(self.df)
        self.assertFalse(merged.empty)
        self.assertIn("ecosystem_rank", merged.columns)

    def test_08_time_series_resampling_and_rolling(self):
        """Test Datetime indexing, resampling, rolling windows, and shifting."""
        ts_prep = prepare_datetime_series(self.df)
        self.assertIn("year_extracted", ts_prep.columns)

        # Resample monthly
        resampled = resample_technology_metric(self.df, tech_name="Python", freq="ME", metric="job_postings")
        self.assertFalse(resampled.empty)
        self.assertGreaterEqual(len(resampled), 48) # at least 4 years of monthly observations

        # Rolling & Lags
        rolling_res = compute_rolling_and_lags(resampled, metric_col="job_postings", windows=[3, 6])
        self.assertIn("MA_3", rolling_res.columns)
        self.assertIn("MA_6", rolling_res.columns)
        self.assertIn("Lag_1", rolling_res.columns)
        self.assertIn("MoM_Growth_Pct", rolling_res.columns)

        # Period arithmetic
        periods = demonstrate_period_arithmetic(self.df)
        self.assertIn("Next_Month_Period", periods.columns)

        # Timezone conversion
        tzs = demonstrate_timezone_handling(self.df)
        self.assertIn("Asia_Kolkata", tzs.columns)

    def test_09_opportunity_scoring(self):
        """Test Opportunity Score calculation and 5-tier classification."""
        scored = calculate_opportunity_scores(self.df)
        self.assertFalse(scored.empty)
        self.assertIn("opportunity_score", scored.columns)
        self.assertIn("classification", scored.columns)
        
        # Verify scores lie strictly between 0 and 100
        self.assertTrue((scored["opportunity_score"] >= 0).all())
        self.assertTrue((scored["opportunity_score"] <= 100).all())

        # Verify classifications belong to valid set
        valid_tiers = {"Emerging", "High-Demand", "Low-Demand / High-Growth", "Established", "Monitor"}
        self.assertTrue(set(scored["classification"].unique()).issubset(valid_tiers))

    def test_10_database_sqlite_integration(self):
        """Test SQLite persistent storage, schema creation, save and load."""
        test_db = os.path.join(os.path.dirname(__file__), "test_techradar.db")
        close_engine(test_db)
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
            except Exception:
                pass

        init_database(db_path=test_db)
        saved = save_metrics_to_db(self.df.head(50), db_path=test_db, replace=True)
        self.assertEqual(saved, 50)

        loaded = load_metrics_from_db(db_path=test_db)
        self.assertEqual(len(loaded), 50)

        close_engine(test_db)
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
            except Exception:
                pass

    def test_11_pdf_report_generation(self):
        """Test ReportLab PDF generation pipeline."""
        summary = {
            "total_technologies": 40,
            "total_categories": 7,
            "total_jobs": 150000,
            "avg_salary": 132000.0,
            "highest_demand_tech": "Python",
            "fastest_growing_tech": "Rust"
        }
        top_df = self.df.head(10)
        opp_df = calculate_opportunity_scores(self.df).head(10)

        pdf_bytes = generate_pdf_report(summary, top_df, opp_df)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

if __name__ == "__main__":
    unittest.main()
