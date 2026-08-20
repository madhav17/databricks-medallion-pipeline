-- Revenue by Customer aggregation from Silver-valid business records.
-- Includes customers with zero valid orders (LEFT JOIN from customer dimension).

SELECT
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    COUNT(o.order_id) AS total_orders,
    CAST(COALESCE(SUM(o.total_amount), 0) AS DECIMAL(10, 2)) AS total_revenue,
    CASE
        WHEN COUNT(o.order_id) = 0 THEN CAST(NULL AS DECIMAL(10, 2))
        ELSE CAST(AVG(o.total_amount) AS DECIMAL(10, 2))
    END AS avg_order_value,
    CAST(COALESCE(SUM(o.total_amount), 0) AS DECIMAL(10, 2)) AS lifetime_value_actual
FROM valid_silver_customers AS c
LEFT JOIN valid_silver_orders AS o
    ON c.customer_id = o.customer_id
GROUP BY
    c.customer_id,
    c.customer_name,
    c.customer_segment
ORDER BY
    c.customer_id
