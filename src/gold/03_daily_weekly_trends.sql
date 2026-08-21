-- Daily and weekly revenue trends from Silver-valid business records.
-- Input view is registered by create_gold_tables.py:
--   valid_silver_orders
--
-- Grain: one row per calendar day (daily) or ISO week start (weekly).

WITH daily_trends AS (
    SELECT
        'daily' AS period_type,
        CAST(order_date AS DATE) AS period_start,
        COUNT(order_id) AS total_orders,
        CAST(COALESCE(SUM(total_amount), 0) AS DECIMAL(10, 2)) AS total_revenue,
        CAST(AVG(total_amount) AS DECIMAL(10, 2)) AS avg_order_value
    FROM valid_silver_orders
    GROUP BY
        order_date
),
weekly_trends AS (
    SELECT
        'weekly' AS period_type,
        CAST(date_trunc('week', order_date) AS DATE) AS period_start,
        COUNT(order_id) AS total_orders,
        CAST(COALESCE(SUM(total_amount), 0) AS DECIMAL(10, 2)) AS total_revenue,
        CAST(AVG(total_amount) AS DECIMAL(10, 2)) AS avg_order_value
    FROM valid_silver_orders
    GROUP BY
        date_trunc('week', order_date)
)
SELECT
    period_type,
    period_start,
    total_orders,
    total_revenue,
    avg_order_value
FROM daily_trends
UNION ALL
SELECT
    period_type,
    period_start,
    total_orders,
    total_revenue,
    avg_order_value
FROM weekly_trends
ORDER BY
    period_type,
    period_start
