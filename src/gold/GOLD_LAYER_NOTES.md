# Gold Layer

## 1. Gold Purpose

Gold consumes Silver datasets and produces business-ready aggregation tables
for analytics and dashboard consumption.

Gold does not read CSV or Bronze directly.

## 2. Silver Inputs

Default Silver roots come from `config/gold_config.yaml`:

- `customers`: `{silver_root}/customers`
- `orders`: `{silver_root}/orders`
- `products`: `{silver_root}/products`

## 3. Three Mandatory Gold Aggregations

Implemented Gold outputs:

1. `sales_by_product`
2. `revenue_by_customer`
3. `customer_segmentation`

## 4. Daily/Weekly Trends Scope Decision

The repository structure references `03_daily_weekly_trends.sql`, but the
assignment acceptance criteria explicitly require the three mandatory Gold
aggregation tables only.

`03_daily_weekly_trends.sql` is **not implemented** in this stage because no
existing project rule or prior human decision required it as a fourth mandatory
Gold table.

## 5. Sales by Product Logic

Source SQL: `src/gold/01_sales_by_product.sql`

- Joins `valid_silver_products` to `valid_silver_orders` on `product_id`
- Calculates:
  - `total_orders = COUNT(order_id)`
  - `total_revenue = SUM(total_amount)`
  - `avg_order_value = AVG(total_amount)` (NULL when no valid orders)
- Includes products with zero valid orders via LEFT JOIN

## 6. Revenue by Customer Logic

Source SQL: `src/gold/02_revenue_by_customer.sql`

- Joins `valid_silver_customers` to `valid_silver_orders` on `customer_id`
- Includes customers with zero valid orders (LEFT JOIN)
- Calculates:
  - `total_orders`
  - `total_revenue`
  - `avg_order_value` (NULL when no valid orders)
  - `lifetime_value_actual` (actual aggregated revenue from valid orders)

`lifetime_value_actual` is distinct from source `lifetime_value`, which is the
stored/expected customer lifetime value from the source customer table.

## 7. Customer Segmentation Logic

Source SQL: `src/gold/04_customer_segmentation.sql`

Derived segment types:

- `Inactive`
- `High-Value`
- `Repeat`
- `One-Time`

Segmentation is derived from actual order behavior, not source `customer_segment`.

## 8. Silver Quality Filtering / Eligibility

Gold uses Silver business-eligible records only:

- `quality_check_result = 'PASS'`

Additional order filter:

- `order_status IN eligible_order_statuses` (default: `Completed`)
- order `customer_id` must exist in valid (PASS) customers
- order `product_id` must exist in valid (PASS) products

This prevents invalid Silver rows (NULL keys, orphan FKs, duplicate IDs) from
corrupting Gold metrics and keeps product/customer/segmentation revenue totals
reconcilable.

Invalid rows remain in Silver for inspection; Gold excludes them from business
aggregations by design.

## 9. Order-Status Handling

The assignment does not define explicit Gold revenue semantics by order status.

Chosen business assumption (documented and configurable):

- Realized revenue metrics use **Completed** orders only.
- Pending and Cancelled orders are excluded even if they pass Silver quality
  checks.

Configure via:

- `config/gold_config.yaml` -> `business_rules.eligible_order_statuses`
- environment variable `GOLD_ELIGIBLE_ORDER_STATUSES` (comma-separated)

## 10. Duplicate Protection

Duplicate protection rules:

- Customers: Silver uniqueness failures are excluded via PASS filter, so valid
  customer keys are unique for Gold joins.
- Orders: duplicate `order_id` rows fail Silver and are excluded from Gold.
- Products: Silver does not enforce product uniqueness; Gold deduplicates
  `product_id` in the valid product dimension before joins to prevent row
  multiplication.

DISTINCT/deduplication is applied only where join safety requires it and is
documented (products dimension).

## 11. NULL Handling

- Revenue sums use `COALESCE(..., 0)` for zero-order groups.
- Average order value is NULL for customers/products with zero valid orders.
- Inactive segmentation segment uses `avg_revenue = 0` and `total_revenue = 0`.

## 12. Lifetime Value Calculation

- Source `lifetime_value`: preserved in Revenue by Customer output as
  `customer_segment` context only (via source customer attributes).
- `lifetime_value_actual`: computed as `SUM(total_amount)` from valid orders.

## 13. Segmentation Rules and Precedence

Precedence (deterministic):

1. `total_orders = 0` -> `Inactive`
2. `total_revenue >= high_value_threshold` -> `High-Value`
3. `total_orders > 1` -> `Repeat`
4. else -> `One-Time`

## 14. High-Value Threshold

No assignment-defined numeric threshold was found in existing project artifacts.

Default threshold:

- `1000.00` in `config/gold_config.yaml`

Override options:

- `HIGH_VALUE_REVENUE_THRESHOLD` environment variable
- `business_rules.high_value_revenue_threshold` in config

Changing the threshold changes High-Value segment membership and related segment
metrics.

## 15. Local Execution

From project root:

```bash
PYTHONPATH=src python src/gold/create_gold_tables.py
```

Or after editable install:

```bash
gold-create-tables
```

Prerequisite: Silver outputs must exist (for example via `silver-create-tables`).

## 16. Databricks Execution

Same business logic runs on Databricks with an active SparkSession reused when
present. Configure paths/registration via environment or config:

- `GOLD_SILVER_ROOT`
- `GOLD_ROOT`
- `HIGH_VALUE_REVENUE_THRESHOLD`
- `GOLD_ELIGIBLE_ORDER_STATUSES`
- `GOLD_CATALOG`
- `GOLD_SCHEMA`
- `GOLD_TABLE_REGISTRATION_ENABLED`

Databricks execution validation in this repository: not performed locally in CI.

## 17. Configuration

Gold configuration uses YAML + Pydantic:

- `config/gold_config.yaml`
- `src/gold/config.py`
- `src/gold/config_loader.py`

Only paths/business-rule thresholds/status policy differ by environment; SQL
aggregation logic is shared.

## 18. Testing

Gold tests validate:

- expected aggregation values
- invalid Silver record exclusion
- inactive customer handling
- segmentation categories
- reconciliation behavior (via pipeline)
- idempotency
- missing Silver input failure

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_gold.py -q
```

## 19. Reconciliation

The orchestrator validates:

- `SUM(sales_by_product.total_revenue)` equals eligible Silver order revenue
- `SUM(revenue_by_customer.total_revenue)` equals eligible Silver order revenue
- `SUM(customer_segmentation.total_revenue)` equals eligible Silver order revenue

Reconciliation failure stops the Gold pipeline.

## 20. Idempotency

Gold writes use configured overwrite mode (`write.mode: overwrite` by default),
so reruns replace prior Gold outputs rather than append duplicate aggregation
rows.

## 21. Output Locations

Default local outputs:

```text
data/gold/
  sales_by_product/
  revenue_by_customer/
  customer_segmentation/
```
