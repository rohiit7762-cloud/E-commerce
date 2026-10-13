"""Database Initialization Script.

Creates all tables, constraints, and indexes defined in the schema.
Usage:
    python -m scripts.init_db
    python -m scripts.init_db --db-url sqlite:///test.db
"""

import argparse
import sys

from app.config.settings import settings
from app.database.connection import get_engine, init_db
from app.utils.logger import setup_logger

logger = setup_logger("init_db")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize database schema.")
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database URL (defaults to settings.DATABASE_URL)",
    )
    args = parser.parse_args()

    target_url = args.db_url or settings.DATABASE_URL
    logger.info(f"Target Database URL: {target_url}")

    try:
        engine = get_engine(target_url)
        init_db(engine)
        print(f"Successfully initialized database schema at: {target_url}")
        return 0
    except Exception as e:
        logger.exception(f"Failed to initialize database: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
