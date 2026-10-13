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

# 2. Modern Glassmorphic CSS Styling & Typography
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@600;700;800&display=swap');

    /* Global styles */
    .stApp {
        background: radial-gradient(circle at 15% 15%, #131d38 0%, #090d16 100%);
        color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Header Container */
    .header-banner {
        padding: 4px 0 16px 0;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.3);
        color: #38bdf8;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 9999px;
        margin-bottom: 8px;
    }
    .header-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff !important;
        margin: 0 0 4px 0;
        letter-spacing: -0.02em;
    }
    .header-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin: 0;
    }

    /* Metric Cards - Strict Prevention of Truncation */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(56, 189, 248, 0.5) !important;
        box-shadow: 0 8px 30px rgba(56, 189, 248, 0.15) !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-family: 'Outfit', 'Inter', sans-serif !important;
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }
    div[data-testid="stMetricValue"] > div {
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px 8px 0 0;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.15) !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-bottom: 2px solid #38bdf8 !important;
        color: #38bdf8 !important;
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
        st.success(f"Warehouse Engine: **{dialect}** (Live / Synced)")

        st.markdown("---")
        st.markdown("#### 🔍 Filter Criteria")

        # Distinct countries
        countries = ["All Countries"] + analytics.get_distinct_countries()
        selected_country = st.selectbox("Select Country", options=countries)
        country_filter = None if selected_country == "All Countries" else selected_country

        # Date Filter Presets
        st.markdown("#### 📅 Dataset Window Preset")
        preset = st.radio(
            "Quick Date Scope",
            options=[
                "All Records (Full Warehouse)",
                "2010–2011 (UCI Online Retail)",
                "2023 (QA Synthetic Fixture)",
                "Custom Date Range",
            ],
            index=0,
        )

        start_date_str, end_date_str = None, None
        if preset == "2010–2011 (UCI Online Retail)":
            start_date_str = "2010-12-01 00:00:00"
            end_date_str = "2011-12-31 23:59:59"
        elif preset == "2023 (QA Synthetic Fixture)":
            start_date_str = "2023-01-01 00:00:00"
            end_date_str = "2023-12-31 23:59:59"
        elif preset == "Custom Date Range":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From Date", pd.to_datetime("2010-12-01"))
                start_date_str = f"{start_date} 00:00:00"
            with col2:
                end_date = st.date_input("To Date", pd.to_datetime("2023-12-31"))
                end_date_str = f"{end_date} 23:59:59"

        st.markdown("---")
        st.markdown("#### ⚡ Pipeline Execution")
        if st.button("🔄 Refresh Data Cache", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Main Header
    st.markdown(
        """
        <div class="header-banner">
            <div class="badge-pill">⚡ SCHNEIDER ELECTRIC • INDUSTRIAL ANALYTICS & QA</div>
            <h1 class="header-title">E-Commerce Sales Analytics & QA Platform</h1>
            <p class="header-subtitle">Production ETL Pipeline • Dual-Verified SQL Warehouse • Automated QA & Test Telemetry</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Fetch Top-level KPIs
    kpis = analytics.get_kpi_summary(
        start_date=start_date_str,
        end_date=end_date_str,
        country=country_filter,
    )

    # Top KPI Metrics (Organized into 2 spacious rows of 3 to eliminate ellipsis truncation)
    row1_c1, row1_c2, row1_c3 = st.columns(3)
    with row1_c1:
        st.metric(
            label="Net Sales Revenue",
            value=format_currency(kpis["net_revenue"]),
            help="Total completed sales minus refunds and cancellations",
        )
    with row1_c2:
        st.metric(
            label="Gross Sales Revenue",
            value=format_currency(kpis["gross_revenue"]),
            help="Gross monetary value of all completed sales",
        )
    with row1_c3:
        st.metric(
            label="Total Refunds / Returns",
            value=format_currency(kpis["total_refunds"]),
            help="Sum of line totals from order returns and cancellations",
        )

    row2_c1, row2_c2, row2_c3 = st.columns(3)
    with row2_c1:
        st.metric(
            label="Completed Orders",
            value=f"{kpis['completed_orders']:,}",
            help="Total count of unique successful sales invoices",
        )
    with row2_c2:
        st.metric(
            label="Average Order Value (AOV)",
            value=format_currency(kpis["average_order_value"]),
            help="Gross Revenue divided by Completed Orders",
        )
    with row2_c3:
        st.metric(
            label="Net Units Dispatched",
            value=f"{kpis['net_units_sold']:,}",
            help="Total quantity of individual items sold",
        )

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

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
