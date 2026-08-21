# Project Specification

## Functional Requirements

1. Generate reproducible synthetic CSV datasets with mandatory anomalies
2. Ingest CSV to Bronze Parquet without business cleansing
3. Apply Silver quality checks and metrics
4. Build Gold business aggregations from valid Silver data
5. Provide dashboard SQL over Gold outputs
6. Document architecture, data model, quality strategy, and AI workflow

## Non-Goals

- Daily/Weekly Trends Gold table (documented scope exclusion)
- Local dashboard UI (Databricks SQL Dashboard is manual setup step)
- Real PII or production data sources

## Quality Checks (Silver)

1. Completeness
2. Uniqueness
3. Referential Integrity
4. Business Logic

## Gold Outputs

1. Sales by Product
2. Revenue by Customer
3. Customer Segmentation

## Submission Artifacts

- Source code and tests
- Sample CSV files (`data/*.csv`)
- Validation reports (`reports/`)
- Database documentation (`database/`)
- Lifecycle documentation (repo root markdown files)
- AI prompt history (`ai-prompts/`)

See `requirements-analysis.md` for ambiguities and evidence-based scope decisions.
