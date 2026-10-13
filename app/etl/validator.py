"""Data Validation Module.

Validates required schemas, data types, business constraints, and separates
clean records from quarantined rejected records with explicit reason tagging.
"""

from typing import Any, Dict, List, Tuple

import pandas as pd

from app.utils.logger import setup_logger

logger = setup_logger("validator")

REQUIRED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


class ValidationError(Exception):
    """Raised when critical schema-level validation fails."""

    pass


def validate_schema(df: pd.DataFrame, required_columns: List[str] = REQUIRED_COLUMNS) -> None:
    """
    Validate that the DataFrame contains all mandatory columns.

    Args:
        df: DataFrame to check.
        required_columns: List of required column names.

    Raises:
        ValidationError: If any required column is absent.
    """
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        err_msg = f"Schema validation failed. Missing required columns: {missing_cols}"
        logger.error(err_msg)
        raise ValidationError(err_msg)
    logger.debug("Schema validation passed: all required columns present.")


def validate_records(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Validate individual transaction records according to documented business rules.

    Rules:
    1. InvoiceNo must not be null, empty, or whitespace.
    2. StockCode must not be null, empty, or whitespace.
    3. Quantity must not be zero (Quantity != 0).
    4. UnitPrice must be strictly positive (UnitPrice > 0.00).
    5. InvoiceDate must be parseable as a valid datetime.
    6. Exact duplicate rows are detected and quarantined.
    7. Missing CustomerID is retained (valid guest checkout).
    8. Missing Description is retained (handled in transformation).

    Args:
        df: Raw DataFrame matching the required schema.

    Returns:
        Tuple:
            - accepted_df: DataFrame of valid records.
            - rejected_df: DataFrame of quarantined records with 'rejection_reason'.
            - metrics: Summary dictionary of validation counts and breakdown.
    """
    validate_schema(df)
    total_records = len(df)
    logger.info(f"Initiating validation on {total_records} records...")

    if total_records == 0:
        empty_rejected = pd.DataFrame(columns=list(df.columns) + ["rejection_reason"])
        return (
            df.copy(),
            empty_rejected,
            {
                "total_records": 0,
                "accepted_records": 0,
                "rejected_records": 0,
                "duplicate_records": 0,
                "reasons": {},
            },
        )

    working_df = df.copy()

    # Initialize rejection reason mask
    reasons = pd.Series(index=working_df.index, dtype=object)

    # 1. Missing or blank InvoiceNo
    invoice_str = working_df["InvoiceNo"].astype(str).str.strip()
    inv_null = (
        working_df["InvoiceNo"].isna()
        | (invoice_str == "")
        | (invoice_str == "nan")
        | (invoice_str == "None")
    )
    reasons[inv_null & reasons.isna()] = "MISSING_INVOICE_NO"

    # 2. Missing or blank StockCode
    stock_str = working_df["StockCode"].astype(str).str.strip()
    stock_null = (
        working_df["StockCode"].isna() | (stock_str == "") | (stock_str == "nan") | (stock_str == "None")
    )
    reasons[stock_null & reasons.isna()] = "MISSING_STOCK_CODE"

    # 3. Numeric conversion for Quantity and UnitPrice
    qty_numeric = pd.to_numeric(working_df["Quantity"], errors="coerce")
    price_numeric = pd.to_numeric(working_df["UnitPrice"], errors="coerce")

    # 4. Zero or non-numeric Quantity
    qty_invalid = qty_numeric.isna() | (qty_numeric == 0)
    reasons[qty_invalid & reasons.isna()] = "ZERO_OR_INVALID_QUANTITY"

    # 5. Non-positive or non-numeric UnitPrice
    price_invalid = price_numeric.isna() | (price_numeric <= 0)
    reasons[price_invalid & reasons.isna()] = "INVALID_UNIT_PRICE"

    # 6. Unparseable InvoiceDate
    parsed_dates = pd.to_datetime(working_df["InvoiceDate"], errors="coerce")
    date_invalid = parsed_dates.isna()
    reasons[date_invalid & reasons.isna()] = "INVALID_INVOICE_DATE"

    # 7. Exact Duplicate detection across clean candidates
    clean_mask_before_dupes = reasons.isna()
    # Check duplicates only among candidates that passed schema rules
    dupe_mask = working_df[clean_mask_before_dupes].duplicated(keep="first")
    duplicate_indices = working_df[clean_mask_before_dupes][dupe_mask].index
    reasons.loc[duplicate_indices] = "DUPLICATE_ROW"

    # Separate accepted vs rejected
    is_rejected = reasons.notna()

    rejected_df = working_df[is_rejected].copy()
    rejected_df["rejection_reason"] = reasons[is_rejected]

    accepted_df = working_df[~is_rejected].copy()

    # Compile validation metrics
    reason_counts = rejected_df["rejection_reason"].value_counts().to_dict()
    metrics = {
        "total_records": total_records,
        "accepted_records": len(accepted_df),
        "rejected_records": len(rejected_df),
        "duplicate_records": reason_counts.get("DUPLICATE_ROW", 0),
        "reasons": reason_counts,
    }

    logger.info(
        f"Validation complete: {metrics['accepted_records']} accepted, "
        f"{metrics['rejected_records']} rejected ({metrics['duplicate_records']} duplicates)."
    )
    return accepted_df, rejected_df, metrics
