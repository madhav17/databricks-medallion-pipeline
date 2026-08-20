# AI Prompts — Gold Layer

The Gold layer consumes Silver datasets and creates business-ready aggregations
for analytics.

The mandatory Gold outputs are:

1. Sales by Product
2. Revenue by Customer
3. Customer Segmentation

Pipeline context:

Data Generation  
↓  
Bronze  
↓  
Silver  
↓  
Gold  
↓  
Dashboard

Data Generation, Bronze, and Silver were completed before Gold implementation
began.

---

## Prompt 1: Gold Layer Requirements and Design

**PROMPT SENT:**

Not performed as a separate prompt in recorded project history.

**AI RESPONSE SUMMARY:**

Not applicable. Gold requirements and design were provided directly as part of
the implementation prompt (Prompt 2).

**YOUR EVALUATION:**

✓ **What was good:**

- Gold requirements were explicitly detailed in the implementation prompt itself.
- Scope ambiguity (Daily/Weekly Trends vs three mandatory tables) was addressed
  in the implementation prompt.

✗ **What needed fixing:**

- A separate design-only prompt was not recorded.

△ **Missing:**

- No standalone human design review prompt before implementation.

**HUMAN DECISION:**

Decision not yet recorded.

---

## Prompt 2: Gold Layer Implementation

**PROMPT SENT:**

You are a Senior Data Engineer implementing the GOLD layer
of our Databricks Medallion Architecture assessment.

IMPORTANT:

The following stages are already COMPLETED:

1. Data Generation
2. Bronze Layer
3. Silver Layer

The next stage is:

4. Gold Layer — Aggregations & Analytics

The Gold layer must consume the EXISTING Silver datasets.

Do NOT read directly from CSV.

Do NOT read directly from Bronze.

Do NOT modify Data Generation.

Do NOT redesign Bronze.

Do NOT redesign Silver.

The Gold layer must work in:

1. Local PySpark execution
2. Databricks

The same business/aggregation logic must work in both
environments.

Only environment-specific configuration such as paths,
catalog/schema, or storage locations should differ.

The complete Prompt 2 user message contained 43 numbered sections
(from repository inspection through acceptance criteria and final
validation). The opening requirement block is recorded above; the
remaining section text matches the Gold implementation user query
from this project session in full.

Begin by inspecting the existing project and Silver
implementation before writing any code.

**AI RESPONSE SUMMARY:**

Implemented Gold as a Silver-consuming aggregation pipeline with three mandatory
business tables, Spark SQL aggregation files, and a Python orchestrator.

**Files created:**

- `src/gold/__init__.py`
- `src/gold/config.py`
- `src/gold/config_loader.py`
- `src/gold/gold_utils.py`
- `src/gold/01_sales_by_product.sql`
- `src/gold/02_revenue_by_customer.sql`
- `src/gold/04_customer_segmentation.sql`
- `src/gold/create_gold_tables.py`
- `src/gold/GOLD_LAYER_NOTES.md`
- `config/gold_config.yaml`
- `tests/test_gold.py`

**Files modified:**

- `pyproject.toml` (added `gold-create-tables` script entry)
- `README.md` (added local Gold execution instructions)

**SQL aggregations:**

- Sales by Product from `valid_silver_products` LEFT JOIN `valid_silver_orders`
- Revenue by Customer from `valid_silver_customers` LEFT JOIN `valid_silver_orders`
- Customer Segmentation from customer-level revenue CTE with deterministic
  segment precedence

**Python orchestration:**

- `create_gold_tables.py` loads config, registers valid Silver temp views,
  executes SQL files, validates schemas/uniqueness, reconciles revenue totals,
  writes Parquet outputs, and optionally registers tables

**Configuration:**

- YAML + Pydantic pattern (`config/gold_config.yaml`)
- Configurable `high_value_revenue_threshold` (default `1000.00`)
- Configurable `eligible_order_statuses` (default `Completed`)
- Environment overrides for paths, threshold, statuses, catalog/schema

**Local compatibility:**

- Local SparkSession creation with shared Bronze local runtime configuration
- Executed locally against existing `data/silver/` outputs

**Databricks compatibility:**

- Reuses active SparkSession when present
- Same SQL/business logic; path/catalog configuration differs by environment
- Databricks execution not validated in this session

**Tests:**

- Added `tests/test_gold.py` with controlled Bronze→Silver→Gold fixture tests

**Reconciliation:**

- Pipeline validates product, customer, and segmentation revenue totals against
  eligible Silver order revenue before write completion

**YOUR EVALUATION:**

✓ **What was good:**

- Gold consumes Silver only (not CSV/Bronze).
- Three mandatory aggregation tables implemented with required output columns.
- SQL holds aggregation logic; Python handles orchestration/configuration.
- Silver PASS filtering and Completed-order policy documented.
- Reconciliation guard added to stop pipeline on revenue mismatch.
- Local tests and full local pipeline run completed successfully.

✗ **What needed fixing:**

- Initial schema validation failed because Spark `SUM()` produced
  `DecimalType(20,2)` instead of expected `DecimalType(10,2)`.
- Initial reconciliation failed because valid PASS orders linked to invalid
  customers were included in product aggregates but excluded from customer
  aggregates.
- Initial test fixture expectations required correction (duplicate-order setup
  and invalid-row counts).

△ **Missing:**

- Databricks workspace execution validation.
- Separate human-reviewed design prompt before implementation.
- `ai-prompts/gold-layer.md` (deferred until this documentation prompt).

**WHAT WAS ACCEPTED:**

- Three-table Gold scope (Sales by Product, Revenue by Customer, Customer
  Segmentation).
- Silver `quality_check_result = 'PASS'` eligibility contract.
- Completed-only order policy for realized revenue (configurable).
- Configurable high-value threshold defaulting to `1000.00`.
- SQL files + `create_gold_tables.py` orchestrator pattern aligned with Silver.
- LEFT JOIN customer/product dimensions to retain zero-order entities.
- Pipeline reconciliation checks before persisting Gold outputs.
- Overwrite/idempotent output strategy consistent with Silver.

**WHAT WAS CHANGED:**

- Added parent-dimension filtering for eligible orders (must exist in valid PASS
  customers and valid PASS products) after reconciliation failure was detected.
- Added explicit `CAST(... AS DECIMAL(10,2))` in SQL aggregation outputs.
- Corrected Gold test fixture duplicate-order setup and expected counts.

**WHAT WAS REJECTED:**

- `03_daily_weekly_trends.sql` was not implemented because the Gold acceptance
  criteria in the implementation prompt required the three mandatory aggregation
  tables only and explicitly said not to add Daily/Weekly Trends unless an
  existing project rule or prior human decision required it.

No other material AI-generated implementation was rejected.

**HUMAN DECISION:**

Decision not yet recorded.

---

## Sales by Product

Required output:

- `product_id`
- `product_name`
- `category`
- `total_orders`
- `total_revenue`
- `avg_order_value`

**Actual implementation (`src/gold/01_sales_by_product.sql`):**

- Source Silver datasets: valid product and order temp views registered by
  `register_valid_silver_views()`
- Join: `valid_silver_products` LEFT JOIN `valid_silver_orders` on `product_id`
- Aggregation:
  - `total_orders = COUNT(order_id)`
  - `total_revenue = SUM(total_amount)` cast to `DECIMAL(10,2)`
  - `avg_order_value = AVG(total_amount)` (NULL when no valid orders)
- Order eligibility: Silver PASS + Completed status + valid PASS customer/product
  parent keys
- NULL handling: revenue sum coalesced to zero; avg NULL when order count is zero
- Duplicate protection: valid products deduplicated on `product_id`; valid orders
  are uniqueness-clean via Silver PASS filter
- Validation: output schema check and `product_id` uniqueness enforced in
  orchestrator

---

## Revenue by Customer

Required output:

- `customer_id`
- `customer_name`
- `customer_segment`
- `total_orders`
- `total_revenue`
- `avg_order_value`
- `lifetime_value_actual`

**Actual implementation (`src/gold/02_revenue_by_customer.sql`):**

- Join: `valid_silver_customers` LEFT JOIN `valid_silver_orders` on `customer_id`
- `total_orders`: count of eligible valid orders per customer
- `total_revenue`: sum of eligible order `total_amount`
- `avg_order_value`: average of eligible order amounts; NULL when customer has
  zero eligible orders
- `lifetime_value_actual`: sum of eligible order revenue (actual realized revenue,
  not source `lifetime_value`)
- Customers with no orders: retained with zero revenue and NULL average order value
- Duplicate protection: valid customers are unique via Silver PASS filter; valid
  orders filtered to valid parent dimensions

---

## Customer Segmentation

Required output:

- `segment_type`
- `customer_count`
- `avg_revenue`
- `total_revenue`

**Segment types implemented:**

- High-Value
- Repeat
- One-Time
- Inactive

**Rules implemented (`src/gold/04_customer_segmentation.sql`):**

Precedence:

1. `total_orders = 0` → Inactive
2. `total_revenue >= high_value_threshold` → High-Value
3. `total_orders > 1` → Repeat
4. else → One-Time

**High-value threshold:**

- Default: `1000.00` in `config/gold_config.yaml`
- Override via `HIGH_VALUE_REVENUE_THRESHOLD` or config value
- No assignment-defined threshold was found in existing project artifacts

**Inactive handling:**

- Inactive segment uses `total_revenue = 0` and `avg_revenue = 0`

**Metrics:**

- `customer_count`: count of customers in segment
- `avg_revenue`: average customer revenue in segment (zero for Inactive)
- `total_revenue`: sum of customer revenue in segment

Segmentation is derived from actual order behavior, not source `customer_segment`.

---

## Requirement Ambiguity — Daily/Weekly Trends

The assignment business requirements define three mandatory Gold aggregation
tables:

1. Sales by Product
2. Revenue by Customer
3. Customer Segmentation

The repository structure also lists:

- `03_daily_weekly_trends.sql`

The Gold acceptance criteria in the implementation prompt explicitly requires
all three Gold aggregation tables and instructs not to automatically add
Daily/Weekly Trends unless an existing project rule or prior human decision
requires it.

**Actual decision:**

The implementation follows the three mandatory Gold aggregation requirements.
Daily/Weekly Trends was not implemented because the Gold acceptance criteria
specifies three aggregation tables and no existing project rule or prior human
decision required a fourth Gold table.

---

## Silver → Gold Quality Contract

**Eligible Silver records for Gold:**

- `quality_check_result = 'PASS'`

**Additional order eligibility:**

- `order_status` in configured eligible statuses (default: `Completed`)
- `customer_id` must exist in valid PASS customers
- `product_id` must exist in valid PASS products

**Invalid Silver records:**

- Retained in Silver for inspection
- Excluded from Gold business aggregations

**Duplicate inflation prevention:**

- Duplicate customer/order rows fail Silver and are excluded via PASS filter
- Products are deduplicated on `product_id` before joins because Silver does not
  enforce product uniqueness

**Orphan handling:**

- Orphan/non-valid-parent orders are excluded from eligible Gold orders even if
  they otherwise pass Silver checks

**NULL business keys:**

- NULL FK/completeness failures fail Silver and are excluded from Gold

---

## Prompt 3: Gold Testing and Validation

**PROMPT SENT:**

Not performed as a separate prompt in recorded project history.  
Testing and validation execution occurred during Prompt 2 implementation.

**AI RESPONSE SUMMARY:**

Created and executed `tests/test_gold.py` covering:

- Sales by Product aggregation correctness
- Revenue by Customer aggregation correctness
- Customer Segmentation categories and totals
- invalid Silver order exclusion
- inactive customer handling
- reconciliation behavior (via orchestrator)
- schema/output-shape validation (via orchestrator)
- idempotency (rerun overwrite)
- missing Silver input failure

End-to-end local Gold pipeline executed against existing `data/silver/` outputs.

**YOUR EVALUATION:**

✓ What passed:

- `PYTHONPATH=src python3 -m pytest tests/test_gold.py -q` → `4 passed in 37.82s`
  (with `JAVA_HOME` set to OpenJDK 17)
- `PYTHONPATH=src python3 src/gold/create_gold_tables.py` completed successfully
  on existing Silver data

✗ What failed:

- Initial test iterations failed before fixes (schema decimal precision,
  reconciliation mismatch, fixture expectation mismatches)

**FIXES APPLIED:**

- Cast aggregated monetary fields to `DECIMAL(10,2)` in Gold SQL outputs.
- Restricted eligible orders to valid PASS parent customer/product dimensions.
- Corrected test fixture duplicate-order setup and invalid-row count expectations.

---

## Reconciliation

Actual reconciliation executed by `run_gold_pipeline()` locally:

Eligible Silver order revenue  
= Gold Sales by Product total revenue  
= Gold Revenue by Customer total revenue  
= Customer Segmentation total revenue

**Actual local full-dataset results:**

- Eligible order revenue: **85,064,788.93**
- `SUM(sales_by_product.total_revenue)`: **85,064,788.93**
- `SUM(revenue_by_customer.total_revenue)`: **85,064,788.93**
- `SUM(customer_segmentation.total_revenue)`: **85,064,788.93**

**Actual segmentation totals (local run on generated dataset):**

| segment_type | customer_count | avg_revenue | total_revenue |
|--------------|----------------|-------------|---------------|
| High-Value | 7,365 | 11,451.11 | 84,337,445.95 |
| Inactive | 1,139 | 0.00 | 0.00 |
| One-Time | 516 | 335.62 | 173,179.38 |
| Repeat | 920 | 602.35 | 554,163.60 |

**Actual pipeline summary (local run):**

- valid_customers_rows: 9,940
- valid_orders_rows: 73,867
- valid_products_rows: 500
- sales_by_product_rows: 500
- revenue_by_customer_rows: 9,940
- customer_segmentation_rows: 4

---

## Local and Databricks Compatibility

**Local execution:**

- SparkSession created locally (or reused if active)
- Reads Silver Parquet from configured `silver_root`
- Executes Spark SQL from `src/gold/*.sql`
- Writes Gold Parquet to configured `gold_root`

Command:

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
PYTHONPATH=src python3 src/gold/create_gold_tables.py
```

**Databricks execution:**

- Same SQL and orchestrator logic
- Active Databricks SparkSession reused when available
- Paths/catalog/schema configured via YAML/env overrides

**Design principle:**

SAME BUSINESS LOGIC  
DIFFERENT ENVIRONMENT CONFIGURATION

**Databricks execution validation:** Not performed.

---

## Debugging and Corrections

### Issue 1

**Problem:**  
Gold pipeline failed schema validation for `sales_by_product.total_revenue`.

**Root Cause:**  
Spark `SUM()` on decimal columns produced `DecimalType(20,2)` while Gold schema
validation expected `DecimalType(10,2)`.

**AI Assistance:**  
Identified mismatch from test/pipeline error output and updated SQL casts.

**Fix:**  
Added explicit `CAST(... AS DECIMAL(10,2))` for aggregated revenue fields in
Gold SQL files.

**Validation:**  
Gold tests passed after cast updates.

### Issue 2

**Problem:**  
Reconciliation failed (`revenue_by_customer` total did not match eligible Silver
order revenue).

**Root Cause:**  
Eligible orders included PASS orders linked to invalid customers; product-side
aggregates counted those orders while customer-side aggregates excluded them.

**AI Assistance:**  
Diagnosed mismatch during test/pipeline reconciliation and tightened eligibility.

**Fix:**  
Updated `register_valid_silver_views()` so eligible orders must semi-join valid
PASS customer and product dimensions.

**Validation:**  
Reconciliation passed in Gold tests and full local pipeline run.

### Issue 3

**Problem:**  
Initial Gold tests had incorrect fixture expectations for invalid-row counts and
eligible-order totals.

**Root Cause:**  
Test data used a non-duplicating order row where duplicate behavior was intended;
expected FAIL counts did not match actual Silver outputs.

**AI Assistance:**  
Adjusted fixture order IDs and expected assertions to match Silver/Gold behavior.

**Fix:**  
Updated `tests/test_gold.py` fixture and assertions.

**Validation:**  
`tests/test_gold.py` → `4 passed`.

---

## Final Evaluation

### What worked well

- Clear Silver→Gold eligibility contract using Silver PASS records.
- SQL-centric aggregation logic with Python orchestration only.
- Reconciliation guard prevented silent revenue drift across Gold tables.
- Configurable high-value threshold and order-status policy.
- Local end-to-end execution and tests on actual Silver outputs.
- Preservation of inactive customers and zero-order products in outputs.

### What needed fixing

- Decimal aggregation type precision required explicit casts.
- Parent-dimension order filtering required for cross-table reconciliation.
- Test fixtures needed refinement after eligibility rules were finalized.

### What was accepted

- Three mandatory Gold tables only (no Daily/Weekly Trends in this stage).
- Completed-order revenue policy.
- Config-driven high-value threshold default (`1000.00`).
- LEFT JOIN dimension strategy for inactive customers and zero-order products.

### What was rejected

- Daily/Weekly Trends Gold table in this implementation stage (scope limited to
  three mandatory aggregations).

### What was changed

- Parent-dimension filtering for eligible orders.
- SQL decimal casts and test fixture/assertion corrections.

### Lessons Learned

- Gold eligibility must be defined consistently across all aggregations or
  reconciliation will fail.
- Spark decimal aggregations may widen precision; cast at output boundaries.
- Silver PASS alone is insufficient when parent dimensions can still be invalid.
- Segmentation thresholds should remain configuration-driven, not hardcoded in SQL.
- AI-assisted implementation benefited from test-driven discovery of join/revenue
  inconsistencies before production use.

---

## Human Ownership

Workflow evidenced in this stage:

AI suggestion  
↓  
Human evaluation  
↓  
Acceptance / modification / rejection  
↓  
Implementation  
↓  
Testing  
↓  
Final decision

Recorded human decisions in this file:

- Decision not yet recorded (Prompt 1 design stage).
- Decision not yet recorded (Prompt 2 acceptance stage).
- Daily/Weekly Trends exclusion followed implementation-prompt scope guidance;
  explicit human sign-off not yet recorded.

---

## Accuracy Notes

Documented from actual implementation artifacts, tests, and executed local runs.

Not performed:

- Databricks workspace execution validation.

Not verified:

- Explicit human approval decisions beyond implementation-prompt scope guidance.
