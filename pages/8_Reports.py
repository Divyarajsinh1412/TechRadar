"""
TechRadar — Page 8: Reports & Academic Deliverables
Redesigned with SaaS UI/UX Architecture.
Enables exporting cleaned datasets, summary tables, and formal PDF project reports.
"""

import os
import streamlit as st
import pandas as pd
from modules.data_loader import load_dataset, get_dataset_metadata
from modules.opportunity_analysis import calculate_opportunity_scores
from modules.report_generator import generate_pdf_report
from modules.ui_components import (
    render_page_header,
    render_sidebar_branding,
    render_sidebar_footer,
    render_callout
)

st.set_page_config(page_title="Reports & Export — TechRadar", page_icon="📄", layout="wide")

# Inject styling
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_branding()
    st.markdown("#### 📄 Export Options")
    st.caption("Generate formal academic PDF documentation and clean CSV datasets.")
    render_sidebar_footer()

# Load active dataset
if "cleaned_df" in st.session_state and st.session_state.cleaned_df is not None:
    df = st.session_state.cleaned_df
    data_label = "Cleaned Dataset"
else:
    df = load_dataset()
    data_label = "Sample Dataset"

metadata = get_dataset_metadata(df)
opportunity_df = calculate_opportunity_scores(df)

top_10 = df.groupby(["technology", "category"]).agg({
    "job_postings": "sum",
    "average_salary": "mean" if "average_salary" in df.columns else "count"
}).reset_index().sort_values("job_postings", ascending=False).head(10)

summary_metrics = {
    "total_technologies": metadata["technologies_count"],
    "total_categories": metadata["categories_count"],
    "total_jobs": int(df["job_postings"].sum()) if "job_postings" in df.columns else 0,
    "avg_salary": float(df["average_salary"].mean()) if "average_salary" in df.columns else 0.0,
    "highest_demand_tech": top_10.iloc[0]["technology"] if not top_10.empty else "N/A",
    "fastest_growing_tech": opportunity_df.sort_values("growth_rate", ascending=False).iloc[0]["technology"] if not opportunity_df.empty else "N/A"
}

render_page_header(
    title="Reports & Academic Deliverables",
    subtitle="Export formatted PDF project defense documents, cleaned datasets, and tabular summary aggregates.",
    badge_text="Academic Deliverables & Documentation",
    status_pill="● Ready for Export"
)

render_callout(
    text="Generate publication-grade PDF documentation containing methodology, top rankings, opportunity classifications, "
         "and viva defense notes suitable for academic evaluation in <b>CSA4503 Data Analytics and Visualization</b>.",
    title="Viva Defense Deliverables",
    kind="success"
)

# Export Action Cards
st.markdown("### 📥 One-Click Deliverable Downloads")

e1, e2 = st.columns(2)

with e1:
    st.markdown(
        """
        <div class="kpi-card" style="min-height: 140px;">
            <div class="kpi-top">
                <span class="kpi-title">ACADEMIC PDF REPORT</span>
                <span style="font-size: 1.2rem;">📄</span>
            </div>
            <p style="font-size: 0.85rem; color: #94a3b8; margin: 0.3rem 0;">
                Complete formal report with executive summary, top 10 demand table, opportunity scorecard, and syllabus alignment notes.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    try:
        pdf_bytes = generate_pdf_report(summary_metrics, top_10, opportunity_df)
        st.download_button(
            label="📥 Download Academic PDF Report",
            data=pdf_bytes,
            file_name="TechRadar_Academic_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error compiling PDF: {e}")

with e2:
    st.markdown(
        f"""
        <div class="kpi-card" style="min-height: 140px;">
            <div class="kpi-top">
                <span class="kpi-title">CLEANED CSV DATASET</span>
                <span style="font-size: 1.2rem;">📊</span>
            </div>
            <p style="font-size: 0.85rem; color: #94a3b8; margin: 0.3rem 0;">
                Export active {data_label} ({len(df):,} rows) with standardized schema taxonomy and imputations.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Cleaned CSV Dataset",
        data=csv_bytes,
        file_name="TechRadar_Active_Data.csv",
        mime="text/csv",
        use_container_width=True
    )

st.markdown("---")

# Executive Findings
st.markdown("### 📝 Executive Analytical Summary & Conclusions")
st.markdown(
    f"""
    - **Total Postings Analyzed:** `{summary_metrics['total_jobs']:,}` job postings across `{summary_metrics['total_technologies']}` technologies and `{summary_metrics['total_categories']}` domains.
    - **Top Demand Leader:** `{summary_metrics['highest_demand_tech']}` commands the largest cumulative market volume.
    - **Fastest Accelerating Technology:** `{summary_metrics['fastest_growing_tech']}` demonstrated the strongest compound growth momentum.
    - **Mean Industry Compensation:** Annual compensation across all technology domains averaged `${summary_metrics['avg_salary']:,.2f}`.
    """
)

# Tabular Exports
st.markdown("#### 📋 Tabular Summary Exports")
tab_top, tab_cat, tab_opp = st.tabs(["🏆 Top 10 Technologies", "🏢 Category Aggregates", "🔮 Opportunity Scores"])

with tab_top:
    st.dataframe(top_10, use_container_width=True)
    st.download_button("Export Top 10 (CSV)", top_10.to_csv(index=False).encode("utf-8"), "top_10_technologies.csv", "text/csv")

with tab_cat:
    cat_summary = df.groupby("category").agg({
        "job_postings": "sum",
        "developer_interest": "mean",
        "company_adoption": "mean",
        "average_salary": "mean" if "average_salary" in df.columns else "count"
    }).round(2).reset_index()
    st.dataframe(cat_summary, use_container_width=True)
    st.download_button("Export Categories (CSV)", cat_summary.to_csv(index=False).encode("utf-8"), "category_aggregates.csv", "text/csv")

with tab_opp:
    st.dataframe(opportunity_df.head(25), use_container_width=True)
    st.download_button("Export Opportunity Scores (CSV)", opportunity_df.to_csv(index=False).encode("utf-8"), "opportunity_scores.csv", "text/csv")
