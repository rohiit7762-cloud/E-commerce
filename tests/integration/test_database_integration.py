import os
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.database.connection import get_engine, get_session_factory, init_db, session_scope
from app.database.loader import load_transactions
from app.database.models import Base, DimProduct, EtlAuditLog, FactTransaction
from app.etl.pipeline import run_etl


@pytest.fixture
def isolated_db_engine(tmp_path: Path):
    """Provide an isolated, clean database for integration testing (PostgreSQL if set, else SQLite)."""
    env_db_url = os.environ.get("DATABASE_URL")
    if env_db_url and "postgresql" in env_db_url:
        engine = get_engine(env_db_url)
        Base.metadata.drop_all(engine)
        init_db(engine)
        yield engine
        Base.metadata.drop_all(engine)
    else:
        db_file = tmp_path / "test_isolated.db"
        db_url = f"sqlite:///{db_file}"
        engine = get_engine(db_url)
        init_db(engine)
        yield engine


def test_initial_load_populates_tables(isolated_db_engine):
    """Verify that records are correctly partitioned into dimensions and facts."""
    etl_result = run_etl("test-data/synthetic_transactions.csv")
    assert etl_result.accepted_count == 7

    load_summary = load_transactions(
        isolated_db_engine,
        etl_result.accepted_df,
        source_file="test-data/synthetic_transactions.csv",
        raw_count=etl_result.raw_count,
        rejected_count=etl_result.rejected_count,
    )

    assert load_summary["status"] == "SUCCESS"
    assert load_summary["inserted_count"] == 7
    assert load_summary["skipped_count"] == 0

    session_factory = get_session_factory(isolated_db_engine)
    with session_scope(session_factory) as session:
        # Verify fact table count
        fact_count = session.scalar(select(func.count(FactTransaction.record_id)))
        assert fact_count == 7

        # Verify dimension counts
        prod_count = session.scalar(select(func.count(DimProduct.stock_code)))
        assert prod_count > 0

        # Verify audit log recorded
        audit_record = session.scalar(select(EtlAuditLog))
        assert audit_record is not None
        assert audit_record.inserted_count == 7
        assert audit_record.raw_count == 13
        assert audit_record.rejected_count == 6


def test_idempotent_loading_prevents_duplicate_inflation(isolated_db_engine):
    """
    Critical Idempotency Test:
    Running the pipeline twice with identical data must not inflate record counts.
    """
    etl_result = run_etl("test-data/synthetic_transactions.csv")

    # Run 1: Initial load
    res1 = load_transactions(isolated_db_engine, etl_result.accepted_df)
    assert res1["inserted_count"] == 7
    assert res1["skipped_count"] == 0

    # Run 2: Re-executing exact same data
    res2 = load_transactions(isolated_db_engine, etl_result.accepted_df)
    assert res2["inserted_count"] == 0
    assert res2["skipped_count"] == 7  # All 7 records recognized as already present

    # Final assertion: Fact table still contains strictly 7 records
    session_factory = get_session_factory(isolated_db_engine)
    with session_scope(session_factory) as session:
        final_fact_count = session.scalar(select(func.count(FactTransaction.record_id)))
        assert final_fact_count == 7


def test_transaction_rollback_on_failure(isolated_db_engine):
    """Verify that database transactions rollback cleanly if an exception is raised."""
    session_factory = get_session_factory(isolated_db_engine)

    # Initial check
    with session_scope(session_factory) as session:
        initial_count = session.scalar(select(func.count(FactTransaction.record_id)))
        assert initial_count >= 0

    # Force a failure inside session_scope
    with pytest.raises(RuntimeError, match="Simulated mid-transaction failure"):
        with session_scope(session_factory) as session:
            # Add an uncommitted dummy row
            prod = DimProduct(stock_code="TEMP_PROD", description="Temp", latest_unit_price=10.0)
            session.add(prod)
            raise RuntimeError("Simulated mid-transaction failure")

    # Verify rollback: TEMP_PROD must not exist in dim_products
    with session_scope(session_factory) as session:
        found_prod = session.get(DimProduct, "TEMP_PROD")
        assert found_prod is None
