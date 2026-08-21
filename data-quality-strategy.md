# Data Quality Strategy

Silver applies four assignment quality checks while preserving every Bronze row.

## 1. Completeness

**Purpose:** Detect missing required field values.

**Rules:**

- Customers: `email` must be non-null
- Orders: `customer_id` and `product_id` must be non-null

**Detection:** Null checks in `src/silver/01_quality_completeness.py`

**Expected behavior:** 50 NULL emails, 100 NULL customer IDs, 200 NULL product IDs
in CORE generated data.

**Handling:** Rows flagged FAIL with `COMPLETENESS:` reasons; not removed.

**Reporting:** `check_name = completeness` in `{silver_root}/quality_metrics`

## 2. Uniqueness

**Purpose:** Detect duplicate primary keys.

**Rules:**

- Customers: `customer_id` unique
- Orders: `order_id` unique

**Detection:** Window/count logic in `src/silver/02_quality_uniqueness.py`

**Expected behavior:** All rows in duplicate groups flagged (10 customer IDs × 2,
20 order IDs × 2).

**Handling:** No deduplication; duplicates remain for inspection.

**Reporting:** `check_name = uniqueness`

## 3. Referential Integrity

**Purpose:** Detect orphan foreign keys.

**Rules (orders only):**

- Non-null `customer_id` must exist in customers
- Non-null `product_id` must exist in products

**Detection:** Left-join against distinct parent keys in
`src/silver/04_quality_referential_integrity.py`

**Expected behavior:** 50 invalid customer FKs, 30 invalid product FKs. NULL FKs
are completeness failures, not referential failures.

**Handling:** Orphan rows flagged; not corrected.

**Reporting:** `check_name = referential_integrity`

## 4. Business Logic

**Purpose:** Detect domain rule violations on otherwise structurally valid rows.

**Rules:** Documented in `src/silver/SILVER_LAYER_NOTES.md` section 7 and
implemented in `src/silver/05_quality_business_logic.py`.

Examples:

- Valid segment and order status enumerations
- Non-negative monetary and quantity fields
- `total_amount = quantity × unit_price` (2dp)
- Temporal consistency (order vs signup, payment vs order)
- Completed orders require `payment_date`

**Detection:** Column expressions and customer signup join for orders.

**Expected behavior:** CORE mandatory anomalies target the first three checks;
business-logic failure rate on standard generated data is expected to be low.

**Handling:** Rows flagged with `BUSINESS_LOGIC:` reasons.

**Reporting:** `check_name = business_logic` for customers, orders, and products.

## Intentional Anomalies

See `src/data_generation/DATA_GENERATION_NOTES.md` and `database/seed-data-notes.md`.

Total mandatory anomaly events: **460**

## Structural Type Validation

Bronze schema conformance is validated before flagging (`type_validation` metric).
Schema failures raise pipeline errors for missing columns or type mismatches.

## Downstream Consumption

Gold reads Silver datasets filtered to `quality_check_result = 'PASS'` for
analytics. Invalid rows remain available in Silver for audit.

## Metrics Output

`{silver_root}/quality_metrics` columns:

- dataset_name, check_name, total_rows, passed_rows, failed_rows,
  pass_percentage, fail_percentage

Percentages computed from actual Spark counts at pipeline runtime.
