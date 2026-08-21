# Project Specification

Design and functional specification used to guide Cursor-assisted implementation.

## Problem Statement

An e-commerce company needs a medallion pipeline that ingests daily sales CSVs,
applies data quality validation, produces business aggregations, and supports BI
dashboards on Databricks. This repository implements that flow with synthetic data
for local development and Databricks-compatible execution.

## Functional Requirements

1. Generate reproducible synthetic CSV datasets with mandatory anomalies
2. Ingest CSV to Bronze Parquet without business cleansing
3. Apply Silver quality checks, flag invalid rows, and emit quality metrics
4. Build Gold business aggregations from valid Silver data
5. Provide dashboard SQL queries over Gold outputs
6. Document architecture, data model, quality strategy, AI workflow, and tests

## Non-Functional Requirements

- Run locally with PySpark for development and pytest validation
- Remain compatible with Databricks via configuration-driven paths
- Preserve intentional source anomalies through Bronze
- Fail fast on invalid configuration and schema mismatches
- Idempotent overwrite writes for repeatable pipeline runs

## Non-Goals

- Real customer PII or production data sources
- Local dashboard UI (Databricks SQL Dashboard is a manual setup step)
- Modifying completed/frozen layers unless explicitly required

## Data Sources

| Dataset | Rows (target) | Format |
|---------|---------------|--------|
| customers | 10,000 | CSV |
| orders | 100,000 | CSV |
| products | 500 | CSV |

Intentional anomalies (~460 rows documented) for Silver testing.

## Silver Quality Checks

Assignment Common Technical Requirements: four checks minimum.

Implemented checks:

1. **Completeness** — NULL checks on critical fields
2. **Uniqueness** — duplicate `customer_id`, `order_id`
3. **Type/schema validation** — dataset-level schema gate
4. **Referential integrity** — orphan FK detection on orders
5. **Business logic** — segment, revenue, date, and amount rules

Output: `quality_check_result`, `quality_check_reason`, and `quality_metrics`.

## Gold Outputs

Core acceptance criteria: three aggregation tables.  
Common Technical Requirements + repository structure: four aggregations.

Implemented outputs:

1. **Sales by Product** — `01_sales_by_product.sql`
2. **Revenue by Customer** — `02_revenue_by_customer.sql`
3. **Daily/Weekly Trends** — `03_daily_weekly_trends.sql`
4. **Customer Segmentation** — `04_customer_segmentation.sql`

Gold consumes Silver rows where `quality_check_result = 'PASS'` and eligible
order statuses (default: `Completed`).

## Dashboard

- Minimum three SQL queries for visualizations:
  - Top 10 products by revenue (bar)
  - Customer revenue distribution (histogram)
  - Customer segmentation (pie)
- Optional fourth KPI query (total revenue)
- Local validation via `validate_dashboard_queries.py`

## Submission Artifacts

- Source code and tests (`src/`, `tests/`)
- Sample CSV files (`data/*.csv`)
- Validation reports (`reports/`)
- Database documentation (`database/`)
- Lifecycle documentation (repo root markdown files)
- AI prompt history (`ai-prompts/`)
- Cursor workflow (`tool-specific/cursor-workflow/`)

## Ambiguities and Decisions

See `requirements-analysis.md` and `src/gold/GOLD_LAYER_NOTES.md` for evidence-based
resolution of Silver check count and Gold aggregation count conflicts in the
assignment PDF.

## Related Files

- `requirements-analysis.md` — requirement mapping
- `design-notes.md` — architecture detail
- `data-model.md` — schemas and relationships
- `.cursor/project-spec.md` — working copy used during development
