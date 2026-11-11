"""
visualizations.py
------------------
Every chart-building function here returns a matplotlib Figure object.
app.py simply calls st.pyplot(fig) on whatever these return. Keeping
chart code separate from the Streamlit layout code makes both easier
to read and test independently.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # headless backend, safe for server-side rendering
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd

# ---- Shared visual theme -----------------------------------------------
PALETTE = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626",
           "#0891B2", "#DB2777", "#65A30D"]

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#D1D5DB",
    "axes.labelcolor": "#374151",
    "text.color": "#111827",
    "xtick.color": "#4B5563",
    "ytick.color": "#4B5563",
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "grid.color": "#E5E7EB",
})


def _format_axis_in_thousands(ax, axis="y"):
    formatter = mticker.FuncFormatter(lambda x, _: f"{x/1000:,.0f}K" if abs(x) >= 1000 else f"{x:,.0f}")
    if axis == "y":
        ax.yaxis.set_major_formatter(formatter)
    else:
        ax.xaxis.set_major_formatter(formatter)


# 1. Monthly revenue trend (line chart) -----------------------------------
def plot_monthly_trend(monthly_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(monthly_df["MonthName"], monthly_df["Revenue"], marker="o",
            color=PALETTE[0], linewidth=2.5, markersize=6)
    ax.fill_between(monthly_df["MonthName"], monthly_df["Revenue"], color=PALETTE[0], alpha=0.08)
    ax.set_title("Monthly Revenue Trend")
    ax.set_xlabel("")
    ax.set_ylabel("Revenue")
    _format_axis_in_thousands(ax)
    plt.xticks(rotation=0)
    fig.tight_layout()
    return fig


# 2. Daily sales trend (line chart) ----------------------------------------
def plot_daily_trend(daily_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(pd.to_datetime(daily_df["Date"]), daily_df["Revenue"],
            color=PALETTE[1], linewidth=1.2, alpha=0.9)
    ax.set_title("Daily Revenue Trend")
    ax.set_xlabel("")
    ax.set_ylabel("Revenue")
    _format_axis_in_thousands(ax)
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    return fig


# 3. Category-wise revenue (bar chart) -------------------------------------
def plot_category_revenue(category_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    data = category_df.sort_values("Revenue", ascending=True)
    bars = ax.barh(data["Category"], data["Revenue"], color=PALETTE[0])
    ax.set_title("Revenue by Category")
    ax.set_xlabel("Revenue")
    _format_axis_in_thousands(ax, axis="x")
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height() / 2, f"  {width/1000:,.0f}K",
                va="center", fontsize=9, color="#374151")
    fig.tight_layout()
    return fig


# 4. Top-selling products (bar chart) --------------------------------------
def plot_top_products(top_products_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    data = top_products_df.sort_values("Revenue", ascending=True)
    ax.barh(data["Product_Name"], data["Revenue"], color=PALETTE[2])
    ax.set_title(f"Top {len(data)} Best-Selling Products (by Revenue)")
    ax.set_xlabel("Revenue")
    _format_axis_in_thousands(ax, axis="x")
    fig.tight_layout()
    return fig


# 5. Payment method distribution (donut chart) -----------------------------
def plot_payment_methods(payment_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    colors = PALETTE[: len(payment_df)]
    wedges, texts, autotexts = ax.pie(
        payment_df["Revenue"], labels=payment_df["Payment_Method"],
        autopct="%1.1f%%", startangle=90, colors=colors, pctdistance=0.8,
        wedgeprops=dict(width=0.4, edgecolor="white"),
    )
    for t in autotexts:
        t.set_color("white")
        t.set_fontsize(9)
        t.set_fontweight("bold")
    ax.set_title("Payment Method Distribution")
    fig.tight_layout()
    return fig


# 6. Regional performance (bar chart) --------------------------------------
def plot_regional_performance(region_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    data = region_df.sort_values("Revenue", ascending=False)
    ax.bar(data["Region"], data["Revenue"], color=PALETTE[3])
    ax.set_title("Revenue by Region")
    ax.set_ylabel("Revenue")
    _format_axis_in_thousands(ax)
    fig.tight_layout()
    return fig


# 7. Weekday x Month heatmap (seaborn heatmap) -----------------------------
def plot_sales_heatmap(pivot_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    sns.heatmap(pivot_df, cmap="Blues", linewidths=0.5, linecolor="white",
                cbar_kws={"label": "Revenue"}, ax=ax, fmt=",.0f",
                annot=False)
    ax.set_title("Sales Intensity: Weekday vs Month")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    return fig


# 8. Order value distribution (histogram) ----------------------------------
def plot_order_value_distribution(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    sns.histplot(df["Total_Amount"], bins=30, color=PALETTE[4], kde=True, ax=ax)
    ax.set_title("Order Value Distribution")
    ax.set_xlabel("Order Value")
    ax.set_ylabel("Number of Orders")
    fig.tight_layout()
    return fig


# 9. Sales channel split (bar chart) ---------------------------------------
def plot_channel_breakdown(channel_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(5, 4.2))
    ax.bar(channel_df["Sales_Channel"], channel_df["Revenue"], color=[PALETTE[0], PALETTE[5]])
    ax.set_title("Online vs In-Store Revenue")
    ax.set_ylabel("Revenue")
    _format_axis_in_thousands(ax)
    fig.tight_layout()
    return fig
