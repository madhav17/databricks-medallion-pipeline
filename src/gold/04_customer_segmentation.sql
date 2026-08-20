-- Customer Segmentation derived from actual order behavior.
-- High-Value threshold is injected by create_gold_tables.py as {high_value_threshold}.

WITH customer_revenue AS (
    SELECT
        c.customer_id,
        COUNT(o.order_id) AS total_orders,
        CAST(COALESCE(SUM(o.total_amount), 0) AS DECIMAL(10, 2)) AS total_revenue
    FROM valid_silver_customers AS c
    LEFT JOIN valid_silver_orders AS o
        ON c.customer_id = o.customer_id
    GROUP BY
        c.customer_id
),
segmented_customers AS (
    SELECT
        customer_id,
        total_orders,
        total_revenue,
        CASE
            WHEN total_orders = 0 THEN 'Inactive'
            WHEN total_revenue >= CAST({high_value_threshold} AS DECIMAL(10, 2)) THEN 'High-Value'
            WHEN total_orders > 1 THEN 'Repeat'
            ELSE 'One-Time'
        END AS segment_type
    FROM customer_revenue
)
SELECT
    segment_type,
    COUNT(*) AS customer_count,
    CASE
        WHEN segment_type = 'Inactive' THEN CAST(0 AS DECIMAL(10, 2))
        ELSE CAST(AVG(total_revenue) AS DECIMAL(10, 2))
    END AS avg_revenue,
    CAST(COALESCE(SUM(total_revenue), 0) AS DECIMAL(10, 2)) AS total_revenue
FROM segmented_customers
GROUP BY
    segment_type
ORDER BY
    segment_type
