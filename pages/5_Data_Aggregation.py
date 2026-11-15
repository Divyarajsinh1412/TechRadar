"""
TechRadar — Page 5: Data Aggregation & Group Operations
Redesigned with SaaS UI/UX Architecture.
Demonstrates CSA4503 Module 4 GroupBy, Pivot Tables, Crosstab, MultiIndex, and Reshaping.
"""

import os
import streamlit as st
import pandas as pd
from modules.data_loader import load_dataset
from modules.aggregation import (
    perform_groupby_analysis,
    create_pivot_table,
    create_crosstab_analysis,
    demonstrate_hierarchical_indexing,
    demonstrate_melt_and_pivot,
    demonstrate_dataset_merging
)
from modules.ui_components import (
    render_page_header,
    render_sidebar_branding,
    render_sidebar_footer,
    render_callout
)

st.set_page_config(page_title="Data Aggregation — TechRadar", page_icon="🗂️", layout="wide")

# Inject styling
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_branding()
    st.markdown("#### ⚙️ Aggregation Scope")
    st.caption("Customize grouping keys, pivot variables, and cross-tabulation normalization.")
    render_sidebar_footer()

# Load dataset
if "cleaned_df" in st.session_state and st.session_state.cleaned_df is not None:
    df = st.session_state.cleaned_df
    status_label = "● Dataset: Cleaned"
else:
    df = load_dataset()
    status_label = "● Dataset: Sample"

render_page_header(
    title="Data Aggregation & Group Operations",
    subtitle="Practical execution of GroupBy split-apply-combine, pivot tables, cross-tabulations, hierarchical indexing, and data merging.",
    badge_text="CSA4503 Module 4",
    status_pill=status_label
)

render_callout(
    text="Demonstrates core Pandas group operations: <code>df.groupby(['cat', 'tech']).agg(...)</code>, "
         "<code>pd.pivot_table(margins=True)</code>, <code>pd.crosstab(normalize='all')</code>, "
         "hierarchical <code>MultiIndex</code> with <code>.unstack()</code> and <code>.stack()</code>, "
         "wide-to-long reshaping with <code>pd.melt()</code>, and relational combining via <code>pd.merge()</code>.",
    title="Curriculum Learning Objectives",
    kind="info"
)

# Tabs
tab_groupby, tab_pivot, tab_crosstab, tab_multiindex, tab_reshape, tab_merge = st.tabs([
    "🧩 GroupBy Split-Apply-Combine",
    "📊 Pivot Tables",
    "📐 Cross-Tabulation (crosstab)",
    "🌲 Hierarchical MultiIndex",
    "🔄 Reshaping (Melt & Pivot)",
    "🔗 Data Merging (pd.merge)"
])

with tab_groupby:
    st.markdown("#### GroupBy Split-Apply-Combine Mechanics")
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        group_keys = st.multiselect("Grouping Keys:", ["category", "technology", "year"], default=["category"])
    with g_col2:
        agg_metrics = st.multiselect("Metrics to Aggregate:", ["job_postings", "average_salary", "developer_interest", "growth_rate"], default=["job_postings", "average_salary"])

    if group_keys and agg_metrics:
        agg_spec = {col: ["sum", "mean", "count"] if col == "job_postings" else ["mean", "median"] for col in agg_metrics}
        grouped_result = df.groupby(group_keys).agg(agg_spec).round(2)
        st.dataframe(grouped_result, use_container_width=True)
    else:
        st.info("Select at least one group key and metric.")

with tab_pivot:
    st.markdown("#### Pivot Tables (`pd.pivot_table()`)")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        p_idx = st.selectbox("Row Index:", ["category", "technology"], index=0)
    with p2:
        p_c = st.selectbox("Column Header:", ["year", "category"], index=0)
    with p3:
        p_v = st.selectbox("Value Field:", ["average_salary", "job_postings", "developer_interest"], index=0)
    with p4:
        p_f = st.selectbox("Function:", ["mean", "sum", "median", "count"], index=0)

    if p_idx != p_c:
        p_res = create_pivot_table(df, index_col=p_idx, column_col=p_c, value_col=p_v, agg_func=p_f, margins=True)
        st.dataframe(p_res, use_container_width=True)
    else:
        st.warning("Row Index and Column Header must be distinct.")

with tab_crosstab:
    st.markdown("#### Cross-Tabulation Frequency Analysis (`pd.crosstab()`)")
    c1, c2, c3 = st.columns(3)
    with c1:
        r_var = st.selectbox("Row Dimension:", ["category", "year"], index=0)
    with c2:
        c_var = st.selectbox("Column Dimension:", ["year", "category"], index=1)
    with c3:
        norm_opt = st.selectbox("Normalization:", ["None", "index", "columns", "all"], index=0)

    if r_var != c_var:
        ct_res = create_crosstab_analysis(df, row_col=r_var, col_col=c_var, normalize=norm_opt, margins=True)
        st.dataframe(ct_res, use_container_width=True)
    else:
        st.warning("Row and Column variables must be distinct.")

with tab_multiindex:
    st.markdown("#### Hierarchical MultiIndex & Index Pivoting")
    multi_df, unstacked, restacked = demonstrate_hierarchical_indexing(df)

    st.markdown("##### 1. MultiIndex Grouped Structure (Category × Technology):")
    st.dataframe(multi_df.head(15), use_container_width=True)

    st.markdown("##### 2. Unstacked Representation (`.unstack(level='year')`):")
    st.dataframe(unstacked, use_container_width=True)

    st.markdown("##### 3. Restacked Representation (`.stack()`):")
    st.dataframe(restacked.head(15), use_container_width=True)

with tab_reshape:
    st.markdown("#### Reshaping: Wide vs. Long Formats (`df.pivot()` & `pd.melt()`)")
    wide_df, long_df = demonstrate_melt_and_pivot(df)
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("##### Wide Format (Pivoted):")
        st.dataframe(wide_df.head(12), use_container_width=True)
    with r2:
        st.markdown("##### Long Format (Melted):")
        st.dataframe(long_df.head(12), use_container_width=True)

with tab_merge:
    st.markdown("#### Combining Datasets with `pd.merge()`")
    merged_data = demonstrate_dataset_merging(df)
    st.dataframe(merged_data, use_container_width=True)
