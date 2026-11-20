"""
TechRadar — Technology Trends & Future Skills Analytics
Tagline: Discover Tomorrow's Technology Skills Today.
MCA Data Analytics Mini-Project for CSA4503 Data Analytics and Visualization.
Main Entry Point & Page 1: Home Dashboard (Upgraded Live Daily, Weekly & Monthly Analytics)
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from modules.data_loader import load_dataset_by_frequency, get_dataset_metadata, clear_data_caches
from modules.chart_styles import PLOTLY_CONFIG
from modules.multi_period_analytics import (
    compute_multi_period_growth_and_averages,
    get_fastest_growing_now,
    get_gaining_github_activity,
    get_newly_posted_technologies,
    get_declining_technologies,
    get_newly_detected_skills
)
from modules.live_collector import refresh_live_intelligence
from modules.ui_components import (
    render_page_header,
    render_kpi_card,
    render_sidebar_branding,
    render_sidebar_footer,
    render_callout,
    render_source_status_badges,
    render_database_environment_badge,
    render_executive_summary_banner,
    render_intelligence_card
)
from modules.visualization import (
    plotly_category_donut,
    plotly_top_technologies_bar,
    plotly_timeseries_lines,
    plotly_scatter_quadrant
)
from database.db import init_database, save_metrics_to_db, get_source_status, is_using_postgres

# ----------------- Page Configuration -----------------
st.set_page_config(
    page_title="TechRadar — Future Skills & Technology Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Central CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize SQLite database
try:
    init_database()
except Exception:
    pass

# Session State for Live Refresh
if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ----------------- Sidebar -----------------
with st.sidebar:
    render_sidebar_branding()

    st.markdown("#### 📅 Analysis Frequency")
    selected_frequency = st.radio(
        "Select Analytical Resolution:",
        ["Daily", "Weekly", "Monthly"],
        index=2, # Default to Monthly for long-term baseline
        help="Switch dynamically between Daily DoD, Weekly WoW, and Monthly MoM/YoY intelligence."
    )
    st.session_state.global_frequency = selected_frequency

    st.markdown("---")
    st.markdown("#### ⚡ Live Intelligence Controls")
    
    col_ref1, col_ref2 = st.columns([1, 1])
    with col_ref1:
        if st.button("🔄 Refresh Data", use_container_width=True, help="Trigger manual live data collection from GitHub, Hugging Face, and Job Feeds"):
            with st.spinner("Collecting live signals..."):
                clear_data_caches()
                active_techs = ["Python", "Rust", "Go", "PyTorch", "Docker", "Kubernetes", "TypeScript", "React", "FastAPI", "Vite", "Zig", "LangChain"]
                res = refresh_live_intelligence(active_techs, frequency=selected_frequency.lower())
                st.session_state.last_refresh_time = res["timestamp"]
                st.success(f"Collected! ({res['github_queries_succeeded']} GitHub, {res['huggingface_queries_succeeded']} HF)")
                st.rerun()

    with col_ref2:
        auto_poll = st.toggle("⏱️ Real-time", value=False, help="Enable automatic periodic polling mode")

    st.caption(f"Last Refreshed: `{st.session_state.last_refresh_time}`")

    st.markdown("---")
    st.markdown("#### 📘 Analytical Horizon")
    st.caption(
        "• **Daily:** Real-time 24h market shifts\n\n"
        "• **Weekly:** 7-day momentum & hiring acceleration\n\n"
        "• **Monthly:** 5-year macro trends & benchmarks"
    )

    st.markdown("---")
    st.markdown("#### 📂 Dataset Mode")
    data_source = st.radio(
        "Data Source Mode:",
        ["Verified Academic Baseline", "Upload Custom CSV/Excel"],
        label_visibility="collapsed"
    )

    uploaded_file = None
    if data_source == "Upload Custom CSV/Excel":
        uploaded_file = st.file_uploader(
            "Upload Dataset File:",
            type=["csv", "xlsx", "xls"],
            help="Upload your job-market or technology trends file."
        )

    st.markdown("---")
    st.markdown("#### 🛠️ Storage Sync")
    db_target_name = "Supabase PostgreSQL" if is_using_postgres() else "SQLite DB"
    if st.button(f"💾 Persist to {db_target_name}", use_container_width=True):
        try:
            active_df = st.session_state.get("cleaned_df", st.session_state.get("raw_df"))
            if active_df is not None:
                saved = save_metrics_to_db(active_df, replace=True)
                st.success(f"Synced {saved:,} records to {db_target_name}!")
        except Exception as e:
            st.warning(f"DB Note: {e}")

    render_sidebar_footer()

# ----------------- Multi-Period Data Ingestion (Session Cached) -----------------
raw_period_df = load_dataset_by_frequency(frequency=selected_frequency, file_source=uploaded_file)

period_cache_key = f"period_df_{selected_frequency}"
if uploaded_file is None and period_cache_key in st.session_state:
    period_df = st.session_state[period_cache_key]
else:
    period_df = compute_multi_period_growth_and_averages(raw_period_df, frequency=selected_frequency)
    if uploaded_file is None:
        st.session_state[period_cache_key] = period_df

metadata = get_dataset_metadata(period_df)

# Page Header
current_date_str = datetime.now().strftime("%B %d, %Y")
render_page_header(
    title=f"Technology Trends & Intelligence — {selected_frequency} Analysis",
    subtitle=f"Live multi-period job market demand, developer activity, and growth trajectories • Updated {current_date_str}",
    badge_text="CSA4503 Multi-Period Analytics",
    status_pill=f"● Mode: {selected_frequency} Resolution"
)

# Fetch Source Status with in-memory caching and reuse across badges
source_status_df = get_source_status()

# Cloud Database & Environment Indicator
render_database_environment_badge(source_status_df)

# Live Data Source Status Banner
render_source_status_badges(source_status_df)

# Academic Transparency Notice Callout
render_callout(
    text=f"<b>Multi-Period Engine:</b> Currently displaying <b>{selected_frequency.upper()}</b> resolution. "
         f"Daily mode tracks day-over-day (DoD) volatility and 7-day moving averages; Weekly mode tracks week-over-week (WoW) "
         f"growth and 4-week acceleration; Monthly mode tracks 5-year longitudinal trends with MoM and YoY calculations. "
         f"All signals use legitimate APIs and verified benchmarks without synthetic inflation.",
    title="Analytical Resolution & Source Hygiene",
    kind="info"
)

# ----------------- Interactive Global Filters -----------------
st.markdown("### 🎛️ Live Filters & Search")

f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 1])

with f_col1:
    all_categories = sorted(period_df["category"].unique().tolist())
    selected_categories = st.multiselect("Filter Technology Domains:", all_categories, default=all_categories)

with f_col2:
    search_keyword = st.text_input("Search Specific Technology:", placeholder="e.g. Python, Rust, Docker, PyTorch")

with f_col3:
    # Date bounds
    min_date = pd.to_datetime(period_df["date"]).min().date()
    max_date = pd.to_datetime(period_df["date"]).max().date()
    date_range = st.date_input("Date Window:", value=(min_date, max_date), min_value=min_date, max_value=max_date)

# Apply filters
filtered_df = period_df.copy()
if selected_categories:
    filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
if search_keyword:
    filtered_df = filtered_df[filtered_df["technology"].str.contains(search_keyword, case=False)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
    filtered_df = filtered_df[(pd.to_datetime(filtered_df["date"]).dt.date >= start_d) & (pd.to_datetime(filtered_df["date"]).dt.date <= end_d)]

if filtered_df.empty:
    st.warning("No records matched the selected filter criteria. Please adjust your filters.")
    filtered_df = period_df.copy()

st.markdown("---")

# ----------------- Dynamic Multi-Period KPI Section -----------------
total_techs = filtered_df["technology"].nunique()
total_categories = filtered_df["category"].nunique()
total_postings = int(filtered_df["job_postings"].sum())
avg_salary = float(filtered_df["average_salary"].mean()) if "average_salary" in filtered_df.columns else 0.0

# Highest demand and fastest growing in current view
if "job_postings" in filtered_df.columns:
    highest_demand_tech = filtered_df.groupby("technology")["job_postings"].sum().idxmax()
    highest_demand_val = filtered_df.groupby("technology")["job_postings"].sum().max()
else:
    highest_demand_tech, highest_demand_val = "N/A", 0

growth_metric_col = "growth_pct" if "growth_pct" in filtered_df.columns else "growth_rate"
valid_growth = filtered_df.dropna(subset=[growth_metric_col])
if not valid_growth.empty:
    fastest_tech = valid_growth.groupby("technology")[growth_metric_col].mean().idxmax()
    fastest_rate = valid_growth.groupby("technology")[growth_metric_col].mean().max()
else:
    fastest_tech, fastest_rate = "N/A", 0.0

# Render Executive Summary Briefing Banner (Easily Understood Takeaways)
summary_dict = {
    "highest_demand_tech": highest_demand_tech,
    "highest_demand_val": highest_demand_val,
    "fastest_tech": fastest_tech,
    "fastest_rate": fastest_rate,
    "avg_salary": avg_salary,
    "total_postings": total_postings
}
render_executive_summary_banner(selected_frequency, summary_dict)

st.markdown(f"### 📊 Key Performance Indicators ({selected_frequency})")

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(render_kpi_card(
        "Tracked Technologies", f"{total_techs}", f"{selected_frequency} active pool", "💻", "#38bdf8"
    ), unsafe_allow_html=True)
with k2:
    postings_formatted = f"{total_postings/1000:.1f}k" if total_postings >= 10000 else f"{total_postings:,}"
    delta_sub = f"Across {selected_frequency.lower()} intervals"
    st.markdown(render_kpi_card(
        f"Total {selected_frequency} Jobs", postings_formatted, delta_sub, "📋", "#0ea5e9", tooltip=f"{total_postings:,} job postings"
    ), unsafe_allow_html=True)
with k3:
    st.markdown(render_kpi_card(
        "Technology Domains", f"{total_categories}", "Active industry sectors", "🗂️", "#818cf8"
    ), unsafe_allow_html=True)

k4, k5, k6 = st.columns(3)
with k4:
    sal_str = f"${avg_salary/1000:.1f}k" if avg_salary >= 1000 else f"${avg_salary:,.0f}"
    st.markdown(render_kpi_card(
        "Average Salary", sal_str, f"Exact: ${avg_salary:,.0f}", "💵", "#10b981", tooltip=f"${avg_salary:,.2f} USD"
    ), unsafe_allow_html=True)
with k5:
    st.markdown(render_kpi_card(
        "Highest Demand", highest_demand_tech, f"{highest_demand_val:,.0f} {selected_frequency.lower()} postings", "🔥", "#f59e0b"
    ), unsafe_allow_html=True)
with k6:
    st.markdown(render_kpi_card(
        "Fastest Accelerating", fastest_tech, f"{fastest_rate:+.1f}% {selected_frequency.lower()} growth", "🚀", "#a855f7"
    ), unsafe_allow_html=True)

st.markdown("---")

# ----------------- Section: Live Technology Intelligence -----------------
st.markdown("### ⚡ Live Technology Intelligence Signals")

intel_c1, intel_c2, intel_c3 = st.columns(3)

# 1. Fastest Growing
with intel_c1:
    fastest_df = get_fastest_growing_now(filtered_df, top_n=4)
    rows_fastest = []
    if not fastest_df.empty:
        for _, r in fastest_df.iterrows():
            g_val = r.get("growth_pct", r.get("growth_rate", 0))
            g_str = f"{g_val:+.1f}%" if pd.notna(g_val) else "N/A"
            rows_fastest.append((r["technology"], r["category"], g_str, "#10b981"))
    render_intelligence_card(
        title="Fastest Growing Today",
        icon="⚡",
        pill_text="DoD Growth",
        pill_color="#10b981",
        rows=rows_fastest,
        empty_msg="No rapid growth observations detected."
    )

# 2. Gaining GitHub Activity
with intel_c2:
    github_df = get_gaining_github_activity(filtered_df, top_n=4)
    rows_gh = []
    if not github_df.empty:
        for _, r in github_df.iterrows():
            gh_val = r.get("github_activity", 0)
            rows_gh.append((r["technology"], r["category"], f"{gh_val:.1f}/100", "#38bdf8"))
    render_intelligence_card(
        title="Top GitHub Activity",
        icon="🐙",
        pill_text="Stars & Repos",
        pill_color="#38bdf8",
        rows=rows_gh,
        empty_msg="No GitHub metrics available."
    )

# 3. New Job Postings Leadership
with intel_c3:
    jobs_top_df = get_newly_posted_technologies(filtered_df, top_n=4)
    rows_jobs = []
    if not jobs_top_df.empty:
        for _, r in jobs_top_df.iterrows():
            j_val = r.get("job_postings", 0)
            rows_jobs.append((r["technology"], r["category"], f"{j_val:,.0f} jobs", "#f59e0b"))
    render_intelligence_card(
        title="Hiring Volume Leaders",
        icon="💼",
        pill_text="Open Roles",
        pill_color="#f59e0b",
        rows=rows_jobs,
        empty_msg="No posting volume data."
    )

intel_c4, intel_c5 = st.columns(2)

# 4. Newly Detected Frameworks
with intel_c4:
    new_skills = get_newly_detected_skills()
    rows_skills = [
        (s["skill"], s["signal"], s["freshness"], "#a855f7")
        for s in new_skills[:4]
    ]
    render_intelligence_card(
        title="Newly Detected Frameworks",
        icon="🧠",
        pill_text="Emerging Tech",
        pill_color="#8b5cf6",
        rows=rows_skills,
        empty_msg="No new skills detected."
    )

# 5. Declining Activity
with intel_c5:
    declining_df = get_declining_technologies(filtered_df, top_n=4)
    rows_dec = []
    if not declining_df.empty:
        for _, r in declining_df.iterrows():
            d_val = r.get("growth_pct", r.get("growth_rate", 0))
            rows_dec.append((r["technology"], r["category"], f"{d_val:.1f}%", "#f43f5e"))
    render_intelligence_card(
        title="Cooling Momentum",
        icon="📉",
        pill_text="Slowing Pace",
        pill_color="#f43f5e",
        rows=rows_dec,
        empty_msg="No technologies showing contraction."
    )

st.markdown("---")

# ----------------- Redesigned Visual Charts -----------------
st.markdown(f"### 📈 Visual Market Breakdown & Trends ({selected_frequency})")

r1_col1, r1_col2 = st.columns(2)

with r1_col1:
    st.markdown("#### 🍩 Category Market Share")
    st.caption("Distribution of active job demand across technology domains (Web, Cloud, AI, Systems).")
    donut_fig = plotly_category_donut(filtered_df, category_col="category", value_col="job_postings")
    st.plotly_chart(donut_fig, use_container_width=True, config=PLOTLY_CONFIG)

with r1_col2:
    st.markdown("#### 📊 Top 10 Most In-Demand Skills")
    st.caption("Ranked by total job postings in the selected period. Sorted highest to lowest.")
    bar_fig = plotly_top_technologies_bar(filtered_df, tech_col="technology", value_col="job_postings", top_n=10)
    st.plotly_chart(bar_fig, use_container_width=True, config=PLOTLY_CONFIG)

st.markdown("---")

r2_col1, r2_col2 = st.columns(2)

with r2_col1:
    st.markdown("#### ⏱️ Multi-Year Trajectories (Top 5)")
    st.caption("Historical demand comparison tracking long-term shifts in developer popularity.")
    top_5_techs = filtered_df.groupby("technology")["job_postings"].sum().nlargest(5).index.tolist()
    line_fig = plotly_timeseries_lines(
        filtered_df, date_col="date", value_col="job_postings", group_col="technology", technologies=top_5_techs
    )
    st.plotly_chart(line_fig, use_container_width=True, config=PLOTLY_CONFIG)

with r2_col2:
    st.markdown("#### 🎯 Growth vs. Enterprise Adoption Matrix")
    st.caption("BCG Matrix: Top-right are High-Growth Market Leaders; top-left are Fast-Rising Disruptors.")
    quad_fig = plotly_scatter_quadrant(
        filtered_df, x_col="company_adoption", y_col="growth_rate", size_col="job_postings", hover_col="technology"
    )
    st.plotly_chart(quad_fig, use_container_width=True, config=PLOTLY_CONFIG)
