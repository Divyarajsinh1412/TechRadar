"""
TechRadar — Data Aggregation and Group Operations Module
Demonstrates CSA4503 Module 4 core syllabus topics:
- GroupBy split-apply-combine
- Pivot tables with margins
- Cross-tabulation (pd.crosstab)
- Hierarchical indexing (MultiIndex) and unstack/stack
- Data reshaping (melting and pivoting)
- Merging and combining datasets
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional, List

def perform_groupby_analysis(
    df: pd.DataFrame, 
    group_cols: List[str], 
    agg_dict: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Perform GroupBy split-apply-combine with single or multiple aggregate functions.
    """
    if not group_cols or not set(group_cols).issubset(set(df.columns)):
        return pd.DataFrame()

    if agg_dict is None:
        agg_dict = {
            "job_postings": ["sum", "mean", "count"],
            "average_salary": ["mean", "median", "std"],
            "developer_interest": "mean"
        }
        # Filter agg_dict to columns present in df
        agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}

    grouped = df.groupby(group_cols).agg(agg_dict)
    return grouped

def create_pivot_table(
    df: pd.DataFrame,
    index_col: str,
    column_col: str,
    value_col: str = "average_salary",
    agg_func: str = "mean",
    margins: bool = True
) -> pd.DataFrame:
    """
    Generate a pivot table using pd.pivot_table.
    Supports margins ('Total') and multiple aggregation functions.
    """
    if not {index_col, column_col, value_col}.issubset(set(df.columns)):
        return pd.DataFrame()

    pivot = pd.pivot_table(
        df,
        values=value_col,
        index=index_col,
        columns=column_col,
        aggfunc=agg_func,
        margins=margins,
        margins_name="Total"
    )
    if agg_func in ["mean", "median", "std"]:
        pivot = pivot.round(2)
    return pivot

def create_crosstab_analysis(
    df: pd.DataFrame,
    row_col: str,
    col_col: str,
    normalize: Optional[str] = None,
    margins: bool = True
) -> pd.DataFrame:
    """
    Compute cross-tabulation table using pd.crosstab().
    Supports normalize='all', 'index', 'columns', or None.
    """
    if not {row_col, col_col}.issubset(set(df.columns)):
        return pd.DataFrame()

    norm_param = None if normalize == "None" or not normalize else normalize
    ct = pd.crosstab(
        index=df[row_col],
        columns=df[col_col],
        normalize=norm_param,
        margins=margins,
        margins_name="Total"
    )
    if norm_param is not None:
        ct = (ct * 100).round(2)
    return ct

def demonstrate_hierarchical_indexing(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Demonstrate Hierarchical MultiIndex operations:
    1. MultiIndex DataFrame (Category -> Technology)
    2. Unstacking (innermost level pivoted to columns)
    3. Stacking (columns reshaped back to index)
    """
    if not {"category", "technology"}.issubset(set(df.columns)):
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    agg_dict = {"job_postings": "sum"}
    if "average_salary" in df.columns:
        agg_dict["average_salary"] = "mean"

    multi_df = df.groupby(["category", "technology"]).agg(agg_dict).round(2)

    # Cross-level demonstration for unstack/stack
    if "year" in df.columns:
        cat_year = df.groupby(["category", "year"])["job_postings"].sum()
        unstacked = cat_year.unstack(level="year").fillna(0).astype(int)
        restacked = unstacked.stack(future_stack=True)
    else:
        unstacked = pd.DataFrame()
        restacked = pd.DataFrame()

    return multi_df, unstacked, restacked

def demonstrate_melt_and_pivot(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Demonstrate pd.melt (wide-to-long) and df.pivot (long-to-wide).
    """
    sample = df.groupby(["technology", "year"])["job_postings"].mean().reset_index()
    # Wide format via pivot
    wide_df = sample.pivot(index="technology", columns="year", values="job_postings").round(0).fillna(0)
    
    # Long format via melt
    long_df = pd.melt(
        wide_df.reset_index(),
        id_vars=["technology"],
        var_name="year",
        value_name="mean_job_postings"
    )
    return wide_df, long_df

def demonstrate_dataset_merging(df: pd.DataFrame) -> pd.DataFrame:
    """
    Demonstrate pd.merge by combining technology metrics with metadata (type, license, creator).
    """
    meta_records = [
        {"technology": "Python", "type": "Interpreted", "license": "PSF", "ecosystem_rank": 1},
        {"technology": "Java", "type": "Compiled (JVM)", "license": "GPL/Commercial", "ecosystem_rank": 2},
        {"technology": "JavaScript", "type": "Interpreted/JIT", "license": "ECMA/MIT", "ecosystem_rank": 3},
        {"technology": "TypeScript", "type": "Transpiled", "license": "Apache 2.0", "ecosystem_rank": 4},
        {"technology": "Rust", "type": "Compiled Native", "license": "MIT / Apache 2.0", "ecosystem_rank": 5},
        {"technology": "Go", "type": "Compiled Native", "license": "BSD", "ecosystem_rank": 6},
        {"technology": "Docker", "type": "Container Engine", "license": "Apache 2.0", "ecosystem_rank": 7},
        {"technology": "Kubernetes", "type": "Orchestrator", "license": "Apache 2.0", "ecosystem_rank": 8},
        {"technology": "PostgreSQL", "type": "RDBMS", "license": "PostgreSQL License", "ecosystem_rank": 9},
        {"technology": "PyTorch", "type": "ML Framework", "license": "BSD", "ecosystem_rank": 10}
    ]
    meta_df = pd.DataFrame(meta_records)

    base = df.groupby("technology")["job_postings"].sum().reset_index()
    merged = pd.merge(base, meta_df, on="technology", how="inner")
    return merged.sort_values("job_postings", ascending=False)
