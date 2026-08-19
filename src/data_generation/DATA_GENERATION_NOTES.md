# Data Generation Notes

## 1. Purpose

This module generates reproducible e-commerce sample CSV files for the Databricks
Medallion Architecture assessment pipeline. The generated files serve as landing
data for the Bronze layer.

## 2. Dataset Interpretation

| Dataset | Unique PK Count | Final CSV Row Count |
|---------|-----------------|---------------------|
| customers | 10,000 | 10,010 |
| orders | 100,000 | 100,020 |
| products | 500 | 500 |

"10,000 customers" means **10,000 unique customer IDs**. Ten duplicate customer IDs
are introduced by appending exact clones, producing 10,010 rows total.

"100,000 orders" means **100,000 unique order IDs**. Twenty duplicate order IDs are
introduced by appending exact clones, producing 100,020 rows total.

## 3. Row-Count Semantics

- `customer_count` / `order_count` in configuration = unique primary key cardinality
- Final CSV row count = base count + duplicate clone count
- Duplicates are **appended**; the base dataset is never reduced

## 4. Customer Generation

- Sequential `customer_id` from 1 to 10,000
- Synthetic names, unique emails, weighted countries and segments
- `lifetime_value` driven by segment using `Decimal` precision
- `signup_date` within configured date range

## 5. Product Generation

- 500 unique products with category-weighted pricing
- `cost <= price`, `stock_quantity >= 0`, `reorder_level >= 0`
- No product anomalies in CORE mode

## 6. Order Generation

- 100,000 unique `order_id` values (1 to 100,000)
- Valid FKs to customers and products during base generation
- `total_amount = quantity × unit_price` (Decimal, 2dp)
- Status-driven `payment_date` rules for clean data

## 7. Relationship Generation

- Pareto-style customer weighting (configurable `pareto_alpha`)
- Product popularity weighting by category (configurable skew)
- Deterministic via seeded sub-RNG (`relationships` phase)

## 8. Inactive Customer Strategy

Approximately 5–10% of customers are designated inactive during relationship
model construction. These customers receive zero orders through weighted sampling
exclusion. This is natural generation behavior, not an anomaly.

## 9. Mandatory Anomaly Strategy

| Anomaly | Count | Mechanism |
|---------|-------|-----------|
| NULL email | 50 | Set email to NULL on selected rows |
| Duplicate customer_id | 10 | Append exact clones |
| NULL customer_id | 100 | Set customer_id to NULL |
| NULL product_id | 200 | Set product_id to NULL |
| Invalid customer FK | 50 | Orphan namespace 10001–10050 |
| Invalid product FK | 30 | Orphan namespace 501–530 |
| Duplicate order_id | 20 | Append exact clones |

**Total anomaly events: 460**

Injection uses disjoint row pools where practical.

## 10. Duplicate Strategy

Duplicates are created by:
1. Selecting N source rows via seeded random sample
2. Deep-copying each source row
3. Appending the clone to the dataset

Each duplicate is an **exact clone** across all columns. Duplicate counting:
- `duplicate_customer_id_count = 10` means 10 customer IDs each appear exactly twice
- `duplicate_order_id_count = 20` means 20 order IDs each appear exactly twice

## 11. Invalid FK Strategy

Invalid foreign keys use reserved orphan-ID namespaces:
- Customer orphans: `customer_count + 1` through `customer_count + invalid_count`
- Product orphans: `product_count + 1` through `product_count + invalid_count`

These IDs are guaranteed absent from parent datasets.

## 12. AnomalyLedger

Internal metadata tracking every injected anomaly:
- dataset, anomaly_type, row_identifier, primary_key
- affected_column, injection_stage, source_record_identifier

The ledger is NOT written to business CSV files.

## 13. CORE vs EXTENDED Mode

- **CORE** (default): mandatory anomalies only
- **EXTENDED**: core + optional anomalies (placeholder; disabled by default)

## 14. Configuration

YAML file (`config/generator_config.yaml`) validated through Pydantic `GeneratorConfig`.
Mandatory counts are lock-enforced when `mandatory_anomalies.locked: true`.

## 15. Reproducibility

- Master seed with phase-derived sub-seeds
- Fixed `end_date` (no system clock in data)
- Deterministic row ordering (generation order preserved)
- Identical config + seed → identical CSV output

## 16. Validation

Two validation layers:
1. **Pre-write**: pipeline validates after generation (via `validate_dataset`)
2. **Independent CLI**: `verify_dataset` reads CSVs and validates independently

The validator does NOT trust the AnomalyLedger as sole source of truth.

## 17. Reporting

Generates:
- `reports/validation_report.json`
- `reports/anomaly_report.md`
- `reports/anomaly_manifest.json` (gitignored generated artifact)

## 18. Expected vs Actual Anomaly Counts

The report includes:
- Anomaly events by type (sum = 460)
- Unique affected rows per dataset
- Overlapping anomaly rows
- Total rows containing at least one anomaly

## 19. 460 vs ~700 Discrepancy

The mandatory anomaly specification sums to **460 anomaly events**. The assignment's
~700 figure may count differently (per-field counts, extended anomalies, rows
involved in duplicates counting twice, or overlapping categories). This generator
reports all metrics transparently without fabricating additional anomalies.

## 20. Known Limitations

- Extended anomaly injection is a placeholder (no-op in CORE mode)
- Email uniqueness is enforced only in clean generation (pre-anomaly)
- Inactive customer percentage varies per seed within 5–10% range

## 21. Human Decisions Incorporated

- 10,000 unique customer IDs → 10,010 CSV rows
- 100,000 unique order IDs → 100,020 CSV rows
- Exact clone duplicates (not partial)
- Disjoint mandatory anomaly pools
- Orphan-ID namespaces for invalid FKs
- YAML + Pydantic configuration with lock enforcement
- CORE mode default; EXTENDED opt-in
- AnomalyLedger as internal metadata only
- Independent `verify_dataset` CLI
