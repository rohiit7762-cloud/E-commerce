-- =============================================================================
-- Monthly Sales Trends Query
-- Groups sales by Year-Month for time-series visualization.
-- =============================================================================

SELECT
    year_month,
    COALESCE(SUM(CASE WHEN is_cancellation = FALSE THEN line_total ELSE 0.0 END), 0.0) AS gross_revenue,
    COALESCE(SUM(CASE WHEN is_cancellation = TRUE THEN line_total ELSE 0.0 END), 0.0) AS refund_amount,
    COALESCE(SUM(line_total), 0.0) AS net_revenue,
    COUNT(DISTINCT invoice_no) AS total_orders,
    COALESCE(SUM(quantity), 0) AS units_sold
FROM fact_transactions
WHERE (:start_date IS NULL OR invoice_date >= :start_date)
  AND (:end_date IS NULL OR invoice_date <= :end_date)
  AND (:country IS NULL OR country = :country)
GROUP BY year_month
ORDER BY year_month ASC;
