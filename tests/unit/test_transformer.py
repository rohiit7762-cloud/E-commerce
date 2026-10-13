"""Unit tests for transformer module."""

import pandas as pd

from app.etl.transformer import generate_record_hash, transform_records


def test_transformer_computes_line_total_and_cancellation():
    data = [
        # Normal sale
        {
            "InvoiceNo": "100",
            "StockCode": "item_a",
            "Description": "Widget A",
            "Quantity": 3,
            "InvoiceDate": "2023-05-10 14:00:00",
            "UnitPrice": 12.50,
            "CustomerID": 12345,
            "Country": "United Kingdom",
        },
        # Cancellation with 'C' prefix
        {
            "InvoiceNo": "C101",
            "StockCode": "item_b",
            "Description": None,
            "Quantity": -2,
            "InvoiceDate": "2023-05-11 15:30:00",
            "UnitPrice": 10.00,
            "CustomerID": 12345,
            "Country": None,
        },
    ]
    df = pd.DataFrame(data)
    transformed = transform_records(df)

    assert len(transformed) == 2

    # Check row 1 (normal sale)
    row0 = transformed.iloc[0]
    assert row0["stock_code"] == "ITEM_A"  # Uppercased
    assert row0["line_total"] == 37.50
    assert not row0["is_cancellation"]
    assert row0["year_month"] == "2023-05"
    assert row0["description"] == "Widget A"
    assert row0["country"] == "United Kingdom"

    # Check row 2 (cancellation & imputed values)
    row1 = transformed.iloc[1]
    assert row1["line_total"] == -20.00
    assert row1["is_cancellation"]
    assert row1["description"] == "UNKNOWN PRODUCT"
    assert row1["country"] == "Unknown"


def test_deterministic_record_hash():
    row1 = pd.Series(
        {
            "InvoiceNo": "1000",
            "StockCode": "ABC",
            "InvoiceDate": "2023-01-01 10:00:00",
            "Quantity": 2,
            "UnitPrice": 15.00,
            "CustomerID": 999,
        }
    )
    row2 = pd.Series(
        {
            "InvoiceNo": "1000",
            "StockCode": "ABC",
            "InvoiceDate": "2023-01-01 10:00:00",
            "Quantity": 2,
            "UnitPrice": 15.00,
            "CustomerID": 999,
        }
    )
    row3 = pd.Series(
        {
            "InvoiceNo": "1001",
            "StockCode": "ABC",
            "InvoiceDate": "2023-01-01 10:00:00",
            "Quantity": 2,
            "UnitPrice": 15.00,
            "CustomerID": 999,
        }
    )

    hash1 = generate_record_hash(row1)
    hash2 = generate_record_hash(row2)
    hash3 = generate_record_hash(row3)

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 32
