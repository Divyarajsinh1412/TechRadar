"""
TechRadar — Professional Chart Styling & Theme Engine
Centralized design system for Plotly, Matplotlib, and Seaborn charts.
Adheres to premium dark-mode SaaS analytics aesthetics.
"""

import os
import tempfile
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "techradar_matplotlib"))

import plotly.graph_objects as go

# ----------------- Color Tokens -----------------
BG_DARK = "#0b1120"
BG_CARD = "#111c33"
BG_TOOLTIP = "#1e293b"
BORDER_COLOR = "#1e293b"
GRID_COLOR = "rgba(148, 163, 184, 0.08)"
TEXT_PRIMARY = "#f8fafc"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"

# Accent Palettes
CYAN = "#38bdf8"
BLUE = "#0ea5e9"
INDIGO = "#6366f1"
PURPLE = "#a855f7"
EMERALD = "#10b981"
AMBER = "#f59e0b"
ROSE = "#f43f5e"
VIOLET = "#8b5cf6"

PALETTE = [CYAN, INDIGO, EMERALD, PURPLE, AMBER, BLUE, ROSE, VIOLET]

# Dedicated category colors for consistent cross-chart recognition
CATEGORY_COLORS = {
    "Programming Languages": CYAN,
    "Web Development": BLUE,
    "AI & Machine Learning": PURPLE,
    "Cloud & DevOps": INDIGO,
    "Cybersecurity": EMERALD,
    "Databases": AMBER,
    "Developer Tools": VIOLET
}

# 5-Tier Opportunity Colors
TIER_COLORS = {
    "Emerging": CYAN,
    "High-Demand": EMERALD,
    "Low-Demand / High-Growth": AMBER,
    "Established": INDIGO,
    "Monitor": TEXT_MUTED
}

# ----------------- Plotly Global Layout Preset & Performance Config -----------------

PLOTLY_CONFIG = {
    "responsive": True,
    "displayModeBar": False,
    "displaylogo": False,
    "scrollZoom": False
}

def apply_plotly_theme(
    fig: go.Figure, 
    height: int = 380, 
    show_legend: bool = True,
    title: Optional[str] = None,
    legend_orientation: str = "h",
    legend_y: float = -0.22,
    legend_x: float = 0.5,
    margin: Optional[dict] = None
) -> go.Figure:
    """
    Apply a consistent, high-end SaaS dark theme to any Plotly figure.
    - Transparent container backgrounds.
    - Subtle gridlines.
    - Modern Inter/system sans typography.
    - Clean hover tooltips.
    - Non-overlapping legends (placed below the chart or customized).
    - Mobile-responsive margins and autosizing.
    """
    layout_updates = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        autosize=True,
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            size=11,
            color=TEXT_SECONDARY
        ),
        hoverlabel=dict(
            bgcolor=BG_TOOLTIP,
            bordercolor=BORDER_COLOR,
            font=dict(color=TEXT_PRIMARY, size=11, family="Inter, sans-serif")
        ),
        showlegend=show_legend,
        xaxis=dict(
            gridcolor=GRID_COLOR,
            zerolinecolor=GRID_COLOR,
            showline=False,
            tickfont=dict(size=10, color=TEXT_MUTED)
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            zerolinecolor=GRID_COLOR,
            showline=False,
            tickfont=dict(size=10, color=TEXT_MUTED)
        )
    )

    if title:
        layout_updates["title"] = dict(
            text=title,
            font=dict(size=13, color=TEXT_PRIMARY, family="Inter, -apple-system, sans-serif"),
            x=0.01,
            xanchor="left",
            y=0.98
        )
        default_margin = dict(t=45, b=45, l=45, r=20)
    elif fig.layout.title and fig.layout.title.text:
        layout_updates["title"] = dict(
            text=fig.layout.title.text,
            font=dict(size=13, color=TEXT_PRIMARY, family="Inter, -apple-system, sans-serif"),
            x=0.01,
            xanchor="left",
            y=0.98
        )
        default_margin = dict(t=45, b=45, l=45, r=20)
    else:
        layout_updates["title"] = None
        default_margin = dict(t=15, b=45, l=45, r=20)

    layout_updates["margin"] = margin if margin is not None else default_margin

    if show_legend:
        layout_updates["legend"] = dict(
            font=dict(size=10, color=TEXT_SECONDARY),
            bgcolor="rgba(17, 28, 51, 0.6)",
            bordercolor="rgba(30, 41, 59, 0.8)",
            borderwidth=1,
            orientation=legend_orientation,
            yanchor="top" if legend_y < 0 else "bottom",
            y=legend_y,
            xanchor="center" if legend_orientation == "h" else "left",
            x=legend_x
        )

    fig.update_layout(**layout_updates)
    return fig

# ----------------- Matplotlib / Seaborn Global Theme -----------------

def apply_mpl_theme():
    """Apply SaaS dark palette to Matplotlib and Seaborn figures (lazily loaded)."""
    import matplotlib.pyplot as plt
    plt.style.use("dark_background")
    plt.rcParams.update({
        "figure.facecolor": BG_DARK,
        "axes.facecolor": BG_CARD,
        "axes.edgecolor": BORDER_COLOR,
        "axes.labelcolor": TEXT_SECONDARY,
        "axes.labelsize": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlecolor": TEXT_PRIMARY,
        "xtick.color": TEXT_MUTED,
        "ytick.color": TEXT_MUTED,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "grid.color": "#243049",
        "grid.linestyle": "--",
        "grid.alpha": 0.4,
        "text.color": TEXT_PRIMARY,
        "legend.facecolor": BG_CARD,
        "legend.edgecolor": BORDER_COLOR,
        "legend.fontsize": 9,
        "font.family": "sans-serif",
        "font.sans-serif": ["Inter", "Segoe UI", "DejaVu Sans", "Arial"]
    })
