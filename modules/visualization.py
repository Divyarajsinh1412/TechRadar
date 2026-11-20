"""
TechRadar — Professional Data Visualization Module
Builds production-grade, publication-ready charts using Plotly, Matplotlib, and Seaborn.
Implements user design guidelines:
- Non-overlapping labels
- Clear legends & tooltips
- Highest-to-lowest sorting
- Quadrant reference lines
- High-contrast SaaS palettes
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, List, Any

from modules.chart_styles import (
    apply_plotly_theme,
    apply_mpl_theme,
    PLOTLY_CONFIG,
    CATEGORY_COLORS,
    TIER_COLORS,
    PALETTE,
    CYAN,
    BLUE,
    INDIGO,
    PURPLE,
    EMERALD,
    AMBER,
    BORDER_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED
)

# ----------------- 1. Category Distribution Donut Chart -----------------

def plotly_category_donut(
    df: pd.DataFrame, 
    category_col: str = "category", 
    value_col: str = "job_postings"
) -> go.Figure:
    """
    Clean, non-crowded Donut Chart:
    - Hole ratio = 0.60
    - Category names positioned in clean vertical right-side legend
    - Percentages displayed in hover tooltips and clean inside text
    - Zero overlapping slice labels
    """
    grouped = df.groupby(category_col)[value_col].sum().reset_index()
    total_val = grouped[value_col].sum()
    grouped["pct"] = (grouped[value_col] / total_val * 100).round(1)

    colors = [CATEGORY_COLORS.get(cat, PALETTE[i % len(PALETTE)]) for i, cat in enumerate(grouped[category_col])]

    fig = go.Figure(data=[
        go.Pie(
            labels=grouped[category_col],
            values=grouped[value_col],
            hole=0.62,
            marker=dict(colors=colors, line=dict(color="#0b1120", width=2)),
            textinfo="percent",
            textposition="inside",
            insidetextorientation="horizontal",
            hovertemplate="<b>%{label}</b><br>Job Postings: %{value:,.0f}<br>Market Share: %{percent:.1%}<extra></extra>"
        )
    ])

    fig.update_layout(
        annotations=[
            dict(
                text=f"<b>{total_val:,.0f}</b><br><span style='font-size:10px;color:#94a3b8;'>TOTAL JOBS</span>",
                x=0.5, y=0.5, font_size=14, showarrow=False,
                font=dict(color=TEXT_PRIMARY, family="Inter, sans-serif")
            )
        ]
    )

    return apply_plotly_theme(
        fig, 
        height=380, 
        show_legend=True,
        legend_orientation="h",
        legend_y=-0.14,
        legend_x=0.5,
        margin=dict(t=15, b=45, l=15, r=15)
    )

# ----------------- 2. Top 10 Technologies Horizontal Bar Chart -----------------

def plotly_top_technologies_bar(
    df: pd.DataFrame, 
    tech_col: str = "technology", 
    value_col: str = "job_postings", 
    top_n: int = 10
) -> go.Figure:
    """
    Horizontal bar chart sorted Highest to Lowest (Rank 1 at the top):
    - Clean gradient bar color
    - Formatted values at bar ends
    - Fully readable technology names
    """
    grouped = df.groupby(tech_col)[value_col].sum().reset_index()
    top_df = grouped.sort_values(by=value_col, ascending=False).head(top_n)

    fig = go.Figure(data=[
        go.Bar(
            x=top_df[value_col],
            y=top_df[tech_col],
            orientation="h",
            marker=dict(
                color=top_df[value_col],
                colorscale=[[0.0, "#0284c7"], [0.5, "#0ea5e9"], [1.0, "#38bdf8"]],
                line=dict(color="rgba(56, 189, 248, 0.4)", width=1)
            ),
            text=[f" {v:,.0f}" for v in top_df[value_col]],
            textposition="auto",
            textfont=dict(color=TEXT_PRIMARY, size=11, family="Inter, sans-serif"),
            hovertemplate="<b>%{y}</b><br>Total Postings: %{x:,.0f}<extra></extra>"
        )
    ])

    fig.update_layout(
        yaxis=dict(autorange="reversed", tickfont=dict(size=11, color=TEXT_PRIMARY)),
        xaxis=dict(title="Total Job Postings", tickformat="~s")
    )

    return apply_plotly_theme(
        fig, 
        height=380, 
        show_legend=False,
        margin=dict(t=15, b=40, l=95, r=40)
    )

# ----------------- 3. Longitudinal Trajectory Multi-Line Chart -----------------

def plotly_timeseries_lines(
    df: pd.DataFrame, 
    date_col: str = "date", 
    value_col: str = "job_postings", 
    group_col: str = "technology", 
    technologies: Optional[List[str]] = None
) -> go.Figure:
    """
    Interactive multi-line trajectory chart:
    - High contrast line colors
    - Unified hover tooltip on cursor
    - Clean date axis
    """
    plot_df = df.copy()
    if technologies:
        plot_df = plot_df[plot_df[group_col].isin(technologies)]

    plot_df[date_col] = pd.to_datetime(plot_df[date_col], errors="coerce")
    agg_df = plot_df.groupby([date_col, group_col])[value_col].mean().reset_index()

    fig = go.Figure()
    
    unique_techs = agg_df[group_col].unique()
    for i, tech in enumerate(unique_techs):
        tech_data = agg_df[agg_df[group_col] == tech].sort_values(date_col)
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(
            x=tech_data[date_col],
            y=tech_data[value_col],
            mode="lines",
            name=str(tech),
            line=dict(color=color, width=2.5),
            hovertemplate=f"<b>{tech}</b>: %{{y:,.1f}}<extra></extra>"
        ))

    metric_name = value_col.replace("_", " ").title()
    fig.update_layout(
        hovermode="x unified",
        xaxis=dict(title="Posting Period", showgrid=True),
        yaxis=dict(title=metric_name, showgrid=True)
    )

    return apply_plotly_theme(
        fig, 
        height=380, 
        show_legend=True,
        legend_orientation="h",
        legend_y=-0.28,
        legend_x=0.5,
        margin=dict(t=15, b=60, l=50, r=20)
    )

# ----------------- 4. Enterprise Adoption vs. Growth Quadrant -----------------

def plotly_scatter_quadrant(
    df: pd.DataFrame, 
    x_col: str = "company_adoption", 
    y_col: str = "growth_rate", 
    size_col: str = "job_postings", 
    hover_col: str = "technology"
) -> go.Figure:
    """
    Adoption vs Growth Quadrant:
    - Prevents overlapping text labels by removing inline text and relying on rich hover tooltips!
    - Category-based dot colors
    - Reference quadrant crosshairs at median x and y=0
    - Quadrant labels in 4 corners
    """
    latest = df.groupby(hover_col).agg({
        x_col: "mean",
        y_col: "mean",
        size_col: "mean",
        "category": "first"
    }).reset_index()

    fig = go.Figure()

    # Add traces per category so legend allows toggling
    for cat in latest["category"].unique():
        cat_data = latest[latest["category"] == cat]
        color = CATEGORY_COLORS.get(cat, CYAN)
        
        fig.add_trace(go.Scatter(
            x=cat_data[x_col],
            y=cat_data[y_col],
            mode="markers",
            name=cat,
            marker=dict(
                size=np.clip(cat_data[size_col] / cat_data[size_col].max() * 24 + 8, 8, 30),
                color=color,
                opacity=0.85,
                line=dict(color="#ffffff", width=1)
            ),
            customdata=cat_data[[hover_col, size_col]],
            hovertemplate=(
                "<b>%{customdata[0]}</b> (" + cat + ")<br>" +
                "Company Adoption: %{x:.1f}/100<br>" +
                "Growth Momentum: %{y:+.1f}%<br>" +
                "Avg Job Postings: %{customdata[1]:,.0f}<extra></extra>"
            )
        ))

    # Add quadrant reference crosshairs
    x_mid = 50.0
    y_mid = 0.0

    fig.add_hline(y=y_mid, line_dash="dash", line_color="rgba(148, 163, 184, 0.25)", line_width=1.2)
    fig.add_vline(x=x_mid, line_dash="dash", line_color="rgba(148, 163, 184, 0.25)", line_width=1.2)

    # Add quadrant corner annotations
    fig.add_annotation(x=15, y=latest[y_col].max() * 0.95, text="⚡ <b>High Growth (Hidden Gems)</b>",
                       showarrow=False, font=dict(color=AMBER, size=10))
    fig.add_annotation(x=85, y=latest[y_col].max() * 0.95, text="🚀 <b>Emerging Leaders</b>",
                       showarrow=False, font=dict(color=CYAN, size=10))
    fig.add_annotation(x=85, y=latest[y_col].min() * 0.95, text="🏛️ <b>Established Pillars</b>",
                       showarrow=False, font=dict(color=INDIGO, size=10))
    fig.add_annotation(x=15, y=latest[y_col].min() * 0.95, text="👁️ <b>Monitor / Niche</b>",
                       showarrow=False, font=dict(color=TEXT_MUTED, size=10))

    fig.update_layout(
        xaxis=dict(title="Enterprise Adoption Score (0–100)", range=[0, 100]),
        yaxis=dict(title="Growth Momentum Rate (%)")
    )

    return apply_plotly_theme(
        fig, 
        height=390, 
        show_legend=True,
        legend_orientation="h",
        legend_y=-0.28,
        legend_x=0.5,
        margin=dict(t=15, b=60, l=50, r=20)
    )

# ----------------- 5. Matplotlib & Seaborn Statistical Charts (Lazily Loaded) -----------------

def plot_histogram_kde(series: pd.Series, title: str, xlabel: str, bins: int = 25):
    """Refined Histogram with KDE."""
    import matplotlib.pyplot as plt
    import seaborn as sns
    apply_mpl_theme()
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=120)
    s = series.dropna()

    sns.histplot(s, bins=bins, kde=True, color=CYAN, ax=ax, edgecolor=BORDER_COLOR, alpha=0.5)
    ax.set_title(title, pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frequency")

    # Mean and Median indicators
    ax.axvline(s.mean(), color=AMBER, linestyle="--", linewidth=1.5, label=f"Mean: {s.mean():,.1f}")
    ax.axvline(s.median(), color=EMERALD, linestyle=":", linewidth=1.5, label=f"Median: {s.median():,.1f}")
    ax.legend()
    plt.tight_layout()
    return fig

def plot_boxplot_by_category(df: pd.DataFrame, x_col: str, y_col: str, title: str):
    """Refined Category Boxplot."""
    import matplotlib.pyplot as plt
    import seaborn as sns
    apply_mpl_theme()
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=120)
    
    order = df.groupby(x_col)[y_col].median().sort_values(ascending=False).index
    sns.boxplot(
        data=df, x=x_col, y=y_col, order=order,
        hue=x_col, palette="Blues_r", legend=False, ax=ax, width=0.55,
        flierprops={"markerfacecolor": AMBER, "markeredgecolor": "none", "markersize": 3.5}
    )
    ax.set_title(title, pad=12)
    ax.set_xlabel(x_col.replace("_", " ").title())
    ax.set_ylabel(y_col.replace("_", " ").title())
    plt.xticks(rotation=22, ha="right")
    plt.tight_layout()
    return fig

def plot_correlation_heatmap(corr_df: pd.DataFrame, title: str = "Feature Correlation Matrix"):
    """Refined Correlation Heatmap with clean annotations."""
    import matplotlib.pyplot as plt
    import seaborn as sns
    apply_mpl_theme()
    fig, ax = plt.subplots(figsize=(7.5, 6), dpi=120)
    mask = np.triu(np.ones_like(corr_df, dtype=bool))
    
    # Custom diverging color map from dark blue to cyan
    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    sns.heatmap(
        corr_df, mask=mask, cmap=cmap, vmin=-1, vmax=1,
        annot=True, fmt=".2f", square=True, linewidths=0.75,
        linecolor="#111c33", cbar_kws={"shrink": 0.8}, ax=ax,
        annot_kws={"size": 9, "weight": "bold"}
    )
    ax.set_title(title, pad=12)
    plt.xticks(rotation=35, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    return fig

def plot_scatter_regression(df: pd.DataFrame, x_col: str, y_col: str, title: str):
    """Refined Bivariate Scatter Regression."""
    import matplotlib.pyplot as plt
    import seaborn as sns
    apply_mpl_theme()
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
    sns.regplot(
        data=df, x=x_col, y=y_col, ax=ax,
        scatter_kws={"color": CYAN, "alpha": 0.45, "s": 28},
        line_kws={"color": PURPLE, "linewidth": 2}
    )
    ax.set_title(title, pad=12)
    ax.set_xlabel(x_col.replace("_", " ").title())
    ax.set_ylabel(y_col.replace("_", " ").title())
    plt.tight_layout()
    return fig
