"""
TechRadar — Page 3: Exploratory & Statistical Analysis
Redesigned with SaaS UI/UX Architecture.
Demonstrates CSA4503 Module 2 & 3 statistical formulations and distribution analysis.
"""

import os
import streamlit as st
import pandas as pd
from modules.data_loader import load_dataset
from modules.statistical_analysis import (
    compute_detailed_descriptive_stats,
    get_correlation_matrix,
    calculate_column_distribution_metrics
)
from modules.visualization import (
    plot_histogram_kde,
    plot_boxplot_by_category,
    plot_correlation_heatmap,
    plot_scatter_regression
)
from modules.ui_components import (
    render_page_header,
    render_sidebar_branding,
    render_sidebar_footer,
    render_callout
)

def _close_fig(fig):
    """Lazy close Matplotlib figure to avoid top-level font caching bottleneck on Windows."""
    if fig is not None:
        import matplotlib.pyplot as plt
        plt.close(fig)

st.set_page_config(page_title="Exploratory Analysis — TechRadar", page_icon="📈", layout="wide")

# Inject styling
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_branding()
    st.markdown("#### ⚙️ Statistical Options")
    corr_method = st.radio("Correlation Method:", ["pearson", "spearman"], index=0)
    render_sidebar_footer()

# Load active dataset
if "cleaned_df" in st.session_state and st.session_state.cleaned_df is not None:
    df = st.session_state.cleaned_df
    status_label = "● Dataset: Cleaned"
else:
    df = load_dataset()
    status_label = "● Dataset: Sample"

render_page_header(
    title="Exploratory & Statistical Analysis",
    subtitle="Rigorous mathematical computation of central tendency, dispersion, skewness, kurtosis, and correlation matrices.",
    badge_text="CSA4503 Module 2 & 3",
    status_pill=status_label
)

render_callout(
    text="Covers textbook statistical metrics: Arithmetic Mean (<code>μ</code>), Median, Mode, "
         "Variance (<code>σ²</code>), Standard Deviation (<code>σ</code>), Quartiles (Q1, Q2, Q3), "
         "Interquartile Range (IQR), Fisher-Pearson Skewness, Kurtosis via <code>scipy.stats</code>, "
         "and Correlation Matrices.",
    title="Curriculum Learning Objectives",
    kind="info"
)

# Tabs
tab_matrix, tab_dist, tab_box, tab_corr, tab_scatter = st.tabs([
    "📊 Descriptive Statistics Matrix",
    "🔔 Distribution & KDE Modeling",
    "📦 Category Dispersion (Box Plots)",
    "🔥 Correlation Heatmap",
    "🎯 Bivariate Scatter & Trendline"
])

with tab_matrix:
    st.markdown("#### Comprehensive Descriptive Statistics Table")
    stats_df = compute_detailed_descriptive_stats(df)
    if not stats_df.empty:
        st.dataframe(stats_df, use_container_width=True)
        st.caption("All metrics computed dynamically from active dataset across numeric variables.")
    else:
        st.info("No numeric features found.")

with tab_dist:
    st.markdown("#### Distribution Modeling with Kernel Density Estimation (KDE)")
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if num_cols:
        target_col = st.selectbox("Select Numeric Feature for Distribution Analysis:", num_cols, index=min(4, len(num_cols)-1))
        
        # Display shape cards
        shape_stats = calculate_column_distribution_metrics(df[target_col])
        if shape_stats:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Mean", f"{shape_stats['mean']:,.2f}")
            with m2:
                st.metric("Median", f"{shape_stats['median']:,.2f}")
            with m3:
                st.metric("Skewness", f"{shape_stats['skewness']:.4f}", delta=shape_stats["skew_desc"])
            with m4:
                st.metric("Kurtosis", f"{shape_stats['kurtosis']:.4f}", delta=shape_stats["kurt_desc"])

        fig_kde = plot_histogram_kde(df[target_col], title=f"Distribution & KDE Profile: {target_col}", xlabel=target_col)
        st.pyplot(fig_kde)
        _close_fig(fig_kde)
    else:
        st.info("No numeric columns available.")

with tab_box:
    st.markdown("#### Salary Dispersion across Technology Categories (Box Plots)")
    if "category" in df.columns and "average_salary" in df.columns:
        fig_box = plot_boxplot_by_category(
            df, x_col="category", y_col="average_salary",
            title="Salary Dispersion across Technology Domains"
        )
        st.pyplot(fig_box)
        _close_fig(fig_box)
    else:
        st.info("Category and average_salary required for box plot analysis.")

with tab_corr:
    st.markdown(f"#### Feature Correlation Matrix ({corr_method.title()})")
    corr_matrix = get_correlation_matrix(df, method=corr_method)
    if not corr_matrix.empty:
        c_h1, c_h2 = st.columns([3, 2])
        with c_h1:
            fig_heat = plot_correlation_heatmap(corr_matrix, title=f"{corr_method.title()} Correlation Heatmap")
            st.pyplot(fig_heat)
            _close_fig(fig_heat)
        with c_h2:
            st.markdown("##### Matrix Values:")
            st.dataframe(corr_matrix, use_container_width=True)
    else:
        st.info("Insufficient numeric features for correlation matrix.")

with tab_scatter:
    st.markdown("#### Bivariate Scatter & Linear Trendline Regression")
    if len(num_cols) >= 2:
        sc1, sc2 = st.columns(2)
        with sc1:
            var_x = st.selectbox("X-Axis Feature:", num_cols, index=0)
        with sc2:
            var_y = st.selectbox("Y-Axis Feature:", num_cols, index=min(1, len(num_cols)-1))

        fig_scat = plot_scatter_regression(
            df, x_col=var_x, y_col=var_y,
            title=f"Bivariate Regression: {var_y} vs. {var_x}"
        )
        st.pyplot(fig_scat)
        _close_fig(fig_scat)
    else:
        st.info("At least two numeric features required.")
