"""
TechRadar — Time Series Analysis Module
Demonstrates CSA4503 Module 4 time-series concepts:
- Datetime indexing and date ranges
- Resampling (Monthly 'ME', Quarterly 'QE', Yearly 'YE')
- Rolling window functions and moving averages (3-mo, 6-mo)
- Time shifting and lag growth analysis (MoM, QoQ, YoY)
- Periods and period arithmetic
- Time-zone conversion
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional, List

def prepare_datetime_series(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """
    Parse date column into datetime64[ns] and sort chronologically.
    Extract year, month, quarter, and period identifiers.
    """
    ts_df = df.copy()
    if date_col not in ts_df.columns:
        return ts_df

    ts_df[date_col] = pd.to_datetime(ts_df[date_col], errors="coerce")
    ts_df = ts_df.dropna(subset=[date_col]).sort_values(by=date_col)
    
    ts_df["year_extracted"] = ts_df[date_col].dt.year
    ts_df["quarter_extracted"] = ts_df[date_col].dt.to_period("Q").astype(str)
    ts_df["month_extracted"] = ts_df[date_col].dt.month
    ts_df["period_m"] = ts_df[date_col].dt.to_period("M")
    
    return ts_df

def resample_technology_metric(
    df: pd.DataFrame,
    tech_name: Optional[str] = None,
    category_name: Optional[str] = None,
    freq: str = "ME",
    metric: str = "job_postings"
) -> pd.DataFrame:
    """
    Resample time series data to specified frequency ('ME' Month-End, 'QE' Quarter-End, 'YE' Year-End).
    Preserves true gaps without inventing data.
    """
    filtered = df.copy()
    if tech_name and tech_name != "All":
        filtered = filtered[filtered["technology"] == tech_name]
    if category_name and category_name != "All":
        filtered = filtered[filtered["category"] == category_name]

    if filtered.empty or "date" not in filtered.columns:
        return pd.DataFrame()

    filtered["date"] = pd.to_datetime(filtered["date"], errors="coerce")
    filtered = filtered.dropna(subset=["date"]).set_index("date").sort_index()

    agg_rules = {metric: "sum" if metric == "job_postings" else "mean"}
    if "average_salary" in filtered.columns and metric != "average_salary":
        agg_rules["average_salary"] = "mean"

    resampled = filtered.resample(freq).agg(agg_rules)
    if metric in resampled.columns and metric != "job_postings":
        resampled[metric] = resampled[metric].round(2)
    if "average_salary" in resampled.columns:
        resampled["average_salary"] = resampled["average_salary"].round(2)

    return resampled

def compute_rolling_and_lags(
    resampled_df: pd.DataFrame,
    metric_col: str = "job_postings",
    windows: List[int] = [3, 6]
) -> pd.DataFrame:
    """
    Compute rolling moving averages, rolling std, shifting, and lag growth metrics:
    - Moving Averages: rolling(window).mean()
    - Rolling Volatility: rolling(window).std()
    - Shifting: shift(1) for MoM, shift(3) for QoQ
    - Growth Rates: pct_change()
    """
    ts = resampled_df.copy()
    if metric_col not in ts.columns:
        return ts

    # Moving window functions
    for w in windows:
        ts[f"MA_{w}"] = ts[metric_col].rolling(window=w).mean().round(2)
        ts[f"Rolling_Std_{w}"] = ts[metric_col].rolling(window=w).std().round(2)

    # Shifting & Lags
    ts["Lag_1"] = ts[metric_col].shift(1)
    ts["Lag_3"] = ts[metric_col].shift(3)

    # Percentage changes
    ts["MoM_Growth_Pct"] = ((ts[metric_col] - ts["Lag_1"]) / ts["Lag_1"] * 100).replace([np.inf, -np.inf], np.nan).round(2)
    ts["QoQ_Growth_Pct"] = ((ts[metric_col] - ts["Lag_3"]) / ts["Lag_3"] * 100).replace([np.inf, -np.inf], np.nan).round(2)

    return ts

def demonstrate_period_arithmetic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Demonstrate Pandas Period and Period Arithmetic (e.g. period + 1 month).
    """
    if "date" not in df.columns:
        return pd.DataFrame()

    sub = df[["technology", "date", "job_postings"]].dropna().head(10).copy()
    sub["date"] = pd.to_datetime(sub["date"])
    
    # Period representations
    sub["Monthly_Period"] = sub["date"].dt.to_period("M")
    sub["Next_Month_Period"] = sub["Monthly_Period"] + 1
    sub["Quarterly_Period"] = sub["date"].dt.to_period("Q")
    sub["Next_Quarter_Period"] = sub["Quarterly_Period"] + 1

    return sub

def demonstrate_timezone_handling(df: pd.DataFrame) -> pd.DataFrame:
    """
    Demonstrate tz_localize and tz_convert functionality in Pandas.
    """
    if "date" not in df.columns:
        return pd.DataFrame()

    sub = df[["technology", "date", "job_postings"]].dropna().head(5).copy()
    sub["date"] = pd.to_datetime(sub["date"])
    
    # Localize to UTC then convert to US/Eastern and Asia/Kolkata
    sub["UTC_Timestamp"] = sub["date"].dt.tz_localize("UTC")
    sub["US_Eastern"] = sub["UTC_Timestamp"].dt.tz_convert("US/Eastern")
    sub["Asia_Kolkata"] = sub["UTC_Timestamp"].dt.tz_convert("Asia/Kolkata")

    # Format for display
    sub["UTC_Timestamp"] = sub["UTC_Timestamp"].astype(str)
    sub["US_Eastern"] = sub["US_Eastern"].astype(str)
    sub["Asia_Kolkata"] = sub["Asia_Kolkata"].astype(str)

    return sub
