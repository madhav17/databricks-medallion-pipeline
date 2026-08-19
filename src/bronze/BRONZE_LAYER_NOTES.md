# Bronze Layer

## Purpose

The Bronze layer ingests raw CSV source files into Parquet datasets without
transforming or cleaning business data. It preserves intentional source-quality
issues so the Silver layer can detect and handle them later.

Flow:

CSV → PySpark → Explicit Schema → Basic Input Validation → Parquet → Bronze Dataset

## Source Files

Configured in `config/bronze_config.yaml`:

| Dataset   | Source file     | Default path              |
|-----------|-----------------|---------------------------|
| customers | `customers.csv` | `{source_root}/customers.csv` |
| orders    | `orders.csv`    | `{source_root}/orders.csv`    |
| products  | `products.csv`  | `{source_root}/products.csv`  |

Default local `source_root`: `./data`

## Source Schemas

Explicit PySpark schemas are defined in `src/bronze/schemas.py`.

Monetary fields use a consistent definition:

- `DecimalType(10, 2)` (`MONETARY_DECIMAL`)
- Two decimal places, matching the data generator CSV formatting

### customers

| Column           | Type                |
|------------------|---------------------|
| customer_id      | IntegerType         |
| customer_name    | StringType          |
| email            | StringType          |
| country          | StringType          |
| signup_date      | DateType            |
| customer_segment | StringType          |
| lifetime_value   | DecimalType(10, 2)  |

### orders

| Column       | Type                |
|--------------|---------------------|
| order_id     | IntegerType         |
| customer_id  | IntegerType         |
| order_date   | DateType            |
| product_id   | IntegerType         |
| quantity     | IntegerType         |
| unit_price   | DecimalType(10, 2)  |
| total_amount | DecimalType(10, 2)  |
| order_status | StringType          |
| payment_date | DateType            |

### products

| Column         | Type                |
|----------------|---------------------|
| product_id     | IntegerType         |
| product_name   | StringType          |
| category       | StringType          |
| price          | DecimalType(10, 2)  |
| cost           | DecimalType(10, 2)  |
| stock_quantity | IntegerType         |
| reorder_level  | IntegerType         |

## CSV → PySpark → Parquet Flow

1. Validate source file exists and is readable.
2. Validate CSV header and required columns.
3. Read CSV with explicit schema (`nullValue=""`, `dateFormat=yyyy-MM-dd`).
4. Count source rows.
5. Write Parquet to the configured Bronze path.
6. Read Parquet back.
7. Verify schema (columns, types, ordering).
8. Compare source and Bronze row counts.
9. Record ingestion metadata separately.

No business columns are added to the datasets.

## Raw Data Preservation

Bronze does not:

- remove or replace NULL values
- deduplicate records
- filter invalid foreign keys
- correct invalid values
- join datasets
- add quality-check columns

Intentional anomalies in the source CSVs (NULL emails, duplicate IDs, invalid
FKs, etc.) are preserved exactly as written.

## Input Validation

Structural validation only:

- source file exists
- source file is readable
- CSV header is present
- required columns exist
- configured paths are valid

Business/data-quality validation is deferred to Silver.

## Schema Strategy

- Explicit schemas in `schemas.py`
- No reliance on `inferSchema=True` for ingestion
- Post-write schema verification on read-back

## Ingestion Metadata

Metadata is stored separately at:

`{bronze_root}/_metadata/ingestion_metadata.parquet`

Fields captured:

- `dataset_name`
- `source_file`
- `source_path`
- `bronze_path`
- `source_row_count`
- `bronze_row_count`
- `ingestion_timestamp`
- `status`
- `run_id`
- `ingestion_duration_seconds`
- `source_file_size_bytes`
- `error_message` (on failure)

## Error Handling

Failures raise `BronzeIngestionError` with dataset and path context for:

- missing/unreadable CSV
- missing required columns
- invalid configuration
- Spark read/write failures
- schema verification failures
- source/Bronze row-count mismatch

If any required dataset fails in `ingest_all.py`, the overall pipeline fails.

## Idempotency

Bronze writes use `mode=overwrite` (configurable in `bronze_config.yaml`).

Re-running ingestion replaces the prior Bronze Parquet output for each dataset
rather than appending duplicate logical data.

## Local Execution

From the project root:

```bash
PYTHONPATH=src python src/bronze/ingest_all.py
```

Or via the package entry point after install:

```bash
pip install -e .
bronze-ingest-all
```

Environment overrides:

- `BRONZE_SOURCE_ROOT`
- `BRONZE_ROOT`
- `BRONZE_CATALOG`
- `BRONZE_SCHEMA` (maps to database)
- `BRONZE_TABLE_REGISTRATION_ENABLED`

## Databricks Execution

Use the same code and configuration model. Databricks provides the active
`SparkSession`; the ingestion code reuses it instead of forcing `local[*]`.

Configure Databricks-accessible paths in `config/bronze_config.yaml` or via
environment variables. Example:

```yaml
paths:
  source_root: "dbfs:/FileStore/medallion/source"
  bronze_root: "dbfs:/FileStore/medallion/bronze"
```

Optional table registration (disabled by default):

```yaml
table_registration:
  enabled: true
  catalog: "main"
  database: "bronze"
```

## Output Structure

```
{bronze_root}/
├── customers/
│   └── *.parquet
├── orders/
│   └── *.parquet
├── products/
│   └── *.parquet
└── _metadata/
    └── ingestion_metadata.parquet
```

## What Bronze Does Not Do

- Silver transformations or data-quality checks
- Gold aggregations
- Dashboard logic
- Delta Lake storage (Bronze physical format is Parquet only)
- Auto Loader / streaming
- Business-rule validation or remediation
