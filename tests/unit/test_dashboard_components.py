"""Unit tests for Streamlit dashboard visualization components."""

import pandas as pd

from app.dashboard.components import (
    build_monthly_trends_chart,
    build_regional_chart,
    build_rejection_donut_chart,
    build_top_products_chart,
    format_currency,
)


def test_format_currency():
    assert format_currency(100.0) == "£100.00"
    assert format_currency(1234567.89) == "£1,234,567.89"
    assert format_currency(0.0) == "£0.00"
    assert format_currency(-50.5) == "£-50.50"


def test_build_monthly_trends_chart():
    empty_fig = build_monthly_trends_chart(pd.DataFrame())
    assert empty_fig is not None

    df = pd.DataFrame(
        {
            "year_month": ["2023-01", "2023-02"],
            "gross_revenue": [100.0, 150.0],
            "refund_amount": [-10.0, -5.0],
            "net_revenue": [90.0, 145.0],
        }
    )
    fig = build_monthly_trends_chart(df)
    assert len(fig.data) == 3  # Gross, Net, Refund


def test_build_top_products_chart():
    empty_fig = build_top_products_chart(pd.DataFrame())
    assert empty_fig is not None

    df = pd.DataFrame(
        {
            "stock_code": ["P1", "P2"],
            "description": ["Product 1", "Product 2"],
            "net_revenue": [500.0, 300.0],
        }
    )
    fig = build_top_products_chart(df)
    assert fig is not None


def test_build_regional_chart():
    empty_fig = build_regional_chart(pd.DataFrame())
    assert empty_fig is not None

    df = pd.DataFrame(
        {
            "country": ["United Kingdom", "Germany"],
            "net_revenue": [1000.0, 400.0],
        }
    )
    fig = build_regional_chart(df)
    assert fig is not None


def test_build_rejection_donut_chart():
    empty_fig = build_rejection_donut_chart({})
    assert empty_fig is not None

    reasons = {"INVALID_UNIT_PRICE": 10, "DUPLICATE_ROW": 5}
    fig = build_rejection_donut_chart(reasons)
    assert len(fig.data) == 1
