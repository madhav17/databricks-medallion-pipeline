# Data Model

Schemas are authoritative in `src/bronze/schemas.py` and `database/schema.sql`.

## customers

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| customer_id | INT | PK | Unique customer identifier (duplicates exist in CSV by design) |
| customer_name | STRING | | Synthetic customer name |
| email | STRING | | Contact email; NULL for 50 intentional anomaly rows |
| country | STRING | | Weighted synthetic country |
| signup_date | DATE | | Customer registration date |
| customer_segment | STRING | | Premium, Standard, or Basic |
| lifetime_value | DECIMAL(10,2) | | Segment-driven synthetic lifetime value |

**Relationships:** Referenced by `orders.customer_id`

## products

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| product_id | INT | PK | Unique product identifier |
| product_name | STRING | | Product name |
| category | STRING | | Electronics, Clothing, Home, Sports, Books |
| price | DECIMAL(10,2) | | List price |
| cost | DECIMAL(10,2) | | Cost (≤ price in clean generation) |
| stock_quantity | INT | | On-hand inventory |
| reorder_level | INT | | Reorder threshold |

**Relationships:** Referenced by `orders.product_id`

## orders

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| order_id | INT | PK | Unique order identifier (duplicates exist by design) |
| customer_id | INT | FK → customers | Customer reference; NULL/invalid values injected |
| order_date | DATE | | Order placement date |
| product_id | INT | FK → products | Product reference; NULL/invalid values injected |
| quantity | INT | | Units ordered (positive in clean generation) |
| unit_price | DECIMAL(10,2) | | Price per unit at order time |
| total_amount | DECIMAL(10,2) | | Expected: quantity × unit_price (2dp) |
| order_status | STRING | | Pending, Completed, or Cancelled |
| payment_date | DATE | | Required for Completed orders in clean generation |

**Relationships:**

- Many orders → one customer
- Many orders → one product

## Silver Quality Columns (added in Silver layer)

| Column | Type | Description |
|--------|------|-------------|
| quality_check_result | STRING | PASS or FAIL |
| quality_check_reason | STRING | Semicolon-separated failure reasons |

## Gold Outputs (aggregated)

| Dataset | Grain | Key columns |
|---------|-------|-------------|
| sales_by_product | product_id | total_revenue, total_orders, avg_order_value |
| revenue_by_customer | customer_id | total_revenue, total_orders, lifetime_value_actual |
| daily_weekly_trends | period_type, period_start | total_revenue, total_orders, avg_order_value |
| customer_segmentation | segment_type | customer_count, total_revenue, avg_revenue |

See `src/gold/GOLD_LAYER_NOTES.md` for full output schemas.
