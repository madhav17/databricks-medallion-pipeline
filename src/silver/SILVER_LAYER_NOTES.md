# Silver Layer

## 1. Silver Purpose

Silver consumes Bronze Parquet datasets and applies quality validation while
preserving all rows. Invalid records are flagged, not deleted.

## 2. Bronze Inputs

Default Bronze roots come from `config/silver_config.yaml`:

- `customers`: `{bronze_root}/customers`
- `orders`: `{bronze_root}/orders`
- `products`: `{bronze_root}/products`

## 3. Completeness Rules

- Customers: `email` must be non-null
- Orders: `customer_id` and `product_id` must be non-null

Failures are flagged with:

- `COMPLETENESS: email is NULL`
- `COMPLETENESS: customer_id is NULL`
- `COMPLETENESS: product_id is NULL`

## 4. Uniqueness Rules

- Customers: `customer_id` must be unique
- Orders: `order_id` must be unique

All rows in duplicate groups are flagged; no deduplication is performed.

## 5. Type / Schema Validation

Type validation compares Bronze DataFrame schemas against Bronze expected
schemas (`src/bronze/schemas.py`) and checks:

- required columns exist
- column ordering is stable
- data types match expected Spark types

Missing columns or mismatched types raise clear errors.

## 6. Referential Integrity Rules

For `orders` only:

- non-null `customer_id` must exist in `customers.customer_id`
- non-null `product_id` must exist in `products.product_id`

Null FKs are treated as completeness failures, not referential failures.

## 7. Quality Result Design

Each Silver dataset preserves business columns and adds:

- `quality_check_result`: `PASS` or `FAIL`
- `quality_check_reason`: semicolon-separated failure reasons

An internal `quality_fail_reasons` array is used to retain multiple failures.

## 8. Multiple Failure Handling

All checks run and append reasons using array union semantics. A row can contain
multiple reasons (for example completeness + uniqueness).

## 9. Metrics Calculation

Silver writes per-check metrics to `{silver_root}/quality_metrics` with:

- `dataset_name`
- `check_name`
- `total_rows`
- `passed_rows`
- `failed_rows`
- `pass_percentage`
- `fail_percentage`

Percentages are dynamically calculated from DataFrame counts.

## 10. Local Execution

From project root:

```bash
PYTHONPATH=src python src/silver/create_silver_tables.py
```

Or after editable install:

```bash
silver-create-tables
```

## 11. Databricks Execution

Same business logic is used on Databricks. An active SparkSession is reused
when present. Configure Bronze/Silver roots using environment or config:

- `SILVER_BRONZE_ROOT`
- `SILVER_ROOT`
- `SILVER_CATALOG`
- `SILVER_SCHEMA`
- `SILVER_TABLE_REGISTRATION_ENABLED`

## 12. Configuration

Silver configuration uses YAML + Pydantic:

- `config/silver_config.yaml`
- `src/silver/config.py`
- `src/silver/config_loader.py`

Only paths/registration are environment-specific; validation logic is shared.

## 13. Testing

Silver tests validate:

- completeness flags
- uniqueness flags
- referential integrity flags
- quality result columns
- metrics generation
- row-count preservation
- schema validation errors

## 14. Expected Intentional Anomalies

Customers:

- 50 NULL emails
- 10 duplicate customer IDs

Orders:

- 100 NULL customer IDs
- 200 NULL product IDs
- 50 invalid customer IDs
- 30 invalid product IDs
- 20 duplicate order IDs

## 15. Known Assumptions

- Bronze schemas are authoritative for Silver type validation.
- Referential checks use distinct parent key sets to avoid row multiplication
  from duplicate parent IDs.
- Silver preserves Bronze row counts; any mismatch raises an error.
