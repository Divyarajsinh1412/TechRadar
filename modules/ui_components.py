"""
TechRadar — Reusable UI Components Engine
Provides standardized, responsive UI elements for a professional SaaS appearance.
"""

import streamlit as st
from typing import Optional
from database.db import is_using_postgres, get_source_status

def render_page_header(
    title: str,
    subtitle: str,
    badge_text: str = "CSA4503 Data Analytics",
    status_pill: Optional[str] = None
):
    """Render a unified, compact, premium header banner for each page."""
    status_html = ""
    if status_pill:
        status_html = f"<span class='status-pill'>{status_pill}</span>"
    
    st.markdown(
        f"""
        <div class="page-header-container">
            <div class="header-badges">
                <span class="academic-badge">{badge_text}</span>
                {status_html}
            </div>
            <h1 class="page-title">{title}</h1>
            <p class="page-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_database_environment_badge():
    """
    Render a SaaS environment pill showing database engine (Supabase PostgreSQL vs SQLite)
    and production data mode status.
    """
    using_pg = is_using_postgres()
    db_label = "Supabase PostgreSQL (Cloud)" if using_pg else "SQLite Engine (Local Dev)"
    db_color = "#10b981" if using_pg else "#38bdf8"
    db_dot = "🟢" if using_pg else "🔵"

    try:
        status_df = get_source_status()
        active_count = len(status_df[status_df["status"] == "active"]) if not status_df.empty else 0
        latest_refresh = status_df["last_refresh"].max() if not status_df.empty else "N/A"
        if isinstance(latest_refresh, str) and len(latest_refresh) > 16:
            latest_refresh = latest_refresh[:16].replace("T", " ")
    except Exception:
        active_count = 0
        latest_refresh = "N/A"

    mode_label = "Production Live Mode" if active_count >= 2 else "Benchmark / Fallback Mode"
    mode_color = "#10b981" if active_count >= 2 else "#8b5cf6"

    st.markdown(
        f"""
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; align-items: center;">
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
                <span>Last Sync: <b>{latest_refresh}</b></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

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
    delta_html = ""
    if delta:
        delta_html = f"<div class='kpi-delta'>{delta}</div>"

    return f"""
    <div class="kpi-card" {title_attr}>
        <div class="kpi-top">
            <span class="kpi-title">{title}</span>
            <div class="kpi-icon-pill" style="color: {color}; border-color: {color}25; background: {color}10;">{icon}</div>
        </div>
        <div class="kpi-value-wrapper">
            <div class="kpi-value" style="color: #ffffff;">{value}</div>
        </div>
        {delta_html}
    </div>
    """

def render_sidebar_branding():
    """Render the official TechRadar logo, tagline, and platform status in sidebar."""
    st.sidebar.markdown(
        """
        <div class="sidebar-brand-container">
            <div class="brand-logo-row">
                <div class="brand-icon">📡</div>
                <div>
                    <div class="brand-title">TechRadar</div>
                    <div class="brand-tag">TECHNOLOGY INTELLIGENCE</div>
                </div>
            </div>
            <div class="brand-subtitle">Discover Tomorrow's Technology Skills Today</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_sidebar_footer():
    """Render compact academic and version metadata at the bottom of the sidebar."""
    using_pg = is_using_postgres()
    db_name = "Supabase PostgreSQL" if using_pg else "SQLite"
    st.sidebar.markdown(
        f"""
        <div class="sidebar-footer-container">
            <div class="footer-divider"></div>
            <div class="footer-meta">
                <b>TechRadar Analytics</b> • v3.0 Cloud<br/>
                DB: <span style="color: #38bdf8;">{db_name}</span><br/>
                MCA Mini-Project • CSA4503<br/>
                <span style="color: #64748b;">Data Analytics & Visualization</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_callout(text: str, title: Optional[str] = None, kind: str = "info"):
    """Render a styled callout box for academic transparency and instructions."""
    title_html = f"<div class='callout-title'>{title}</div>" if title else ""
    st.markdown(
        f"""
        <div class="saas-callout saas-callout-{kind}">
            {title_html}
            <div class="callout-body">{text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_source_status_badges(source_df):
    """Render clean, responsive status chips for live intelligence sources."""
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

        chips.append(
            f"""
            <div class="source-chip" style="border: 1px solid {color}35; background: {color}10;">
                <span class="chip-dot">{dot}</span>
                <span class="chip-name"><b>{name}</b></span>
                <span class="chip-badge" style="color: {color};">[{badge} • {freq}]</span>
            </div>
            """
        )

    chips_html = "".join(chips)
    st.markdown(f"<div class='source-chip-container'>{chips_html}</div>", unsafe_allow_html=True)
