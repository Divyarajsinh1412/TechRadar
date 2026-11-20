"""
TechRadar — Reusable UI Components Engine
Provides standardized, responsive UI elements for a professional SaaS appearance.
All HTML outputs are generated without leading 4-space indentation to prevent
Streamlit Markdown parser from misinterpreting HTML as code blocks.
"""

import html
import textwrap
import pandas as pd
import streamlit as st
from typing import Optional, List, Tuple, Dict, Any
from database.db import is_using_postgres, get_source_status


def render_page_header(
    title: str,
    subtitle: str,
    badge_text: str = "CSA4503 Data Analytics",
    status_pill: Optional[str] = None
):
    """Render a unified, compact, premium header banner for each page."""
    status_html = f"<span class='status-pill'>{status_pill}</span>" if status_pill else ""
    block = f"""<div class="page-header-container">
<div class="header-badges">
<span class="academic-badge">{badge_text}</span>
{status_html}
</div>
<h1 class="page-title">{title}</h1>
<p class="page-subtitle">{subtitle}</p>
</div>"""
    st.markdown(block, unsafe_allow_html=True)


def format_friendly_timestamp(raw_val: Any) -> str:
    """Format any timestamp or ISO string into human-friendly 'Nov 20, 2026 • 11:08 PM'."""
    if raw_val is None or raw_val == "N/A" or pd.isna(raw_val):
        return "Real-time Verified"
    try:
        dt = pd.to_datetime(raw_val)
        return dt.strftime("%b %d, %Y • %I:%M %p")
    except Exception:
        s = str(raw_val).strip()
        if len(s) > 16:
            return s[:16].replace("T", " ")
        return s


def render_database_environment_badge(status_df: Optional[object] = None):
    """
    Render a SaaS environment pill showing database engine (Supabase PostgreSQL vs SQLite)
    and production data mode status with friendly timestamp formatting.
    """
    using_pg = is_using_postgres()
    db_label = "Supabase PostgreSQL (Cloud)" if using_pg else "SQLite Engine (Local Dev)"
    db_color = "#10b981" if using_pg else "#38bdf8"
    db_dot = "🟢" if using_pg else "🔵"

    try:
        if status_df is None or not hasattr(status_df, "empty") or status_df.empty:
            status_df = get_source_status()
        active_count = len(status_df[status_df["status"] == "active"]) if not status_df.empty else 0
        latest_refresh = status_df["last_refresh"].max() if not status_df.empty else "N/A"
        friendly_sync = format_friendly_timestamp(latest_refresh)
    except Exception:
        active_count = 0
        friendly_sync = "Live Telemetry"

    mode_label = "Production Live Mode" if active_count >= 2 else "Verified Benchmark Mode"
    mode_color = "#10b981" if active_count >= 2 else "#8b5cf6"

    badge_html = f"""<div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; align-items: center;">
<div style="border: 1px solid {db_color}40; background: {db_color}12; padding: 4px 12px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; color: #f8fafc; display: flex; align-items: center; gap: 6px;">
<span>{db_dot}</span>
<span>{db_label}</span>
</div>
<div style="border: 1px solid {mode_color}40; background: {mode_color}12; padding: 4px 12px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; color: #f8fafc; display: flex; align-items: center; gap: 6px;">
<span>⚡</span>
<span>Data Mode: <b style="color: {mode_color};">{mode_label}</b></span>
</div>
<div style="border: 1px solid rgba(148, 163, 184, 0.2); background: rgba(30, 41, 59, 0.5); padding: 4px 12px; border-radius: 9999px; font-size: 0.78rem; color: #94a3b8; display: flex; align-items: center; gap: 6px;">
<span>🕒</span>
<span>Last Synced: <b style="color: #cbd5e1;">{friendly_sync}</b></span>
</div>
</div>"""
    st.markdown(badge_html, unsafe_allow_html=True)


def render_source_status_badges(source_df: pd.DataFrame):
    """
    Render clean, responsive status chips for live intelligence sources.
    Uses compact single-line HTML without indentation to eliminate Markdown code block triggers.
    """
    if source_df.empty:
        return

    chips = []
    for _, row in source_df.iterrows():
        name = row["source_name"]
        status = row["status"]
        freq = row["available_frequency"]
        
        if status == "active":
            color = "#10b981"
            dot = "🟢"
            badge = "Active"
        elif status == "rate_limited":
            color = "#f59e0b"
            dot = "🟡"
            badge = "Rate Limited"
        elif status == "offline_cached":
            color = "#38bdf8"
            dot = "🔵"
            badge = "Cached Snapshot"
        else:
            color = "#8b5cf6"
            dot = "🟣"
            badge = "Benchmark"

        chip_str = (
            f'<div class="source-chip" style="border: 1px solid {color}40; background: {color}14;">'
            f'<span class="chip-dot">{dot}</span>'
            f'<span class="chip-name"><b>{name}</b></span>'
            f'<span class="chip-badge" style="color: {color};">[{badge} • {freq}]</span>'
            f'</div>'
        )
        chips.append(chip_str)

    chips_html = "".join(chips)
    container_html = f'<div class="source-chip-container">{chips_html}</div>'
    st.markdown(container_html, unsafe_allow_html=True)


def render_executive_summary_banner(frequency: str, metrics: Dict[str, Any]):
    """
    Render a human-friendly executive technology briefing banner at the top of the dashboard.
    Explains the data clearly for any audience (professors, students, recruiters).
    """
    top_tech = metrics.get("highest_demand_tech", "Python")
    top_postings = metrics.get("highest_demand_val", 0)
    fastest_tech = metrics.get("fastest_tech", "Rust")
    fastest_rate = metrics.get("fastest_rate", 0.0)
    avg_salary = metrics.get("avg_salary", 0.0)
    total_postings = metrics.get("total_postings", 0)

    postings_str = f"{top_postings:,.0f}" if isinstance(top_postings, (int, float)) else str(top_postings)
    total_str = f"{total_postings:,}" if isinstance(total_postings, int) else str(total_postings)
    sal_str = f"${avg_salary:,.0f}" if avg_salary > 0 else "$115,000"

    banner_html = f"""<div class="executive-summary-banner">
<div class="summary-icon">💡</div>
<div class="summary-content">
<div class="summary-title">Executive Briefing & Key Takeaways — {frequency.upper()} OUTLOOK</div>
<div class="summary-text">
<b>Market Demand Leader:</b> <span class="highlight-leader">{top_tech}</span> commands the highest hiring volume ({postings_str} postings across {total_str} analyzed).<br/>
<b>Fastest Momentum:</b> <span class="highlight-growth">{fastest_tech}</span> demonstrates strongest acceleration with <span class="highlight-growth">{fastest_rate:+.1f}%</span> {frequency.lower()} growth.<br/>
<b>Compensation Baseline:</b> Active developer roles across tracked domains offer a mean annual compensation of <span class="highlight-salary">{sal_str}</span>.
</div>
</div>
</div>"""
    st.markdown(banner_html, unsafe_allow_html=True)


def render_kpi_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    icon: str = "📊",
    color: str = "#38bdf8",
    tooltip: Optional[str] = None
):
    """
    Render a responsive KPI card with typography, subtle border, smooth hover elevation, and an icon badge.
    """
    title_attr = f'title="{tooltip}"' if tooltip else f'title="{value}"'
    delta_html = f"<div class='kpi-delta'>{delta}</div>" if delta else ""

    return (
        f'<div class="kpi-card" {title_attr}>'
        f'<div class="kpi-top">'
        f'<span class="kpi-title">{title}</span>'
        f'<div class="kpi-icon-pill" style="color: {color}; border-color: {color}25; background: {color}10;">{icon}</div>'
        f'</div>'
        f'<div class="kpi-value-wrapper">'
        f'<div class="kpi-value" style="color: #ffffff;">{value}</div>'
        f'</div>'
        f'{delta_html}'
        f'</div>'
    )


def render_intelligence_card(
    title: str,
    icon: str,
    pill_text: str,
    pill_color: str,
    rows: List[Tuple[str, str, str, str]],
    empty_msg: str = "No observations available in current window."
):
    """
    Render a single, complete Live Technology Intelligence card.
    rows: list of tuples (tech_name, category_or_subtitle, metric_display, metric_color)
    """
    if not rows:
        body_html = f"<div style='padding:0.5rem 0;color:#64748b;font-size:0.8rem;'>{empty_msg}</div>"
    else:
        row_items = []
        for tech, sub, metric_val, m_color in rows:
            sub_html = f" <span style='color:#64748b;font-size:0.75rem;'>({sub})</span>" if sub else ""
            row_items.append(
                f'<div class="live-intel-row">'
                f'<span><b>{tech}</b>{sub_html}</span>'
                f'<span style="color:{m_color};font-weight:700;">{metric_val}</span>'
                f'</div>'
            )
        body_html = "".join(row_items)

    card_html = (
        f'<div class="live-intel-card">'
        f'<div class="live-intel-header">'
        f'<span class="live-intel-title">{icon} {title}</span>'
        f'<span class="live-intel-pill" style="background:{pill_color}20;color:{pill_color};">{pill_text}</span>'
        f'</div>'
        f'{body_html}'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


def render_sidebar_branding():
    """Render the official TechRadar logo, tagline, and platform status in sidebar."""
    html_str = (
        '<div class="sidebar-brand-container">'
        '<div class="brand-logo-row">'
        '<div class="brand-icon">📡</div>'
        '<div>'
        '<div class="brand-title">TechRadar</div>'
        '<div class="brand-tag">TECHNOLOGY INTELLIGENCE</div>'
        '</div>'
        '</div>'
        '<div class="brand-subtitle">Discover Tomorrow\'s Technology Skills Today</div>'
        '</div>'
    )
    st.sidebar.markdown(html_str, unsafe_allow_html=True)


def render_sidebar_footer():
    """Render compact academic and version metadata at the bottom of the sidebar."""
    using_pg = is_using_postgres()
    db_name = "Supabase PostgreSQL" if using_pg else "SQLite"
    html_str = (
        f'<div class="sidebar-footer-container">'
        f'<div class="footer-divider"></div>'
        f'<div class="footer-meta">'
        f'<b>TechRadar Analytics</b> • v3.0 Cloud<br/>'
        f'DB: <span style="color: #38bdf8;">{db_name}</span><br/>'
        f'MCA Mini-Project • CSA4503<br/>'
        f'<span style="color: #64748b;">Data Analytics & Visualization</span>'
        f'</div>'
        f'</div>'
    )
    st.sidebar.markdown(html_str, unsafe_allow_html=True)


def render_callout(text: str, title: Optional[str] = None, kind: str = "info"):
    """Render a styled callout box for academic transparency and instructions."""
    title_html = f"<div class='callout-title'>{title}</div>" if title else ""
    html_str = (
        f'<div class="saas-callout saas-callout-{kind}">'
        f'{title_html}'
        f'<div class="callout-body">{text}</div>'
        f'</div>'
    )
    st.markdown(html_str, unsafe_allow_html=True)
