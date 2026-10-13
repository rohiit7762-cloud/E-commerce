"""Regression test suite for verified defect resolutions."""

from pathlib import Path

import pandas as pd

from app.analytics.engine import AnalyticsEngine
from app.database.connection import get_engine, init_db
from app.database.loader import load_transactions
from app.etl.transformer import transform_records
from app.etl.validator import validate_records


def test_defect_001_guest_checkout_null_safety():
    """
    Regression Test for DEFECT-001:
    Guest checkout transactions with null CustomerID must not raise ValueError
    and must NOT be discarded from revenue calculations.
    """
    raw_guest_data = pd.DataFrame(
        [
            {
                "InvoiceNo": "999001",
                "StockCode": "GUEST_ITEM",
                "Description": "Guest Purchased Item",
                "Quantity": 3,
                "InvoiceDate": "2023-04-01 12:00:00",
                "UnitPrice": 20.00,
                "CustomerID": None,  # Guest checkout
                "Country": "United Kingdom",
            }
        ]
    )

    accepted, rejected, metrics = validate_records(raw_guest_data)
    assert len(accepted) == 1
    assert len(rejected) == 0

    transformed = transform_records(accepted)
    assert len(transformed) == 1
    assert pd.isna(transformed.iloc[0]["customer_id"])
    assert transformed.iloc[0]["line_total"] == 60.00


def test_defect_002_repeated_loading_does_not_inflate_revenue(tmp_path: Path):
    """
    Regression Test for DEFECT-002:
    Repeated pipeline execution on identical data must not duplicate rows or inflate revenue.
    """
    db_file = tmp_path / "regression_db.db"
    engine = get_engine(f"sqlite:///{db_file}")
    init_db(engine)

    raw_data = pd.DataFrame(
        [
            {
                "InvoiceNo": "777001",
                "StockCode": "REG_ITEM_1",
                "Description": "Test Item 1",
                "Quantity": 2,
                "InvoiceDate": "2023-04-10 10:00:00",
                "UnitPrice": 50.00,
                "CustomerID": 555,
                "Country": "Germany",
            }
        ]
    )

    accepted, _, _ = validate_records(raw_data)
    transformed = transform_records(accepted)

    # Initial Load
    res1 = load_transactions(engine, transformed)
    assert res1["inserted_count"] == 1

    # Second Load of Identical Batch
    res2 = load_transactions(engine, transformed)
    assert res2["inserted_count"] == 0
    assert res2["skipped_count"] == 1

    # Verify Revenue through SQL
    analytics = AnalyticsEngine(engine)
    kpis = analytics.get_kpi_summary()
    assert kpis["gross_revenue"] == 100.00
    assert kpis["completed_orders"] == 1


def test_defect_003_whitespace_and_casing_normalization():
    """
    Regression Test for DEFECT-003:
    Stock codes with trailing/leading whitespace and lowercase characters must be
    normalized to uppercase trimmed strings to prevent duplicate dimension entries.
    """
    raw_data = pd.DataFrame(
        [
            {
                "InvoiceNo": "888001",
                "StockCode": "  abc123z  ",
                "Description": "   Sample Description   ",
                "Quantity": 1,
                "InvoiceDate": "2023-04-15 09:00:00",
                "UnitPrice": 10.00,
                "CustomerID": 100,
                "Country": "  United Kingdom  ",
            }
        ]
    )

    accepted, _, _ = validate_records(raw_data)
    transformed = transform_records(accepted)

    row = transformed.iloc[0]
    assert row["stock_code"] == "ABC123Z"
    assert row["description"] == "Sample Description"
    assert row["country"] == "United Kingdom"
