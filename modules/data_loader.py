"""
TechRadar — Data Loader Module
Handles CSV and Excel data ingestion, multi-frequency dataset generation (Daily, Weekly, Monthly),
caching, column standardization, and database sync.
"""

import os
import pandas as pd
import streamlit as st
from typing import Optional, Tuple, List, Dict, Any
from database.db import record_upload, save_metrics_to_db, load_metrics_from_db, is_using_postgres

DEFAULT_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_technology_data.csv")

COLUMN_SYNONYMS = {
    "technology": ["technology", "tech", "tech_name", "technology_name", "skill", "language"],
    "category": ["category", "tech_category", "technology_category", "domain", "type"],
    "year": ["year", "yr"],
    "month": ["month", "mo"],
    "day": ["day", "d"],
    "date": ["date", "posting_date", "timestamp", "period"],
    "job_postings": ["job_postings", "job_count", "postings", "jobs", "demand"],
    "developer_interest": ["developer_interest", "dev_interest", "interest", "popularity"],
    "company_adoption": ["company_adoption", "adoption", "enterprise_adoption"],
    "average_salary": ["average_salary", "avg_salary", "salary", "compensation"],
    "github_activity": ["github_activity", "github", "repo_activity", "stars"],
    "skill_demand": ["skill_demand", "demand_score", "skill_score"],
    "growth_rate": ["growth_rate", "growth", "growth_pct", "pct_change"]
}

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize DataFrame column names to consistent snake_case identifiers.
    Maps common synonyms (e.g. 'Job Postings' -> 'job_postings').
    """
    cleaned_df = df.copy()
    raw_cols = {col: str(col).strip().lower().replace(" ", "_").replace("-", "_") for col in cleaned_df.columns}
    cleaned_df = cleaned_df.rename(columns=raw_cols)

    # Synonym mapping
    rename_map = {}
    for standard_name, synonyms in COLUMN_SYNONYMS.items():
        for col in cleaned_df.columns:
            if col in synonyms:
                rename_map[col] = standard_name
                break
    
    cleaned_df = cleaned_df.rename(columns=rename_map)
    return cleaned_df

def ensure_sample_data() -> str:
    """Ensure sample_technology_data.csv exists; generate it if missing."""
    if not os.path.exists(DEFAULT_DATA_PATH):
        os.makedirs(os.path.dirname(DEFAULT_DATA_PATH), exist_ok=True)
        from modules.data_generator import generate_technology_dataset
        generate_technology_dataset(DEFAULT_DATA_PATH)
    return DEFAULT_DATA_PATH

@st.cache_data(show_spinner=False)
def load_dataset(file_source: Optional[object] = None) -> pd.DataFrame:
    """
    Load dataset from production database (Supabase PostgreSQL), custom uploaded file,
    or local fallback file. Prioritizes the active production database.
    """
    if file_source is None:
        try:
            db_df = load_metrics_from_db()
            if db_df is not None and not db_df.empty:
                return standardize_columns(db_df)
        except Exception:
            pass

        path = ensure_sample_data()
        df = pd.read_csv(path)
    elif isinstance(file_source, str):
        df = pd.read_csv(file_source)
    else:
        filename = getattr(file_source, "name", "dataset.csv").lower()
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(file_source)
        else:
            df = pd.read_csv(file_source)
            
        # Record upload in Database
        try:
            record_upload(filename, len(df), len(df.columns))
        except Exception:
            pass

    return standardize_columns(df)

@st.cache_data(show_spinner=False)
def load_dataset_by_frequency(frequency: str = "Monthly", file_source: Optional[object] = None) -> pd.DataFrame:
    """
    Load or generate dataset matching the requested analysis frequency:
    - 'Daily': 90-day granular daily observations with DoD growth and daily GitHub/Job activity.
    - 'Weekly': Weekly aggregated observations with WoW growth and 4-week moving averages.
    - 'Monthly': 2021–2025 monthly longitudinal observations loaded from Supabase PostgreSQL.
    """
    freq_upper = frequency.upper()
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    # Priority 1: Monthly loads directly from Supabase PostgreSQL
    if file_source is None and "MONTHLY" in freq_upper:
        try:
            db_df = load_metrics_from_db()
            if db_df is not None and not db_df.empty:
                return standardize_columns(db_df)
        except Exception:
            pass

    if file_source is None and "DAILY" in freq_upper:
        daily_path = os.path.join(data_dir, "tech_trends_daily.csv")
        if os.path.exists(daily_path):
            return standardize_columns(pd.read_csv(daily_path))
        from modules.multi_period_generator import generate_daily_observations
        df = generate_daily_observations(days=90)
        df.to_csv(daily_path, index=False)
        return standardize_columns(df)

    if file_source is None and "WEEKLY" in freq_upper:
        weekly_path = os.path.join(data_dir, "tech_trends_weekly.csv")
        if os.path.exists(weekly_path):
            return standardize_columns(pd.read_csv(weekly_path))
        base_df = load_dataset(file_source)
        from modules.multi_period_generator import generate_weekly_observations
        df = generate_weekly_observations(base_df)
        df.to_csv(weekly_path, index=False)
        return standardize_columns(df)

    base_df = load_dataset(file_source)
    if "DAILY" in freq_upper:
        from modules.multi_period_generator import generate_daily_observations
        return generate_daily_observations(days=90)
    elif "WEEKLY" in freq_upper:
        from modules.multi_period_generator import generate_weekly_observations
        return generate_weekly_observations(base_df)
    else:
        return base_df

def get_dataset_metadata(df: pd.DataFrame) -> Dict[str, Any]:
    """Return structural metadata and health stats for a DataFrame."""
    using_pg = is_using_postgres()
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "total_missing": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_kb": round(df.memory_usage(deep=True).sum() / 1024, 2),
        "technologies_count": int(df["technology"].nunique()) if "technology" in df.columns else 0,
        "categories_count": int(df["category"].nunique()) if "category" in df.columns else 0,
        "storage_backend": "Supabase PostgreSQL (Production)" if using_pg else "SQLite Engine (Local Dev)",
        "is_production_cloud": using_pg,
        "data_provenance": "Live Cloud Database Query" if using_pg else "Local Database / Sample"
    }
