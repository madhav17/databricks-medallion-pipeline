# Database Setup Notes

## Overview

This project uses a Medallion Architecture on Parquet datasets rather than a
traditional operational RDBMS as the primary processing store. `database/schema.sql`
documents the logical relational model that maps to CSV, Bronze, Silver, and Gold
datasets.

## Local Setup

### Prerequisites

- Python 3.9+
- Java 17 (OpenJDK) for local PySpark
- `uv` for dependency management

```bash
uv sync
export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home  # macOS example
```

### Schema Reference

Review or execute `database/schema.sql` in a SQL client if a relational reference
schema is needed. The pipeline itself does not require loading this DDL into a
local database for normal execution.

### Data Loading Path

1. Generate CSV landing files (`generate-sample-data`)
2. Ingest to Bronze Parquet (`bronze-ingest-all`)
3. Run Silver quality processing (`silver-create-tables`)
4. Run Gold aggregations (`gold-create-tables`)
5. Validate dashboard SQL (`validate-dashboard-queries`)

Physical paths are configuration-driven:

| Layer | Default root |
|-------|--------------|
| CSV | `./data/` |
| Bronze | `./data/bronze/` |
| Silver | `./data/silver/` |
| Gold | `./data/gold/` |

## Databricks Setup

**Databricks execution not independently verified in this repository workspace.**

To verify on Databricks:

1. Upload or mount the repository.
2. Configure environment variables or YAML overrides for cloud storage paths:
   - Bronze/Silver/Gold roots
   - Optional Unity Catalog registration (`*_CATALOG`, `*_SCHEMA`, `*_TABLE_REGISTRATION_ENABLED`)
3. Run the same Python entry points with an active Databricks SparkSession.
4. Register Gold outputs as tables/views referenced by `src/dashboard/dashboard_queries.sql`.
5. Create the SQL Dashboard manually using `src/dashboard/DASHBOARD_GUIDE.md`.

Environment-specific differences are limited to paths and table registration;
transformation logic is shared with local execution.

## Environment-Specific Configuration

Override paths via YAML files under `config/` or documented environment variables
in each layer's notes:

- `src/data_generation/DATA_GENERATION_NOTES.md`
- `src/bronze/BRONZE_LAYER_NOTES.md`
- `src/silver/SILVER_LAYER_NOTES.md`
- `src/gold/GOLD_LAYER_NOTES.md`
- `src/dashboard/DASHBOARD_GUIDE.md`
