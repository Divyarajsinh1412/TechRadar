"""
TechRadar — Page 7: Future Technology Opportunity Insights
Redesigned with SaaS UI/UX Architecture.
Demonstrates Explainable Analytics, Min-Max Normalization, and 5-Tier Opportunity Scoring.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_loader import load_dataset
from modules.opportunity_analysis import calculate_opportunity_scores, get_classification_summary
from modules.chart_styles import apply_plotly_theme, PLOTLY_CONFIG, TIER_COLORS, CYAN, INDIGO, EMERALD, AMBER
from modules.ui_components import (
    render_page_header,
    render_sidebar_branding,
    render_sidebar_footer,
    render_callout,
    render_database_environment_badge
)

st.set_page_config(page_title="Future Insights — TechRadar", page_icon="🔮", layout="wide")

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
    st.markdown("#### 📅 Temporal Resolution")
    opp_freq = st.radio(
        "Opportunity Delta Window:",
        ["Daily Signal Changes", "Weekly Opportunity Changes", "Monthly Opportunity Baseline"],
        index=2
    )

    st.markdown("#### ⚖️ Scoring Model Weights")
    w_jobs = st.slider("Job Demand Weight:", 0.0, 1.0, 0.35, step=0.05)
    w_dev = st.slider("Developer Interest Weight:", 0.0, 1.0, 0.25, step=0.05)
    w_adopt = st.slider("Company Adoption Weight:", 0.0, 1.0, 0.20, step=0.05)
    w_growth = st.slider("Historical Growth Weight:", 0.0, 1.0, 0.20, step=0.05)

    tot_w = w_jobs + w_dev + w_adopt + w_growth
    if abs(tot_w - 1.0) > 0.01:
        st.caption(f"Renormalizing weights (sum={tot_w:.2f})")
        w_jobs /= tot_w
        w_dev /= tot_w
        w_adopt /= tot_w
        w_growth /= tot_w

    render_sidebar_footer()

render_page_header(
    title=f"Future Technology Opportunity Insights ({opp_freq})",
    subtitle="Explainable multi-criteria ranking identifying emerging, high-growth, and hidden early-stage technology opportunities.",
    badge_text="Explainable Decision Analytics",
    status_pill=f"● {opp_freq}"
)

render_database_environment_badge()

render_callout(
    text="<b>Academic Scoring Methodology:</b> The Technology Opportunity Score (0–100) linearly synthesizes four min-max normalized "
         "empirical signals: Job Postings, Developer Admiration, Enterprise Adoption, and Growth Momentum.<br/>"
         "<b>Confidence vs. FOI:</b> Confidence scores are tracked independently (based on signal variance and observation volume). "
         "Momentum classifications explicitly separate short-term spikes from sustained multi-period acceleration.",
    title="Explainable Scoring & Spike Rejection Model",
    kind="info"
)

# Calculate Opportunity Scores
scored_df = calculate_opportunity_scores(
    df, weight_job=w_jobs, weight_dev=w_dev, weight_adopt=w_adopt, weight_growth=w_growth, frequency=opp_freq
)
class_summary = get_classification_summary(scored_df)

# Top tier summary cards
tiers = ["Emerging", "High-Demand", "Low-Demand / High-Growth", "Established", "Monitor"]
tier_cols = st.columns(5)

for idx, tier_name in enumerate(tiers):
    matching = scored_df[scored_df["classification"] == tier_name]
    with tier_cols[idx]:
        st.metric(
            tier_name,
            f"{len(matching)} Techs",
            delta=f"Avg: {matching['opportunity_score'].mean():.1f} pts" if not matching.empty else "None"
        )

st.markdown("<br/>", unsafe_allow_html=True)

# Tabs
tab_rankings, tab_quadrant, tab_breakdown, tab_hidden = st.tabs([
    "🏆 Opportunity Rankings Table",
    "🎯 Adoption vs. Growth Quadrant",
    "🔍 Signal Decomposition",
    "✨ Hidden Opportunity Detector"
])

with tab_rankings:
    st.markdown("#### Complete Technology Opportunity Scorecard")
    f1, f2 = st.columns(2)
    with f1:
        cat_filter = st.selectbox("Filter by Category:", ["All"] + sorted(scored_df["category"].unique().tolist()))
    with f2:
        class_filter = st.selectbox("Filter by Classification Tier:", ["All"] + tiers)

    filtered_scores = scored_df.copy()
    if cat_filter != "All":
        filtered_scores = filtered_scores[filtered_scores["category"] == cat_filter]
    if class_filter != "All":
        filtered_scores = filtered_scores[filtered_scores["classification"] == class_filter]

    display_cols = [
        "technology", "category", "opportunity_score", "confidence_score", "score_change", "momentum_type",
        "classification", "job_postings", "developer_interest", "company_adoption", "growth_rate"
    ]
    st.dataframe(filtered_scores[display_cols], use_container_width=True, height=400)

with tab_quadrant:
    st.markdown("#### Strategic Opportunity Quadrant (Size = Opportunity Score)")
    fig_quad = px.scatter(
        scored_df,
        x="company_adoption",
        y="growth_rate",
        size="opportunity_score",
        color="classification",
        hover_name="technology",
        color_discrete_map=TIER_COLORS,
        title="Enterprise Adoption vs. Growth Rate"
    )
    fig_quad = apply_plotly_theme(fig_quad, height=420)
    st.plotly_chart(fig_quad, use_container_width=True, config=PLOTLY_CONFIG)

with tab_breakdown:
    st.markdown("#### Normalized Sub-Indicator Decomposition")
    tech_inspect = st.selectbox("Select Technology for Score Breakdown:", scored_df["technology"].tolist(), index=0)
    tech_row = scored_df[scored_df["technology"] == tech_inspect].iloc[0]

    decomp_df = pd.DataFrame({
        "Signal": ["Job Demand", "Developer Interest", "Enterprise Adoption", "Growth Momentum"],
        "Normalized (0-100)": [tech_row["norm_jobs"], tech_row["norm_dev"], tech_row["norm_adopt"], tech_row["norm_growth"]],
        "Configured Weight": [w_jobs, w_dev, w_adopt, w_growth],
        "Weighted Points": [
            tech_row["norm_jobs"] * w_jobs,
            tech_row["norm_dev"] * w_dev,
            tech_row["norm_adopt"] * w_adopt,
            tech_row["norm_growth"] * w_growth
        ]
    })
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.dataframe(decomp_df, use_container_width=True)
    with col_d2:
        fig_decomp = px.bar(
            decomp_df, x="Signal", y="Normalized (0-100)", color="Signal",
            title=f"{tech_inspect}: Sub-Indicator Components (Score: {tech_row['opportunity_score']:.1f})",
            color_discrete_sequence=[CYAN, INDIGO, EMERALD, AMBER]
        )
        fig_decomp = apply_plotly_theme(fig_decomp, height=320, show_legend=False)
        st.plotly_chart(fig_decomp, use_container_width=True, config=PLOTLY_CONFIG)

with tab_hidden:
    st.markdown("#### ✨ Early-Stage & Hidden Opportunities (Low Demand / High Growth)")
    st.markdown(
        "Technologies with lower current job counts but exceptional developer interest and compound growth momentum."
    )
    hidden_gems = scored_df[scored_df["classification"] == "Low-Demand / High-Growth"]
    if not hidden_gems.empty:
        st.dataframe(
            hidden_gems[["technology", "category", "opportunity_score", "growth_rate", "developer_interest", "job_postings"]],
            use_container_width=True
        )
    else:
        st.info("No technologies currently matched the hidden opportunity criteria.")
