# databricks-medallion-pipeline

E-commerce Medallion Architecture pipeline (Data Generation -> Bronze -> Silver -> Gold -> Dashboard).

## Run Gold Layer (Local)

Prerequisite: Silver outputs must exist.

```bash
PYTHONPATH=src python src/gold/create_gold_tables.py
```

Or:

```bash
gold-create-tables
```

## Validate Dashboard Queries (Local)

Prerequisite: Gold outputs must exist.

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
PYTHONPATH=src python src/dashboard/validate_dashboard_queries.py
```

Or:

```bash
validate-dashboard-queries
```

See `src/dashboard/DASHBOARD_GUIDE.md` for Databricks SQL Dashboard setup.