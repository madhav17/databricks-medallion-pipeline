# databricks-medallion-pipeline

E-commerce Medallion Architecture assessment pipeline:

**CSV → Bronze → Silver → Gold → Databricks SQL Dashboard**

All data is synthetic. No real customer PII is used.

## Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Java 17 (OpenJDK) for local PySpark

```bash
uv sync
export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home  # macOS example
```

## Quick Start (End-to-End, Local)

### 1. Generate sample CSV data

```bash
PYTHONPATH=src python src/data_generation/generate_sample_data.py
```

Or: `generate-sample-data`

Landing files are written to `./data/landing/`. Ensure Bronze source files exist at
`./data/customers.csv`, `./data/orders.csv`, and `./data/products.csv` (copy from
landing if needed).

### 2. Validate generated data

```bash
PYTHONPATH=src python src/data_generation/verify_dataset.py
```

Or: `verify-dataset`

Reports: `./reports/validation_report.json`, `./reports/anomaly_report.md`

### 3. Bronze ingestion (CSV → Parquet)

```bash
PYTHONPATH=src python src/bronze/ingest_all.py
```

Or: `bronze-ingest-all`

Output: `./data/bronze/`

### 4. Silver quality processing

```bash
PYTHONPATH=src python src/silver/create_silver_tables.py
```

Or: `silver-create-tables`

Runs four quality checks: completeness, uniqueness, referential integrity,
business logic. Output: `./data/silver/` and `./data/silver/quality_metrics`

### 5. Gold aggregations

```bash
PYTHONPATH=src python src/gold/create_gold_tables.py
```

Or: `gold-create-tables`

Output: `./data/gold/` (three aggregation datasets)

### 6. Validate dashboard SQL

```bash
PYTHONPATH=src python src/dashboard/validate_dashboard_queries.py
```

Or: `validate-dashboard-queries`

See `src/dashboard/DASHBOARD_GUIDE.md` for Databricks SQL Dashboard setup.

## Run Tests

```bash
PYTHONPATH=src python -m pytest tests/ -q
```

Includes layer tests and medallion integration test (`tests/test_medallion_e2e.py`).

## Configuration

| Layer | Config file |
|-------|-------------|
| Data Generation | `config/generator_config.yaml` |
| Bronze | `config/bronze_config.yaml` |
| Silver | `config/silver_config.yaml` |
| Gold | `config/gold_config.yaml` |

Paths and optional Unity Catalog registration are environment-specific; business
logic is shared between local and Databricks execution.

## Project Documentation

| Document | Purpose |
|----------|---------|
| `requirements-analysis.md` | Assignment scope and ambiguities |
| `design-notes.md` | Architecture and data flow |
| `data-model.md` | Entity schemas and relationships |
| `data-quality-strategy.md` | Silver quality checks |
| `database/` | SQL schema and setup notes |
| `ai-prompts/` | AI prompt history and evaluations |
| `src/*/ *_LAYER_NOTES.md` | Layer-specific implementation notes |

## Databricks Execution

Same Python entry points run on Databricks with an active SparkSession. Configure
cloud storage paths and optional table registration via YAML or environment variables.

**Databricks execution not independently verified in this workspace.** See
`database/setup-notes.md` for manual verification steps.

## Responsible AI

- Synthetic assessment data only
- AI-assisted development with human review and pytest validation
- See `final-ai-usage-summary.md` and `tool-workflow.md`

## Dependencies

Primary dependency definition: `pyproject.toml`

Optional export: `requirements.txt` (generated from project metadata for submission)
