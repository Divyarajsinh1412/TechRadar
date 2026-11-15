"""
TechRadar — Page 4: Visual Analytics
Redesigned with SaaS UI/UX Architecture.
Demonstrates CSA4503 Module 3 Visual Data Storytelling across Matplotlib, Seaborn, and Plotly.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_loader import load_dataset
from modules.visualization import (
    plotly_category_donut,
    plotly_top_technologies_bar,
    plotly_timeseries_lines
)
from modules.chart_styles import apply_plotly_theme, CATEGORY_COLORS, CYAN, INDIGO
from modules.ui_components import (
    render_page_header,
    render_sidebar_branding,
    render_sidebar_footer,
    render_callout
)

st.set_page_config(page_title="Visualizations — TechRadar", page_icon="📊", layout="wide")

# Inject styling
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_branding()
    st.markdown("#### ⚙️ Display Presets")
    top_n_slider = st.slider("Top N Technologies in Bar Chart:", 5, 25, 10)
    render_sidebar_footer()

# Load dataset
if "cleaned_df" in st.session_state and st.session_state.cleaned_df is not None:
    df = st.session_state.cleaned_df
    status_label = "● Dataset: Cleaned"
else:
    df = load_dataset()
    status_label = "● Dataset: Sample"

render_page_header(
    title="Visual Data Storytelling",
    subtitle="Interactive visual intelligence comparing job demand, market shares, trajectories, and comparative technology scorecards.",
    badge_text="CSA4503 Module 3",
    status_pill=status_label
)

render_callout(
    text="Demonstrates comprehensive visual analytics: bar charts, donut charts, multi-line temporal trajectories, "
         "multivariate bubble visualizations, and side-by-side head-to-head comparison cards.",
    title="Curriculum Learning Objectives",
    kind="info"
)

# Tabs
tab_bar, tab_line, tab_pie, tab_scatter, tab_compare = st.tabs([
    "📊 Bar Charts (Demand & Salary)",
    "📈 Line Charts (Trajectories)",
    "🍩 Market Share Donut",
    "🎯 Multivariate Bubble Analysis",
    "⚔️ Head-to-Head Comparison"
])

with tab_bar:
    st.markdown("#### Technology Demand & Compensation Rankings")
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        fig_bar = plotly_top_technologies_bar(df, tech_col="technology", value_col="job_postings", top_n=top_n_slider)
        st.plotly_chart(fig_bar, use_container_width=True)
    with b_col2:
        if "average_salary" in df.columns:
            sal_by_cat = df.groupby("category")["average_salary"].mean().reset_index().sort_values("average_salary", ascending=True)
            fig_sal = px.bar(
                sal_by_cat, x="average_salary", y="category", orientation="h",
                color="average_salary", color_continuous_scale="Purples",
                title="Average Annual Salary by Category ($ USD)",
                labels={"average_salary": "Mean Salary ($)", "category": "Category"}
            )
            fig_sal.update_layout(yaxis=dict(autorange="reversed"))
            fig_sal = apply_plotly_theme(fig_sal, height=360, show_legend=False)
            st.plotly_chart(fig_sal, use_container_width=True)

with tab_line:
    st.markdown("#### Longitudinal Multi-Technology Trajectories")
    all_techs = sorted(df["technology"].unique().tolist())
    sel_techs = st.multiselect(
        "Technologies to Compare:",
        options=all_techs,
        default=["Python", "Rust", "Go", "PyTorch", "Docker"] if set(["Python", "Rust", "Go", "PyTorch", "Docker"]).issubset(set(all_techs)) else all_techs[:4]
    )
    metric_choice = st.selectbox("Trajectory Metric:", ["job_postings", "developer_interest", "average_salary"], index=0)
    
    if sel_techs:
        fig_lines = plotly_timeseries_lines(
            df, date_col="date", value_col=metric_choice, group_col="technology", technologies=sel_techs
        )
        st.plotly_chart(fig_lines, use_container_width=True)
    else:
        st.info("Select at least one technology to display trajectory.")

with tab_pie:
    st.markdown("#### Category Market Share & Volume Breakdown")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        if "category" in df.columns:
            fig_donut = plotly_category_donut(df, category_col="category", value_col="job_postings")
            st.plotly_chart(fig_donut, use_container_width=True)
    with p_col2:
        st.markdown("##### Category Aggregate Breakdown:")
        cat_tbl = df.groupby("category").agg({
            "job_postings": "sum",
            "developer_interest": "mean",
            "average_salary": "mean" if "average_salary" in df.columns else "count"
        }).reset_index()
        cat_tbl["developer_interest"] = cat_tbl["developer_interest"].round(1)
        if "average_salary" in df.columns:
            cat_tbl["average_salary"] = cat_tbl["average_salary"].round(0)
        st.dataframe(cat_tbl, use_container_width=True)

with tab_scatter:
    st.markdown("#### Multivariate Bubble Plot (Adoption vs. Interest vs. Salary)")
    if {"developer_interest", "company_adoption", "average_salary", "technology", "category"}.issubset(set(df.columns)):
        scatter_data = df.groupby(["technology", "category"]).agg({
            "developer_interest": "mean",
            "company_adoption": "mean",
            "job_postings": "sum",
            "average_salary": "mean"
        }).reset_index()

        fig_bubble = px.scatter(
            scatter_data,
            x="company_adoption",
            y="developer_interest",
            size="job_postings",
            color="average_salary",
            hover_name="technology",
            color_continuous_scale="Viridis",
            title="Developer Interest vs. Company Adoption (Size = Total Jobs, Color = Salary)",
            labels={"company_adoption": "Enterprise Adoption (0-100)", "developer_interest": "Developer Interest (0-100)"}
        )
        fig_bubble = apply_plotly_theme(fig_bubble, height=400)
        st.plotly_chart(fig_bubble, use_container_width=True)

with tab_compare:
    st.markdown("#### Head-to-Head Comparative Scorecard")
    all_techs = sorted(df["technology"].unique().tolist())
    cmp1, cmp2 = st.columns(2)
    with cmp1:
        tech_a = st.selectbox("Select Technology A:", all_techs, index=0)
    with cmp2:
        tech_b = st.selectbox("Select Technology B:", all_techs, index=min(1, len(all_techs)-1))

    df_a = df[df["technology"] == tech_a]
    df_b = df[df["technology"] == tech_b]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(f"{tech_a} Total Jobs", f"{int(df_a['job_postings'].sum()):,}")
        st.metric(f"{tech_b} Total Jobs", f"{int(df_b['job_postings'].sum()):,}")
    with m2:
        st.metric(f"{tech_a} Dev Interest", f"{df_a['developer_interest'].mean():.1f}/100")
        st.metric(f"{tech_b} Dev Interest", f"{df_b['developer_interest'].mean():.1f}/100")
    with m3:
        st.metric(f"{tech_a} Adoption", f"{df_a['company_adoption'].mean():.1f}/100")
        st.metric(f"{tech_b} Adoption", f"{df_b['company_adoption'].mean():.1f}/100")
    with m4:
        st.metric(f"{tech_a} Avg Salary", f"${df_a['average_salary'].mean():,.0f}")
        st.metric(f"{tech_b} Avg Salary", f"${df_b['average_salary'].mean():,.0f}")

    comp_df = pd.DataFrame({
        "Metric": ["Developer Interest", "Company Adoption", "Skill Demand", "Growth Rate"],
        tech_a: [df_a["developer_interest"].mean(), df_a["company_adoption"].mean(), df_a["skill_demand"].mean(), df_a["growth_rate"].mean()],
        tech_b: [df_b["developer_interest"].mean(), df_b["company_adoption"].mean(), df_b["skill_demand"].mean(), df_b["growth_rate"].mean()]
    })

    fig_cmp = px.bar(
        comp_df.melt(id_vars="Metric", var_name="Technology", value_name="Score"),
        x="Metric", y="Score", color="Technology", barmode="group",
        color_discrete_sequence=[CYAN, INDIGO],
        title=f"Head-to-Head Benchmark: {tech_a} vs. {tech_b}"
    )
    fig_cmp = apply_plotly_theme(fig_cmp, height=340)
    st.plotly_chart(fig_cmp, use_container_width=True)
