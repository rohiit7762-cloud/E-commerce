"""Independent Pandas KPI calculation module for dual-verification against SQL results."""

from typing import Any, Dict, Optional

import pandas as pd


def compute_pandas_kpis(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Independently calculate e-commerce KPIs using Pandas.
    Used for automated QA dual-verification against SQL query outputs.

    Args:
        df: Transformed clean transactions DataFrame.
        start_date: Optional lower date bound filter.
        end_date: Optional upper date bound filter.
        country: Optional country filter.

    Returns:
        Dict: Manually verified financial and operational metrics.
    """
    if df.empty:
        return {
            "gross_revenue": 0.0,
            "total_refunds": 0.0,
            "net_revenue": 0.0,
            "total_invoices": 0,
            "completed_orders": 0,
            "cancelled_orders": 0,
            "average_order_value": 0.0,
            "net_units_sold": 0,
        }

    filtered_df = df.copy()

    # Convert invoice_date if string
    if not pd.api.types.is_datetime64_any_dtype(filtered_df["invoice_date"]):
        filtered_df["invoice_date"] = pd.to_datetime(filtered_df["invoice_date"])

    if start_date:
        filtered_df = filtered_df[filtered_df["invoice_date"] >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[filtered_df["invoice_date"] <= pd.to_datetime(end_date)]
    if country:
        filtered_df = filtered_df[filtered_df["country"] == country]

    if filtered_df.empty:
        return {
            "gross_revenue": 0.0,
            "total_refunds": 0.0,
            "net_revenue": 0.0,
            "total_invoices": 0,
            "completed_orders": 0,
            "cancelled_orders": 0,
            "average_order_value": 0.0,
            "net_units_sold": 0,
        }

    # Partition completed sales vs cancellations
    sales_mask = ~filtered_df["is_cancellation"]
    cancellation_mask = filtered_df["is_cancellation"]

    gross_rev = float(round(filtered_df.loc[sales_mask, "line_total"].sum(), 2))
    refund_val = float(round(filtered_df.loc[cancellation_mask, "line_total"].sum(), 2))
    net_rev = float(round(filtered_df["line_total"].sum(), 2))

    total_invoices = int(filtered_df["invoice_no"].nunique())
    completed_orders = int(filtered_df.loc[sales_mask, "invoice_no"].nunique())
    cancelled_orders = int(filtered_df.loc[cancellation_mask, "invoice_no"].nunique())

    aov = float(round(gross_rev / completed_orders, 2)) if completed_orders > 0 else 0.0

    net_units = int(filtered_df["quantity"].sum())

    return {
        "gross_revenue": gross_rev,
        "total_refunds": refund_val,
        "net_revenue": net_rev,
        "total_invoices": total_invoices,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders,
        "average_order_value": aov,
        "net_units_sold": net_units,
    }
