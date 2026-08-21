# Debugging Notes

Issues documented below are supported by repository artifacts (layer notes,
`ai-prompts/`, and test history). Incidents without verifiable history are not
invented.

## 1. Local Spark / Java Runtime

**Problem:** Bronze/Silver/Gold pytest and CLI runs failed with Spark/Hadoop Java
errors (e.g., `UnsupportedOperationException: getSubject is not supported`).

**Root cause:** Incompatible or missing Java runtime for PySpark 3.5+.

**AI assistance:** Suggested OpenJDK 17 and local Spark runtime configuration in
`src/bronze/ingestion_utils.py`.

**Human decision:** ACCEPTED — set `JAVA_HOME` to OpenJDK 17 for local runs.

**Fix:** `_configure_local_spark_runtime()` and documented `JAVA_HOME` in README.

**Validation:** Layer tests pass when Java 17 is configured. Not verified from
repository history for every environment.

## 2. Silver Test Fixture Schema Types

**Problem:** Early Silver tests failed due to fixture rows not matching explicit
Bronze schemas (type/nullable mismatches).

**Root cause:** Test data created without `CUSTOMERS_SCHEMA` / `ORDERS_SCHEMA`.

**AI assistance:** Updated fixtures to use Bronze schema definitions.

**Human decision:** ACCEPTED.

**Fix:** `tests/test_silver.py` fixture uses explicit schemas.

**Validation:** Silver tests pass.

## 3. Gold Decimal Schema Mismatch

**Problem:** Gold output schema validation failed after `SUM()` aggregations.

**Root cause:** Spark inferred `DecimalType(20,2)` vs expected `Decimal(10,2)`.

**AI assistance:** Added explicit `CAST(... AS DECIMAL(10,2))` in Gold SQL.

**Human decision:** ACCEPTED.

**Fix:** `src/gold/01_sales_by_product.sql`, related SQL files.

**Validation:** Gold tests pass (`tests/test_gold.py`).

## 4. Gold Revenue Reconciliation Failure

**Problem:** Product/customer revenue totals did not reconcile to eligible Silver
order revenue.

**Root cause:** Orders linked to invalid customers were included in product-side
aggregates.

**AI assistance:** Semi-join to valid PASS parent dimensions before aggregation.

**Human decision:** ACCEPTED.

**Fix:** Gold SQL + `gold_utils.py` reconciliation logic.

**Validation:** Gold pipeline reconciliation passes locally.

## 5. Dashboard SQL Section Parsing

**Problem:** Dashboard validation failed to load queries from `dashboard_queries.sql`.

**Root cause:** Naive split separated section titles from SQL bodies.

**AI assistance:** Regex-based section parser in `dashboard_utils.py`.

**Human decision:** ACCEPTED.

**Fix:** `load_dashboard_queries()` parser update.

**Validation:** Dashboard tests pass (`tests/test_dashboard.py`).

## 6. Missing Silver Business Logic Check (Gap Analysis)

**Problem:** Assignment requires four Silver checks; business logic module was
missing (`05_quality_business_logic.py`).

**Root cause:** Initial Silver implementation covered completeness, uniqueness,
referential integrity, and structural type validation only.

**AI assistance:** Implemented business logic module aligned with
`dataset_validator.py` rules and integrated into orchestrator/metrics.

**Human decision:** ACCEPTED — minimal addition without redesigning other checks.

**Fix:** `src/silver/05_quality_business_logic.py`, orchestrator update.

**Validation:** Silver tests include business logic assertion; metrics include
`business_logic` check rows.

## Unverified / Not Reconstructed

- Specific Databricks cluster debugging sessions: **Not verified from repository history.**
- Individual prompt-by-prompt Bronze design iterations: partially recorded in
  `ai-prompts/bronze-layer.md` only.
