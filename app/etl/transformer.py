"""Data Transformation Module.

Cleans, normalizes, casts data types, computes financial KPIs (line total,
cancellation flags), and generates deterministic surrogate keys for idempotent loading.
"""

import hashlib
from datetime import datetime, timezone

import pandas as pd

from app.utils.logger import setup_logger

logger = setup_logger("transformer")


def generate_record_hash(row: pd.Series) -> str:
    """
    Generate a deterministic SHA-256 hash for a transaction row to ensure idempotency.
    Based on immutable natural business composite keys:
    (InvoiceNo, StockCode, InvoiceDate, Quantity, UnitPrice, CustomerID)
    """
    raw_str = (
        f"{str(row['InvoiceNo']).strip()}|"
        f"{str(row['StockCode']).strip()}|"
        f"{str(row['InvoiceDate']).strip()}|"
        f"{int(row['Quantity'])}|"
        f"{float(row['UnitPrice']):.2f}|"
        f"{'' if pd.isna(row['CustomerID']) else str(int(float(row['CustomerID'])))}"
    )
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:32]


def transform_records(accepted_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply transformations, standardizations, and derived analytical fields.

    Args:
        accepted_df: DataFrame of validated, accepted records.

    Returns:
        pd.DataFrame: Cleaned, transformed DataFrame ready for database loading.
    """
    if accepted_df.empty:
        logger.warning("Empty DataFrame passed to transform_records.")
        return pd.DataFrame(
            columns=[
                "record_id",
                "invoice_no",
                "stock_code",
                "description",
                "quantity",
                "invoice_date",
                "unit_price",
                "customer_id",
                "country",
                "line_total",
                "is_cancellation",
                "year_month",
                "created_at",
            ]
        )

    logger.info(f"Transforming {len(accepted_df)} accepted records...")
    df = accepted_df.copy()

    # 1. Clean string fields
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()
    df["Description"] = (
        df["Description"].fillna("UNKNOWN PRODUCT").astype(str).str.strip().replace("", "UNKNOWN PRODUCT")
    )
    df["Country"] = df["Country"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")

    # 2. Convert numerics & dates
    df["Quantity"] = df["Quantity"].astype(int)
    df["UnitPrice"] = df["UnitPrice"].astype(float).round(2)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # 3. Handle CustomerID (nullable integer)
    customer_series = pd.to_numeric(df["CustomerID"], errors="coerce")
    df["CustomerID"] = customer_series.astype("Int64")

    # 4. Derive financial and status fields
    df["line_total"] = (df["Quantity"] * df["UnitPrice"]).round(2)
    df["is_cancellation"] = df["InvoiceNo"].str.upper().str.startswith("C") | (df["Quantity"] < 0)
    df["year_month"] = df["InvoiceDate"].dt.strftime("%Y-%m")

    # 5. Timestamp of ETL processing
    now_utc = datetime.now(timezone.utc)
    df["created_at"] = now_utc

    # 6. Generate deterministic natural composite key hash (idempotency key)
    df["record_id"] = df.apply(generate_record_hash, axis=1)

    # 7. Normalize column names to relational snake_case standard
    column_mapping = {
        "record_id": "record_id",
        "InvoiceNo": "invoice_no",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "UnitPrice": "unit_price",
        "CustomerID": "customer_id",
        "Country": "country",
        "line_total": "line_total",
        "is_cancellation": "is_cancellation",
        "year_month": "year_month",
        "created_at": "created_at",
    }

    transformed_df = df[list(column_mapping.keys())].rename(columns=column_mapping)
    logger.info(f"Transformation complete. {len(transformed_df)} records ready for persistence.")
    return transformed_df
