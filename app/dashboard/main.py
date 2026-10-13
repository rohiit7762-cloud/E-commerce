"""E-commerce Sales Analytics & Automated QA Platform - Streamlit Dashboard.

Delivers interactive visual KPIs, financial trends, product intelligence,
and automated data quality health monitoring.
"""

import json
import sys
from pathlib import Path

# Ensure repository root is on sys.path to prevent module shadowing
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app.analytics.engine import AnalyticsEngine  # noqa: E402
from app.config.settings import settings  # noqa: E402
from app.dashboard.components import (  # noqa: E402
    build_monthly_trends_chart,
    build_regional_chart,
    build_rejection_donut_chart,
    build_top_products_chart,
    format_currency,
)
from app.database.connection import get_engine, init_db  # noqa: E402

# 1. Page Configuration
st.set_page_config(
    page_title="Schneider Electric | E-Commerce Sales & QA Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Modern Glassmorphic CSS Styling
st.markdown(
    """
    <style>
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #38bdf8;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px 8px 0 0;
        color: #cbd5e1;
        font-weight: 600;
        padding: 0 24px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.15) !important;
        border-bottom: 2px solid #38bdf8 !important;
        color: #38bdf8 !important;
    }

    /* Header branding */
    .brand-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .brand-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_analytics():
    """Cache database engine and analytics interface."""
    engine = get_engine()
    init_db(engine)
    return AnalyticsEngine(engine)


def run_dashboard():
    analytics = get_analytics()

    # Sidebar Controls
    with st.sidebar:
        st.markdown("### ⚙️ Platform Controls")

        # Database Status Badge
        dialect = analytics.engine.dialect.name.upper()
        st.info(f"Connected: **{dialect} Warehouse**")

        st.markdown("---")
        st.markdown("#### 🔍 Filter Criteria")

        # Distinct countries
        countries = ["All Countries"] + analytics.get_distinct_countries()
        selected_country = st.selectbox("Select Country", options=countries)
        country_filter = None if selected_country == "All Countries" else selected_country

        # Date filter toggle
        enable_date_filter = st.checkbox("Enable Date Window Filter", value=False)
        start_date_str, end_date_str = None, None
        if enable_date_filter:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From Date", pd.to_datetime("2010-12-01"))
                start_date_str = f"{start_date} 00:00:00"
            with col2:
                end_date = st.date_input("To Date", pd.to_datetime("2011-12-31"))
                end_date_str = f"{end_date} 23:59:59"

        st.markdown("---")
        st.markdown("#### ⚡ Pipeline Execution")
        if st.button("🔄 Refresh Data Cache"):
            st.cache_data.clear()
            st.rerun()

    # Main Header
    st.markdown(
        '<div class="brand-title">E-Commerce Sales Analytics & Automated QA Platform</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="brand-subtitle">Enterprise Data Pipeline, Dual-Verified SQL Analytics & Quality Assurance Telemetry</div>',
        unsafe_allow_html=True,
    )

    # Fetch Top-level KPIs
    kpis = analytics.get_kpi_summary(
        start_date=start_date_str,
        end_date=end_date_str,
        country=country_filter,
    )

    # Top KPI Metrics Row
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Net Revenue", format_currency(kpis["net_revenue"]))
    k2.metric("Gross Revenue", format_currency(kpis["gross_revenue"]))
    k3.metric("Total Refunds", format_currency(kpis["total_refunds"]))
    k4.metric("Completed Orders", f"{kpis['completed_orders']:,}")
    k5.metric("Avg Order Value", format_currency(kpis["average_order_value"]))
    k6.metric("Net Units Sold", f"{kpis['net_units_sold']:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 4 Main Analysis Tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📈 Revenue & Trends",
            "📦 Product & Customer Intelligence",
            "🛡️ Automated QA & Data Health",
            "📂 Data Explorer & Export",
        ]
    )

    # Tab 1: Revenue Trends & Regional Performance
    with tab1:
        c1, c2 = st.columns([3, 2])
        with c1:
            trends_df = analytics.get_monthly_trends(
                start_date=start_date_str,
                end_date=end_date_str,
                country=country_filter,
            )
            fig_trends = build_monthly_trends_chart(trends_df)
            st.plotly_chart(fig_trends, use_container_width=True)

        with c2:
            regional_df = analytics.get_regional_performance(
                start_date=start_date_str,
                end_date=end_date_str,
            )
            fig_regional = build_regional_chart(regional_df)
            st.plotly_chart(fig_regional, use_container_width=True)

        st.markdown("#### Monthly Performance Summary Table")
        if not trends_df.empty:
            st.dataframe(
                trends_df.style.format(
                    {
                        "gross_revenue": "£{:,.2f}",
                        "refund_amount": "£{:,.2f}",
                        "net_revenue": "£{:,.2f}",
                        "total_orders": "{:,}",
                        "units_sold": "{:,}",
                    }
                ),
                use_container_width=True,
            )
        else:
            st.info("No transaction records found for the selected filter criteria.")

    # Tab 2: Products & Customers
    with tab2:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### 🏆 Top Products by Net Revenue")
            products_df = analytics.get_product_performance(
                limit=10,
                start_date=start_date_str,
                end_date=end_date_str,
                country=country_filter,
            )
            fig_prod = build_top_products_chart(products_df)
            st.plotly_chart(fig_prod, use_container_width=True)

        with col_p2:
            st.markdown("#### 👥 Top Customers by Spend")
            cust_df = analytics.get_customer_frequency(
                limit=10,
                start_date=start_date_str,
                end_date=end_date_str,
                country=country_filter,
            )
            if not cust_df.empty:
                st.dataframe(
                    cust_df.style.format(
                        {
                            "net_spend": "£{:,.2f}",
                            "avg_spend_per_order": "£{:,.2f}",
                            "total_orders": "{:,}",
                        }
                    ),
                    use_container_width=True,
                )

    # Tab 3: QA Health & Telemetry
    with tab3:
        st.markdown("### 🛡️ Pipeline Data Quality Health & Execution Audit")

        # Load latest quality report from disk if exists
        reports_dir = Path(settings.REPORTS_DIR)
        report_files = sorted(
            reports_dir.glob("dq_report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )

        if report_files:
            latest_report_file = report_files[0]
            with open(latest_report_file, "r", encoding="utf-8") as rf:
                dq_data = json.load(rf)

            q1, q2, q3, q4 = st.columns(4)
            summary = dq_data["summary"]
            q1.metric("Latest Raw Records", f"{summary['total_raw_records']:,}")
            q2.metric("Accepted Clean Records", f"{summary['accepted_records']:,}")
            q3.metric("Quarantined Failures", f"{summary['rejected_records']:,}")
            q4.metric("Acceptance Quality Rate", f"{summary['acceptance_rate_pct']}%")

            reasons = dq_data.get("rejection_breakdown", {})
            col_chart, col_sample = st.columns([1, 1])
            with col_chart:
                fig_donut = build_rejection_donut_chart(reasons)
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_sample:
                st.markdown("#### Quarantined Rejections Audit Sample")
                rejected_csv_path = Path(settings.REJECTED_RECORDS_PATH)
                if rejected_csv_path.exists():
                    rej_sample = pd.read_csv(rejected_csv_path, nrows=10)
                    st.dataframe(rej_sample, use_container_width=True)
                else:
                    st.info("No quarantined records file present.")
        else:
            st.info("No data quality report generated yet. Run the ETL pipeline to generate audit telemetry.")

        st.markdown("---")
        st.markdown("#### 📜 Database Ingestion Audit Log")
        audit_df = analytics.get_audit_history()
        if not audit_df.empty:
            st.dataframe(
                audit_df.style.format(
                    {
                        "raw_count": "{:,}",
                        "accepted_count": "{:,}",
                        "rejected_count": "{:,}",
                        "inserted_count": "{:,}",
                        "skipped_count": "{:,}",
                        "gross_revenue": "£{:,.2f}",
                        "net_revenue": "£{:,.2f}",
                    }
                ),
                use_container_width=True,
            )

    # Tab 4: Live Data Explorer & Export
    with tab4:
        st.markdown("### 📂 Filtered Fact Transactions Explorer")
        sql_export = """
        SELECT record_id, invoice_no, stock_code, quantity, unit_price, line_total,
               invoice_date, country, is_cancellation, year_month
        FROM fact_transactions
        WHERE (:start_date IS NULL OR invoice_date >= :start_date)
          AND (:end_date IS NULL OR invoice_date <= :end_date)
          AND (:country IS NULL OR country = :country)
        ORDER BY invoice_date DESC
        LIMIT 500;
        """
        with analytics.engine.connect() as conn:
            export_df = pd.read_sql_query(
                sql_export,
                conn,
                params={
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "country": country_filter,
                },
            )

        st.dataframe(export_df, use_container_width=True)
        csv_bytes = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered Results (CSV)",
            data=csv_bytes,
            file_name="filtered_ecommerce_analytics.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    run_dashboard()
