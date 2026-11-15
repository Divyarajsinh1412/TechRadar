"""
TechRadar — Page 1: Data Explorer
Redesigned with SaaS UI/UX Architecture.
Demonstrates CSA4503 Module 1 & 2 structural inspection and data profiling.
"""

import os
import streamlit as st
import pandas as pd
from modules.data_loader import load_dataset, get_dataset_metadata
from modules.exploratory_analysis import get_structural_profile, get_numeric_summary
from modules.ui_components import (
    render_page_header,
    render_kpi_card,
    render_sidebar_branding,
    render_sidebar_footer,
    render_callout,
    render_database_environment_badge
)

st.set_page_config(page_title="Data Explorer — TechRadar", page_icon="🔍", layout="wide")

# Inject styling
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    render_sidebar_branding()
    st.markdown("#### 📁 Ingestion Options")
    uploaded_file = st.file_uploader("Upload CSV or Excel:", type=["csv", "xlsx", "xls"], key="exp_up")
    if st.button("🔄 Reset to Default Sample", use_container_width=True):
        st.session_state.cleaned_df = None
        st.rerun()
    render_sidebar_footer()

# Determine active dataset
if "cleaned_df" in st.session_state and st.session_state.cleaned_df is not None:
    df = st.session_state.cleaned_df
    status_label = "● Dataset: Cleaned"
elif uploaded_file is not None:
    df = load_dataset(uploaded_file)
    status_label = "● Dataset: Uploaded"
else:
    df = load_dataset()
    status_label = "● Dataset: Sample"

metadata = get_dataset_metadata(df)
profile = get_structural_profile(df)

# Page Header
render_page_header(
    title="Data Explorer & Ingestion",
    subtitle="Inspect dataset dimensions, column data types, missing cell profiles, and duplicate records.",
    badge_text="CSA4503 Module 1 & 2",
    status_pill=status_label
)

# Cloud Database Environment Status
render_database_environment_badge()

# Academic Callout
render_callout(
    text="Demonstrates core Pandas structural commands: <code>pd.read_csv()</code>, <code>pd.read_excel()</code>, "
         "<code>df.shape</code>, <code>df.info()</code>, <code>df.dtypes</code>, <code>df.isnull().sum()</code>, "
         "and <code>df.duplicated()</code>.",
    title="Syllabus Implementation (Data Science Process & EDA)",
    kind="info"
)

# Responsive Metric Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(render_kpi_card("Total Rows", f"{metadata['rows']:,}", "Observations", "📄", "#38bdf8"), unsafe_allow_html=True)
with c2:
    st.markdown(render_kpi_card("Total Columns", f"{metadata['columns']}", "Variables", "🏷️", "#0ea5e9"), unsafe_allow_html=True)
with c3:
    st.markdown(render_kpi_card("Missing Cells", f"{metadata['total_missing']:,}", "Null Values", "⚠️", "#f59e0b" if metadata['total_missing'] > 0 else "#10b981"), unsafe_allow_html=True)
with c4:
    st.markdown(render_kpi_card("Duplicate Rows", f"{metadata['duplicate_rows']:,}", "Identical Records", "👥", "#f43f5e" if metadata['duplicate_rows'] > 0 else "#10b981"), unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# Tabs
tab_data, tab_types, tab_missing, tab_dups, tab_stats = st.tabs([
    "📋 Interactive Dataset Viewer",
    "🏷️ Column Types & Health",
    "⚠️ Missing Values Profile",
    "👥 Duplicate Records",
    "📈 Quick Numeric Summary"
])

with tab_data:
    st.markdown("#### Interactive Dataset View")
    f_col1, f_col2 = st.columns([3, 1])
    with f_col1:
        selected_cols = st.multiselect("Visible Columns:", options=list(df.columns), default=list(df.columns))
    with f_col2:
        search_query = st.text_input("Search (any column):", placeholder="e.g. Python, Cloud")

    display_df = df[selected_cols]
    if search_query:
        mask = display_df.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
        display_df = display_df[mask]

    st.dataframe(display_df, use_container_width=True, height=420)
    st.caption(f"Showing {len(display_df):,} of {len(df):,} total records.")

with tab_types:
    st.markdown("#### Column Architecture & Data Types (`df.dtypes` & `df.info()`)")
    st.dataframe(profile["columns_df"], use_container_width=True)

with tab_missing:
    st.markdown("#### Missing Values Detection (`df.isnull().sum()`)")
    missing_df = profile["columns_df"][profile["columns_df"]["Null Count"] > 0]
    if not missing_df.empty:
        st.dataframe(missing_df[["Column", "Null Count", "Null (%)", "Data Type"]], use_container_width=True)
        st.bar_chart(missing_df.set_index("Column")["Null Count"])
    else:
        st.success("✅ No missing values detected in the active dataset!")

with tab_dups:
    st.markdown("#### Duplicate Records (`df.duplicated()`)")
    duplicate_mask = df.duplicated(keep=False)
    dup_rows = df[duplicate_mask]
    if not dup_rows.empty:
        st.warning(f"Found {len(dup_rows):,} duplicate records.")
        st.dataframe(dup_rows, use_container_width=True)
    else:
        st.success("✅ No duplicate records detected in the active dataset!")

with tab_stats:
    st.markdown("#### High-Level Descriptive Summary (`df.describe().T`)")
    summary = get_numeric_summary(df)
    if not summary.empty:
        st.dataframe(summary, use_container_width=True)
    else:
        st.info("No numeric columns available.")
