"""
data_processing.py
-------------------
Handles everything related to getting raw CSV data into a clean,
analysis-ready pandas DataFrame.

Responsibilities:
    1. Load a CSV file (uploaded or the bundled sample dataset).
    2. Report data-quality issues (missing values, duplicates).
    3. Clean the data (drop duplicates, handle missing values).
    4. Enforce correct dtypes (dates, numbers).
    5. Add a few derived columns used throughout the dashboard
       (Month, MonthName, Weekday, Year).

Kept intentionally simple and well-commented so a BCA student can
follow the logic end-to-end.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "Transaction_ID", "Date", "Customer_ID", "Product_ID", "Product_Name",
    "Category", "Quantity", "Unit_Price", "Discount_Percent", "Total_Amount",
    "Payment_Method", "Region", "City", "Sales_Channel",
]


class DataValidationError(Exception):
    """
    Raised when a file can't be used by the dashboard at all (missing
    required columns, for example). app.py catches this specifically
    to show a friendly, actionable message -- naming the exact column(s)
    to fix -- instead of crashing or falling through to a generic error.
    """
    pass


def load_csv(file_or_path) -> pd.DataFrame:
    """Load a CSV from a path or an uploaded file-like object."""
    df = pd.read_csv(file_or_path)
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DataValidationError(
            f"Uploaded file is missing required column(s): {', '.join(missing_cols)}"
        )
    return df


def get_data_quality_report(df: pd.DataFrame) -> dict:
    """Return a summary of data-quality issues BEFORE cleaning."""
    return {
        "total_rows": len(df),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values_total": int(df.isnull().sum().sum()),
        "missing_by_column": df.isnull().sum()[df.isnull().sum() > 0].to_dict(),
    }


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Clean the raw dataframe:
      - Remove exact duplicate rows.
      - Fill/handle missing values column by column using sensible rules.
      - Fix dtypes.
      - Add derived date columns.

    Returns the cleaned dataframe AND a log dict describing what changed,
    so the dashboard can show the user exactly what was done.
    """
    df = df.copy()
    log = {}

    # --- 1. Remove exact duplicate rows -----------------------------
    before = len(df)
    df = df.drop_duplicates()
    log["duplicates_removed"] = before - len(df)

    # --- 2. Handle missing values ------------------------------------
    # Numeric columns: fill with the column median (robust to outliers)
    for col in ["Quantity", "Discount_Percent"]:
        if col in df.columns:
            n_missing = int(df[col].isnull().sum())
            if n_missing:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                log[f"{col}_filled_with_median"] = n_missing

    # Categorical columns: fill with the column mode (most frequent value)
    for col in ["Payment_Method", "Region", "City"]:
        if col in df.columns:
            n_missing = int(df[col].isnull().sum())
            if n_missing:
                mode_val = df[col].mode(dropna=True)
                fill_val = mode_val.iloc[0] if not mode_val.empty else "Unknown"
                df[col] = df[col].fillna(fill_val)
                log[f"{col}_filled_with_mode"] = n_missing

    # Drop rows still missing anything critical (IDs, dates, amounts)
    critical_cols = ["Transaction_ID", "Date", "Total_Amount", "Product_Name", "Category"]
    before = len(df)
    df = df.dropna(subset=[c for c in critical_cols if c in df.columns])
    log["rows_dropped_critical_na"] = before - len(df)

    # --- 3. Fix dtypes -------------------------------------------------
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["Date"])
    log["rows_dropped_bad_date"] = before - len(df)

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(1).astype(int)
    df["Unit_Price"] = pd.to_numeric(df["Unit_Price"], errors="coerce")
    df["Discount_Percent"] = pd.to_numeric(df["Discount_Percent"], errors="coerce").fillna(0)
    df["Total_Amount"] = pd.to_numeric(df["Total_Amount"], errors="coerce")
    df = df.dropna(subset=["Unit_Price", "Total_Amount"])

    # Remove nonsensical rows (negative/zero prices or quantities)
    before = len(df)
    df = df[(df["Unit_Price"] > 0) & (df["Quantity"] > 0) & (df["Total_Amount"] > 0)]
    log["rows_dropped_invalid_values"] = before - len(df)

    # --- 4. Derived columns ---------------------------------------------
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["MonthName"] = df["Date"].dt.strftime("%b")
    df["Weekday"] = df["Date"].dt.day_name()
    df["Week"] = df["Date"].dt.isocalendar().week.astype(int)

    # Final safety net: after filling missing values, two previously
    # "different" rows can become identical, or two rows can still share
    # the same Transaction_ID (the real-world definition of a duplicate
    # sales record). Remove those, keeping the first occurrence.
    before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["Transaction_ID"], keep="first")
    log["duplicates_removed_post_fill"] = before - len(df)

    df = df.reset_index(drop=True)
    log["final_row_count"] = len(df)

    return df, log


def get_available_fields(df: pd.DataFrame) -> dict:
    """
    Report which optional columns are present and contain usable data,
    so the UI can hide filters/sections for data that isn't in the
    current file instead of raising a KeyError.
    """
    optional_cols = ["Customer_ID", "Region", "City", "Payment_Method", "Sales_Channel"]
    return {col: (col in df.columns and df[col].notna().any()) for col in optional_cols}


def filter_data(
    df: pd.DataFrame,
    date_range=None,
    categories=None,
    regions=None,
    payment_methods=None,
    channels=None,
) -> pd.DataFrame:
    """Apply the sidebar filters to the cleaned dataframe."""
    out = df.copy()

    if date_range and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        out = out[(out["Date"] >= start) & (out["Date"] <= end)]

    if categories:
        out = out[out["Category"].isin(categories)]

    if regions:
        out = out[out["Region"].isin(regions)]

    if payment_methods:
        out = out[out["Payment_Method"].isin(payment_methods)]

    if channels:
        out = out[out["Sales_Channel"].isin(channels)]

    return out
