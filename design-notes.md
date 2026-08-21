# Design Notes

## Architecture

```text
Source CSV
    ↓
Bronze (Parquet, raw preservation)
    ↓
Silver (quality flags + metrics)
    ↓
Gold (business aggregations)
    ↓
Dashboard SQL (Databricks SQL Dashboard)
```

## Layer Responsibilities

### Data Generation

- Deterministic synthetic data (`seed=42`)
- Mandatory anomaly injection (460 events in CORE mode)
- Independent CSV validation CLI

### Bronze

- Explicit PySpark schemas (`src/bronze/schemas.py`)
- Structural validation only; no business cleansing
- Parquet output + ingestion metadata

### Silver

- Preserves all Bronze rows
- Runs completeness → uniqueness → referential integrity → business logic
- Adds `quality_check_result`, `quality_check_reason`
- Writes `quality_metrics` Parquet dataset

### Gold

- Consumes Silver rows with `quality_check_result = 'PASS'`
- Completed orders only for revenue (configurable)
- Three aggregation datasets with reconciliation checks

### Dashboard

- Reads registered Gold temp views/tables
- Four SQL queries (3 required visualizations + KPI)
- Local validation via `validate_dashboard_queries.py`

## Configuration Strategy

Each layer uses YAML + Pydantic:

- `config/generator_config.yaml`
- `config/bronze_config.yaml`
- `config/silver_config.yaml`
- `config/gold_config.yaml`

Environment-specific values (paths, catalog, schema) are configurable; business
logic is shared between local and Databricks execution.

## Local vs Databricks Execution

| Concern | Local | Databricks |
|---------|-------|------------|
| SparkSession | Created with `local[*]` when none active | Reuses cluster session |
| Storage paths | Relative project paths | Cloud URIs via config/env |
| Table registration | Disabled by default | Optional Unity Catalog registration |
| Dashboard | SQL validated locally; UI manual on Databricks | Databricks SQL Dashboard |

## Quality Validation Strategy

Silver detects and flags anomalies introduced at generation time plus any
unexpected business-rule violations. Gold filters to PASS rows for analytics.

## Aggregation Strategy

Gold SQL files under `src/gold/` define aggregations. Eligible orders join valid
PASS customer and product dimensions to keep reconciliation consistent.

## Testing Strategy

- Unit tests per layer
- Data generation E2E validation
- Medallion pipeline integration test with small fixture config

Persistent AI context: `.cursor/rules/*.mdc`
