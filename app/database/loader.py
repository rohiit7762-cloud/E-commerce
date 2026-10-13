"""Database Loading Module.

Performs transactional, idempotent loading of dimensional and fact records.
Ensures referential integrity and prevents record duplication on re-execution.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.database.connection import get_session_factory, session_scope
from app.database.models import DimCustomer, DimProduct, EtlAuditLog, FactTransaction
from app.utils.logger import setup_logger

logger = setup_logger("loader")


class DatabaseLoadError(Exception):
    """Raised when database loading fails."""

    pass


def load_dimensions(session: Session, df: pd.DataFrame) -> None:
    """
    Upsert dimensional records (dim_products, dim_customers) to maintain referential integrity.
    """
    # 1. DimProduct
    product_records = (
        df.sort_values("invoice_date")
        .groupby("stock_code")
        .agg({"description": "last", "unit_price": "last"})
        .reset_index()
    )

    existing_stock_codes = set(session.scalars(select(DimProduct.stock_code)).all())

    new_products = []
    for _, row in product_records.iterrows():
        code = str(row["stock_code"]).strip()
        if code not in existing_stock_codes:
            new_products.append(
                DimProduct(
                    stock_code=code,
                    description=str(row["description"]),
                    latest_unit_price=float(row["unit_price"]),
                )
            )
            existing_stock_codes.add(code)
        else:
            # Update latest price and description
            prod = session.get(DimProduct, code)
            if prod:
                prod.description = str(row["description"])
                prod.latest_unit_price = float(row["unit_price"])
                prod.updated_at = datetime.now(timezone.utc)

    if new_products:
        session.add_all(new_products)
        session.flush()
        logger.info(f"Loaded {len(new_products)} new products into dim_products.")

    # 2. DimCustomer (only for non-null customer_id)
    cust_mask = df["customer_id"].notna()
    if cust_mask.any():
        cust_records = (
            df[cust_mask]
            .sort_values("invoice_date")
            .groupby("customer_id")
            .agg({"country": "last"})
            .reset_index()
        )

        existing_customer_ids = set(session.scalars(select(DimCustomer.customer_id)).all())

        new_customers = []
        for _, row in cust_records.iterrows():
            cid = int(row["customer_id"])
            if cid not in existing_customer_ids:
                new_customers.append(
                    DimCustomer(
                        customer_id=cid,
                        country=str(row["country"]),
                    )
                )
                existing_customer_ids.add(cid)

        if new_customers:
            session.add_all(new_customers)
            session.flush()
            logger.info(f"Loaded {len(new_customers)} new customers into dim_customers.")


def load_transactions(
    engine: Engine,
    transformed_df: pd.DataFrame,
    source_file: str = "pipeline_execution",
    raw_count: Optional[int] = None,
    rejected_count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Idempotently load transformed transaction records into fact_transactions.

    Strategy:
    - Verifies existing record_ids in the target database.
    - Discards existing record_ids to prevent duplication (idempotent).
    - Inserts only unrecorded fact rows.
    - Captures run metadata into etl_audit_log.
    - Managed within an ACID transaction (rolls back on failure).

    Args:
        engine: SQLAlchemy Engine.
        transformed_df: Cleaned and transformed DataFrame.
        source_file: Origin identifier for audit tracking.
        raw_count: Total raw rows processed.
        rejected_count: Count of quarantined rows.

    Returns:
        Dict: Loading summary statistics.
    """
    if transformed_df.empty:
        logger.warning("Empty DataFrame passed to load_transactions. Nothing to load.")
        return {"inserted_count": 0, "skipped_count": 0, "status": "EMPTY"}

    session_factory = get_session_factory(engine)
    run_id = f"RUN_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    logger.info(f"Starting database load [Run ID: {run_id}]...")

    try:
        with session_scope(session_factory) as session:
            # 1. Upsert Dimensions
            load_dimensions(session, transformed_df)

            # 2. Identify candidate record_ids and check against existing
            incoming_ids = transformed_df["record_id"].tolist()

            # Query existing IDs in batches of 500 to stay well under query limits
            existing_record_ids = set()
            chunk_size = 500
            for i in range(0, len(incoming_ids), chunk_size):
                batch = incoming_ids[i : i + chunk_size]
                found = session.scalars(
                    select(FactTransaction.record_id).where(FactTransaction.record_id.in_(batch))
                ).all()
                existing_record_ids.update(found)

            # 3. Filter only genuinely new records
            new_records_df = transformed_df[~transformed_df["record_id"].isin(existing_record_ids)]
            skipped_count = len(transformed_df) - len(new_records_df)

            fact_rows: List[FactTransaction] = []
            for _, row in new_records_df.iterrows():
                cid = None if pd.isna(row["customer_id"]) else int(row["customer_id"])
                inv_dt = pd.to_datetime(row["invoice_date"]).to_pydatetime()

                fact_rows.append(
                    FactTransaction(
                        record_id=str(row["record_id"]),
                        invoice_no=str(row["invoice_no"]),
                        stock_code=str(row["stock_code"]),
                        customer_id=cid,
                        quantity=int(row["quantity"]),
                        unit_price=float(row["unit_price"]),
                        line_total=float(row["line_total"]),
                        invoice_date=inv_dt,
                        country=str(row["country"]),
                        is_cancellation=bool(row["is_cancellation"]),
                        year_month=str(row["year_month"]),
                    )
                )

            if fact_rows:
                session.add_all(fact_rows)
                session.flush()

            inserted_count = len(fact_rows)

            # 4. Compute financial KPIs for audit logging
            sales_rows = transformed_df[~transformed_df["is_cancellation"]]
            gross_rev = float(round(sales_rows["line_total"].sum(), 2)) if not sales_rows.empty else 0.0
            refund_rows = transformed_df[transformed_df["is_cancellation"]]
            refund_val = float(round(refund_rows["line_total"].sum(), 2)) if not refund_rows.empty else 0.0
            net_rev = float(round(gross_rev + refund_val, 2))

            audit_log = EtlAuditLog(
                run_id=run_id,
                source_file=source_file,
                raw_count=raw_count if raw_count is not None else len(transformed_df),
                accepted_count=len(transformed_df),
                rejected_count=rejected_count if rejected_count is not None else 0,
                inserted_count=inserted_count,
                skipped_count=skipped_count,
                gross_revenue=gross_rev,
                net_revenue=net_rev,
                status="SUCCESS",
            )
            session.add(audit_log)

            logger.info(
                f"Database load completed: {inserted_count} inserted, {skipped_count} skipped (idempotent duplicate prevention)."
            )

            return {
                "run_id": run_id,
                "inserted_count": inserted_count,
                "skipped_count": skipped_count,
                "total_processed": len(transformed_df),
                "status": "SUCCESS",
            }
    except Exception as e:
        logger.exception(f"Failed to load records into database: {e}")
        raise DatabaseLoadError(f"Database load operation aborted: {e}") from e
