"""
TechRadar — Academic Report Generator Module
Generates downloadable PDF and CSV analytical reports using ReportLab.
"""

import io
import pandas as pd
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(
    summary_metrics: dict,
    top_technologies_df: pd.DataFrame,
    opportunity_df: pd.DataFrame
) -> bytes:
    """
    Generate an academic-grade PDF report containing project summary,
    top technologies, and opportunity rankings.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15
    )
    heading2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("TechRadar — Technology Trends & Future Skills Analytics", title_style))
    story.append(Paragraph("MCA Data Analytics Mini-Project Report (Course: CSA4503 Data Analytics and Visualization)", subtitle_style))
    story.append(Spacer(1, 10))

    # Executive Overview
    story.append(Paragraph("1. Executive Analytics Summary", heading2_style))
    overview_text = (
        f"This academic report provides empirical analysis of technology job-market demand, developer interest, "
        f"and longitudinal trends across {summary_metrics.get('total_technologies', 40)} technologies and "
        f"{summary_metrics.get('total_categories', 7)} domains. Total analyzed job postings stand at "
        f"<b>{summary_metrics.get('total_jobs', 0):,}</b> with an average annual compensation of "
        f"<b>${summary_metrics.get('avg_salary', 0):,.2f}</b>. The highest demand technology identified is "
        f"<b>{summary_metrics.get('highest_demand_tech', 'N/A')}</b>, and the fastest growing technology is "
        f"<b>{summary_metrics.get('fastest_growing_tech', 'N/A')}</b>."
    )
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 12))

    # Top Technologies Table
    story.append(Paragraph("2. Top 10 Technologies by Job Market Demand", heading2_style))
    if not top_technologies_df.empty:
        # Prepare table data
        table_data = [["Rank", "Technology", "Category", "Job Postings", "Avg Salary ($)"]]
        for idx, row in top_technologies_df.head(10).iterrows():
            table_data.append([
                str(idx + 1),
                str(row.get("technology", "")),
                str(row.get("category", "")),
                f"{int(row.get('job_postings', 0)):,}",
                f"${float(row.get('average_salary', 0)):,.0f}" if 'average_salary' in row else "N/A"
            ])

        top_table = Table(table_data, colWidths=[40, 130, 150, 100, 100])
        top_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white])
        ]))
        story.append(top_table)
    story.append(Spacer(1, 12))

    # Opportunity Classification Table
    story.append(Paragraph("3. Future Opportunity & Emerging Technology Classifications", heading2_style))
    if not opportunity_df.empty:
        opp_data = [["Technology", "Category", "Opportunity Score", "Classification", "Growth Rate (%)"]]
        for _, row in opportunity_df.head(10).iterrows():
            opp_data.append([
                str(row.get("technology", "")),
                str(row.get("category", "")),
                f"{float(row.get('opportunity_score', 0)):.1f}",
                str(row.get("classification", "")),
                f"{float(row.get('growth_rate', 0)):+.1f}%"
            ])

        opp_table = Table(opp_data, colWidths=[120, 140, 100, 110, 80])
        opp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white])
        ]))
        story.append(opp_table)
    story.append(Spacer(1, 15))

    # Academic Disclaimer & Methodology
    story.append(Paragraph("4. Academic Methodology & Viva Notes", heading2_style))
    notes = (
        "<b>Course Module Alignment:</b><br/>"
        "• Module 1: Data science workflow and exploratory data analysis.<br/>"
        "• Module 2: NumPy vectorization, Pandas Series/DataFrames, IQR outlier detection, string normalization.<br/>"
        "• Module 3: Matplotlib & Seaborn visualization, pivot tables, hierarchical indexing.<br/>"
        "• Module 4: GroupBy split-apply-combine, longitudinal time series, resampling ('ME'), rolling moving averages.<br/><br/>"
        "<i>Disclaimer: This document is prepared for academic evaluation in CSA4503. Demonstration records are synthetic.</i>"
    )
    story.append(Paragraph(notes, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
