-- =============================================================================
-- Regional / Country Performance Query
-- Analyzes sales distribution by customer geographic jurisdiction.
-- =============================================================================

SELECT
    country,
    COUNT(DISTINCT invoice_no) AS total_orders,
    COUNT(DISTINCT customer_id) AS distinct_customers,
    COALESCE(SUM(CASE WHEN is_cancellation = FALSE THEN line_total ELSE 0.0 END), 0.0) AS gross_revenue,
    COALESCE(SUM(line_total), 0.0) AS net_revenue,
    COALESCE(SUM(quantity), 0) AS units_sold
FROM fact_transactions
WHERE (:start_date IS NULL OR invoice_date >= :start_date)
  AND (:end_date IS NULL OR invoice_date <= :end_date)
GROUP BY country
ORDER BY net_revenue DESC;
