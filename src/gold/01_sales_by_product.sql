-- Sales by Product aggregation from Silver-valid business records.
-- Input views are registered by create_gold_tables.py:
--   valid_silver_products
--   valid_silver_orders

SELECT
    p.product_id,
    p.product_name,
    p.category,
    COUNT(o.order_id) AS total_orders,
    CAST(COALESCE(SUM(o.total_amount), 0) AS DECIMAL(10, 2)) AS total_revenue,
    CASE
        WHEN COUNT(o.order_id) = 0 THEN CAST(NULL AS DECIMAL(10, 2))
        ELSE CAST(AVG(o.total_amount) AS DECIMAL(10, 2))
    END AS avg_order_value
FROM valid_silver_products AS p
LEFT JOIN valid_silver_orders AS o
    ON p.product_id = o.product_id
GROUP BY
    p.product_id,
    p.product_name,
    p.category
ORDER BY
    p.product_id
