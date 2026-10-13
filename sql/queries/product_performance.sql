-- =============================================================================
-- Product Performance Query
-- Evaluates sales volume, net revenue, and return rates per product.
-- =============================================================================

SELECT
    f.stock_code,
    COALESCE(p.description, 'UNKNOWN PRODUCT') AS description,
    SUM(CASE WHEN f.is_cancellation = FALSE THEN f.quantity ELSE 0 END) AS units_sold,
    SUM(CASE WHEN f.is_cancellation = TRUE THEN ABS(f.quantity) ELSE 0 END) AS units_returned,
    COALESCE(SUM(f.line_total), 0.0) AS net_revenue,
    COUNT(DISTINCT f.invoice_no) AS order_appearances
FROM fact_transactions f
LEFT JOIN dim_products p ON f.stock_code = p.stock_code
WHERE (:start_date IS NULL OR f.invoice_date >= :start_date)
  AND (:end_date IS NULL OR f.invoice_date <= :end_date)
  AND (:country IS NULL OR f.country = :country)
GROUP BY f.stock_code, p.description
ORDER BY net_revenue DESC
LIMIT :limit_rows;
