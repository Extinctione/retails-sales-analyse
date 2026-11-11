"""
app.py
------
Retail Sales Analysis and Visualization System
Main Streamlit application entry point.

Run with:
    python -m streamlit run app.py

Architecture:
    app.py                 -> UI / layout / user interaction only
    src/data_processing.py -> loading + cleaning + multi-schema mapping
    src/analytics.py       -> business metric calculations
    src/charts_plotly.py   -> interactive Plotly charts for the dashboard
    src/visualizations.py  -> matplotlib/seaborn charts for the PDF report
    src/report_generator.py-> PDF report builder (ReportLab)
"""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from src import data_processing as dp
from src import analytics as an
from src import charts_plotly as cviz
from src import visualizations as viz
from src import report_generator as rg

# ------------------------------------------------------------------
# Page configuration (must be the first Streamlit call)
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Retail Sales Analytics Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).parent / "data" / "retail_sales_raw.csv"

# ------------------------------------------------------------------
# Premium SaaS styling (Linear / Stripe inspired)
# ------------------------------------------------------------------
# NOTE on the header-contrast fix: newer Streamlit releases changed the
# internal DOM, so the old ".main { background-color: ... }" selector no
# longer matches anything, and the app silently falls back to Streamlit's
# native theme (which follows the OS/browser light-dark preference). That
# is what made dark navy heading text disappear against a dark background.
# This stylesheet (a) targets every current + legacy container selector so
# the light background always applies, and (b) gives the header its own
# explicit dark panel with forced white text, so it is readable no matter
# what theme the surrounding app happens to render in. See also
# .streamlit/config.toml, which pins the app to a light theme at the
# Streamlit level as a second line of defence.
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,500,0,0" rel="stylesheet">
<style>
    :root {
        --bg: #F6F7FB;
        --surface: #FFFFFF;
        --border: #E5E7EB;
        --text-primary: #0B1222;
        --text-secondary: #5B6472;
        --text-muted: #94A0B2;
        --accent: #2563EB;
        --accent-dark: #1D4ED8;
        --accent-soft: #EFF4FF;
        --success: #059669;
        --success-soft: #ECFDF5;
        --warning: #D97706;
        --warning-soft: #FFFBEB;
        --danger: #DC2626;
        --danger-soft: #FEF2F2;
        --radius-lg: 16px;
        --radius-md: 12px;
        --radius-sm: 8px;
        --shadow-card: 0 1px 2px rgba(15,23,42,0.04), 0 1px 10px rgba(15,23,42,0.04);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif !important;
    }

    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined';
        font-size: 20px;
        vertical-align: middle;
        line-height: 1;
    }

    /* Force a light surface regardless of OS/browser theme + Streamlit version */
    html, body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main {
        background-color: var(--bg) !important;
    }
    [data-testid="stHeader"] { background-color: transparent !important; }
    .block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1280px; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ---------------- Sidebar ---------------- */
    section[data-testid="stSidebar"] {
        background-color: #0B1222;
        border-right: 1px solid #1B2440;
    }
    section[data-testid="stSidebar"] * { color: #E3E7EF !important; }
    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] .stDateInput input,
    section[data-testid="stSidebar"] .stTextInput input {
        background-color: #151D34 !important;
        border-color: #27304C !important;
        border-radius: var(--radius-sm) !important;
    }
    section[data-testid="stSidebar"] .stFileUploader section {
        background-color: #151D34 !important;
        border: 1.5px dashed #2E3A5C !important;
        border-radius: var(--radius-md) !important;
    }
    section[data-testid="stSidebar"] hr { border-color: #1B2440 !important; }
    section[data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: #121A30 !important;
        border: 1px solid #1B2440 !important;
        border-radius: var(--radius-sm) !important;
    }
    .sidebar-brand {
        display: flex; align-items: center; gap: 10px;
        padding: 2px 0 14px 0;
    }
    .sidebar-brand-icon {
        width: 34px; height: 34px; border-radius: 9px;
        background: linear-gradient(135deg, var(--accent), #7C3AED);
        display: flex; align-items: center; justify-content: center;
        font-size: 17px; flex-shrink: 0;
    }
    .sidebar-brand-text { font-size: 15.5px; font-weight: 700; color: #FFFFFF !important; line-height: 1.2; }
    .sidebar-brand-sub { font-size: 11.5px; color: #8992AB !important; }
    .sidebar-section-label {
        font-size: 11px; font-weight: 700; letter-spacing: 0.06em;
        color: #6B7694 !important; text-transform: uppercase; margin: 2px 0 8px 0;
    }

    /* ---------------- Hero header ---------------- */
    .hero-header {
        position: relative;
        isolation: isolate;
        background: linear-gradient(120deg, #0A1024 0%, #111A36 45%, #15224A 100%);
        border-radius: var(--radius-lg);
        padding: 30px 32px;
        margin-bottom: 22px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(10,16,36,0.18);
    }
    .hero-header::before {
        content: "";
        position: absolute; inset: 0;
        background: radial-gradient(600px circle at 85% -10%, rgba(37,99,235,0.35), transparent 60%);
        pointer-events: none;
    }
    .hero-header-inner { position: relative; z-index: 1; }
    .hero-title {
        font-size: 28px;
        font-weight: 800;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF;
        margin: 0 0 6px 0;
        letter-spacing: -0.01em;
        line-height: 1.25;
    }
    .hero-subtitle {
        font-size: 14.5px;
        font-weight: 400;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF;
        opacity: 0.88;
        margin: 0;
        line-height: 1.5;
    }
    .hero-meta-row { margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap; }
    .hero-pill {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.14);
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF;
        font-size: 12.5px; font-weight: 500;
        padding: 5px 12px; border-radius: 999px;
    }
    .hero-pill .material-symbols-outlined { font-size: 15px; }

    /* ---------------- KPI cards ---------------- */
    .kpi-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 18px 20px;
        box-shadow: var(--shadow-card);
        height: 128px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: box-shadow 0.15s ease, transform 0.15s ease;
    }
    .kpi-card:hover { box-shadow: 0 4px 18px rgba(15,23,42,0.09); transform: translateY(-1px); }
    .kpi-top-row { display: flex; align-items: center; justify-content: space-between; }
    .kpi-icon {
        width: 34px; height: 34px; border-radius: 9px;
        background: var(--accent-soft); color: var(--accent);
        display: flex; align-items: center; justify-content: center;
    }
    .kpi-label {
        font-size: 12.5px;
        font-weight: 600;
        color: var(--text-secondary);
        letter-spacing: 0.01em;
        cursor: help;
    }
    .kpi-value {
        font-size: 23px;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.15;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .kpi-sub { font-size: 12px; color: var(--text-muted); }

    /* ---------------- Section headers ---------------- */
    .section-header-row { display: flex; align-items: center; gap: 10px; margin: 6px 0 2px 0; }
    .section-icon {
        width: 30px; height: 30px; border-radius: 8px;
        background: var(--accent-soft); color: var(--accent);
        display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .section-title { font-size: 18px; font-weight: 700; color: var(--text-primary); margin: 0; }
    .section-sub { font-size: 13px; color: var(--text-secondary); margin: 2px 0 16px 40px; }

    /* ---------------- Empty states ---------------- */
    .empty-state {
        background: var(--surface);
        border: 1.5px dashed var(--border);
        border-radius: var(--radius-lg);
        padding: 36px 24px;
        text-align: center;
        color: var(--text-secondary);
    }
    .empty-state .material-symbols-outlined { font-size: 34px; color: var(--text-muted); }
    .empty-state-title { font-size: 14.5px; font-weight: 600; color: var(--text-primary); margin: 10px 0 4px 0; }
    .empty-state-sub { font-size: 13px; color: var(--text-secondary); max-width: 440px; margin: 0 auto; }

    /* ---------------- Quality stat chips ---------------- */
    .quality-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-md); padding: 16px 18px;
        box-shadow: var(--shadow-card); height: 96px;
    }
    .quality-value { font-size: 21px; font-weight: 700; color: var(--text-primary); }
    .quality-label { font-size: 12px; color: var(--text-secondary); font-weight: 600; margin-top: 2px; }
    .assumption-chip {
        display: flex; gap: 10px; align-items: flex-start;
        background: var(--warning-soft); border: 1px solid #FDE8C8;
        border-radius: var(--radius-sm); padding: 10px 12px; margin-bottom: 8px;
        font-size: 13px; color: #7C4A03;
    }
    .assumption-chip .material-symbols-outlined { font-size: 17px; color: var(--warning); margin-top: 1px; }

    /* ---------------- Misc ---------------- */
    [data-testid="stTabs"] button[role="tab"] { font-weight: 600; font-size: 13.5px; }
    .stDownloadButton button, .stButton button {
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
    }
    div[data-testid="stDataFrame"] { border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--border); }

    /* Responsive: let KPI / chart column rows wrap on narrow screens */
    @media (max-width: 900px) {
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        [data-testid="stHorizontalBlock"] > div { min-width: 240px !important; flex: 1 1 240px !important; }
        .hero-title { font-size: 22px; }
    }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------
# Small reusable UI components
# ------------------------------------------------------------------
def kpi_card(label, value, icon="analytics", sub="", help_text=""):
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-top-row">
                <span class="kpi-label" title="{help_text}">{label}</span>
                <div class="kpi-icon"><span class="material-symbols-outlined">{icon}</span></div>
            </div>
            <div>
                <div class="kpi-value" title="{value}">{value}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def section_header(title, subtitle="", icon="bar_chart"):
    st.markdown(f"""
        <div class="section-header-row">
            <div class="section-icon"><span class="material-symbols-outlined">{icon}</span></div>
            <div class="section-title">{title}</div>
        </div>
        <div class="section-sub">{subtitle}</div>
    """, unsafe_allow_html=True)


def empty_state(title, message, icon="info"):
    st.markdown(f"""
        <div class="empty-state">
            <span class="material-symbols-outlined">{icon}</span>
            <div class="empty-state-title">{title}</div>
            <div class="empty-state-sub">{message}</div>
        </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------------
# Cached data loading + cleaning
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_and_clean(file_bytes_or_path):
    raw = dp.load_csv(file_bytes_or_path)
    quality_before = dp.get_data_quality_report(raw)
    clean, log = dp.clean_data(raw)
    return raw, quality_before, clean, log


REQUIRED_COLUMNS_HELP = """
**Format A — simple**
`Order_ID, Order_Date, Product, Category, Unit_Price, Quantity`

**Format B — expanded**
`Transaction_ID, Date, Customer_ID, Product_ID, Product_Name, Category,
Discount_Percent, Total_Amount, Payment_Method, Region, City, Sales_Channel`

You can also mix and match columns from either format. At minimum every
file needs a **date**, a **product name** and a **category** column, plus
either a **Total_Amount** column or both **Unit_Price** and **Quantity**
so revenue can be calculated. Columns like Customer_ID, Payment_Method,
Region, City and Sales_Channel are optional — sections that depend on
them are simply hidden if they're not in your file.
"""

# ------------------------------------------------------------------
# Sidebar — data source + filters
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon">🛍️</div>
            <div>
                <div class="sidebar-brand-text">Retail Analytics</div>
                <div class="sidebar-brand-sub">Sales Analysis & Visualization</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="sidebar-section-label">Data Source</div>', unsafe_allow_html=True)
    source_mode = st.radio(
        "Data source", ["Use sample data", "Upload my own CSV"],
        label_visibility="collapsed", key="data_source_mode",
    )

    uploaded_file = None
    if source_mode == "Upload my own CSV":
        uploaded_file = st.file_uploader(
            "Upload a CSV file", type=["csv"],
            help="Upload a retail sales CSV. See 'What columns do I need?' below.",
        )
        with st.expander("ℹ️ What columns do I need?"):
            st.markdown(REQUIRED_COLUMNS_HELP)

    source = uploaded_file if uploaded_file is not None else str(DATA_PATH)

    try:
        with st.spinner("Loading and cleaning your data..."):
            raw_df, quality_before, clean_df, clean_log = load_and_clean(source)
    except dp.DataValidationError as e:
        st.error(f"⚠️ We couldn't use this file.\n\n{e}")
        with st.expander("ℹ️ What columns do I need?", expanded=True):
            st.markdown(REQUIRED_COLUMNS_HELP)
        st.info("Fix the file and upload it again, or switch to 'Use sample data' above.")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Something went wrong while loading this file: {e}")
        st.stop()

    if uploaded_file is not None:
        st.success(f"✅ Loaded **{uploaded_file.name}** — {len(clean_df):,} valid records.")

    st.divider()
    st.markdown('<div class="sidebar-section-label">Filters</div>', unsafe_allow_html=True)

    available = dp.get_available_fields(clean_df)

    min_date, max_date = clean_df["Date"].min().date(), clean_df["Date"].max().date()
    date_range = st.date_input(
        "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date,
        key="filter_date_range",
    )

    categories = st.multiselect(
        "Category", sorted(clean_df["Category"].unique()), default=[], key="filter_categories",
    )

    regions = []
    if available["Region"]:
        regions = st.multiselect(
            "Region", sorted(clean_df["Region"].dropna().unique()), default=[], key="filter_regions",
        )

    payment_methods = []
    if available["Payment_Method"]:
        payment_methods = st.multiselect(
            "Payment Method", sorted(clean_df["Payment_Method"].dropna().unique()), default=[],
            key="filter_payment_methods",
        )

    channels = []
    if available["Sales_Channel"]:
        channels = st.multiselect(
            "Sales Channel", sorted(clean_df["Sales_Channel"].dropna().unique()), default=[],
            key="filter_channels",
        )

    if st.button("🔄 Reset Filters", width='stretch'):
        for k in ["filter_date_range", "filter_categories", "filter_regions",
                  "filter_payment_methods", "filter_channels", "explorer_search"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.divider()
    st.caption(
        f"🧹 {quality_before['duplicate_rows']} duplicate row(s) and "
        f"{quality_before['missing_values_total']} missing value(s) were found "
        f"and handled automatically. See the **Data Quality** tab for details."
    )

# ------------------------------------------------------------------
# Apply filters
# ------------------------------------------------------------------
date_range_val = date_range if isinstance(date_range, tuple) and len(date_range) == 2 else (min_date, max_date)

filtered_df = dp.filter_data(
    clean_df,
    date_range=date_range_val,
    categories=categories or None,
    regions=regions or None,
    payment_methods=payment_methods or None,
    channels=channels or None,
)

# ------------------------------------------------------------------
# Hero header  (text is unchanged per spec — styling only)
# ------------------------------------------------------------------
source_label = f'📁 Custom dataset: {uploaded_file.name}' if uploaded_file is not None else '📊 Sample dataset'
st.markdown(f"""
<div class="hero-header">
    <div class="hero-header-inner">
        <div class="hero-title">Retail Sales Analytics Dashboard</div>
        <div class="hero-subtitle">A complete view of revenue, products, customers and regional performance</div>
        <div class="hero-meta-row">
            <span class="hero-pill"><span class="material-symbols-outlined">database</span>{source_label}</span>
            <span class="hero-pill"><span class="material-symbols-outlined">receipt_long</span>{len(filtered_df):,} records in view</span>
            <span class="hero-pill"><span class="material-symbols-outlined">event</span>{min_date.strftime('%d %b %Y')} – {max_date.strftime('%d %b %Y')}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if filtered_df.empty:
    empty_state(
        "No records match your filters",
        "Try widening the date range or clearing some filters in the sidebar, "
        "then use the 'Reset Filters' button to start over.",
        icon="filter_alt_off",
    )
    st.stop()

# ------------------------------------------------------------------
# KPI Cards  (6 cards, 2 rows of 3)
# ------------------------------------------------------------------
kpis = an.get_kpis(filtered_df)

row1 = st.columns(3)
with row1[0]:
    kpi_card("TOTAL REVENUE", f"₹{kpis['total_revenue']:,.0f}", icon="payments",
              sub=f"{len(filtered_df):,} line items",
              help_text="The sum of Total_Amount across every order currently in view.")
with row1[1]:
    kpi_card("TRANSACTIONS", f"{kpis['total_transactions']:,}", icon="receipt_long",
              sub="Unique orders",
              help_text="The number of distinct orders / transaction IDs in view.")
with row1[2]:
    kpi_card("AVG ORDER VALUE", f"₹{kpis['avg_order_value']:,.0f}", icon="trending_up",
              sub="Per transaction",
              help_text="Total Revenue divided by the number of orders — how much a typical order is worth.")

row2 = st.columns(3)
with row2[0]:
    kpi_card("UNITS SOLD", f"{kpis['total_quantity']:,}", icon="inventory_2",
              sub="Total quantity",
              help_text="The sum of the Quantity column across every order in view.")
with row2[1]:
    kpi_card("BEST-SELLING PRODUCT", f"{kpis['top_product']}", icon="stars",
              sub="By revenue",
              help_text="The single product that generated the most revenue in the current view.")
with row2[2]:
    customers_sub = f"{kpis['unique_customers']:,} customers" if kpis['unique_customers'] is not None else "Customer data not in file"
    kpi_card("TOP CATEGORY", f"{kpis['top_category']}", icon="category",
              sub=customers_sub,
              help_text="The product category that generated the most revenue in the current view.")

st.write("")

# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tab_trends, tab_products, tab_categories, tab_perf, tab_data, tab_quality, tab_report = st.tabs(
    ["📈 Revenue Trends", "🏆 Products", "📦 Categories", "🌍 Sales Performance",
     "🔍 Data Explorer", "🧹 Data Quality", "📄 PDF Report"]
)

# ---- TAB 1: Revenue Trends -------------------------------------------
with tab_trends:
    section_header("Revenue Over Time", "Monthly and daily revenue trends for the selected filters", "show_chart")

    monthly_df = an.monthly_sales(filtered_df)
    daily_df = an.daily_sales(filtered_df)
    heatmap_df = an.weekday_month_heatmap_data(filtered_df)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(cviz.plot_monthly_trend(monthly_df), width='stretch')
    with col2:
        st.plotly_chart(cviz.plot_daily_trend(daily_df), width='stretch')

    st.plotly_chart(cviz.plot_sales_heatmap(heatmap_df), width='stretch')

    section_header("Order Value Distribution", "How individual order values are spread across the dataset", "ssid_chart")
    st.plotly_chart(cviz.plot_order_value_distribution(filtered_df), width='stretch')

# ---- TAB 2: Products ---------------------------------------------------
with tab_products:
    section_header("Best-Selling Products", "Top products ranked by revenue", "emoji_events")
    top_n = st.slider("Number of top products to show", 5, 15, 10)
    top_products_df = an.best_selling_products(filtered_df, top_n=top_n)
    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.plotly_chart(cviz.plot_top_products(top_products_df), width='stretch')
    with col2:
        st.dataframe(
            top_products_df.style.format({"Revenue": "₹{:,.0f}"}),
            width='stretch', hide_index=True,
        )

# ---- TAB 3: Categories --------------------------------------------------
with tab_categories:
    section_header("Category-wise Revenue", "Revenue and quantity broken down by product category", "category")
    category_df = an.category_revenue(filtered_df)
    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.plotly_chart(cviz.plot_category_revenue(category_df), width='stretch')
    with col2:
        st.dataframe(
            category_df.style.format({"Revenue": "₹{:,.0f}", "Revenue_Share_%": "{:.1f}%"}),
            width='stretch', hide_index=True,
        )

# ---- TAB 4: Sales Performance (Region / Payment / Channel) --------------
with tab_perf:
    region_df = an.regional_performance(filtered_df)
    payment_df = an.payment_method_breakdown(filtered_df)
    channel_df = an.channel_breakdown(filtered_df)

    section_header("Regional Performance", "Revenue and average order value by region", "public")
    if region_df is not None:
        col1, col2 = st.columns([1.3, 1])
        with col1:
            st.plotly_chart(cviz.plot_regional_performance(region_df), width='stretch')
        with col2:
            st.dataframe(
                region_df.style.format({"Revenue": "₹{:,.0f}", "Avg_Order_Value": "₹{:,.0f}"}),
                width='stretch', hide_index=True,
            )
    else:
        empty_state("Regional data not available",
                     "Your dataset doesn't include a Region column, so regional analytics can't be shown. "
                     "Upload a file with a Region column to unlock this section.",
                     icon="public_off")

    st.write("")
    section_header("Payment Methods & Sales Channel", "How customers paid, and where the sale happened", "credit_card")
    col1, col2 = st.columns(2)
    with col1:
        if payment_df is not None:
            st.plotly_chart(cviz.plot_payment_methods(payment_df), width='stretch')
        else:
            empty_state("Payment data not available",
                         "Your dataset doesn't include a Payment_Method column.", icon="credit_card_off")
    with col2:
        if channel_df is not None:
            st.plotly_chart(cviz.plot_channel_breakdown(channel_df), width='stretch')
        else:
            empty_state("Sales channel data not available",
                         "Your dataset doesn't include a Sales_Channel column.", icon="storefront")

# ---- TAB 5: Data Explorer ------------------------------------------------
with tab_data:
    section_header("Cleaned, Filtered Dataset", f"{len(filtered_df):,} records match the current filters", "table_view")

    search_query = st.text_input(
        "🔍 Search records", key="explorer_search", placeholder="Search by product, category, or any text value…"
    )
    display_df = filtered_df
    if search_query:
        mask = filtered_df.astype(str).apply(
            lambda col: col.str.contains(search_query, case=False, na=False)
        ).any(axis=1)
        display_df = filtered_df[mask]
        st.caption(f"Found {len(display_df):,} matching record(s) for \"{search_query}\".")

    st.dataframe(display_df, width='stretch', height=420)

    csv_buffer = io.StringIO()
    display_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "⬇️ Download This Data (CSV)",
        data=csv_buffer.getvalue(),
        file_name="retail_sales_filtered.csv",
        mime="text/csv",
        width='content',
    )

# ---- TAB 6: Data Quality --------------------------------------------------
with tab_quality:
    section_header("Data Quality Report", "What we found in your file, and what was automatically fixed", "verified")

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.markdown(f"""<div class="quality-card"><div class="quality-value">{quality_before['total_rows']:,}</div>
            <div class="quality-label">Raw rows loaded</div></div>""", unsafe_allow_html=True)
    with q2:
        st.markdown(f"""<div class="quality-card"><div class="quality-value">{quality_before['duplicate_rows']:,}</div>
            <div class="quality-label">Duplicate rows found</div></div>""", unsafe_allow_html=True)
    with q3:
        st.markdown(f"""<div class="quality-card"><div class="quality-value">{quality_before['missing_values_total']:,}</div>
            <div class="quality-label">Missing values found</div></div>""", unsafe_allow_html=True)
    with q4:
        st.markdown(f"""<div class="quality-card"><div class="quality-value">{clean_log['final_row_count']:,}</div>
            <div class="quality-label">Clean rows used</div></div>""", unsafe_allow_html=True)

    st.write("")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Missing values by column (before cleaning)**")
        if quality_before["missing_by_column"]:
            missing_tbl = pd.DataFrame(
                list(quality_before["missing_by_column"].items()), columns=["Column", "Missing Values"]
            )
            st.dataframe(missing_tbl, hide_index=True, width='stretch')
        else:
            st.caption("No missing values were found. ✅")

    with col_b:
        st.markdown("**What we did automatically**")
        st.markdown(f"- Removed **{clean_log.get('duplicates_removed', 0)}** exact duplicate row(s)")
        st.markdown(f"- Removed **{clean_log.get('duplicates_removed_post_fill', 0)}** additional duplicate(s) found after cleaning")
        st.markdown(f"- Dropped **{clean_log.get('rows_dropped_critical_na', 0)}** row(s) missing critical fields (ID, date, product, category)")
        st.markdown(f"- Dropped **{clean_log.get('rows_dropped_bad_date', 0)}** row(s) with an unreadable date")
        st.markdown(f"- Dropped **{clean_log.get('rows_dropped_invalid_values', 0)}** row(s) with invalid/zero quantity or revenue")
        st.caption("Missing numeric values were filled with the column median; missing "
                   "categorical values were filled with the column's most common value.")

    assumptions = clean_log.get("assumptions", [])
    if assumptions:
        st.write("")
        st.markdown("**Assumptions made about your data**")
        for note in assumptions:
            st.markdown(f"""<div class="assumption-chip"><span class="material-symbols-outlined">info</span>
                <div>{note}</div></div>""", unsafe_allow_html=True)

    st.write("")
    st.markdown("**Columns detected in your file**")
    mapping = quality_before.get("column_mapping", {"mapped": {}, "unrecognised": []})
    if mapping["mapped"]:
        map_df = pd.DataFrame(list(mapping["mapped"].items()), columns=["Your column", "Used as"])
        st.dataframe(map_df, hide_index=True, width='stretch')
    if mapping["unrecognised"]:
        st.caption(f"Columns not used by the dashboard: {', '.join(mapping['unrecognised'])}")

# ---- TAB 7: PDF Report -------------------------------------------------
with tab_report:
    section_header("Generate Analytical Report", "Builds a PDF with KPIs, category revenue, top products and regional performance based on the current filters.", "picture_as_pdf")

    if st.button("📄 Generate PDF Report", type="primary"):
        with st.spinner("Building report..."):
            category_df = an.category_revenue(filtered_df)
            top_products_df = an.best_selling_products(filtered_df, top_n=10)
            region_df = an.regional_performance(filtered_df)
            monthly_df = an.monthly_sales(filtered_df)

            monthly_fig = viz.plot_monthly_trend(monthly_df)
            category_fig = viz.plot_category_revenue(category_df)

            filters_desc_parts = []
            if categories: filters_desc_parts.append(f"Category: {', '.join(categories)}")
            if regions: filters_desc_parts.append(f"Region: {', '.join(regions)}")
            if payment_methods: filters_desc_parts.append(f"Payment: {', '.join(payment_methods)}")
            if channels: filters_desc_parts.append(f"Channel: {', '.join(channels)}")
            filters_desc = "; ".join(filters_desc_parts) if filters_desc_parts else "All data (no filters applied)"

            pdf_bytes = rg.build_pdf_report(
                kpis=kpis, category_df=category_df, top_products_df=top_products_df,
                region_df=region_df, monthly_fig=monthly_fig, category_fig=category_fig,
                filters_summary=filters_desc,
            )
        st.success("✅ Report generated successfully.")
        st.download_button(
            "⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name="retail_sales_report.pdf",
            mime="application/pdf",
        )
    else:
        st.caption("Click the button above to build a downloadable PDF summary of everything currently in view.")

st.write("")
st.caption("Retail Sales Analysis and Visualization System — built with Python, Pandas, NumPy, Plotly, Matplotlib & Streamlit.")
