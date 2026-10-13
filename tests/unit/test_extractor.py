"""Unit tests for extractor module."""

from pathlib import Path

import pytest

from app.etl.extractor import ExtractionError, extract_csv


def test_extract_missing_file_raises_error(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist.csv"
    with pytest.raises(ExtractionError, match="does not exist"):
        extract_csv(non_existent)


def test_extract_empty_file_raises_error(tmp_path: Path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ExtractionError, match="is empty"):
        extract_csv(empty_file)


def test_extract_valid_csv(tmp_path: Path):
    sample_file = tmp_path / "sample.csv"
    content = (
        "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country\n"
        "536365,85123A,WHITE HANGING HEART,6,2010-12-01 08:26:00,2.55,17850,United Kingdom\n"
        "536366,22633,HAND WARMER,6,2010-12-01 08:28:00,1.85,17850,United Kingdom\n"
    )
    sample_file.write_text(content, encoding="utf-8")

    df = extract_csv(sample_file)
    assert len(df) == 2
    assert "InvoiceNo" in df.columns
    assert df.iloc[0]["InvoiceNo"] == "536365"
    assert df.iloc[1]["StockCode"] == "22633"


def test_extract_with_nrows_limit(tmp_path: Path):
    sample_file = tmp_path / "sample_limit.csv"
    content = (
        "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country\n"
        "1,A,Item 1,1,2023-01-01,10.0,101,UK\n"
        "2,B,Item 2,2,2023-01-01,20.0,102,UK\n"
        "3,C,Item 3,3,2023-01-01,30.0,103,UK\n"
    )
    sample_file.write_text(content, encoding="utf-8")

    df = extract_csv(sample_file, nrows=2)
    assert len(df) == 2
