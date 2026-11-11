"""
app.py
------
Retail Sales Analysis and Visualization System
Main Streamlit application entry point.

Run with:
    streamlit run app.py

Architecture:
    app.py                -> UI / layout / user interaction only
    src/data_processing.py -> loading + cleaning data
    src/analytics.py       -> business metric calculations
    src/visualizations.py  -> matplotlib/seaborn chart builders
    src/report_generator.py-> PDF report builder (ReportLab)
"""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from src import data_processing as dp
from src import analytics as an
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
# Custom CSS — professional light theme
# ------------------------------------------------------------------
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Segoe UI', 'Inter', sans-serif; }

    .main { background-color: #F8FAFC; }

    /* Hide default Streamlit chrome we don't need */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* KPI card */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        height: 118px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-label {
        font-size: 13px;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #111827;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 12px;
        color: #9CA3AF;
        margin-top: 4px;
    }

    /* Section headers */
    .section-title {
        font-size: 19px;
        font-weight: 700;
        color: #111827;
        margin-top: 8px;
        margin-bottom: 2px;
        border-left: 4px solid #2563EB;
        padding-left: 10px;
    }
    .section-sub {
        font-size: 13px;
        color: #6B7280;
        padding-left: 14px;
        margin-bottom: 14px;
    }

    /* App title banner */
    .app-header {
        padding: 6px 0 14px 0;
    }
    .app-title {
        font-size: 30px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0px;
    }
    .app-subtitle {
        font-size: 14px;
        color: #6B7280;
    }

    section[data-testid="stSidebar"] {
        background-color: #111827;
    }
    section[data-testid="stSidebar"] * { color: #E5E7EB !important; }
    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #1F2937;
    }
</style>
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


def kpi_card(label, value, sub=""):
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------------
# Sidebar — data source + filters
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛍️ Retail Analytics")
    st.caption("Sales Analysis & Visualization System")
    st.divider()

    st.markdown("### 📁 Data Source")
    uploaded_file = st.file_uploader("Upload a CSV (optional)", type=["csv"])
    source = uploaded_file if uploaded_file is not None else str(DATA_PATH)

    try:
        raw_df, quality_before, clean_df, clean_log = load_and_clean(source)
    except Exception as e:
        st.error(f"Could not load data: {e}")
        st.stop()

    st.divider()
    st.markdown("### 🔎 Filters")

    min_date, max_date = clean_df["Date"].min().date(), clean_df["Date"].max().date()
    date_range = st.date_input(
        "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date,
    )

    categories = st.multiselect(
        "Category", sorted(clean_df["Category"].unique()), default=[]
    )
    regions = st.multiselect(
        "Region", sorted(clean_df["Region"].unique()), default=[]
    )
    payment_methods = st.multiselect(
        "Payment Method", sorted(clean_df["Payment_Method"].unique()), default=[]
    )
    channels = st.multiselect(
        "Sales Channel", sorted(clean_df["Sales_Channel"].unique()), default=[]
    )

    if st.button("🔄 Reset Filters", width='stretch'):
        st.rerun()

    st.divider()
    with st.expander("🧹 Data Cleaning Report"):
        st.write(f"**Raw rows loaded:** {quality_before['total_rows']}")
        st.write(f"**Duplicate rows found:** {quality_before['duplicate_rows']}")
        st.write(f"**Missing values found:** {quality_before['missing_values_total']}")
        st.write(f"**Rows after cleaning:** {clean_log['final_row_count']}")
        st.caption(
            "Missing numeric values filled with column median; missing "
            "categorical values filled with column mode; duplicate and "
            "invalid rows removed."
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

if filtered_df.empty:
    st.warning("No records match the selected filters. Please broaden your filter selection.")
    st.stop()

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.markdown("""
<div class="app-header">
    <div class="app-title">Retail Sales Analytics Dashboard</div>
    <div class="app-subtitle">A complete view of revenue, products, customers and regional performance</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# KPI Cards
# ------------------------------------------------------------------
kpis = an.get_kpis(filtered_df)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_card("Total Revenue", f"₹{kpis['total_revenue']:,.0f}", f"{len(filtered_df):,} records")
with c2:
    kpi_card("Transactions", f"{kpis['total_transactions']:,}")
with c3:
    kpi_card("Avg Order Value", f"₹{kpis['avg_order_value']:,.0f}")
with c4:
    kpi_card("Units Sold", f"{kpis['total_quantity']:,}")
with c5:
    kpi_card("Top Category", f"{kpis['top_category']}", f"{kpis['unique_customers']:,} customers")

st.write("")

# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tab_trends, tab_products, tab_geo, tab_data, tab_report = st.tabs(
    ["📈 Sales Trends", "🏆 Products & Categories", "🌍 Region & Payments",
     "📋 Data Explorer", "📄 PDF Report"]
)

# ---- TAB 1: Sales Trends -------------------------------------------
with tab_trends:
    st.markdown('<div class="section-title">Revenue Over Time</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Monthly and daily revenue trends for the selected filters</div>', unsafe_allow_html=True)

    monthly_df = an.monthly_sales(filtered_df)
    daily_df = an.daily_sales(filtered_df)
    heatmap_df = an.weekday_month_heatmap_data(filtered_df)

    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(viz.plot_monthly_trend(monthly_df), width='stretch')
    with col2:
        st.pyplot(viz.plot_daily_trend(daily_df), width='stretch')

    st.pyplot(viz.plot_sales_heatmap(heatmap_df), width='stretch')

    st.markdown('<div class="section-title">Order Value Distribution</div>', unsafe_allow_html=True)
    st.pyplot(viz.plot_order_value_distribution(filtered_df), width='stretch')

# ---- TAB 2: Products & Categories -----------------------------------
with tab_products:
    st.markdown('<div class="section-title">Category-wise Revenue</div>', unsafe_allow_html=True)
    category_df = an.category_revenue(filtered_df)
    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.pyplot(viz.plot_category_revenue(category_df), width='stretch')
    with col2:
        st.dataframe(
            category_df.style.format({"Revenue": "₹{:,.0f}", "Revenue_Share_%": "{:.1f}%"}),
            width='stretch', hide_index=True,
        )

    st.markdown('<div class="section-title">Best-Selling Products</div>', unsafe_allow_html=True)
    top_n = st.slider("Number of top products to show", 5, 15, 10)
    top_products_df = an.best_selling_products(filtered_df, top_n=top_n)
    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.pyplot(viz.plot_top_products(top_products_df), width='stretch')
    with col2:
        st.dataframe(
            top_products_df.style.format({"Revenue": "₹{:,.0f}"}),
            width='stretch', hide_index=True,
        )

# ---- TAB 3: Region & Payments ----------------------------------------
with tab_geo:
    st.markdown('<div class="section-title">Regional Performance</div>', unsafe_allow_html=True)
    region_df = an.regional_performance(filtered_df)
    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.pyplot(viz.plot_regional_performance(region_df), width='stretch')
    with col2:
        st.dataframe(
            region_df.style.format({"Revenue": "₹{:,.0f}", "Avg_Order_Value": "₹{:,.0f}"}),
            width='stretch', hide_index=True,
        )

    st.markdown('<div class="section-title">Payment Methods & Sales Channel</div>', unsafe_allow_html=True)
    payment_df = an.payment_method_breakdown(filtered_df)
    channel_df = an.channel_breakdown(filtered_df)
    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(viz.plot_payment_methods(payment_df), width='stretch')
    with col2:
        st.pyplot(viz.plot_channel_breakdown(channel_df), width='stretch')

# ---- TAB 4: Data Explorer ---------------------------------------------
with tab_data:
    st.markdown('<div class="section-title">Cleaned, Filtered Dataset</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{len(filtered_df):,} records match the current filters</div>', unsafe_allow_html=True)
    st.dataframe(filtered_df, width='stretch', height=420)

    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "⬇️ Download Filtered Data (CSV)",
        data=csv_buffer.getvalue(),
        file_name="retail_sales_filtered.csv",
        mime="text/csv",
        width='content',
    )

# ---- TAB 5: PDF Report -------------------------------------------------
with tab_report:
    st.markdown('<div class="section-title">Generate Analytical Report</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Builds a PDF with KPIs, category revenue, top products '
        'and regional performance based on the current filters.</div>',
        unsafe_allow_html=True,
    )

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
        st.success("Report generated successfully.")
        st.download_button(
            "⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name="retail_sales_report.pdf",
            mime="application/pdf",
        )

st.write("")
st.caption("Retail Sales Analysis and Visualization System — built with Python, Pandas, NumPy, Matplotlib, Seaborn & Streamlit.")
