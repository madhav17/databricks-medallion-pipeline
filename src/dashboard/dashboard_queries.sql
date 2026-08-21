-- Dashboard Queries
-- Gold-backed Spark SQL queries for Databricks SQL Dashboard tiles.
-- Local validation registers parquet-backed temp views:
--   gold_sales_by_product
--   gold_revenue_by_customer
--   gold_customer_segmentation

------------------------------------------------------------
-- 1. Top 10 Products by Revenue
------------------------------------------------------------

SELECT
    product_id,
    product_name,
    category,
    total_orders,
    total_revenue,
    avg_order_value
FROM gold_sales_by_product
ORDER BY
    total_revenue DESC,
    product_id ASC
LIMIT 10;

------------------------------------------------------------
-- 2. Customer Revenue Distribution
------------------------------------------------------------

SELECT
    customer_id,
    customer_name,
    customer_segment,
    total_orders,
    total_revenue,
    avg_order_value,
    lifetime_value_actual
FROM gold_revenue_by_customer
ORDER BY
    total_revenue DESC,
    customer_id ASC;

------------------------------------------------------------
-- 3. Customer Segmentation
------------------------------------------------------------

SELECT
    segment_type,
    customer_count,
    avg_revenue,
    total_revenue
FROM gold_customer_segmentation
ORDER BY
    segment_type ASC;

------------------------------------------------------------
-- 4. Optional KPI - Total Revenue
------------------------------------------------------------

SELECT
    CAST(SUM(total_revenue) AS DECIMAL(10, 2)) AS total_revenue
FROM gold_revenue_by_customer;
