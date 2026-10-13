-- =============================================================================
-- Core KPI Summary Query
-- Calculates Gross Revenue, Refund Value, Net Revenue, Distinct Invoices, and AOV.
-- =============================================================================

SELECT
    -- Gross Revenue (Sum of line totals for completed sales, excluding cancellations)
    COALESCE(SUM(CASE WHEN is_cancellation = FALSE THEN line_total ELSE 0.0 END), 0.0) AS gross_revenue,

    -- Total Refund Value (Sum of negative line totals for cancellations / returns)
    COALESCE(SUM(CASE WHEN is_cancellation = TRUE THEN line_total ELSE 0.0 END), 0.0) AS total_refunds,

    -- Net Revenue (Gross Revenue + Total Refunds)
    COALESCE(SUM(line_total), 0.0) AS net_revenue,

    -- Total Distinct Invoices (Sales + Cancellations)
    COUNT(DISTINCT invoice_no) AS total_invoices,

    -- Completed Sales Invoices
    COUNT(DISTINCT CASE WHEN is_cancellation = FALSE THEN invoice_no END) AS completed_orders,

    -- Cancellation Invoices
    COUNT(DISTINCT CASE WHEN is_cancellation = TRUE THEN invoice_no END) AS cancelled_orders,

    -- Average Order Value (AOV) on completed sales = Gross Revenue / Completed Orders
    CASE 
        WHEN COUNT(DISTINCT CASE WHEN is_cancellation = FALSE THEN invoice_no END) > 0 
        THEN ROUND(
            SUM(CASE WHEN is_cancellation = FALSE THEN line_total ELSE 0.0 END) / 
            COUNT(DISTINCT CASE WHEN is_cancellation = FALSE THEN invoice_no END), 
            2
        )
        ELSE 0.0 
    END AS average_order_value,

    -- Net Units Sold (Total Quantity)
    COALESCE(SUM(quantity), 0) AS net_units_sold

FROM fact_transactions
WHERE (:start_date IS NULL OR invoice_date >= :start_date)
  AND (:end_date IS NULL OR invoice_date <= :end_date)
  AND (:country IS NULL OR country = :country);
