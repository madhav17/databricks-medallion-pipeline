# databricks-medallion-pipeline

E-commerce Medallion Architecture pipeline (Data Generation -> Bronze -> Silver -> Gold).

## Run Gold Layer (Local)

Prerequisite: Silver outputs must exist.

```bash
PYTHONPATH=src python src/gold/create_gold_tables.py
```

Or:

```bash
gold-create-tables
```