"""
TechRadar — Exploratory Analysis Module
Implements structural inspection, column profiling, and frequency analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

def get_structural_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """Return structural profile corresponding to df.info(), df.shape, and memory usage."""
    profiles = []
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        non_null_count = int(df[col].notnull().sum())
        unique_count = int(df[col].nunique())
        dtype_str = str(df[col].dtype)
        
        sample_vals = df[col].dropna().head(3).tolist()
        sample_str = ", ".join([str(v) for v in sample_vals])
        
        profiles.append({
            "Column": col,
            "Non-Null": non_null_count,
            "Null Count": null_count,
            "Null (%)": round(null_count / len(df) * 100, 2),
            "Data Type": dtype_str,
            "Unique Count": unique_count,
            "Sample Values": sample_str
        })

    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "memory_kb": round(df.memory_usage(deep=True).sum() / 1024, 2),
        "columns_df": pd.DataFrame(profiles)
    }

def get_frequency_tables(df: pd.DataFrame, max_unique: int = 20) -> Dict[str, pd.DataFrame]:
    """Calculate frequency and relative frequency distributions for categorical variables."""
    cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns
    tables = {}

    for col in cat_cols:
        vc = df[col].value_counts(dropna=False).head(max_unique)
        pct = (vc / len(df) * 100).round(2)
        tbl = pd.DataFrame({
            "Value": vc.index.astype(str),
            "Frequency": vc.values,
            "Percentage (%)": pct.values
        })
        tables[col] = tbl

    return tables

def get_numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Generate high-level quick overview table of numeric features."""
    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty:
        return pd.DataFrame()
    return num_df.describe().T.round(2)
