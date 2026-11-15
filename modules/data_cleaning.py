"""
TechRadar — Data Cleaning and Preprocessing Module
Implements CSA4503 Module 2 & 3 core operations:
- Duplicate record removal
- Missing value imputation (Mean/Median/Mode/Drop)
- String normalization and entity standardization
- Data type conversions
- IQR outlier detection and filtering
- Column filtering and transformations
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Any, Optional

TECH_STANDARDIZATION_MAP = {
    "python": "Python", "PYTHON": "Python", "py": "Python",
    "golang": "Go", "GOLANG": "Go", "go": "Go",
    "reactjs": "React", "REACT": "React", "react": "React",
    "k8s": "Kubernetes", "K8S": "Kubernetes", "K8s": "Kubernetes", "kubernetes": "Kubernetes",
    "postgres": "PostgreSQL", "postgresql": "PostgreSQL", "POSTGRESQL": "PostgreSQL",
    "tf": "TensorFlow", "tensorflow": "TensorFlow", "TENSORFLOW": "TensorFlow",
    "pytorch": "PyTorch", "PYTORCH": "PyTorch",
    "docker": "Docker", "DOCKER": "Docker",
    "aws": "AWS", "azure": "Azure", "AZURE": "Azure",
    "mongodb": "MongoDB", "MONGODB": "MongoDB"
}

def inspect_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Compute missing value counts and percentages for each column."""
    null_counts = df.isnull().sum()
    null_pct = (null_counts / len(df) * 100).round(2)
    missing_summary = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": null_counts.values,
        "Missing (%)": null_pct.values,
        "Data Type": [str(t) for t in df.dtypes.values]
    })
    return missing_summary[missing_summary["Missing Count"] > 0].sort_values("Missing Count", ascending=False)

def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Identify and drop duplicate rows."""
    initial_len = len(df)
    deduped = df.drop_duplicates()
    removed = initial_len - len(deduped)
    return deduped, removed

def impute_missing_values(
    df: pd.DataFrame, 
    numerical_strategy: str = "median",
    categorical_strategy: str = "mode"
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Handle missing values:
    - numerical_strategy: 'mean', 'median', 'constant_zero', 'drop', 'none'
    - categorical_strategy: 'mode', 'unknown', 'drop', 'none'
    """
    cleaned = df.copy()
    logs = {}

    # Numerical columns
    num_cols = cleaned.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if cleaned[col].isnull().any():
            missing_cnt = int(cleaned[col].isnull().sum())
            if numerical_strategy == "median":
                val = cleaned[col].median()
                cleaned[col] = cleaned[col].fillna(val)
                logs[col] = f"Imputed {missing_cnt} nulls with median ({val:,.2f})"
            elif numerical_strategy == "mean":
                val = cleaned[col].mean()
                cleaned[col] = cleaned[col].fillna(val)
                logs[col] = f"Imputed {missing_cnt} nulls with mean ({val:,.2f})"
            elif numerical_strategy == "constant_zero":
                cleaned[col] = cleaned[col].fillna(0)
                logs[col] = f"Imputed {missing_cnt} nulls with 0"
            elif numerical_strategy == "drop":
                cleaned = cleaned.dropna(subset=[col])
                logs[col] = f"Dropped {missing_cnt} rows with missing {col}"

    # Categorical columns
    cat_cols = cleaned.select_dtypes(include=["object", "string", "category"]).columns
    for col in cat_cols:
        if cleaned[col].isnull().any():
            missing_cnt = int(cleaned[col].isnull().sum())
            if categorical_strategy == "mode":
                mode_val = cleaned[col].mode()[0] if not cleaned[col].mode().empty else "Unknown"
                cleaned[col] = cleaned[col].fillna(mode_val)
                logs[col] = f"Imputed {missing_cnt} nulls with mode ('{mode_val}')"
            elif categorical_strategy == "unknown":
                cleaned[col] = cleaned[col].fillna("Unknown")
                logs[col] = f"Imputed {missing_cnt} nulls with 'Unknown'"
            elif categorical_strategy == "drop":
                cleaned = cleaned.dropna(subset=[col])
                logs[col] = f"Dropped {missing_cnt} rows with missing {col}"

    return cleaned, logs

def normalize_technology_names(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Clean whitespace, strip string characters, and map aliases to canonical names.
    """
    if "technology" not in df.columns:
        return df, 0

    cleaned = df.copy()
    changes = 0

    def clean_name(val):
        nonlocal changes
        if pd.isna(val):
            return val
        s = str(val).strip()
        lower = s.lower()
        if lower in TECH_STANDARDIZATION_MAP:
            target = TECH_STANDARDIZATION_MAP[lower]
            if target != s:
                changes += 1
            return target
        return s

    cleaned["technology"] = cleaned["technology"].apply(clean_name)
    return cleaned, changes

def convert_data_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Convert columns to appropriate analytical types."""
    cleaned = df.copy()
    logs = []

    if "date" in cleaned.columns:
        cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
        logs.append("Converted 'date' to datetime64[ns].")

    numeric_targets = ["year", "month", "job_postings", "developer_interest",
                       "company_adoption", "average_salary", "github_activity",
                       "skill_demand", "growth_rate"]
    for col in numeric_targets:
        if col in cleaned.columns and not pd.api.types.is_numeric_dtype(cleaned[col]):
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
            logs.append(f"Converted '{col}' to numeric.")

    if "category" in cleaned.columns:
        cleaned["category"] = cleaned["category"].astype("category")
        logs.append("Optimized 'category' to categorical dtype.")

    return cleaned, logs

def detect_iqr_outliers(df: pd.DataFrame, col: str = "average_salary") -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Calculate Interquartile Range (IQR) bounds and isolate outliers.
    Formulas:
      Q1 = 25th percentile
      Q3 = 75th percentile
      IQR = Q3 - Q1
      Lower Bound = Q1 - 1.5 * IQR
      Upper Bound = Q3 + 1.5 * IQR
    """
    if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
        return pd.DataFrame(), {}

    series = df[col].dropna()
    if len(series) == 0:
        return pd.DataFrame(), {}

    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
    outliers_df = df[outlier_mask].copy()

    metrics = {
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_count": len(outliers_df),
        "outlier_pct": round(len(outliers_df) / len(df) * 100, 2)
    }
    return outliers_df, metrics

def filter_iqr_outliers(df: pd.DataFrame, col: str = "average_salary") -> pd.DataFrame:
    """Remove records outside the IQR lower and upper bounds."""
    _, metrics = detect_iqr_outliers(df, col)
    if not metrics:
        return df

    lower = metrics["lower_bound"]
    upper = metrics["upper_bound"]
    mask = (df[col].isna()) | ((df[col] >= lower) & (df[col] <= upper))
    return df[mask].copy()

def remove_columns(df: pd.DataFrame, cols_to_remove: List[str]) -> pd.DataFrame:
    """Drop selected unnecessary columns."""
    existing = [c for c in cols_to_remove if c in df.columns]
    if existing:
        return df.drop(columns=existing)
    return df
