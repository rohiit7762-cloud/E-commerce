"""Integration tests for SQL analytical queries and dual verification with Pandas."""

import os
from pathlib import Path

import pytest

from app.analytics.engine import AnalyticsEngine
from app.analytics.pandas_verifier import compute_pandas_kpis
from app.database.connection import get_engine, init_db
from app.database.loader import load_transactions
from app.database.models import Base
from app.etl.pipeline import run_etl

FIXTURE_PATH = "test-data/synthetic_transactions.csv"


@pytest.fixture(scope="module")
def populated_analytics_engine(tmp_path_factory):
    """Provide an AnalyticsEngine backed by an isolated database loaded with deterministic test data."""
    env_db_url = os.environ.get("DATABASE_URL")
    if env_db_url and "postgresql" in env_db_url:
        engine = get_engine(env_db_url)
        Base.metadata.drop_all(engine)
        init_db(engine)
    else:
        tmp_dir = tmp_path_factory.mktemp("analytics_test")
        db_file = tmp_dir / "analytics_test.db"
        db_url = f"sqlite:///{db_file}"
        engine = get_engine(db_url)
        init_db(engine)

    etl_result = run_etl(FIXTURE_PATH)
    load_transactions(engine, etl_result.accepted_df)

    yield AnalyticsEngine(engine), etl_result.accepted_df

    if env_db_url and "postgresql" in env_db_url:
        Base.metadata.drop_all(engine)


def test_sql_kpis_match_manual_baseline(populated_analytics_engine):
    """
    Gate 3 Assertion 1:
    SQL queries must match manually calculated financial numbers for the deterministic fixture.
    """
    engine, _ = populated_analytics_engine
    sql_kpis = engine.get_kpi_summary()

    # Exact manual baseline verification
    assert sql_kpis["gross_revenue"] == 280.00
    assert sql_kpis["total_refunds"] == -10.00
    assert sql_kpis["net_revenue"] == 270.00
    assert sql_kpis["total_invoices"] == 6
    assert sql_kpis["completed_orders"] == 5
    assert sql_kpis["cancelled_orders"] == 1
    assert sql_kpis["average_order_value"] == 56.00  # 280.00 / 5
    assert sql_kpis["net_units_sold"] == 16


def test_sql_kpis_match_pandas_dual_verification(populated_analytics_engine):
    """
    Gate 3 Assertion 2:
    Dual-verification: SQL query outputs must match Pandas calculations across varied filters.
    """
    engine, df = populated_analytics_engine

    filter_scenarios = [
        # Scenario A: No filters (entire dataset)
        {"start_date": None, "end_date": None, "country": None},
        # Scenario B: Date lower bound
        {"start_date": "2023-02-01", "end_date": None, "country": None},
        # Scenario C: Closed Date window (January only)
        {"start_date": "2023-01-01", "end_date": "2023-01-31", "country": None},
        # Scenario D: Country filter
        {"start_date": None, "end_date": None, "country": "United Kingdom"},
        # Scenario E: France country filter
        {"start_date": None, "end_date": None, "country": "France"},
        # Scenario F: Boundary condition: non-matching filter (empty slice)
        {"start_date": "2099-01-01", "end_date": "2099-12-31", "country": None},
    ]

    for scenario in filter_scenarios:
        sql_metrics = engine.get_kpi_summary(
            start_date=scenario["start_date"],
            end_date=scenario["end_date"],
            country=scenario["country"],
        )
        pandas_metrics = compute_pandas_kpis(
            df,
            start_date=scenario["start_date"],
            end_date=scenario["end_date"],
            country=scenario["country"],
        )

        assert sql_metrics["gross_revenue"] == pytest.approx(pandas_metrics["gross_revenue"], 0.01)
        assert sql_metrics["total_refunds"] == pytest.approx(pandas_metrics["total_refunds"], 0.01)
        assert sql_metrics["net_revenue"] == pytest.approx(pandas_metrics["net_revenue"], 0.01)
        assert sql_metrics["total_invoices"] == pandas_metrics["total_invoices"]
        assert sql_metrics["completed_orders"] == pandas_metrics["completed_orders"]
        assert sql_metrics["cancelled_orders"] == pandas_metrics["cancelled_orders"]
        assert sql_metrics["average_order_value"] == pytest.approx(
            pandas_metrics["average_order_value"], 0.01
        )
        assert sql_metrics["net_units_sold"] == pandas_metrics["net_units_sold"]


def test_sql_monthly_trends(populated_analytics_engine):
    """Verify monthly aggregation logic."""
    engine, _ = populated_analytics_engine
    trends_df = engine.get_monthly_trends()

    assert not trends_df.empty
    # Expect 3 months: 2023-01, 2023-02, 2023-03
    months = trends_df["year_month"].tolist()
    assert "2023-01" in months
    assert "2023-02" in months
    assert "2023-03" in months


def test_sql_product_performance(populated_analytics_engine):
    """Verify product-level aggregation."""
    engine, _ = populated_analytics_engine
    products_df = engine.get_product_performance(limit=5)

    assert not products_df.empty
    top_product = products_df.iloc[0]
    # Product Beta (ITEM_B) has net revenue = 120.00 (Row 2: 1*20, Row 13: 5*20)
    assert top_product["stock_code"] == "ITEM_B"
    assert top_product["net_revenue"] == 120.00
    assert top_product["units_sold"] == 6


def test_sql_empty_database_boundary(tmp_path: Path):
    """Verify that querying an empty database returns zeros gracefully without error."""
    db_file = tmp_path / "empty_db.db"
    engine = get_engine(f"sqlite:///{db_file}")
    init_db(engine)

    analytics = AnalyticsEngine(engine)
    kpis = analytics.get_kpi_summary()

    assert kpis["gross_revenue"] == 0.0
    assert kpis["total_refunds"] == 0.0
    assert kpis["net_revenue"] == 0.0
    assert kpis["completed_orders"] == 0
    assert kpis["average_order_value"] == 0.0


def test_sql_customer_frequency_and_regional(populated_analytics_engine):
    """Verify customer frequency, regional performance, and metadata retrieval."""
    engine, _ = populated_analytics_engine

    # Customer frequency
    cust_df = engine.get_customer_frequency(limit=5)
    assert not cust_df.empty
    assert "customer_identifier" in cust_df.columns
    assert "net_spend" in cust_df.columns

    # Regional performance
    reg_df = engine.get_regional_performance()
    assert not reg_df.empty
    assert "country" in reg_df.columns
    assert "United Kingdom" in reg_df["country"].values

    # Distinct countries
    countries = engine.get_distinct_countries()
    assert "United Kingdom" in countries
    assert "Germany" in countries

    # Audit history
    audit_df = engine.get_audit_history()
    assert not audit_df.empty
    assert "status" in audit_df.columns
    assert audit_df.iloc[0]["status"] == "SUCCESS"
