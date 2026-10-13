"""Data Extraction Module.

Extracts raw e-commerce transaction data from CSV files with robust encoding
and format handling.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from app.utils.logger import setup_logger

logger = setup_logger("extractor")


class ExtractionError(Exception):
    """Raised when data extraction fails."""

    pass


def extract_csv(filepath: str | Path, nrows: Optional[int] = None) -> pd.DataFrame:
    """
    Extract raw e-commerce transaction records from a CSV file.

    Args:
        filepath: Path to the target CSV file.
        nrows: Optional maximum number of rows to read.

    Returns:
        pd.DataFrame: Raw ingested transaction data.

    Raises:
        ExtractionError: If the file does not exist, is empty, or cannot be parsed.
    """
    path = Path(filepath)
    if not path.exists():
        raise ExtractionError(f"Source file does not exist: {path.resolve()}")
    if path.stat().st_size == 0:
        raise ExtractionError(f"Source file is empty (0 bytes): {path.resolve()}")

    logger.info(f"Extracting raw data from {path.name} (size: {path.stat().st_size} bytes)...")

    # Try standard encodings commonly found in e-commerce CSV dumps
    encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
    last_err: Optional[Exception] = None

    for enc in encodings:
        try:
            df = pd.read_csv(
                path,
                dtype={
                    "InvoiceNo": str,
                    "StockCode": str,
                    "Description": str,
                    "Country": str,
                },
                nrows=nrows,
                encoding=enc,
            )
            logger.info(f"Successfully extracted {len(df)} raw records using encoding: {enc}")
            return df
        except UnicodeDecodeError as ude:
            last_err = ude
            continue
        except Exception as e:
            raise ExtractionError(f"Failed to parse CSV file {path}: {e}") from e

    raise ExtractionError(f"Failed to decode CSV {path} with tested encodings: {last_err}")
