"""SQLAlchemy ORM models defining the relational data warehouse schema."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


class DimProduct(Base):
    """Product dimension table."""

    __tablename__ = "dim_products"

    stock_code = Column(String(50), primary_key=True)
    description = Column(String(255), nullable=False, default="UNKNOWN PRODUCT")
    latest_unit_price = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    transactions = relationship("FactTransaction", back_populates="product")

    def __repr__(self) -> str:
        return f"<DimProduct(stock_code='{self.stock_code}', description='{self.description}')>"


class DimCustomer(Base):
    """Customer dimension table."""

    __tablename__ = "dim_customers"

    customer_id = Column(Integer, primary_key=True)
    country = Column(String(100), nullable=False, default="Unknown")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    transactions = relationship("FactTransaction", back_populates="customer")

    def __repr__(self) -> str:
        return f"<DimCustomer(customer_id={self.customer_id}, country='{self.country}')>"


class FactTransaction(Base):
    """Transaction fact table."""

    __tablename__ = "fact_transactions"

    record_id = Column(String(64), primary_key=True)
    invoice_no = Column(String(20), nullable=False, index=True)
    stock_code = Column(String(50), ForeignKey("dim_products.stock_code"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("dim_customers.customer_id"), nullable=True, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    invoice_date = Column(DateTime, nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    is_cancellation = Column(Boolean, nullable=False, default=False)
    year_month = Column(String(7), nullable=False, index=True)
    loaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    product = relationship("DimProduct", back_populates="transactions")
    customer = relationship("DimCustomer", back_populates="transactions")

    __table_args__ = (Index("idx_fact_inv_stock", "invoice_no", "stock_code"),)

    def __repr__(self) -> str:
        return (
            f"<FactTransaction(record_id='{self.record_id}', invoice_no='{self.invoice_no}', "
            f"line_total={self.line_total})>"
        )


class EtlAuditLog(Base):
    """ETL execution and data quality audit log table."""

    __tablename__ = "etl_audit_log"

    run_id = Column(String(64), primary_key=True)
    source_file = Column(String(255), nullable=False)
    raw_count = Column(Integer, nullable=False)
    accepted_count = Column(Integer, nullable=False)
    rejected_count = Column(Integer, nullable=False)
    inserted_count = Column(Integer, nullable=False)
    skipped_count = Column(Integer, nullable=False)
    gross_revenue = Column(Float, nullable=False)
    net_revenue = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<EtlAuditLog(run_id='{self.run_id}', status='{self.status}', inserted={self.inserted_count})>"
        )
