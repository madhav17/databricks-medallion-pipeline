# AI Prompts — Silver Layer

## Silver Layer Context

The Silver layer consumes the existing Bronze output.

Pipeline:

Data Generation  
↓  
Bronze  
↓  
Silver  
↓  
Gold  
↓  
Dashboard

Data Generation and Bronze were completed before Silver implementation began.

Silver was implemented to use the same business logic for:

- local PySpark execution
- Databricks execution

with configuration-driven paths per environment.

---

## Prompt 1: Silver Layer Requirements and Design

### PROMPT SENT:

Not performed as a separate prompt in recorded project history.

### AI RESPONSE SUMMARY:

Not applicable. Silver requirements and design were provided directly as part of the implementation prompt.

### YOUR EVALUATION:

✓ What was good:
- Silver requirements were explicitly detailed in the implementation prompt itself.

✗ What needed fixing:
- A separate design-only prompt was not recorded.

△ What required clarification:
- None required beyond the implementation prompt.

### HUMAN DECISION:

Decision not yet recorded.

---

## Prompt 2: Silver Layer Implementation

### PROMPT SENT:

You are a Senior Data Engineer implementing the Silver layer
of our Data Engineering competency assessment.

IMPORTANT CONTEXT:

The following stages are ALREADY COMPLETED:

1. Data generation
2. Bronze layer ingestion

Do NOT modify the data-generation implementation.

Do NOT modify the Bronze implementation unless a genuine,
blocking dependency is discovered.

The Silver layer must consume the EXISTING Bronze output.

The objective is to implement a robust, testable Silver layer
that works both:

1. Locally using PySpark
2. On Databricks

The same business logic must work in both environments.
Only environment-specific configuration such as input/output
paths may differ.

============================================================
1. FIRST INSPECT THE EXISTING PROJECT
============================================================

Before writing code, inspect the existing repository.

Inspect:

.cursor/rules/
src/data_generation/
src/bronze/
data/
tests/
README.md
existing configuration files
existing utility modules
existing AI prompt files

Pay particular attention to:

.cursor/rules/02-requirements.mdc
.cursor/rules/03-architecture.mdc
.cursor/rules/04-coding-guidelines.mdc
.cursor/rules/07-silver-layer.mdc
.cursor/rules/08-testing.mdc

If these files exist.

Also inspect the actual Bronze implementation and determine:

- Bronze input locations
- Bronze output locations
- actual Bronze schemas
- actual table/file names
- storage format
- configuration mechanism
- how SparkSession is created
- how local execution currently works
- how Databricks execution currently works

DO NOT assume paths, table names, schemas, or configuration.

Use the existing project implementation as the source of truth.

============================================================
2. CURRENT ARCHITECTURE
============================================================

The current pipeline is:

CSV
  |
  v
Data Generation
  |
  v
Bronze
  |
  v
Parquet
  |
  v
SILVER   <-- IMPLEMENT NOW
  |
  v
Gold
  |
  v
Dashboard

Silver MUST consume Bronze output.

Do NOT read the original CSV files directly.

Do NOT bypass Bronze.

============================================================
3. DATASETS
============================================================

There are three source datasets:

customers
orders
products

Expected logical schemas are:

CUSTOMERS:

customer_id
customer_name
email
country
signup_date
customer_segment
lifetime_value

ORDERS:

order_id
customer_id
order_date
product_id
quantity
unit_price
total_amount
order_status
payment_date

PRODUCTS:

product_id
product_name
category
price
cost
stock_quantity
reorder_level

IMPORTANT:

Use the actual Bronze schema discovered in the repository.

Do not blindly recreate the schema above if the existing Bronze
implementation uses an explicit schema.

============================================================
4. EXACT INTENTIONAL DATA QUALITY ISSUES
============================================================

The generated sample data intentionally contains the following
issues.

DO NOT change these expectations.

CUSTOMERS:

1. 50 rows with NULL email
   -> Completeness

2. 10 rows with duplicate customer_id
   -> Uniqueness

ORDERS:

3. 100 rows with NULL customer_id
   -> Completeness

4. 200 rows with NULL product_id
   -> Completeness

5. 50 rows with customer_id values that do not exist in
   the customers table
   -> Referential Integrity

6. 30 rows with product_id values that do not exist in
   the products table
   -> Referential Integrity

7. 20 duplicate order_id rows
   -> Uniqueness

The assessment describes these as approximately:

~700 problematic rows out of ~100,000 rows
(~0.7%)

IMPORTANT:

The ~700 figure represents the documented quality issues /
problematic records and should NOT be interpreted as a
requirement that the final number of DISTINCT failed rows
must equal exactly 700.

A single row may fail multiple checks.

Do not hardcode expected percentages.

============================================================
5. FOUR SILVER VALIDATION COMPONENTS
============================================================

Implement these four validation components:

1. Completeness
2. Uniqueness
3. Type/Schema Validation
4. Referential Integrity

IMPORTANT:

The intentional data-quality issues supplied by the assessment
are specifically for:

- Completeness
- Uniqueness
- Referential Integrity

Type/schema validation is also required as a Silver validation
component because the repository structure includes it.

Do NOT artificially modify the data to create type-validation
failures.

If the actual Bronze data has the correct schema, the type
validation should pass.

Do NOT invent additional business-rule failures.

============================================================
6. CHECK 1 — COMPLETENESS
============================================================

Implement completeness validation.

Critical fields are:

CUSTOMERS:

email

ORDERS:

customer_id
product_id

The following must be detected:

- 50 NULL customer email rows
- 100 NULL order customer_id rows
- 200 NULL order product_id rows

NULL values must NOT be deleted.

NULL values must NOT be replaced with fake/default values.

The original row must remain in Silver.

Flag the row as failed.

For example:

quality_check_result = FAIL

and capture:

COMPLETENESS: email is NULL

or:

COMPLETENESS: customer_id is NULL

or:

COMPLETENESS: product_id is NULL

If a row has more than one failure, preserve all failures.

Do NOT overwrite one failure with another.

============================================================
7. CHECK 2 — UNIQUENESS
============================================================

Implement uniqueness validation.

CUSTOMERS:

customer_id must be unique.

ORDERS:

order_id must be unique.

The following intentional issues must be detected:

- 10 rows with duplicate customer_id
- 20 duplicate order_id rows

IMPORTANT:

For a duplicate key group, ALL rows belonging to the duplicate
group should be identifiable as uniqueness failures.

Example:

customer_id = 123 appears twice.

Both records should be flagged:

UNIQUENESS: duplicate customer_id

Do NOT arbitrarily select one row as valid.

Do NOT delete duplicates.

Do NOT use dropDuplicates() as the Silver validation mechanism.

The purpose of Silver is to FLAG the bad records.

============================================================
8. CHECK 3 — TYPE / SCHEMA VALIDATION
============================================================

Implement:

src/silver/03_quality_type_validation.py

This is a supporting Silver validation component.

Validate the actual Bronze schema against the expected schema.

Validate appropriate types for:

CUSTOMERS:

customer_id
customer_name
email
country
signup_date
customer_segment
lifetime_value

ORDERS:

order_id
customer_id
order_date
product_id
quantity
unit_price
total_amount
order_status
payment_date

PRODUCTS:

product_id
product_name
category
price
cost
stock_quantity
reorder_level

The implementation must:

- verify required columns exist
- verify expected data types
- identify schema/type mismatches
- fail clearly if required columns are missing
- avoid silently coercing incorrect data into valid values

IMPORTANT:

The Bronze layer already performs ingestion/schema handling.

Therefore, do not manufacture type failures.

If Bronze has the expected schema, the type validation should
pass.

Type validation must work with Spark DataFrames and should not
require collecting the full dataset to the driver.

============================================================
9. CHECK 4 — REFERENTIAL INTEGRITY
============================================================

Implement referential integrity validation.

ORDERS.customer_id must exist in:

customers.customer_id

ORDERS.product_id must exist in:

products.product_id

The following intentional issues must be detected:

- 50 orders with customer_id not present in customers
- 30 orders with product_id not present in products

IMPORTANT DISTINCTION:

NULL customer_id:

-> Completeness failure

Non-null customer_id that does not exist in customers:

-> Referential Integrity failure

NULL product_id:

-> Completeness failure

Non-null product_id that does not exist in products:

-> Referential Integrity failure

Do NOT classify NULL foreign keys as orphan records.

This distinction is important.

============================================================
10. DO NOT ADD EXTRA INTENTIONAL ISSUES
============================================================

Do NOT introduce additional data-quality requirements such as:

- arbitrary email regex validation
- arbitrary date ranges
- arbitrary price rules
- arbitrary order status rules
- arbitrary quantity rules
- cost > price rules
- payment date rules
- customer signup-date rules

unless such a rule already exists explicitly in the existing
project rules or requirements.

The current assessment data intentionally provides issues for:

Completeness
Uniqueness
Referential Integrity

Do not create additional failures that could make the expected
quality report inconsistent with the assessment.

============================================================
11. BAD ROWS MUST NOT BE DELETED
============================================================

This is mandatory.

Silver MUST preserve all Bronze records.

Do NOT:

drop NULL records
drop duplicate records
drop orphan records
drop invalid records
deduplicate the dataset
replace invalid foreign keys
replace NULL values

Instead:

Bronze
  |
  v
Validation
  |
  +--> PASS
  |
  +--> FAIL
          |
          +--> reason(s)

Then write the complete dataset to Silver.

The Silver layer should therefore preserve the ability to
inspect all source records and understand their quality status.

============================================================
12. QUALITY RESULT DESIGN
============================================================

Add quality metadata to the Silver datasets.

At minimum:

quality_check_result

Recommended:

quality_check_result
quality_check_reason

Use a consistent representation across customers,
orders, and products.

For example:

PASS

or:

FAIL

with reasons such as:

COMPLETENESS: email is NULL

UNIQUENESS: duplicate customer_id

REFERENTIAL_INTEGRITY: customer_id not found in customers

For a row failing multiple checks:

FAIL

with all applicable reasons preserved.

Example:

COMPLETENESS: customer_id is NULL;
UNIQUENESS: duplicate order_id

Do NOT use an if/else chain where the first failure hides
subsequent failures.

ALL validation checks must run.

============================================================
13. MULTIPLE FAILURES
============================================================

A row may fail more than one validation.

Example:

An order could potentially have:

customer_id = NULL

and

duplicate order_id

In this case, the row must be marked as:

FAIL

and both reasons must be retained.

Conceptually:

run completeness
run uniqueness
run type validation
run referential integrity

then:

combine all failures

Do NOT implement:

if completeness_failed:
    return "FAIL"
elif uniqueness_failed:
    return "FAIL"
elif referential_integrity_failed:
    return "FAIL"

because this hides useful diagnostic information.

============================================================
14. QUALITY METRICS
============================================================

Generate a quality metrics report.

At minimum include:

dataset_name
check_name
total_rows
passed_rows
failed_rows
pass_percentage
fail_percentage

Examples:

customers | completeness
customers | uniqueness
customers | type_validation

orders | completeness
orders | uniqueness
orders | type_validation
orders | referential_integrity

products | type_validation

The exact number of rows/check combinations can be determined
from the implemented validation scope.

Calculate:

passed_rows
failed_rows
pass_percentage
fail_percentage

from the actual DataFrames.

Formula:

pass_percentage =
(passed_rows / total_rows) * 100

fail_percentage =
(failed_rows / total_rows) * 100

Do not hardcode:

50
10
100
200
50
30
20

as metric results.

Those numbers are expectations for validation testing,
not values to hardcode into the report.

============================================================
15. IMPORTANT METRIC SEMANTICS
============================================================

For each individual quality check:

A row passes the check if it does not violate that specific
check.

Example:

An order with NULL customer_id:

Completeness:
FAIL

Uniqueness:
PASS, assuming order_id is unique

Referential Integrity:
Do not classify NULL as an orphan FK.
It should be handled by completeness.

This means the same row can have different results across
different checks.

The metrics must be calculated independently per check.

============================================================
16. SILVER DATASET STRUCTURE
============================================================

Preserve the original business columns.

Add quality metadata.

Do not unnecessarily rename columns.

Do not unnecessarily transform business values.

Recommended structure:

data/
  silver/
    customers/
    orders/
    products/
    quality_metrics/

However:

Use the project's existing configuration/path convention if
one already exists.

Do not introduce hardcoded paths.

============================================================
17. LOCAL EXECUTION
============================================================

The Silver implementation must run locally.

Use a standard SparkSession when running locally.

Example conceptually:

SparkSession.builder \
    .appName("SilverLayer") \
    .master("local[*]") \
    .getOrCreate()

But reuse the project's existing SparkSession/configuration
mechanism if one already exists.

The local implementation should read:

existing Bronze output

and write:

local Silver output

Do NOT hardcode machine-specific paths.

============================================================
18. DATABRICKS EXECUTION
============================================================

The same implementation must run on Databricks.

Do NOT create separate business logic for Databricks.

Use the existing SparkSession provided by Databricks when
running in a notebook/job environment.

Configuration should determine:

bronze_root
silver_root

or equivalent.

Do NOT hardcode:

/Users/<username>
/dbfs/
specific workspace paths
specific catalog/schema names

unless the existing project already uses those values through
configuration.

============================================================
19. ENVIRONMENT CONFIGURATION
============================================================

If the project already has configuration management:

REUSE IT.

Do not create a second competing configuration framework.

If no configuration mechanism exists, create a small,
simple configuration mechanism supporting:

local

and

databricks

environments.

Example concept:

ENVIRONMENT=local

or:

ENVIRONMENT=databricks

with corresponding paths.

Do not duplicate transformation logic.

Only configuration should differ.

============================================================
20. REQUIRED FILE STRUCTURE
============================================================

Follow the assessment repository structure:

src/
  silver/
    01_quality_completeness.py
    02_quality_uniqueness.py
    03_quality_type_validation.py
    04_quality_referential_integrity.py
    create_silver_tables.py

If the existing project already contains:

05_quality_business_logic.py

DO NOT remove it.

But do not introduce additional business-rule failures unless
explicitly required by existing project rules.

You may add a small shared utility module if necessary.

For example:

silver_utils.py

Keep the implementation simple and maintainable.

============================================================
21. CREATE_SILVER_TABLES.PY
============================================================

Implement:

src/silver/create_silver_tables.py

This is the Silver orchestration entry point.

Conceptual flow:

1. Load Bronze customers
2. Load Bronze orders
3. Load Bronze products

3. Validate schema/types

4. Run completeness validation

5. Run uniqueness validation

6. Run referential integrity validation

7. Combine quality results

8. Write Silver customers

9. Write Silver orders

10. Write Silver products

11. Generate quality metrics

12. Write quality metrics

13. Validate Silver outputs

Do not unnecessarily read/write the entire dataset multiple
times.

Use Spark-native transformations.

============================================================
22. PERFORMANCE REQUIREMENTS
============================================================

Approximate data volume:

Customers: ~10,000
Orders: ~100,000
Products: ~500

Use Spark efficiently.

Avoid:

collect()
toPandas()
Python loops over every record
driver-side processing
unnecessary repeated scans
unnecessary repeated writes

Use Spark-native operations:

groupBy
count
join
when
col
isNull
isNotNull
broadcast where appropriate
window functions where appropriate

Products and customers are small compared with orders, so a
broadcast join may be considered where appropriate.

Do not over-optimize at the expense of readability.

============================================================
23. REFERENTIAL INTEGRITY IMPLEMENTATION
============================================================

Use left joins or equivalent Spark-native logic.

For example:

orders
  LEFT JOIN customers
  ON orders.customer_id = customers.customer_id

and:

orders
  LEFT JOIN products
  ON orders.product_id = products.product_id

Be careful with duplicate customer_id values.

The source intentionally contains duplicate customer IDs.

Therefore, the referential-integrity validation must NOT
accidentally multiply order records because of a many-to-one
join.

The implementation must account for the fact that the
customers dataset itself contains duplicate customer_id
records.

Use a distinct/reference-key DataFrame for FK existence
checking if appropriate.

Example conceptual approach:

valid_customer_ids =
customers.select("customer_id").where(...).distinct()

Then check whether orders.customer_id exists in that key set.

Do NOT use a raw non-deduplicated parent DataFrame in a way
that multiplies order rows.

============================================================
24. UNIQUENESS IMPLEMENTATION
============================================================

For customers:

duplicate customer_id groups must be identified.

For orders:

duplicate order_id groups must be identified.

Use Spark groupBy/count or an equivalent window-based approach.

Do NOT remove duplicates.

The original row count must remain intact in Silver.

============================================================
25. EXPECTED VALIDATION TESTS
============================================================

Create or update tests.

The tests must verify:

COMPLETENESS:

[ ] NULL customer email is detected.

[ ] NULL order customer_id is detected.

[ ] NULL order product_id is detected.

UNIQUENESS:

[ ] Duplicate customer_id is detected.

[ ] Duplicate order_id is detected.

[ ] All records belonging to duplicate groups are flagged.

TYPE VALIDATION:

[ ] Expected Bronze schema passes.

[ ] Missing required column is detected.

[ ] Incorrect schema/type is detected where testable.

REFERENTIAL INTEGRITY:

[ ] Invalid customer_id is detected.

[ ] Invalid product_id is detected.

[ ] NULL customer_id is NOT classified as orphan.

[ ] NULL product_id is NOT classified as orphan.

QUALITY RESULT:

[ ] Valid records receive PASS.

[ ] Invalid records receive FAIL.

[ ] Multiple failures are preserved.

METRICS:

[ ] Total rows are correct.

[ ] Passed rows are correct.

[ ] Failed rows are correct.

[ ] Percentages are calculated correctly.

END-TO-END:

[ ] Bronze -> Silver works locally.

[ ] Silver output can be read back.

[ ] Row counts are preserved.

============================================================
26. TEST USING THE EXISTING GENERATED DATA
============================================================

After implementation:

DO NOT regenerate the source data.

DO NOT modify customers.csv.

DO NOT modify orders.csv.

DO NOT modify products.csv.

DO NOT modify Bronze simply to make tests pass.

Run the Silver implementation against the actual existing
Bronze data.

Verify the expected intentional issues are detected.

Expected issue categories:

CUSTOMERS
- 50 NULL email rows
- 10 duplicate customer_id rows

ORDERS
- 100 NULL customer_id rows
- 200 NULL product_id rows
- 50 invalid customer_id values
- 30 invalid product_id values
- 20 duplicate order_id rows

The actual metrics must come from execution.

Do not fabricate results.

============================================================
27. NO SILENT DATA LOSS
============================================================

Compare:

Bronze row count

against:

Silver row count

for:

customers
orders
products

The Silver dataset containing quality flags should preserve
the Bronze row count.

If row counts differ:

STOP and investigate.

Do not simply filter the records to make the output clean.

============================================================
28. ERROR HANDLING
============================================================

Implement clear error handling for:

- missing Bronze input
- missing required columns
- invalid schema
- missing parent dataset
- invalid configuration
- invalid paths
- Spark failures
- output write failures
- metrics failures

Errors should be meaningful and actionable.

Do not silently ignore errors.

============================================================
29. DOCUMENTATION
============================================================

Create/update:

src/silver/SILVER_LAYER_NOTES.md

Document:

1. Silver purpose
2. Bronze inputs
3. Completeness rules
4. Uniqueness rules
5. Type/schema validation
6. Referential integrity rules
7. Quality result design
8. Multiple failure handling
9. Metrics calculation
10. Local execution
11. Databricks execution
12. Configuration
13. Testing
14. Expected intentional anomalies
15. Known assumptions

Explicitly document the intentional issues:

Customers:
- 50 NULL emails
- 10 duplicate customer IDs

Orders:
- 100 NULL customer IDs
- 200 NULL product IDs
- 50 invalid customer IDs
- 30 invalid product IDs
- 20 duplicate order IDs

============================================================
30. AI PROMPT HISTORY
============================================================

Do NOT write the prompt-history documentation yet.

A separate prompt will be provided for generating:

ai-prompts/silver-layer.md

============================================================
31. DO NOT IMPLEMENT GOLD
============================================================

Do NOT implement:

Gold aggregations
Dashboard
BI queries
Customer segmentation
Sales-by-product aggregation
Revenue-by-customer aggregation

Those are later tasks.

============================================================
32. ACCEPTANCE CRITERIA
============================================================

The Silver implementation is complete only when:

[ ] Bronze is the input.

[ ] Customers Silver dataset is produced.

[ ] Orders Silver dataset is produced.

[ ] Products Silver dataset is produced.

[ ] Completeness check works.

[ ] Uniqueness check works.

[ ] Type/schema validation works.

[ ] Referential integrity check works.

[ ] 50 NULL customer emails are detectable.

[ ] 10 duplicate customer IDs are detectable.

[ ] 100 NULL order customer IDs are detectable.

[ ] 200 NULL order product IDs are detectable.

[ ] 50 invalid customer foreign keys are detectable.

[ ] 30 invalid product foreign keys are detectable.

[ ] 20 duplicate order IDs are detectable.

[ ] Bad records are flagged, not deleted.

[ ] quality_check_result exists.

[ ] Quality failure reasons are retained.

[ ] Multiple failures are retained.

[ ] Quality metrics are generated.

[ ] Metrics are calculated dynamically.

[ ] Bronze/Silver row counts are preserved.

[ ] Local execution works.

[ ] Databricks execution is supported.

[ ] No environment-specific business logic is duplicated.

[ ] Tests cover all quality checks.

[ ] Documentation is updated.

============================================================
33. FINAL VALIDATION
============================================================

Before declaring completion:

1. Run unit/data-quality tests.

2. Run the complete Silver pipeline locally.

3. Read Silver output back.

4. Verify row counts.

5. Verify quality columns.

6. Verify intentional issues.

7. Verify quality metrics.

8. Verify no unexpected data loss.

9. Check code for local/Databricks compatibility.

10. Check that no hardcoded machine-specific paths exist.

11. Check that no Bronze or source data was modified.

12. Report actual execution results.

Do NOT fabricate any test result.

Do NOT claim Databricks execution passed unless it was
actually executed in Databricks.

============================================================
34. FINAL RESPONSE FROM CURSOR
============================================================

After implementation, report:

1. Files created
2. Files modified
3. Silver architecture
4. Four validation components
5. Exact intentional issues detected
6. Quality result design
7. Metrics design
8. Local execution instructions
9. Databricks execution instructions
10. Tests executed
11. Actual test results
12. Actual row counts
13. Actual quality metrics
14. Any assumptions
15. Any unresolved issues
16. Whether Silver is ready for Gold

Begin by inspecting the repository and existing project rules.
Do not start coding until you understand the existing Bronze
output and configuration.

### AI RESPONSE SUMMARY:

Implemented Silver as a Bronze-consuming Parquet pipeline with four quality components (completeness, uniqueness, type/schema validation, referential integrity), quality flag columns, dynamic metrics generation, and row-count preservation checks. Added configuration (`config/silver_config.yaml`), Silver modules under `src/silver/`, Silver notes, and Silver tests. Executed local tests and pipeline runs, fixed test/setup issues, and validated outputs against actual Bronze data.

### YOUR EVALUATION:

✓ What was good:
- Silver consumes Bronze Parquet directly and does not bypass Bronze.
- All four required validation components were implemented.
- Bad rows are retained and flagged; multiple failures are preserved.
- Metrics are dynamic and check-specific.
- Row-count preservation Bronze -> Silver was validated.

✗ What needed fixing:
- Initial Silver tests failed due to fixture type mismatches and overwrite/read conflict in one test.
- Type/schema validation initially ran after adding quality helper columns; order was corrected.
- One verification script initially read Silver outputs before the pipeline completed due parallel command timing; rerun succeeded.

△ What required changes:
- Test fixtures updated to use proper Python `date`/`Decimal` objects for Spark schema typing.
- Missing-column test updated to write to a temporary path then atomically replace source test path.

### WHAT WAS ACCEPTED:

- Silver module structure in `src/silver/` with:
  - `01_quality_completeness.py`
  - `02_quality_uniqueness.py`
  - `03_quality_type_validation.py`
  - `04_quality_referential_integrity.py`
  - `create_silver_tables.py`
  - `silver_utils.py`
  - config loader/model and notes
- Quality columns:
  - `quality_check_result`
  - `quality_check_reason`
- Dynamic metrics parquet output with required fields.
- Local Spark execution and shared logic compatibility design for Databricks.

### WHAT WAS CHANGED:

- Reordered type validation to run before quality helper column injection.
- Fixed referential/fixture test path handling and Spark-compatible typed fixture data.

### WHAT WAS REJECTED:

No material AI-generated implementation was rejected.

---

## Intentional Data Quality Issues Used for Validation

### Customers

- 50 rows with NULL email  
  - Completeness

- 10 rows with duplicate customer_id  
  - Uniqueness

### Orders

- 100 rows with NULL customer_id  
  - Completeness

- 200 rows with NULL product_id  
  - Completeness

- 50 rows with customer_id not present in customers  
  - Referential Integrity

- 30 rows with product_id not present in products  
  - Referential Integrity

- 20 duplicate order_id rows  
  - Uniqueness

Approximately 700 problematic rows/issues out of approximately 100,000 rows (~0.7%) as specified by the assessment.

Note: this is not a requirement that distinct failed rows must equal exactly 700, since one row can fail multiple checks.

---

## Prompt 3: Quality Check Implementation

### PROMPT SENT:

Not performed as a separate prompt in recorded project history.  
Quality checks were implemented within Prompt 2.

### AI RESPONSE SUMMARY:

Implemented:

1. Completeness checks for customers email and orders customer_id/product_id.
2. Uniqueness checks for customers customer_id and orders order_id using Spark windows.
3. Type/schema validation against Bronze expected schemas, with missing-column/type mismatch errors.
4. Referential integrity checks for non-null orders foreign keys using distinct parent key sets and broadcast joins.

### YOUR EVALUATION:

✓ What was good:
- Check logic matches assignment intent and preserves row cardinality.
- Referential checks avoid row multiplication by using distinct parent keys.

✗ What needed fixing:
- Type validation execution order needed correction (now runs before helper columns are appended).

### VALIDATION:

Actual validation performed:

- `PYTHONPATH=src python3 -m pytest tests/test_silver.py -q`  
  Result: `2 passed`

- `PYTHONPATH=src python3 src/silver/create_silver_tables.py`  
  Result: success

- Post-run Spark validation script (actual results):
  - Bronze/Silver row counts preserved for customers/orders/products
  - Detected issue counts:
    - null_customer_email: 50
    - duplicate_customer_id_groups: 10 (duplicate rows flagged: 20)
    - null_order_customer_id: 100
    - null_order_product_id: 200
    - invalid_customer_fk: 50
    - invalid_product_fk: 30
    - duplicate_order_id_groups: 20 (duplicate rows flagged: 40)

---

### Completeness

Expected intentional issues:

- 50 NULL customer emails
- 100 NULL order customer IDs
- 200 NULL order product IDs

Implementation flags these via null checks and appends completeness reasons.  
NULL foreign keys are classified as completeness failures, not referential-integrity orphan failures.

### Uniqueness

Expected intentional issues:

- 10 duplicate customer IDs
- 20 duplicate order IDs

Implementation uses Spark partition-based duplicate detection and flags records instead of deleting.  
All records in each duplicate key group are identified as duplicate records.

### Type / Schema Validation

Implementation validates:

- required columns
- expected column ordering
- expected Spark data types

against Bronze expected schemas.  
Bronze schema enforcement remained valid in tested runs; type checks passed on actual Bronze outputs.

### Referential Integrity

Expected intentional issues:

- 50 invalid customer foreign keys
- 30 invalid product foreign keys

Implementation distinguishes:

- NULL FK -> completeness
- non-null FK missing in parent -> referential integrity

Duplicate parent customer IDs are handled through distinct parent key DataFrames so order rows are not multiplied during checks.

### Bad Record Handling

Bad rows are retained and flagged (not deleted) using:

- `quality_check_result`
- `quality_check_reason`

Multiple failures are retained and combined (e.g., completeness + uniqueness on same row).

### Quality Metrics

Implemented metrics fields:

- dataset_name
- check_name
- total_rows
- passed_rows
- failed_rows
- pass_percentage
- fail_percentage

Percentages are calculated dynamically from runtime DataFrame counts; expected anomaly counts are not hardcoded into metric outputs.

---

## Local and Databricks Compatibility

- Local: Spark session is created in-process and reads/writes local Bronze/Silver roots from config.
- Databricks: active SparkSession reuse is supported; same transformation/validation logic is used.
- Paths are configuration-driven (`silver_config.yaml` and env overrides).
- Same business logic; only path/environment configuration differs.

Databricks execution validation: Not performed.

---

## Prompt 4: Silver Layer Testing and Validation

### PROMPT SENT:

Not performed as a separate prompt in recorded project history.  
Testing/validation execution occurred during Prompt 2 implementation.

### AI RESPONSE SUMMARY:

Created and executed Silver tests covering:

- completeness flagging
- uniqueness flagging
- referential integrity flagging
- quality result columns
- metrics output shape and values
- row-count preservation
- missing required column detection

Executed end-to-end Silver pipeline locally against existing Bronze output.

### YOUR EVALUATION:

✓ What passed:
- `tests/test_silver.py` passed after fixes.
- End-to-end Silver pipeline run succeeded locally.
- Bronze/Silver row counts and expected issue categories were verified from actual output.

✗ What failed:
- Initial test iterations failed before fixes (fixture types, overwrite/read conflict, and validation-order issue).

### FIXES APPLIED:

- Converted fixture values to Spark-compatible types (`date`, `Decimal`).
- Changed missing-column test write strategy to temp path + replace.
- Moved type/schema validation step before quality helper-column injection.

---

## Debugging and Corrections

### Issue 1

**Problem:**  
Silver tests failed when creating DataFrames with DateType/DecimalType schemas.

**Root Cause:**  
Fixture rows used strings for date/decimal fields instead of Python date/Decimal objects.

**AI Assistance:**  
Identified schema mismatch from test traces and adjusted fixtures.

**Fix:**  
Updated fixtures to use `datetime.date` and `decimal.Decimal`.

**Validation:**  
`tests/test_silver.py` passed.

### Issue 2

**Problem:**  
Missing-column test failed with file-not-found/read inconsistency during overwrite.

**Root Cause:**  
Overwriting the same source path being read in Spark caused file reference invalidation.

**AI Assistance:**  
Adjusted test strategy to write to a temporary path and replace directory.

**Fix:**  
Write broken dataset to `orders_broken` and move into place.

**Validation:**  
`tests/test_silver.py` passed.

### Issue 3

**Problem:**  
Type/schema validation failed because helper quality column existed before schema validation.

**Root Cause:**  
Validation order in orchestrator placed type-check after helper-column initialization.

**AI Assistance:**  
Detected mismatch and changed operation order.

**Fix:**  
Run `validate_type_schemas(...)` immediately after Bronze read/required-column checks.

**Validation:**  
Pipeline run succeeded and type-validation metrics show zero failures.

---

## Final Evaluation

### What worked well

- Spark-native quality checks with no row deletion.
- Multi-failure retention through aggregated reason arrays.
- Dynamic per-check metrics generation.
- Referential integrity implementation avoided row multiplication with distinct parent keys.
- Local execution succeeded on actual Bronze outputs.
- Same business logic is reusable for Databricks with path/config changes.

### What was changed from the AI-generated implementation

- Adjusted schema-validation order.
- Improved test fixture typing and overwrite strategy in tests.
- Added `05_quality_business_logic.py` in gap remediation (fourth assignment check).

### What was rejected

No material AI-generated implementation was rejected.

### Gap remediation (post-implementation)

**Business Logic check:** ACCEPTED — implemented in `05_quality_business_logic.py`,
integrated into orchestration and `quality_metrics` (`check_name = business_logic`).
Rules aligned with `dataset_validator.py`. CORE dataset shows 100% business-logic
pass rate because mandatory anomalies target completeness/uniqueness/RI only.

### Lessons Learned

- Quality frameworks should validate schema before adding helper metadata columns.
- Referential checks should use distinct parent key sets when parent tables can contain duplicates.
- Duplicate-group semantics should distinguish key-group counts from flagged-row counts.
- Dynamic metrics are essential for transparent quality reporting.
- Environment portability benefits from configuration-driven runtime setup and shared logic across local/Databricks.

