"""Unit tests for validator module."""

import pandas as pd
import pytest

from app.etl.validator import ValidationError, validate_records, validate_schema


def test_validate_schema_missing_column_raises_error():
    df = pd.DataFrame({"InvoiceNo": ["1"], "StockCode": ["A"]})
    with pytest.raises(ValidationError, match="Missing required columns"):
        validate_schema(df)


def test_validate_records_rejections():
    data = [
        # Missing InvoiceNo
        {
            "InvoiceNo": None,
            "StockCode": "A",
            "Description": "D",
            "Quantity": 1,
            "InvoiceDate": "2023-01-01",
            "UnitPrice": 10.0,
            "CustomerID": 1,
            "Country": "UK",
        },
        # Missing StockCode
        {
            "InvoiceNo": "1",
            "StockCode": "  ",
            "Description": "D",
            "Quantity": 1,
            "InvoiceDate": "2023-01-01",
            "UnitPrice": 10.0,
            "CustomerID": 1,
            "Country": "UK",
        },
        # Zero Quantity
        {
            "InvoiceNo": "2",
            "StockCode": "B",
            "Description": "D",
            "Quantity": 0,
            "InvoiceDate": "2023-01-01",
            "UnitPrice": 10.0,
            "CustomerID": 1,
            "Country": "UK",
        },
        # Negative UnitPrice
        {
            "InvoiceNo": "3",
            "StockCode": "C",
            "Description": "D",
            "Quantity": 1,
            "InvoiceDate": "2023-01-01",
            "UnitPrice": -2.5,
            "CustomerID": 1,
            "Country": "UK",
        },
        # Zero UnitPrice
        {
            "InvoiceNo": "4",
            "StockCode": "D",
            "Description": "D",
            "Quantity": 1,
            "InvoiceDate": "2023-01-01",
            "UnitPrice": 0.0,
            "CustomerID": 1,
            "Country": "UK",
        },
        # Valid Row
        {
            "InvoiceNo": "5",
            "StockCode": "E",
            "Description": "D",
            "Quantity": 2,
            "InvoiceDate": "2023-01-01",
            "UnitPrice": 15.0,
            "CustomerID": 2,
            "Country": "UK",
        },
        # Duplicate of Valid Row
        {
            "InvoiceNo": "5",
            "StockCode": "E",
            "Description": "D",
            "Quantity": 2,
            "InvoiceDate": "2023-01-01",
            "UnitPrice": 15.0,
            "CustomerID": 2,
            "Country": "UK",
        },
        # Guest checkout (missing CustomerID) -> VALID
        {
            "InvoiceNo": "6",
            "StockCode": "F",
            "Description": "D",
            "Quantity": 1,
            "InvoiceDate": "2023-01-01",
            "UnitPrice": 5.0,
            "CustomerID": None,
            "Country": "UK",
        },
    ]
    df = pd.DataFrame(data)
    accepted, rejected, metrics = validate_records(df)

    assert len(accepted) == 2  # Row 5 and Row 6 (guest)
    assert len(rejected) == 6

    rejection_reasons = rejected["rejection_reason"].tolist()
    assert "MISSING_INVOICE_NO" in rejection_reasons
    assert "MISSING_STOCK_CODE" in rejection_reasons
    assert "ZERO_OR_INVALID_QUANTITY" in rejection_reasons
    assert "INVALID_UNIT_PRICE" in rejection_reasons
    assert "DUPLICATE_ROW" in rejection_reasons
    assert metrics["duplicate_records"] == 1


def test_validate_empty_dataframe():
    df = pd.DataFrame(
        columns=[
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "CustomerID",
            "Country",
        ]
    )
    accepted, rejected, metrics = validate_records(df)
    assert len(accepted) == 0
    assert len(rejected) == 0
    assert metrics["total_records"] == 0
