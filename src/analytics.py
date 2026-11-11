"""
analytics.py
------------
All business-metric calculations live here, separate from the UI
(app.py) and from plotting (visualizations.py). Every function takes
a cleaned/filtered DataFrame and returns either a number, a Series,
or a small summary DataFrame.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


# ---------------------------------------------------------------
# Core KPIs
# ---------------------------------------------------------------
def get_kpis(df: pd.DataFrame) -> dict:
    """Return the headline KPI numbers shown in the dashboard cards."""
    if df.empty:
        return {
            "total_revenue": 0, "total_transactions": 0, "avg_order_value": 0,
            "total_quantity": 0, "unique_customers": 0, "top_category": "N/A",
            "top_product": "N/A",
        }

    total_revenue = float(df["Total_Amount"].sum())
    total_transactions = int(df["Transaction_ID"].nunique())
    avg_order_value = float(df["Total_Amount"].mean())
    total_quantity = int(df["Quantity"].sum())
    unique_customers = int(df["Customer_ID"].nunique())
    top_category = (
        df.groupby("Category")["Total_Amount"].sum().idxmax()
        if not df.empty else "N/A"
    )

    # Best-selling product, ranked by revenue -- this matches the KPI card's
    # own label ("By revenue") and help text in app.py, and the default sort
    # order of best_selling_products() below. Guards against a dataset with
    # no Product_Name column, or one where every product name is missing.
    top_product = "N/A"
    if "Product_Name" in df.columns:
        product_revenue = df.dropna(subset=["Product_Name"]).groupby("Product_Name")["Total_Amount"].sum()
        if not product_revenue.empty:
            top_product = product_revenue.idxmax()

    return {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "avg_order_value": avg_order_value,
        "total_quantity": total_quantity,
        "unique_customers": unique_customers,
        "top_category": top_category,
        "top_product": top_product,
    }


# ---------------------------------------------------------------
# Product performance
# ---------------------------------------------------------------
def best_selling_products(df: pd.DataFrame, top_n: int = 10, by: str = "Total_Amount") -> pd.DataFrame:
    """Top N products ranked by revenue ('Total_Amount') or units ('Quantity')."""
    agg = (
        df.groupby("Product_Name")
        .agg(Revenue=("Total_Amount", "sum"), Units_Sold=("Quantity", "sum"),
             Transactions=("Transaction_ID", "nunique"))
        .reset_index()
    )
    sort_col = "Revenue" if by == "Total_Amount" else "Units_Sold"
    return agg.sort_values(sort_col, ascending=False).head(top_n)


# ---------------------------------------------------------------
# Category analysis
# ---------------------------------------------------------------
def category_revenue(df: pd.DataFrame) -> pd.DataFrame:
    agg = (
        df.groupby("Category")
        .agg(Revenue=("Total_Amount", "sum"), Units_Sold=("Quantity", "sum"),
             Transactions=("Transaction_ID", "nunique"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    agg["Revenue_Share_%"] = (agg["Revenue"] / agg["Revenue"].sum() * 100).round(2)
    return agg


# ---------------------------------------------------------------
# Time-based analysis
# ---------------------------------------------------------------
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    agg = (
        df.groupby(["Month", "MonthName"])
        .agg(Revenue=("Total_Amount", "sum"), Transactions=("Transaction_ID", "nunique"))
        .reset_index()
        .sort_values("Month")
    )
    return agg


def daily_sales(df: pd.DataFrame) -> pd.DataFrame:
    agg = (
        df.groupby(df["Date"].dt.date)
        .agg(Revenue=("Total_Amount", "sum"), Transactions=("Transaction_ID", "nunique"))
        .reset_index()
        .rename(columns={"Date": "Date"})
    )
    agg.columns = ["Date", "Revenue", "Transactions"]
    return agg


def weekday_month_heatmap_data(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot table: rows = weekday, columns = month, values = revenue. Used for the heatmap chart."""
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = df.pivot_table(
        index="Weekday", columns="MonthName", values="Total_Amount", aggfunc="sum", fill_value=0
    )
    pivot = pivot.reindex(index=[d for d in weekday_order if d in pivot.index])
    month_cols = [m for m in MONTH_ORDER if m in pivot.columns]
    pivot = pivot[month_cols]
    return pivot


# ---------------------------------------------------------------
# Payment method & regional analysis
# ---------------------------------------------------------------
def payment_method_breakdown(df: pd.DataFrame):
    """Revenue/transactions by payment method, or None if the column isn't in this dataset."""
    if "Payment_Method" not in df.columns:
        return None
    agg = (
        df.groupby("Payment_Method")
        .agg(Revenue=("Total_Amount", "sum"), Transactions=("Transaction_ID", "nunique"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    return agg


def regional_performance(df: pd.DataFrame):
    """Revenue/AOV by region, or None if the column isn't in this dataset."""
    if "Region" not in df.columns:
        return None
    agg = (
        df.groupby("Region")
        .agg(Revenue=("Total_Amount", "sum"), Transactions=("Transaction_ID", "nunique"),
             Avg_Order_Value=("Total_Amount", "mean"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    agg["Avg_Order_Value"] = agg["Avg_Order_Value"].round(2)
    return agg


def channel_breakdown(df: pd.DataFrame):
    """Revenue/transactions by sales channel, or None if the column isn't in this dataset."""
    if "Sales_Channel" not in df.columns:
        return None
    agg = (
        df.groupby("Sales_Channel")
        .agg(Revenue=("Total_Amount", "sum"), Transactions=("Transaction_ID", "nunique"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    return agg
