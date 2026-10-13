"""
Dataset Preparation Script
Downloads the official UCI Online Retail dataset, saves the raw transaction data,
and produces a deterministic synthetic dataset with known, manually verifiable metrics.
"""

import io
import os
import urllib.request
import zipfile

import pandas as pd

UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
RAW_DATA_DIR = "data/raw"
TEST_DATA_DIR = "test-data"
FIXTURES_DIR = "tests/fixtures"


def download_uci_dataset(max_rows: int = 50000) -> str:
    """Download and extract UCI Online Retail dataset to CSV format."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    raw_csv_path = os.path.join(RAW_DATA_DIR, "online_retail.csv")

    if os.path.exists(raw_csv_path) and os.path.getsize(raw_csv_path) > 1000:
        print(f"Raw dataset already exists at {raw_csv_path}")
        return raw_csv_path

    print(f"Downloading UCI Online Retail dataset from {UCI_ZIP_URL}...")
    req = urllib.request.Request(UCI_ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        zip_data = resp.read()

    print("Extracting Online Retail.xlsx from zip archive...")
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        with z.open("Online Retail.xlsx") as f:
            print(f"Reading up to {max_rows} rows from Excel file...")
            df = pd.read_excel(f, nrows=max_rows)

    # Save exactly as raw CSV to preserve raw state
    df.to_csv(raw_csv_path, index=False)
    print(f"Preserved raw dataset saved to {raw_csv_path} ({len(df)} rows).")
    return raw_csv_path


def create_deterministic_fixtures():
    """
    Generate deterministic synthetic test data with exact known values for unit/integration/SQL QA.
    Contains:
    - Normal completed orders
    - Order cancellations (Invoice starts with 'C', negative quantity)
    - Missing CustomerIDs (guest checkouts)
    - Invalid UnitPrices (zero and negative)
    - Duplicate records
    - Missing Descriptions
    - Multiple countries
    """
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    os.makedirs(FIXTURES_DIR, exist_ok=True)

    records = [
        # Normal order 1: Invoice 100001, Customer 101, UK, 2 items
        {
            "InvoiceNo": "100001",
            "StockCode": "ITEM_A",
            "Description": "Product Alpha",
            "Quantity": 2,
            "InvoiceDate": "2023-01-10 10:00:00",
            "UnitPrice": 10.00,
            "CustomerID": 101,
            "Country": "United Kingdom",
        },
        {
            "InvoiceNo": "100001",
            "StockCode": "ITEM_B",
            "Description": "Product Beta",
            "Quantity": 1,
            "InvoiceDate": "2023-01-10 10:00:00",
            "UnitPrice": 20.00,
            "CustomerID": 101,
            "Country": "United Kingdom",
        },
        # Normal order 2: Invoice 100002, Customer 102, France, 1 item
        {
            "InvoiceNo": "100002",
            "StockCode": "ITEM_C",
            "Description": "Product Gamma",
            "Quantity": 4,
            "InvoiceDate": "2023-01-15 11:30:00",
            "UnitPrice": 15.00,
            "CustomerID": 102,
            "Country": "France",
        },
        # Duplicate row of order 2 item (to test duplicate deduction)
        {
            "InvoiceNo": "100002",
            "StockCode": "ITEM_C",
            "Description": "Product Gamma",
            "Quantity": 4,
            "InvoiceDate": "2023-01-15 11:30:00",
            "UnitPrice": 15.00,
            "CustomerID": 102,
            "Country": "France",
        },
        # Normal order 3: Invoice 100003, Customer 101, UK, repeat purchase in February
        {
            "InvoiceNo": "100003",
            "StockCode": "ITEM_A",
            "Description": "Product Alpha",
            "Quantity": 3,
            "InvoiceDate": "2023-02-05 14:15:00",
            "UnitPrice": 10.00,
            "CustomerID": 101,
            "Country": "United Kingdom",
        },
        # Cancellation order: Invoice C100004, Customer 101, UK (Return of 1 Item A)
        {
            "InvoiceNo": "C100004",
            "StockCode": "ITEM_A",
            "Description": "Product Alpha Return",
            "Quantity": -1,
            "InvoiceDate": "2023-02-10 09:00:00",
            "UnitPrice": 10.00,
            "CustomerID": 101,
            "Country": "United Kingdom",
        },
        # Normal order 4: Guest checkout (missing CustomerID) - valid business transaction
        {
            "InvoiceNo": "100005",
            "StockCode": "ITEM_D",
            "Description": "Product Delta",
            "Quantity": 2,
            "InvoiceDate": "2023-02-12 16:45:00",
            "UnitPrice": 25.00,
            "CustomerID": None,
            "Country": "Germany",
        },
        # Invalid Record 1: Negative UnitPrice (-5.00) -> MUST BE REJECTED
        {
            "InvoiceNo": "100006",
            "StockCode": "BAD_P1",
            "Description": "Damaged goods adjustment",
            "Quantity": 1,
            "InvoiceDate": "2023-02-15 10:00:00",
            "UnitPrice": -5.00,
            "CustomerID": 103,
            "Country": "United Kingdom",
        },
        # Invalid Record 2: Zero UnitPrice (0.00) -> MUST BE REJECTED (unless explicit free gift rule, here pricing anomaly)
        {
            "InvoiceNo": "100007",
            "StockCode": "BAD_P2",
            "Description": "Pricing Glitch",
            "Quantity": 5,
            "InvoiceDate": "2023-02-16 11:00:00",
            "UnitPrice": 0.00,
            "CustomerID": 104,
            "Country": "United Kingdom",
        },
        # Invalid Record 3: Missing InvoiceNo -> MUST BE REJECTED
        {
            "InvoiceNo": None,
            "StockCode": "ITEM_E",
            "Description": "Missing Invoice Number",
            "Quantity": 1,
            "InvoiceDate": "2023-02-17 12:00:00",
            "UnitPrice": 12.00,
            "CustomerID": 105,
            "Country": "United Kingdom",
        },
        # Invalid Record 4: Missing StockCode -> MUST BE REJECTED
        {
            "InvoiceNo": "100008",
            "StockCode": None,
            "Description": "Missing Stock Code",
            "Quantity": 2,
            "InvoiceDate": "2023-02-18 13:00:00",
            "UnitPrice": 8.00,
            "CustomerID": 106,
            "Country": "United Kingdom",
        },
        # Invalid Record 5: Zero Quantity -> MUST BE REJECTED
        {
            "InvoiceNo": "100009",
            "StockCode": "ITEM_F",
            "Description": "Zero Quantity Item",
            "Quantity": 0,
            "InvoiceDate": "2023-02-19 14:00:00",
            "UnitPrice": 15.00,
            "CustomerID": 107,
            "Country": "United Kingdom",
        },
        # Normal order 5: Invoice 100010, Customer 108, Germany
        {
            "InvoiceNo": "100010",
            "StockCode": "ITEM_B",
            "Description": "Product Beta",
            "Quantity": 5,
            "InvoiceDate": "2023-03-01 10:20:00",
            "UnitPrice": 20.00,
            "CustomerID": 108,
            "Country": "Germany",
        },
    ]

    df = pd.DataFrame(records)
    test_path = os.path.join(TEST_DATA_DIR, "synthetic_transactions.csv")
    fixture_path = os.path.join(FIXTURES_DIR, "fixture_transactions.csv")

    df.to_csv(test_path, index=False)
    df.to_csv(fixture_path, index=False)
    print(f"Deterministic test fixture saved to {test_path} and {fixture_path} ({len(df)} records).")


if __name__ == "__main__":
    download_uci_dataset(max_rows=50000)
    create_deterministic_fixtures()
