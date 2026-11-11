"""
charts_plotly.py
------------------
Interactive Plotly chart-building functions for the live Streamlit
dashboard. Every function here returns a plotly.graph_objects.Figure.
app.py calls st.plotly_chart(cviz.<fn>(...), width='stretch') on
whatever these return.

This module mirrors the function names and input shapes of
src/visualizations.py (which builds the static matplotlib charts used
in the PDF report) so the two stay easy to compare, but renders each
chart as an interactive Plotly figure instead of a static image.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

# ---- Shared visual theme (matches app.py's CSS palette) -----------------
PALETTE = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626",
           "#0891B2", "#DB2777", "#65A30D"]

FONT_FAMILY = "Inter, -apple-system, 'Segoe UI', sans-serif"
TEXT_PRIMARY = "#0B1222"
TEXT_SECONDARY = "#5B6472"
GRID_COLOR = "#E5E7EB"


def _color_cycle(n: int) -> list[str]:
    """Repeat the palette to cover n categories, however many there are."""
    if n <= 0:
        return []
    reps = (n // len(PALETTE)) + 1
    return (PALETTE * reps)[:n]


def _base_layout(fig: go.Figure, title: str, height: int = 420) -> go.Figure:
    """Apply a consistent, dashboard-matching theme to any figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=TEXT_PRIMARY, family=FONT_FAMILY),
                    x=0.01, xanchor="left"),
        font=dict(family=FONT_FAMILY, color=TEXT_SECONDARY, size=12),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=50, b=10),
        height=height,
        hoverlabel=dict(bgcolor="white", font_size=12, font_family=FONT_FAMILY, bordercolor=GRID_COLOR),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID_COLOR)
    fig.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, zeroline=False, linecolor=GRID_COLOR)
    return fig


# 1. Monthly revenue trend (line chart) ------------------------------------
def plot_monthly_trend(monthly_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=monthly_df["MonthName"], y=monthly_df["Revenue"],
        mode="lines+markers",
        line=dict(color=PALETTE[0], width=3, shape="spline"),
        marker=dict(size=7, color=PALETTE[0]),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
        hovertemplate="<b>%{x}</b><br>Revenue: \u20b9%{y:,.0f}<extra></extra>",
        name="Revenue",
    ))
    fig.update_yaxes(title_text="Revenue")
    return _base_layout(fig, "Monthly Revenue Trend")


# 2. Daily sales trend (line chart) ----------------------------------------
def plot_daily_trend(daily_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=pd.to_datetime(daily_df["Date"]), y=daily_df["Revenue"],
        mode="lines",
        line=dict(color=PALETTE[1], width=1.6),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Revenue: \u20b9%{y:,.0f}<extra></extra>",
        name="Revenue",
    ))
    fig.update_yaxes(title_text="Revenue")
    return _base_layout(fig, "Daily Revenue Trend")


# 3. Category-wise revenue (horizontal bar) --------------------------------
def plot_category_revenue(category_df: pd.DataFrame) -> go.Figure:
    data = category_df.sort_values("Revenue", ascending=True)
    fig = go.Figure(go.Bar(
        x=data["Revenue"], y=data["Category"], orientation="h",
        marker=dict(color=PALETTE[0]),
        text=[f"\u20b9{v/1000:,.0f}K" for v in data["Revenue"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Revenue: \u20b9%{x:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(title_text="Revenue")
    return _base_layout(fig, "Revenue by Category")


# 4. Top-selling products (horizontal bar) ----------------------------------
def plot_top_products(top_products_df: pd.DataFrame) -> go.Figure:
    data = top_products_df.sort_values("Revenue", ascending=True)
    has_units = "Units_Sold" in data.columns
    fig = go.Figure(go.Bar(
        x=data["Revenue"], y=data["Product_Name"], orientation="h",
        marker=dict(color=PALETTE[2]),
        customdata=data["Units_Sold"] if has_units else None,
        hovertemplate=(
            "<b>%{y}</b><br>Revenue: \u20b9%{x:,.0f}<br>Units Sold: %{customdata:,.0f}<extra></extra>"
            if has_units else
            "<b>%{y}</b><br>Revenue: \u20b9%{x:,.0f}<extra></extra>"
        ),
    ))
    fig.update_xaxes(title_text="Revenue")
    return _base_layout(fig, f"Top {len(data)} Best-Selling Products (by Revenue)", height=460)


# 5. Payment method distribution (donut chart) ------------------------------
def plot_payment_methods(payment_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=payment_df["Payment_Method"], values=payment_df["Revenue"],
        hole=0.55,
        marker=dict(colors=_color_cycle(len(payment_df)), line=dict(color="white", width=2)),
        textinfo="percent",
        textfont=dict(size=12, color="white"),
        hovertemplate="<b>%{label}</b><br>Revenue: \u20b9%{value:,.0f}<br>Share: %{percent}<extra></extra>",
    ))
    return _base_layout(fig, "Payment Method Distribution")


# 6. Regional performance (bar chart) ---------------------------------------
def plot_regional_performance(region_df: pd.DataFrame) -> go.Figure:
    data = region_df.sort_values("Revenue", ascending=False)
    has_aov = "Avg_Order_Value" in data.columns
    fig = go.Figure(go.Bar(
        x=data["Region"], y=data["Revenue"],
        marker=dict(color=PALETTE[3]),
        customdata=data["Avg_Order_Value"] if has_aov else None,
        hovertemplate=(
            "<b>%{x}</b><br>Revenue: \u20b9%{y:,.0f}<br>Avg Order Value: \u20b9%{customdata:,.0f}<extra></extra>"
            if has_aov else
            "<b>%{x}</b><br>Revenue: \u20b9%{y:,.0f}<extra></extra>"
        ),
    ))
    fig.update_yaxes(title_text="Revenue")
    return _base_layout(fig, "Revenue by Region")


# 7. Weekday x Month heatmap (interactive heatmap) ---------------------------
def plot_sales_heatmap(pivot_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=pivot_df.values,
        x=list(pivot_df.columns),
        y=list(pivot_df.index),
        colorscale="Blues",
        colorbar=dict(title="Revenue", tickprefix="\u20b9"),
        hovertemplate="<b>%{y}, %{x}</b><br>Revenue: \u20b9%{z:,.0f}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", title_text="")
    fig.update_xaxes(title_text="")
    return _base_layout(fig, "Sales Intensity: Weekday vs Month", height=380)


# 8. Order value distribution (histogram) ------------------------------------
def plot_order_value_distribution(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Histogram(
        x=df["Total_Amount"], nbinsx=30,
        marker=dict(color=PALETTE[4]),
        hovertemplate="Order Value Range: \u20b9%{x:,.0f}<br>Orders: %{y}<extra></extra>",
    ))
    fig.update_xaxes(title_text="Order Value")
    fig.update_yaxes(title_text="Number of Orders")
    return _base_layout(fig, "Order Value Distribution")


# 9. Sales channel split (bar chart) ------------------------------------------
def plot_channel_breakdown(channel_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=channel_df["Sales_Channel"], y=channel_df["Revenue"],
        marker=dict(color=_color_cycle(len(channel_df))),
        hovertemplate="<b>%{x}</b><br>Revenue: \u20b9%{y:,.0f}<extra></extra>",
    ))
    fig.update_yaxes(title_text="Revenue")
    return _base_layout(fig, "Online vs In-Store Revenue", height=380)
