"""SQL Analytics Execution Engine.

Executes parameterized, production SQL queries against the relational warehouse,
returning typed summaries and analytical Pandas DataFrames.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import Engine, text

from app.utils.logger import setup_logger

logger = setup_logger("analytics_engine")

SQL_QUERIES_DIR = Path(__file__).resolve().parent.parent.parent / "sql" / "queries"


class AnalyticsEngine:
    """Interface for executing SQL analytical queries."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def _read_query(self, query_filename: str) -> str:
        query_path = SQL_QUERIES_DIR / query_filename
        if not query_path.exists():
            raise FileNotFoundError(f"SQL file not found: {query_path.resolve()}")
        return query_path.read_text(encoding="utf-8")

    def get_kpi_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch high-level financial and operational KPIs."""
        sql = self._read_query("kpi_summary.sql")
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "country": country,
        }

        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params).mappings().one()
            return {
                "gross_revenue": float(round(result["gross_revenue"], 2)),
                "total_refunds": float(round(result["total_refunds"], 2)),
                "net_revenue": float(round(result["net_revenue"], 2)),
                "total_invoices": int(result["total_invoices"]),
                "completed_orders": int(result["completed_orders"]),
                "cancelled_orders": int(result["cancelled_orders"]),
                "average_order_value": float(round(result["average_order_value"], 2)),
                "net_units_sold": int(result["net_units_sold"]),
            }

    def get_monthly_trends(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch monthly sales trends."""
        sql = self._read_query("monthly_trends.sql")
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "country": country,
        }
        with self.engine.connect() as conn:
            return pd.read_sql_query(text(sql), conn, params=params)

    def get_product_performance(
        self,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch top products by revenue."""
        sql = self._read_query("product_performance.sql")
        params = {
            "limit_rows": limit,
            "start_date": start_date,
            "end_date": end_date,
            "country": country,
        }
        with self.engine.connect() as conn:
            return pd.read_sql_query(text(sql), conn, params=params)

    def get_customer_frequency(
        self,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch customer frequency and spend metrics."""
        sql = self._read_query("customer_frequency.sql")
        params = {
            "limit_rows": limit,
            "start_date": start_date,
            "end_date": end_date,
            "country": country,
        }
        with self.engine.connect() as conn:
            return pd.read_sql_query(text(sql), conn, params=params)

    def get_regional_performance(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch regional/country sales distribution."""
        sql = self._read_query("regional_performance.sql")
        params = {
            "start_date": start_date,
            "end_date": end_date,
        }
        with self.engine.connect() as conn:
            return pd.read_sql_query(text(sql), conn, params=params)

    def get_distinct_countries(self) -> List[str]:
        """Fetch list of all unique countries in the fact table."""
        sql = "SELECT DISTINCT country FROM fact_transactions ORDER BY country ASC;"
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql)).scalars().all()
            return list(rows)

    def get_audit_history(self) -> pd.DataFrame:
        """Fetch past pipeline run execution and audit records."""
        sql = "SELECT * FROM etl_audit_log ORDER BY executed_at DESC;"
        with self.engine.connect() as conn:
            return pd.read_sql_query(text(sql), conn)
