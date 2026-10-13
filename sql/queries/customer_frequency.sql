-- =============================================================================
-- Customer Purchase Frequency Query
-- Measures RFM / frequency indicators (orders count, total spend, net revenue).
-- =============================================================================

SELECT
    COALESCE(CAST(f.customer_id AS VARCHAR), 'GUEST') AS customer_identifier,
    MAX(f.country) AS country,
    COUNT(DISTINCT f.invoice_no) AS total_orders,
    COALESCE(SUM(f.line_total), 0.0) AS net_spend,
    ROUND(CAST(COALESCE(SUM(f.line_total), 0.0) / COUNT(DISTINCT f.invoice_no) AS NUMERIC), 2) AS avg_spend_per_order
FROM fact_transactions f
WHERE (:start_date IS NULL OR f.invoice_date >= :start_date)
  AND (:end_date IS NULL OR f.invoice_date <= :end_date)
  AND (:country IS NULL OR f.country = :country)
GROUP BY f.customer_id
ORDER BY net_spend DESC
LIMIT :limit_rows;
