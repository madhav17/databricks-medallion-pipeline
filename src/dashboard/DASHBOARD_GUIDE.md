# Dashboard Guide

## 1. Purpose

The dashboard query layer consumes Gold aggregation outputs and provides SQL
queries for a Databricks SQL Dashboard.

Flow:

Gold  
↓  
`dashboard_queries.sql`  
↓  
Databricks SQL Dashboard

The dashboard does not read CSV, Bronze, or Silver directly.

## 2. Gold Data Sources

Gold outputs used by the dashboard (default local paths from
`config/gold_config.yaml`):

| Logical dataset | Gold path | Dashboard temp view / table reference |
|-----------------|-----------|---------------------------------------|
| Sales by Product | `{gold_root}/sales_by_product` | `gold_sales_by_product` |
| Revenue by Customer | `{gold_root}/revenue_by_customer` | `gold_revenue_by_customer` |
| Customer Segmentation | `{gold_root}/customer_segmentation` | `gold_customer_segmentation` |

On Databricks, register or mount these datasets as tables/views using the
project's existing Gold table registration configuration when enabled
(`GOLD_CATALOG`, `GOLD_SCHEMA`, `GOLD_TABLE_REGISTRATION_ENABLED`).

## 3. Query Inventory

File: `src/dashboard/dashboard_queries.sql`

1. Top 10 Products by Revenue
2. Customer Revenue Distribution
3. Customer Segmentation
4. Optional KPI - Total Revenue

Each query is independently executable.

## 4. Dashboard Name

Recommended dashboard name:

**E-Commerce Sales Analytics Dashboard**

## 5. Tile Configuration

### Tile 1

**Title:** Top 10 Products by Revenue  
**Query:** Dashboard Query 1  
**Visualization:** Bar chart  
**X-axis:** `product_name`  
**Y-axis:** `total_revenue`  
**Sort:** descending by `total_revenue`  
**Limit:** 10 (already enforced in SQL)

Useful additional field for tooltips/filters: `category`

### Tile 2

**Title:** Customer Revenue Distribution  
**Query:** Dashboard Query 2  
**Visualization:** Histogram  
**Value field:** `total_revenue`  
**Granularity:** one row per customer

Databricks configuration guidance:

- Use `total_revenue` as the numeric value for the histogram
- Do not aggregate customer rows before visualization
- Expected shape: one customer-level revenue value per row

### Tile 3

**Title:** Customer Segmentation  
**Query:** Dashboard Query 3  
**Visualization:** Pie chart  
**Category:** `segment_type`  
**Value:** `customer_count`

Expected categories:

- High-Value
- Repeat
- One-Time
- Inactive

### Optional Tile 4

**Title:** Total Revenue  
**Query:** Dashboard Query 4  
**Visualization:** KPI / single-value counter  
**Value:** `total_revenue`

This tile is optional but included to satisfy the assignment's 3+ tile
requirement with a simple business KPI.

## 6. Filters

`src/dashboard/dashboard_queries.sql` contains **base queries without dashboard
parameters**. This is intentional: Databricks SQL Dashboard filters are configured
in the dashboard UI (or by replacing the query text with the parameterized wrappers
below). Do not add unused `:parameter` placeholders to the committed base SQL.

Gold does not expose an order-date field suitable for dashboard date filtering.
Do not invent date filters from raw data.

Recommended filters:

### Product Category

- **Field:** `category`
- **Applied to:** Top 10 Products by Revenue
- **Scope:** visualization-level filter
- **Type:** single-select or multi-select
- **Behavior:** filter products before ranking/limit

Suggested Databricks query wrapper for Tile 1:

```sql
SELECT
    product_id,
    product_name,
    category,
    total_orders,
    total_revenue,
    avg_order_value
FROM gold_sales_by_product
WHERE (:product_category IS NULL OR category = :product_category)
ORDER BY total_revenue DESC, product_id ASC
LIMIT 10;
```

### Customer Segment (source customer attribute)

- **Field:** `customer_segment`
- **Applied to:** Customer Revenue Distribution
- **Scope:** visualization-level filter
- **Type:** single-select or multi-select
- **Behavior:** filters customer rows before histogram rendering

Suggested Databricks query wrapper for Tile 2:

```sql
SELECT
    customer_id,
    customer_name,
    customer_segment,
    total_orders,
    total_revenue,
    avg_order_value,
    lifetime_value_actual
FROM gold_revenue_by_customer
WHERE (:customer_segment IS NULL OR customer_segment = :customer_segment)
ORDER BY total_revenue DESC, customer_id ASC;
```

### Segment Type (derived Gold segmentation)

- **Field:** `segment_type`
- **Applied to:** Customer Segmentation
- **Scope:** visualization-level filter
- **Type:** single-select or multi-select

Suggested Databricks query wrapper for Tile 3:

```sql
SELECT
    segment_type,
    customer_count,
    avg_revenue,
    total_revenue
FROM gold_customer_segmentation
WHERE (:segment_type IS NULL OR segment_type = :segment_type)
ORDER BY segment_type ASC;
```

### Revenue Range

- **Field:** `total_revenue`
- **Applied to:** Customer Revenue Distribution
- **Scope:** visualization-level filter
- **Type:** numeric range
- **Behavior:** filter customer rows by actual revenue before histogram display

Example wrapper:

```sql
...
FROM gold_revenue_by_customer
WHERE (:min_revenue IS NULL OR total_revenue >= :min_revenue)
  AND (:max_revenue IS NULL OR total_revenue <= :max_revenue)
```

Important:

- These are visualization-level filters, not misleading global filters.
- Base queries in `dashboard_queries.sql` are unfiltered and used for local
  validation.
- Apply filter wrappers in Databricks when configuring dashboard parameters.

## 7. Recommended Layout

```text
-------------------------------------------------
| E-Commerce Sales Analytics Dashboard          |
-------------------------------------------------
| Top 10 Products       | Customer Segmentation |
| by Revenue             |                      |
| Bar Chart              | Pie Chart            |
-------------------------------------------------
| Customer Revenue Distribution                  |
| Histogram                                     |
-------------------------------------------------
| Filters                                       |
-------------------------------------------------
| Optional Total Revenue KPI                    |
-------------------------------------------------
```

## 8. Local Validation

Prerequisite: Gold outputs must exist.

Command:

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
PYTHONPATH=src python src/dashboard/validate_dashboard_queries.py
```

Or after editable install:

```bash
validate-dashboard-queries
```

Local validation:

1. Creates/reuses SparkSession
2. Reads Gold Parquet datasets
3. Registers temp views (`gold_*`)
4. Executes each dashboard query
5. Validates schemas, row counts, sorting, and reconciliation
6. Prints sample results

Local validation does not create the Databricks dashboard UI.

## 9. Databricks Setup

Manual Databricks action required.

Steps:

1. Ensure Gold datasets are available in Databricks (Parquet location or
   registered tables from the Gold pipeline).
2. Create SQL objects or queries referencing:
   - `gold_sales_by_product`
   - `gold_revenue_by_customer`
   - `gold_customer_segmentation`
3. Open **SQL** → **Dashboards** → **Create dashboard**.
4. Name the dashboard **E-Commerce Sales Analytics Dashboard**.
5. Add a visualization tile for each query in `dashboard_queries.sql`.
6. Configure visualizations per section 5 above.
7. Add visualization-level filters per section 6.
8. Save and publish the dashboard.

Databricks dashboard creation was not executed in this repository session.

## 10. Expected Results

Using the current generated dataset and Gold configuration:

- Top 10 Products returns up to 10 rows sorted by descending `total_revenue`
- Customer Revenue Distribution returns one row per Gold customer
- Customer Segmentation returns up to four segment rows
- Total Revenue KPI equals the sum of Gold customer revenue

Example local full-dataset validation results from the existing Gold run:

- Gold sales rows: 500
- Gold customer rows: 9940
- Gold segmentation rows: 4
- Total revenue KPI / customer revenue total: 85064788.93

## 11. Reconciliation Rules

Dashboard queries must not alter Gold numbers.

Validated relationships:

- Top 10 product revenue sum <= total Gold product revenue
- Customer revenue distribution total = Gold `revenue_by_customer` total
- Segmentation `SUM(total_revenue)` = Gold customer revenue total
- Segmentation `SUM(customer_count)` = Gold segmentation customer count total
- Total Revenue KPI = Gold customer revenue total

## 12. Empty Data Behavior

If Gold outputs are empty:

- Top 10 query returns zero rows
- Customer revenue query returns zero rows
- Segmentation query returns zero rows
- Total Revenue KPI returns zero or NULL depending on Spark aggregation behavior

Queries should not fail with divide-by-zero or invalid pie/histogram input when
Gold is empty.

## 13. Troubleshooting

### Gold input missing

Run Gold first:

```bash
PYTHONPATH=src python src/gold/create_gold_tables.py
```

### Dashboard query validation fails reconciliation

Verify Gold outputs were generated successfully and have not been modified
outside the pipeline.

### Databricks tile shows no data

Confirm the dashboard query references the correct Gold table/view names and
that Gold datasets exist in the configured catalog/schema or storage location.

### Filter appears to do nothing

Confirm the filter is attached to the visualization that exposes the filtered
field. Filters documented here are visualization-level, not global, unless you
explicitly configure a dashboard parameter across all tiles.

## 14. Daily/Weekly Trends Note

The repository structure references `03_daily_weekly_trends.sql`, but the current
Gold implementation provides only the three mandatory aggregation tables. The
dashboard therefore does not expose Daily/Weekly Trends unless that Gold dataset
is added in a future stage.

## 15. Architecture Boundary

Medallion flow enforced by the dashboard layer:

Bronze → Silver → Gold → Dashboard

The dashboard SQL never reads raw CSV or bypasses Gold.
