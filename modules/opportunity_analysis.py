"""
TechRadar — Future Technology Opportunity Analysis Module
Calculates an explainable Technology Opportunity Score (0–100) using
normalized indicators and categorizes technologies into 5 analytical tiers.
Supports Multi-Period change detection (Daily, Weekly, Monthly) and confidence scoring.

NOTICE:
Opportunity scores are analytical syntheses of observed historical metrics
and do not represent guaranteed future job-market popularity.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

def min_max_normalize(series: pd.Series) -> pd.Series:
    """Min-max normalize a numeric series to 0–100 scale."""
    s = series.fillna(series.median())
    min_val = s.min()
    max_val = s.max()
    if max_val == min_val:
        return pd.Series(50.0, index=series.index)
    return ((s - min_val) / (max_val - min_val) * 100).round(2)

def calculate_opportunity_scores(
    df: pd.DataFrame,
    weight_job: float = 0.35,
    weight_dev: float = 0.25,
    weight_adopt: float = 0.20,
    weight_growth: float = 0.20,
    frequency: str = "Monthly"
) -> pd.DataFrame:
    """
    Calculate explainable Technology Opportunity Score (0–100):
      Score = (Norm_Jobs * w_job) + (Norm_Dev * w_dev) + (Norm_Adopt * w_adopt) + (Norm_Growth * w_growth)
    Keeps Opportunity Score (FOI) and Confidence Score separate.
    Categorizes technologies into:
      1. Emerging
      2. High-Demand
      3. Low-Demand / High-Growth
      4. Established
      5. Monitor
    """
    if "technology" not in df.columns:
        return pd.DataFrame()

    # Aggregate latest / representative metrics per technology
    tech_summary = df.groupby(["technology", "category"]).agg({
        "job_postings": ["mean", "count", "std"],
        "developer_interest": "mean",
        "company_adoption": "mean",
        "growth_rate": "mean",
        "average_salary": "mean" if "average_salary" in df.columns else "count"
    })
    
    # Flatten columns
    tech_summary.columns = [
        "job_postings", "obs_count", "job_std", "developer_interest",
        "company_adoption", "growth_rate", "average_salary"
    ]
    tech_summary = tech_summary.reset_index()

    # Normalize metrics to 0-100
    tech_summary["norm_jobs"] = min_max_normalize(tech_summary["job_postings"])
    tech_summary["norm_dev"] = min_max_normalize(tech_summary["developer_interest"])
    tech_summary["norm_adopt"] = min_max_normalize(tech_summary["company_adoption"])
    tech_summary["norm_growth"] = min_max_normalize(tech_summary["growth_rate"])

    # Calculate weighted Opportunity Score (FOI)
    tech_summary["opportunity_score"] = (
        (tech_summary["norm_jobs"] * weight_job) +
        (tech_summary["norm_dev"] * weight_dev) +
        (tech_summary["norm_adopt"] * weight_adopt) +
        (tech_summary["norm_growth"] * weight_growth)
    ).round(2)

    # Calculate Confidence Score (0–100) kept separate from FOI
    # Based on observation density and signal variance
    max_obs = tech_summary["obs_count"].max() if tech_summary["obs_count"].max() > 0 else 1
    density_factor = (tech_summary["obs_count"] / max_obs) * 50.0
    stability_factor = 50.0 - np.clip(tech_summary["job_std"].fillna(0) / (tech_summary["job_postings"] + 1) * 25.0, 0, 30.0)
    tech_summary["confidence_score"] = (density_factor + stability_factor).clip(30.0, 98.0).round(1)

    # Classifications
    def classify(row):
        jobs = row["norm_jobs"]
        growth = row["norm_growth"]
        dev = row["norm_dev"]
        adopt = row["norm_adopt"]

        if jobs < 45 and (growth >= 60 or dev >= 70):
            return "Low-Demand / High-Growth"
        elif growth >= 60 and dev >= 65:
            return "Emerging"
        elif jobs >= 60 and adopt >= 65:
            return "High-Demand"
        elif adopt >= 70 and jobs >= 50:
            return "Established"
        else:
            return "Monitor"

    tech_summary["classification"] = tech_summary.apply(classify, axis=1)

    # Calculate Multi-Period delta changes if date column is available
    tech_summary["score_change"] = 0.0
    if "date" in df.columns:
        date_series = pd.to_datetime(df["date"], errors="coerce").dropna()
        if not date_series.empty:
            dates_sorted = sorted(date_series.unique())
            if len(dates_sorted) >= 2:
                latest_d = dates_sorted[-1]
                prev_d = dates_sorted[-2]
                
                latest_slice = df[df["date"] == latest_d.strftime("%Y-%m-%d")]
                prev_slice = df[df["date"] == prev_d.strftime("%Y-%m-%d")]
                
                prev_jobs = prev_slice.set_index("technology")["job_postings"].to_dict()
                latest_jobs = latest_slice.set_index("technology")["job_postings"].to_dict()

                def calc_delta(t):
                    pj = prev_jobs.get(t)
                    lj = latest_jobs.get(t)
                    if pj is not None and lj is not None and pj > 0:
                        return round(((lj - pj) / pj) * 5.0, 2) # scaled opportunity point delta
                    return 0.0

                tech_summary["score_change"] = tech_summary["technology"].apply(calc_delta)

    # Momentum classification to prevent mistaking short-term spikes for sustained trends
    def momentum_tier(row):
        chg = row["score_change"]
        conf = row["confidence_score"]
        if chg > 3.0 and conf < 65.0:
            return "Short-Term Spike"
        elif chg > 1.5 and conf >= 65.0:
            return "Sustained Acceleration"
        elif chg < -1.5:
            return "Cooling Activity"
        else:
            return "Stable Momentum"

    tech_summary["momentum_type"] = tech_summary.apply(momentum_tier, axis=1)

    return tech_summary.sort_values(by="opportunity_score", ascending=False).reset_index(drop=True)

def get_classification_summary(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize counts, average salary, and top technologies per classification tier."""
    if scored_df.empty or "classification" not in scored_df.columns:
        return pd.DataFrame()

    summary = scored_df.groupby("classification").agg(
        Count=("technology", "count"),
        Avg_Score=("opportunity_score", "mean"),
        Avg_Confidence=("confidence_score", "mean") if "confidence_score" in scored_df.columns else ("opportunity_score", "mean"),
        Avg_Salary=("average_salary", "mean") if "average_salary" in scored_df.columns else ("opportunity_score", "count"),
        Technologies=("technology", lambda x: ", ".join(list(x)[:4]))
    ).reset_index()

    summary["Avg_Score"] = summary["Avg_Score"].round(2)
    if "Avg_Confidence" in summary.columns:
        summary["Avg_Confidence"] = summary["Avg_Confidence"].round(1)
    if "average_salary" in scored_df.columns:
        summary["Avg_Salary"] = summary["Avg_Salary"].round(2)

    return summary.sort_values("Avg_Score", ascending=False)
