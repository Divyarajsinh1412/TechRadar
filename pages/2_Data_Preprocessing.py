"""
TechRadar — Page 2: Data Cleaning & Preprocessing
Redesigned with SaaS UI/UX Architecture.
Demonstrates CSA4503 Module 2 & 3 data hygiene, imputation, and IQR outlier detection.
"""

import os
import streamlit as st
import pandas as pd
from modules.data_loader import load_dataset, get_dataset_metadata
from modules.data_cleaning import (
    remove_duplicates,
    impute_missing_values,
    normalize_technology_names,
    convert_data_types,
    detect_iqr_outliers,
    filter_iqr_outliers,
    remove_columns
)
from modules.ui_components import (
    render_page_header,
    render_kpi_card,
    render_sidebar_branding,
    render_sidebar_footer,
    render_callout
)

st.set_page_config(page_title="Data Preprocessing — TechRadar", page_icon="🧹", layout="wide")

# Inject styling
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load base raw data
if "raw_df" in st.session_state and st.session_state.raw_df is not None:
    raw_df = st.session_state.raw_df
else:
    raw_df = load_dataset()
    st.session_state.raw_df = raw_df

# Sidebar Pipeline Controls
with st.sidebar:
    render_sidebar_branding()
    st.markdown("#### ⚙️ Pipeline Controls")
    
    do_dedup = st.checkbox("1. Remove Duplicates", value=True)
    
    st.markdown("---")
    st.markdown("##### 2. Missing Value Imputation")
    num_strategy = st.selectbox(
        "Numerical Strategy:",
        ["median", "mean", "constant_zero", "drop", "none"],
        index=0
    )
    cat_strategy = st.selectbox(
        "Categorical Strategy:",
        ["mode", "unknown", "drop", "none"],
        index=0
    )

    st.markdown("---")
    do_normalize = st.checkbox("3. Standardize Tech Names", value=True)
    do_typecast = st.checkbox("4. Enforce Data Types", value=True)
    
    st.markdown("---")
    st.markdown("##### 5. IQR Outlier Filtering")
    do_iqr = st.checkbox("Filter Outliers via IQR", value=False)
    iqr_col = st.selectbox("Target Column:", ["average_salary", "job_postings"], index=0)

    st.markdown("---")
    cols_to_drop = st.multiselect("6. Drop Columns:", options=list(raw_df.columns), default=[])
    
    render_sidebar_footer()

# Execute Pipeline
cleaned_df = raw_df.copy()
audit_log = []

if do_dedup:
    cleaned_df, dups_removed = remove_duplicates(cleaned_df)
    audit_log.append(f"Removed <b>{dups_removed}</b> duplicate rows.")

cleaned_df, imp_logs = impute_missing_values(cleaned_df, numerical_strategy=num_strategy, categorical_strategy=cat_strategy)
for col, log_msg in imp_logs.items():
    audit_log.append(f"<b>{col}:</b> {log_msg}")

if do_normalize:
    cleaned_df, norm_count = normalize_technology_names(cleaned_df)
    audit_log.append(f"Standardized <b>{norm_count}</b> non-canonical technology aliases.")

if do_typecast:
    cleaned_df, type_logs = convert_data_types(cleaned_df)
    for t_log in type_logs:
        audit_log.append(f"{t_log}")

outliers_df, iqr_metrics = detect_iqr_outliers(cleaned_df, col=iqr_col)
if do_iqr:
    cleaned_df = filter_iqr_outliers(cleaned_df, col=iqr_col)
    audit_log.append(f"Filtered <b>{iqr_metrics.get('outlier_count', 0)}</b> outliers from <code>{iqr_col}</code>.")

if cols_to_drop:
    cleaned_df = remove_columns(cleaned_df, cols_to_drop)
    audit_log.append(f"Dropped {len(cols_to_drop)} columns: {', '.join(cols_to_drop)}.")

# Page Header
render_page_header(
    title="Data Cleaning & Preprocessing",
    subtitle="Interactive transformation pipeline with live before-and-after auditing and IQR outlier diagnostics.",
    badge_text="CSA4503 Module 2 & 3",
    status_pill="● Status: Preprocessing Engine Active"
)

# Academic Callout
render_callout(
    text="Implements textbook data hygiene algorithms: duplicate purging (<code>df.drop_duplicates()</code>), "
         "imputation with measures of central tendency (Mean/Median/Mode), canonical alias mapping, "
         "and outlier rejection using Tukey's Interquartile Range (IQR) rule: <code>[Q1 - 1.5×IQR, Q3 + 1.5×IQR]</code>.",
    title="Curriculum Learning Objectives",
    kind="info"
)

# Before vs After Metrics
raw_meta = get_dataset_metadata(raw_df)
clean_meta = get_dataset_metadata(cleaned_df)

c1, c2, c3, c4 = st.columns(4)
with c1:
    diff_rows = clean_meta['rows'] - raw_meta['rows']
    delta_str = f"{diff_rows:+d} rows" if diff_rows != 0 else "Unchanged"
    st.markdown(render_kpi_card("Active Rows", f"{clean_meta['rows']:,}", delta_str, "📄", "#38bdf8"), unsafe_allow_html=True)
with c2:
    diff_null = clean_meta['total_missing'] - raw_meta['total_missing']
    delta_str = f"{diff_null:+d} nulls" if diff_null != 0 else "0 missing"
    st.markdown(render_kpi_card("Missing Cells", f"{clean_meta['total_missing']:,}", delta_str, "⚠️", "#10b981" if clean_meta['total_missing'] == 0 else "#f59e0b"), unsafe_allow_html=True)
with c3:
    st.markdown(render_kpi_card("Duplicates", f"{clean_meta['duplicate_rows']:,}", f"-{raw_meta['duplicate_rows']} removed", "👥", "#10b981"), unsafe_allow_html=True)
with c4:
    diff_cols = clean_meta['columns'] - raw_meta['columns']
    delta_str = f"{diff_cols:+d} columns" if diff_cols != 0 else "Preserved"
    st.markdown(render_kpi_card("Total Columns", f"{clean_meta['columns']}", delta_str, "🏷️", "#0ea5e9"), unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# Tabs
tab_audit, tab_iqr, tab_preview, tab_commit, tab_real_jobs = st.tabs([
    "📋 Execution Audit Log",
    "📐 IQR Outlier Diagnostics",
    "👁️ Cleaned Dataset Preview",
    "💾 Commit & Download",
    "💼 Ingest Real Job Postings CSV"
])

with tab_audit:
    st.markdown("#### Applied Preprocessing Operations:")
    if audit_log:
        for item in audit_log:
            st.markdown(f"- {item}", unsafe_allow_html=True)
    else:
        st.info("No preprocessing operations applied yet.")

with tab_iqr:
    st.markdown(f"#### Interquartile Range (IQR) Boundary Diagnostics for `{iqr_col}`")
    if iqr_metrics:
        iq1, iq2, iq3, iq4, iq5 = st.columns(5)
        with iq1:
            st.metric("Q1 (25th)", f"${iqr_metrics['q1']:,.0f}" if 'salary' in iqr_col else f"{iqr_metrics['q1']:.0f}")
        with iq2:
            st.metric("Q3 (75th)", f"${iqr_metrics['q3']:,.0f}" if 'salary' in iqr_col else f"{iqr_metrics['q3']:.0f}")
        with iq3:
            st.metric("IQR (Q3 - Q1)", f"${iqr_metrics['iqr']:,.0f}" if 'salary' in iqr_col else f"{iqr_metrics['iqr']:.0f}")
        with iq4:
            st.metric("Lower Bound", f"${iqr_metrics['lower_bound']:,.0f}" if 'salary' in iqr_col else f"{iqr_metrics['lower_bound']:.0f}")
        with iq5:
            st.metric("Upper Bound", f"${iqr_metrics['upper_bound']:,.0f}" if 'salary' in iqr_col else f"{iqr_metrics['upper_bound']:.0f}")

        st.markdown(f"**Identified Outliers:** `{iqr_metrics['outlier_count']}` records ({iqr_metrics['outlier_pct']}% of dataset)")
        if not outliers_df.empty:
            st.dataframe(outliers_df, use_container_width=True, height=220)
    else:
        st.info("Select a valid numeric column to compute IQR.")

with tab_preview:
    st.markdown("#### Cleaned Dataset Records Preview")
    p_sz1, p_sz2 = st.columns([1, 2])
    with p_sz1:
        prev_page_size = st.selectbox("Rows per view:", [50, 100, 200, "All"], index=0, key="prev_ps")
    
    if prev_page_size == "All":
        preview_slice = cleaned_df
        prev_num = 1
        total_p = 1
    else:
        import math
        total_p = max(1, math.ceil(len(cleaned_df) / int(prev_page_size)))
        with p_sz2:
            prev_num = st.number_input("Page:", min_value=1, max_value=total_p, value=1, step=1, key="prev_pn")
        st_idx = (prev_num - 1) * int(prev_page_size)
        preview_slice = cleaned_df.iloc[st_idx:st_idx + int(prev_page_size)]

    st.dataframe(preview_slice, use_container_width=True, height=380)
    st.caption(f"Showing {len(preview_slice):,} records (Page {prev_num} of {total_p}) • Total: {len(cleaned_df):,} rows.")

with tab_commit:
    st.markdown("#### Commit Cleaned Dataset to Active Session State")
    st.markdown(
        "Committing this dataset promotes it as the primary data source across all analytical dashboards "
        "(EDA, Visualizations, Aggregation, Time Series, and Reports)."
    )
    col_act1, col_act2 = st.columns(2)
    with col_act1:
        if st.button("🚀 Commit Dataset as Active", use_container_width=True):
            st.session_state.cleaned_df = cleaned_df
            st.success("Successfully committed cleaned dataset to active session state!")
    with col_act2:
        csv_bytes = cleaned_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Cleaned CSV",
            data=csv_bytes,
            file_name="TechRadar_Cleaned_Data.csv",
            mime="text/csv",
            use_container_width=True
        )

with tab_real_jobs:
    st.markdown("#### Real Job Market Telemetry Ingestion (Adzuna CSV Alternative)")
    st.markdown(
        "If live Adzuna API credentials are not active or rate-limited, you can ingest genuine external job postings "
        "from any CSV file (e.g., Kaggle, LinkedIn, Indeed exports). The system will extract technology skills, "
        "deduplicate postings into `raw_job_postings`, and store verified skill demand in the cloud database."
    )
    
    real_csv = st.file_uploader(
        "Upload Real Job Postings CSV (Must contain 'job_title' or 'title' column):",
        type=["csv"],
        key="real_job_csv_uploader"
    )
    
    if real_csv is not None:
        if st.button("⚡ Extract Real Skills & Ingest into Production DB", use_container_width=True):
            with st.spinner("Extracting technology skills and deduplicating job records..."):
                try:
                    from collectors.adzuna_collector import AdzunaCollector
                    from database.db import bulk_save_live_observations
                    collector = AdzunaCollector()
                    observations = collector.import_jobs_from_csv(real_csv)
                    saved = bulk_save_live_observations(observations)
                    st.success(f"Successfully processed real job data: Ingested {saved} live skill observations!")
                except Exception as e:
                    st.error(f"Error parsing job postings CSV: {e}")
