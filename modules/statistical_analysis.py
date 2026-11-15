"""
TechRadar — Statistical Analysis Module
Demonstrates CSA4503 statistical concepts:
- Central Tendency: Mean, Median, Mode
- Dispersion: Variance, Standard Deviation, Range, Quartiles, IQR
- Distribution Shape: Skewness, Kurtosis (SciPy)
- Correlation Analysis: Pearson & Spearman
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, Tuple

def compute_detailed_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute comprehensive statistical indicators for all numeric variables.
    Demonstrates central tendency, dispersion, quartiles, and shape metrics.
    """
    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty:
        return pd.DataFrame()

    results = []
    for col in num_df.columns:
        s = num_df[col].dropna()
        n = len(s)
        if n == 0:
            continue

        mean_val = float(s.mean())
        median_val = float(s.median())
        
        # Mode
        mode_res = s.mode()
        mode_val = float(mode_res.iloc[0]) if not mode_res.empty else np.nan

        std_val = float(s.std())
        var_val = float(s.var())
        min_val = float(s.min())
        max_val = float(s.max())
        range_val = max_val - min_val

        q1 = float(s.quantile(0.25))
        q2 = median_val
        q3 = float(s.quantile(0.75))
        iqr = q3 - q1

        skew_val = float(stats.skew(s)) if n > 2 else np.nan
        kurt_val = float(stats.kurtosis(s)) if n > 3 else np.nan

        results.append({
            "Feature": col,
            "Count": n,
            "Mean": round(mean_val, 2),
            "Median": round(median_val, 2),
            "Mode": round(mode_val, 2),
            "Std Dev": round(std_val, 2),
            "Variance": round(var_val, 2),
            "Min": round(min_val, 2),
            "Q1 (25%)": round(q1, 2),
            "Median (Q2)": round(q2, 2),
            "Q3 (75%)": round(q3, 2),
            "Max": round(max_val, 2),
            "Range": round(range_val, 2),
            "IQR": round(iqr, 2),
            "Skewness": round(skew_val, 4),
            "Kurtosis": round(kurt_val, 4)
        })

    return pd.DataFrame(results)

def get_correlation_matrix(df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """
    Compute correlation matrix for numeric columns using Pearson or Spearman method.
    """
    num_df = df.select_dtypes(include=[np.number])
    if num_df.shape[1] < 2:
        return pd.DataFrame()
    return num_df.corr(method=method).round(4)

def calculate_column_distribution_metrics(series: pd.Series) -> Dict[str, Any]:
    """Calculate single-column distribution metrics for display and interpretation."""
    s = series.dropna()
    if len(s) == 0:
        return {}
    
    mean = float(s.mean())
    median = float(s.median())
    std = float(s.std())
    skew = float(stats.skew(s)) if len(s) > 2 else 0.0
    kurt = float(stats.kurtosis(s)) if len(s) > 3 else 0.0

    # Interpretation
    if abs(skew) < 0.5:
        skew_desc = "Fairly Symmetrical"
    elif skew > 0.5:
        skew_desc = "Positively Skewed (Right-tailed)"
    else:
        skew_desc = "Negatively Skewed (Left-tailed)"

    if kurt > 0.5:
        kurt_desc = "Leptokurtic (Heavy tails, sharp peak)"
    elif kurt < -0.5:
        kurt_desc = "Platykurtic (Light tails, flatter peak)"
    else:
        kurt_desc = "Mesokurtic (Normal-like peak)"

    return {
        "mean": mean,
        "median": median,
        "std": std,
        "skewness": skew,
        "skew_desc": skew_desc,
        "kurtosis": kurt,
        "kurt_desc": kurt_desc,
        "min": float(s.min()),
        "max": float(s.max())
    }
