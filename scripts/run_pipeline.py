"""Command-line entrypoint for running the E-commerce ETL & QA Pipeline.

Usage:
    python -m scripts.run_pipeline
    python -m scripts.run_pipeline --input test-data/synthetic_transactions.csv
    python -m scripts.run_pipeline --load-db
"""

import argparse
import sys
from pathlib import Path

from app.config.settings import settings
from app.etl.pipeline import run_etl
from app.utils.logger import setup_logger

logger = setup_logger("run_pipeline")


def main() -> int:
    parser = argparse.ArgumentParser(description="E-commerce Sales Analytics ETL & Automated QA Pipeline")
    parser.add_argument(
        "--input",
        type=str,
        default=settings.RAW_DATA_PATH,
        help="Path to source raw transactions CSV (defaults to settings.RAW_DATA_PATH)",
    )
    parser.add_argument(
        "--output-clean",
        type=str,
        default=settings.PROCESSED_DATA_PATH,
        help="Path to output clean CSV",
    )
    parser.add_argument(
        "--output-rejected",
        type=str,
        default=settings.REJECTED_RECORDS_PATH,
        help="Path to output rejected records CSV",
    )
    parser.add_argument(
        "--reports-dir",
        type=str,
        default=settings.REPORTS_DIR,
        help="Directory to save audit and data quality reports",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of rows to ingest (for testing/benchmarks)",
    )
    parser.add_argument(
        "--load-db",
        action="store_true",
        help="Load transformed records into relational database",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Override database connection URL",
    )

    args = parser.parse_args()

    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file.resolve()}")
        return 1

    try:
        # Run ETL
        etl_result = run_etl(
            input_path=str(input_file),
            output_clean_path=args.output_clean,
            output_rejected_path=args.output_rejected,
            reports_dir=args.reports_dir,
            nrows=args.limit,
        )

        print("\n" + "=" * 65)
        print("          ETL & DATA QUALITY SUMMARY REPORT")
        print("=" * 65)
        print(f" Source File:         {input_file}")
        print(f" Ingested Records:    {etl_result.raw_count:,}")
        print(f" Accepted Records:    {etl_result.accepted_count:,}")
        print(f" Quarantined Records: {etl_result.rejected_count:,}")
        print(f" Gross Revenue:       £{etl_result.gross_revenue:,.2f}")
        print(f" Refunds / Returns:   £{etl_result.refund_total:,.2f}")
        print(f" Net Revenue:         £{etl_result.net_revenue:,.2f}")
        print(f" Audit Report:        {etl_result.report_path}")
        print("=" * 65)

        # Database loading if requested
        if args.load_db:
            from app.database.connection import get_engine, init_db
            from app.database.loader import load_transactions

            db_url = args.db_url or settings.DATABASE_URL
            logger.info(f"Connecting to database: {db_url}...")
            engine = get_engine(db_url)
            init_db(engine)
            load_summary = load_transactions(engine, etl_result.accepted_df)
            print(f" Database Inserted:   {load_summary['inserted_count']} new rows")
            print(f" Database Skipped:    {load_summary['skipped_count']} duplicate rows")
            print("=" * 65)

        return 0
    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
