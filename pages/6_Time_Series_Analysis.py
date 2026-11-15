"""
TechRadar — Page 6: Time Series Analysis
Redesigned with SaaS UI/UX Architecture.
Demonstrates CSA4503 Module 4 Temporal Indexing, Resampling, Moving Windows, and Lags.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_loader import load_dataset
from modules.time_series import (
    prepare_datetime_series,
    resample_technology_metric,
    compute_rolling_and_lags,
    demonstrate_period_arithmetic,
    demonstrate_timezone_handling
)
from modules.chart_styles import apply_plotly_theme, CYAN, INDIGO, TEXT_MUTED
from modules.ui_components import (
    render_page_header,
    render_sidebar_branding,
    render_sidebar_footer,
    render_callout
)

st.set_page_config(page_title="Time Series Analysis — TechRadar", page_icon="⏱️", layout="wide")

# Inject styling
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load dataset
if "cleaned_df" in st.session_state and st.session_state.cleaned_df is not None:
    df = st.session_state.cleaned_df
    status_label = "● Dataset: Cleaned"
else:
    df = load_dataset()
    status_label = "● Dataset: Sample"

with st.sidebar:
    render_sidebar_branding()
    st.markdown("#### ⚙️ Temporal Parameters")
    all_techs = sorted(df["technology"].unique().tolist())
    selected_tech = st.selectbox("Select Target Technology:", all_techs, index=0)
    
    freq_label = st.selectbox(
        "Frequency Resampling:",
        ["Daily (D)", "Weekly (W-MON)", "Monthly (ME)", "Quarterly (QE)", "Yearly (YE)"],
        index=2
    )
    freq_map = {
        "Daily (D)": "D",
        "Weekly (W-MON)": "W-MON",
        "Monthly (ME)": "ME",
        "Quarterly (QE)": "QE",
        "Yearly (YE)": "YE"
    }
    selected_freq = freq_map[freq_label]

    metric_target = st.selectbox(
        "Observation Metric:",
        ["job_postings", "developer_interest", "average_salary", "growth_rate"],
        index=0
    )
    render_sidebar_footer()

render_page_header(
    title="Time Series & Longitudinal Analytics",
    subtitle="Temporal modeling, frequency resampling, rolling moving averages, lag shifting, and period arithmetic.",
    badge_text="CSA4503 Module 4",
    status_pill=status_label
)

render_callout(
    text="Demonstrates textbook longitudinal tools in Pandas: DatetimeIndex parsing, frequency resampling "
         "(<code>.resample('ME')</code>), rolling window moving averages (<code>.rolling(window=3).mean()</code>), "
         "lag shifting (<code>.shift(1)</code>) for Month-over-Month (MoM) growth rates, Period arithmetic, and "
         "timezone localization (<code>tz_localize</code> / <code>tz_convert</code>).",
    title="Curriculum Learning Objectives",
    kind="info"
)

# Resample target technology data
resampled_data = resample_technology_metric(
    df, tech_name=selected_tech, freq=selected_freq, metric=metric_target
)

# Tabs
tab_drilldown, tab_rolling, tab_periods, tab_tz = st.tabs([
    "📈 Growth Trajectory",
    "🌊 Moving Windows & Lags",
    "📅 Period Arithmetic",
    "🌍 Time Zone Localization"
])

with tab_drilldown:
    st.markdown(f"#### Longitudinal Trajectory: `{selected_tech}` ({freq_label})")
    
    if not resampled_data.empty:
        t1, t2, t3 = st.columns(3)
        with t1:
            tot_val = resampled_data[metric_target].sum() if metric_target == "job_postings" else resampled_data[metric_target].mean()
            st.metric(f"Summary ({metric_target.replace('_', ' ').title()})", f"{tot_val:,.1f}")
        with t2:
            st.metric("Latest Observation", f"{resampled_data[metric_target].iloc[-1]:,.2f}")
        with t3:
            first_v = resampled_data[metric_target].iloc[0]
            last_v = resampled_data[metric_target].iloc[-1]
            pct = ((last_v - first_v) / first_v * 100) if first_v > 0 else 0
            st.metric("Total Cumulative Growth", f"{pct:+.1f}%")

        fig_ts = px.line(
            resampled_data.reset_index(),
            x="date", y=metric_target,
            title=f"{selected_tech}: {metric_target.replace('_', ' ').title()} Over Time",
            markers=True,
            color_discrete_sequence=[CYAN]
        )
        fig_ts = apply_plotly_theme(fig_ts, height=360, show_legend=False)
        st.plotly_chart(fig_ts, use_container_width=True)

        st.markdown("##### Resampled Observation Table:")
        st.dataframe(resampled_data.reset_index(), use_container_width=True)
    else:
        st.warning(f"No temporal records available for {selected_tech}.")

with tab_rolling:
    st.markdown("#### Moving Windows (3-Month & 6-Month) & Lag Shifting")
    if not resampled_data.empty:
        rolling_df = compute_rolling_and_lags(resampled_data, metric_col=metric_target, windows=[3, 6])
        
        fig_ma = px.line(
            rolling_df.reset_index(),
            x="date",
            y=[metric_target, "MA_3", "MA_6"],
            labels={"value": "Observation", "variable": "Series"},
            title=f"{selected_tech}: Actual vs. 3-Month & 6-Month Moving Averages",
            color_discrete_sequence=[TEXT_MUTED, CYAN, INDIGO]
        )
        fig_ma = apply_plotly_theme(fig_ma, height=360, show_legend=True)
        st.plotly_chart(fig_ma, use_container_width=True)

        st.markdown("##### Moving Window & Shifting (Lag) Table:")
        st.dataframe(rolling_df.reset_index(), use_container_width=True)
    else:
        st.info("Resample data first to view moving windows.")

with tab_periods:
    st.markdown("#### Pandas Periods & Period Arithmetic (`dt.to_period('M')`)")
    p_df = demonstrate_period_arithmetic(df)
    st.dataframe(p_df, use_container_width=True)

with tab_tz:
    st.markdown("#### Time Zone Localization (`tz_localize` & `tz_convert`)")
    tz_df = demonstrate_timezone_handling(df)
    st.dataframe(tz_df, use_container_width=True)
