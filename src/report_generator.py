"""
report_generator.py
--------------------
Builds a downloadable PDF analytical report summarising the current
(filtered) dataset: KPIs, top products, category revenue table, and
two embedded charts. Uses ReportLab, a pure-Python PDF library, so
no external binaries (like LaTeX or wkhtmltopdf) are required.
"""

from __future__ import annotations

import io
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak,
)


def _fig_to_image(fig, width_cm=16):
    """Convert a matplotlib figure into a ReportLab Image flowable."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width_cm * cm, height=width_cm * cm * 0.5)


def build_pdf_report(
    kpis: dict,
    category_df: pd.DataFrame,
    top_products_df: pd.DataFrame,
    region_df: pd.DataFrame,
    monthly_fig=None,
    category_fig=None,
    filters_summary: str = "All data (no filters applied)",
) -> bytes:
    """Return the generated PDF report as raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom", parent=styles["Title"], fontSize=20, textColor=colors.HexColor("#1E3A8A")
    )
    heading_style = ParagraphStyle(
        "HeadingCustom", parent=styles["Heading2"], fontSize=13,
        textColor=colors.HexColor("#1F2937"), spaceBefore=14, spaceAfter=6,
    )
    normal = styles["Normal"]
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=9, textColor=colors.grey)

    elements = []

    # --- Header -----------------------------------------------------
    elements.append(Paragraph("Retail Sales Analytical Report", title_style))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}", small
    ))
    elements.append(Paragraph(f"Scope: {filters_summary}", small))
    elements.append(Spacer(1, 0.6 * cm))

    # --- KPI summary table -------------------------------------------
    elements.append(Paragraph("Key Performance Indicators", heading_style))
    kpi_table_data = [
        ["Metric", "Value"],
        ["Total Revenue", f"Rs. {kpis['total_revenue']:,.2f}"],
        ["Total Transactions", f"{kpis['total_transactions']:,}"],
        ["Average Order Value", f"Rs. {kpis['avg_order_value']:,.2f}"],
        ["Total Units Sold", f"{kpis['total_quantity']:,}"],
        ["Unique Customers", f"{kpis['unique_customers']:,}"],
        ["Top Category", str(kpis["top_category"])],
    ]
    kpi_table = Table(kpi_table_data, colWidths=[8 * cm, 8 * cm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(kpi_table)

    # --- Charts --------------------------------------------------------
    if monthly_fig is not None:
        elements.append(Paragraph("Monthly Revenue Trend", heading_style))
        elements.append(_fig_to_image(monthly_fig))

    if category_fig is not None:
        elements.append(Paragraph("Revenue by Category", heading_style))
        elements.append(_fig_to_image(category_fig))

    elements.append(PageBreak())

    # --- Category revenue table -----------------------------------------
    elements.append(Paragraph("Category-wise Revenue", heading_style))
    cat_data = [["Category", "Revenue", "Units Sold", "Share %"]]
    for _, row in category_df.iterrows():
        cat_data.append([
            row["Category"], f"Rs. {row['Revenue']:,.0f}",
            f"{int(row['Units_Sold']):,}", f"{row['Revenue_Share_%']:.1f}%",
        ])
    cat_table = Table(cat_data, colWidths=[6 * cm, 4 * cm, 3 * cm, 3 * cm])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#059669")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
    ]))
    elements.append(cat_table)
    elements.append(Spacer(1, 0.6 * cm))

    # --- Top products table ----------------------------------------------
    elements.append(Paragraph("Top-Selling Products", heading_style))
    prod_data = [["Product", "Revenue", "Units Sold"]]
    for _, row in top_products_df.head(10).iterrows():
        prod_data.append([
            row["Product_Name"], f"Rs. {row['Revenue']:,.0f}", f"{int(row['Units_Sold']):,}",
        ])
    prod_table = Table(prod_data, colWidths=[8 * cm, 4 * cm, 4 * cm])
    prod_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7C3AED")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
    ]))
    elements.append(prod_table)
    elements.append(Spacer(1, 0.6 * cm))

    # --- Regional performance table ---------------------------------------
    elements.append(Paragraph("Regional Performance", heading_style))
    region_data = [["Region", "Revenue", "Transactions", "Avg Order Value"]]
    for _, row in region_df.iterrows():
        region_data.append([
            row["Region"], f"Rs. {row['Revenue']:,.0f}",
            f"{int(row['Transactions']):,}", f"Rs. {row['Avg_Order_Value']:,.2f}",
        ])
    region_table = Table(region_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
    region_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D97706")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
    ]))
    elements.append(region_table)

    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph(
        "Report generated automatically by the Retail Sales Analysis and "
        "Visualization System.", small
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
