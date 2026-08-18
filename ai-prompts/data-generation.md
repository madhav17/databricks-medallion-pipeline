# AI Prompts - Data Generation

## Prompt 1: Data Generation Design (Stages 1–3)

**PROMPT SENT:**

You are acting as a Senior/Principal Data Engineer designing a
reproducible e-commerce sample-data generator for a Databricks
Medallion Architecture project.

IMPORTANT:
Do NOT write implementation code yet.

Your task is to perform the following three stages sequentially:

STAGE 1 — DATA GENERATION REQUIREMENTS & DESIGN
STAGE 2 — CRITICAL REVIEW OF THE DESIGN
STAGE 3 — CONFIGURATION DESIGN

Do not skip any stage.

============================================================
PROJECT CONTEXT
============================================================

We are building a Databricks-based Medallion Architecture pipeline:

CSV
  ↓
Bronze
  ↓
Silver
  ↓
Gold
  ↓
Databricks SQL Dashboard

The generated CSV files will be used as the input/landing data
for the Bronze layer.

Bronze will convert the CSV files to Parquet while preserving
the source data and intentional anomalies.

Silver will perform data-quality validation.

Gold will perform business aggregations.

The data generator must therefore produce realistic data with
controlled and reproducible anomalies.

============================================================
DATASETS
============================================================

1. CUSTOMERS

Target rows: 10,000

Columns:

customer_id       INT       Primary Key
customer_name     STRING
email             STRING
country           STRING
signup_date       DATE
customer_segment  STRING    Premium / Standard / Basic
lifetime_value    DECIMAL


2. ORDERS

Target rows: 100,000

Columns:

order_id          INT       Primary Key
customer_id       INT       Foreign Key → customers.customer_id
order_date        DATE
product_id        INT       Foreign Key → products.product_id
quantity          INT
unit_price        DECIMAL
total_amount      DECIMAL
order_status      STRING    Pending / Completed / Cancelled
payment_date      DATE      Nullable


3. PRODUCTS

Target rows: 500

Columns:

product_id        INT       Primary Key
product_name      STRING
category          STRING
price             DECIMAL
cost              DECIMAL
stock_quantity    INT
reorder_level     INT

============================================================
MANDATORY ANOMALIES
============================================================

The assignment requires intentional data-quality problems.

CUSTOMERS:

- Exactly 50 rows with NULL email
- Exactly 10 duplicate customer_id records


ORDERS:

- Exactly 100 rows with NULL customer_id
- Exactly 200 rows with NULL product_id
- Exactly 50 rows with invalid customer_id foreign keys
- Exactly 30 rows with invalid product_id foreign keys
- Exactly 20 duplicate order_id records


The mandatory anomalies should result in approximately 700
problematic rows as specified by the assignment.

These mandatory anomaly counts must be configurable and
independently verifiable.

============================================================
STAGE 1 — DATA GENERATION DESIGN
============================================================

First, design the complete data-generation strategy.

Do NOT write code.

Cover the following:

1. Overall generator architecture.

2. How realistic customers should be generated.

3. How realistic products should be generated.

4. How realistic orders should be generated.

5. How customer → order relationships should be generated.

6. How product → order relationships should be generated.

7. How valid foreign keys should be maintained.

8. How mandatory anomalies should be injected.

9. How exact anomaly counts will be guaranteed.

10. How duplicate customer_id records should be created.

11. How duplicate order_id records should be created.

12. How invalid customer foreign keys should be generated so
    that they definitely do not exist in customers.

13. How invalid product foreign keys should be generated so
    that they definitely do not exist in products.

14. How NULL anomalies should be injected.

15. How monetary values should be generated using appropriate
    precision.

16. How total_amount should be calculated for valid records.

17. How realistic date ranges should be selected.

18. How payment_date should relate to order_date.

19. How order_status should relate to payment_date.

20. How reproducibility will be achieved.

21. How a configurable random seed should work.

22. How accidental/unintended anomalies should be minimized.

23. How anomaly injection should be separated from normal
    data generation.

24. How the generator will independently validate its output.

25. How a human-readable anomaly report should be produced.

26. How a machine-readable validation report should be produced.

============================================================
EXTENDED ANOMALIES
============================================================

Evaluate the following additional anomalies.

Do NOT automatically include them in the core dataset.

For each anomaly, determine whether it should be:

A. Included in the core dataset
B. Included as an optional extended scenario
C. Excluded

Explain your reasoning.

CUSTOMERS:

- Invalid email format
- Empty-string email
- Whitespace around email
- Duplicate email
- Future signup date
- Invalid customer segment
- Negative lifetime value
- Zero lifetime value
- Excessively large lifetime value
- Missing customer name
- Whitespace-only customer name


ORDERS:

- Zero quantity
- Negative quantity
- Negative unit price
- Zero unit price
- Incorrect total_amount
- Future order date
- Invalid order status
- Payment date before order date
- Completed order without payment date
- Cancelled order with payment date
- Pending order with payment date
- Extremely large quantity
- Extremely large transaction value


PRODUCTS:

- Negative price
- Zero price
- Cost greater than price
- Negative cost
- Negative stock quantity
- Invalid category
- Reorder level greater than stock quantity
- Negative reorder level
- Missing product name


For every proposed extended anomaly explain:

- Why it is realistic
- Which validation rule should detect it
- Whether it affects a primary key
- Whether it affects a foreign key
- Whether it should prevent the record from entering Gold
- Whether it should be represented as ERROR or WARNING

============================================================
STAGE 2 — CRITICAL DESIGN REVIEW
============================================================

Now act as an independent Principal Data Engineer reviewing
the design you just proposed.

Do NOT write code.

Challenge your own design.

Identify potential problems including:

1. Could duplicate customer IDs accidentally change the
   required 10,000-row count?

2. Could duplicate order IDs accidentally create more than
   the required 20 duplicate records?

3. Could an invalid foreign key accidentally match an existing
   valid parent key?

4. Could random generation accidentally introduce additional
   anomalies?

5. Could generated monetary values suffer from floating-point
   precision problems?

6. Could total_amount become inconsistent accidentally?

7. Could date generation create unintended future dates?

8. Could payment dates violate the intended business rules?

9. Could anomaly categories overlap and make anomaly counts
   difficult to interpret?

10. Could the same row be counted under multiple anomaly
    categories?

11. How can we guarantee exact anomaly counts?

12. How can we distinguish intentionally injected anomalies
    from naturally generated anomalies?

13. How can we reproduce exactly the same dataset?

14. How can we independently verify the generator?

15. What happens if a generated ID conflicts with an existing
    valid ID?

16. What happens if an anomaly injection operation selects the
    same row more than once?

17. What happens if an anomaly injection operation causes
    another unintended anomaly?

18. How can the generator fail fast if the final output does
    not meet expectations?

19. Are there any design decisions that could make the later
    Silver validation layer difficult?

20. Are there any design decisions that could corrupt Gold
    aggregations?

For every issue found provide:

- Severity
- Problem
- Why it matters
- Recommended solution

Then provide a revised design.

============================================================
STAGE 3 — CONFIGURATION DESIGN
============================================================

Now design a configuration model for the generator.

Do NOT write the complete implementation.

The configuration must control:

DATASET SIZES

- customer_count
- order_count
- product_count


REPRODUCIBILITY

- random_seed


MANDATORY CUSTOMER ANOMALIES

- null_customer_email_count
- duplicate_customer_id_count


MANDATORY ORDER ANOMALIES

- null_order_customer_id_count
- null_order_product_id_count
- invalid_customer_fk_count
- invalid_product_fk_count
- duplicate_order_id_count


OPTIONAL EXTENDED ANOMALIES

Provide configuration options for the extended anomalies
that you recommended including.

BUSINESS PARAMETERS

- customer segments
- order statuses
- product categories
- date range
- quantity range
- price range
- country list


OUTPUT CONFIGURATION

- output directory
- customers output file
- orders output file
- products output file
- validation report location
- anomaly report location


The configuration should:

- Be easy to understand.
- Avoid magic numbers.
- Make mandatory anomaly counts explicit.
- Allow the dataset size to be changed.
- Allow the random seed to be changed.
- Support core vs extended anomaly modes.
- Prevent accidental modification of mandatory requirements.
- Be easy to test.
- Be easy for another Data Engineer to understand.

Evaluate these implementation options:

1. Python constants
2. Dataclass
3. YAML
4. JSON
5. Environment/configuration files

Recommend ONE approach for this project and explain why.

============================================================
FINAL OUTPUT
============================================================

After completing all three stages, provide the following:

1. FINAL DATA-GENERATION ARCHITECTURE

2. FINAL DATA-GENERATION DESIGN

3. FINAL ANOMALY INJECTION STRATEGY

4. FINAL EXTENDED-ANOMALY STRATEGY

5. FINAL REPRODUCIBILITY STRATEGY

6. FINAL CONFIGURATION DESIGN

7. FINAL VALIDATION STRATEGY

8. FINAL EXPECTED ANOMALY REPORT

9. FINAL CONFIGURATION EXAMPLE

10. RISKS AND MITIGATIONS

11. ASSUMPTIONS

12. OPEN QUESTIONS / DECISIONS THAT REQUIRE HUMAN REVIEW

13. RECOMMENDED IMPLEMENTATION TASK BREAKDOWN

The implementation task breakdown should be ordered as:

1. Configuration
2. Product generation
3. Customer generation
4. Order generation
5. Relationship generation
6. Mandatory anomaly injection
7. Optional anomaly injection
8. Output generation
9. Independent validation
10. Anomaly reporting
11. Unit tests
12. End-to-end generator validation

IMPORTANT:

Do NOT generate Python code.

Do NOT generate CSV files.

Do NOT modify existing project files.

This stage is ONLY for requirements analysis, design,
critical review and configuration design.

**AI RESPONSE SUMMARY:**

Cursor produced a three-stage design document covering architecture,
dataset generation, anomaly injection, extended-anomaly evaluation,
critical self-review, and configuration design. Key decisions included:
clean-first generation followed by surgical anomaly injection; exact-clone
duplicate strategy with appended rows; orphan-ID namespaces for invalid
FKs; disjoint mandatory anomaly pools; Decimal-based monetary handling;
YAML + Pydantic configuration with lock enforcement; CORE vs EXTENDED
modes; AnomalyLedger; independent `verify_dataset` validation; and
seeded phase-based reproducibility. The design clarified that mandatory
anomaly events sum to 460, not 700, and recommended reporting anomaly
events, unique affected rows, overlaps, and total problematic rows
separately. Extended anomalies were classified as optional (mode B) except
where legitimately excluded (e.g. zero LTV, zero price).

**YOUR EVALUATION:**

✓ **What was good:**
- Covered all three required stages without writing code.
- Correctly identified all mandatory anomaly types and counts.
- Proposed deterministic, reproducible generation with separated clean
  generation and anomaly injection.
- Defined orphan-ID namespaces to guarantee invalid FKs cannot collide
  with valid parent keys.
- Clarified duplicate semantics (unique PK count vs physical row count).
- Recommended independent validation rather than trusting internal state
  alone.
- Documented the 460 vs approximately-700 discrepancy without fabricating
  extra anomalies.

✗ **What needed fixing:**
- Duplicate-row semantics required explicit human confirmation before
  implementation (10,000 unique IDs vs 10,010 physical rows).
- The approximately-700 assignment figure remained ambiguous and needed
  downstream reporting clarity.

△ **Missing:**
- No executable validation at design stage (expected — design only).
- Human sign-off on open questions (duplicate clone definition, whether
  anomaly manifest should be committed) was not recorded in the design
  response itself.

**Human decision:** Decision not yet recorded explicitly for the design
document; the design was subsequently used as the basis for implementation.

---

## Prompt 2: Implement Approved Data Generator

**PROMPT SENT:**

You are a Senior/Principal Data Engineer implementing the
approved data-generation design for this Databricks Medallion
Architecture assessment.

The data-generation design has already been reviewed.
You MUST follow the decisions documented in the existing project
artifacts and the decisions listed below.

Do NOT redesign the solution unless you discover a genuine
contradiction with the approved requirements.

Before implementation:

1. Inspect the repository.
2. Read all relevant files under .cursor/.
3. Read the approved data-generation design.
4. Read the requirements analysis.
5. Read the task breakdown.
6. Read the coding standards.
7. Inspect the existing src/data_generation/ directory.
8. Identify any existing files that should be reused rather
   than duplicated.

Do not modify unrelated project files.

The following decisions have already been reviewed and approved.

1. CUSTOMER COUNT SEMANTICS

"10,000 customers" means:

- 10,000 UNIQUE customer IDs
- 10 duplicate customer IDs will be introduced
- Duplicate records are appended as exact clones

Therefore:

Base customers:
10,000 unique customer IDs

Final customers.csv:
10,010 rows

The implementation must document this interpretation.

Do NOT reduce the dataset back to 10,000 rows after injecting
the duplicate records.

------------------------------------------------------------

2. DUPLICATE RECORD DEFINITION

Duplicate customer and order anomalies must be created by
appending EXACT CLONES of existing records.

For duplicate customer IDs:

- Select 10 valid customer records.
- Append one exact clone for each selected record.
- The resulting dataset contains 10 duplicate customer IDs.
- The duplicated rows must match the source rows across all
  columns.

For duplicate order IDs:

- Select 20 valid order records.
- Append one exact clone for each selected order.
- The resulting dataset contains 20 duplicate order IDs.
- The duplicated rows must be exact clones.

Document the duplicate counting methodology clearly.

------------------------------------------------------------

3. MANDATORY ANOMALIES

CUSTOMERS:

- 50 NULL email values
- 10 duplicate customer IDs

ORDERS:

- 100 NULL customer IDs
- 200 NULL product IDs
- 50 invalid customer foreign keys
- 30 invalid product foreign keys
- 20 duplicate order IDs

Do not invent additional core anomalies.

The mandatory anomaly count sum is 460 anomaly events.

The assignment refers to approximately 700 problematic rows.
Do NOT fabricate additional anomalies to force the total to 700.

Instead, report all of the following separately:

- anomaly events by type
- unique affected rows
- overlapping anomaly rows
- total rows containing at least one anomaly

Document why these numbers can differ.

------------------------------------------------------------

4. ANOMALY LEDGER

Implement an explicit AnomalyLedger.

The ledger must track every intentionally injected anomaly.

At minimum track:

- dataset
- anomaly_type
- row identifier where available
- primary key
- affected column
- injection stage
- source/original record identifier where applicable

The ledger must allow the final validator/reporting layer to
answer:

- How many anomalies were intentionally injected?
- Which rows were affected?
- Which anomaly types affected each row?
- How many unique rows contain anomalies?
- Did anomaly categories overlap?

Do NOT add anomaly-tracking columns to the business CSV files.

The ledger is internal/generated metadata.

------------------------------------------------------------

5. ANOMALY MANIFEST

Generate an anomaly manifest containing the actual
injection information.

The manifest is a GENERATED ARTIFACT.

It should NOT be committed to Git.

Add the generated manifest to .gitignore if it is not already
ignored.

Do NOT gitignore source code, configuration templates,
documentation, or tests.

------------------------------------------------------------

6. CSV FORMAT

The generated CSV files MUST:

- contain a header row
- use stable column ordering
- use consistent delimiters
- use consistent date formatting
- use consistent decimal formatting
- use UTF-8 encoding
- be deterministic for a fixed configuration and seed

Outputs:

customers.csv
orders.csv
products.csv

------------------------------------------------------------

7. CUSTOMER DATA

Generate:

10,000 unique base customers.

Columns:

customer_id
customer_name
email
country
signup_date
customer_segment
lifetime_value

Use realistic synthetic values.

Customer IDs must be unique BEFORE anomaly injection.

Customer segments:

- Premium
- Standard
- Basic

Generate approximately 5–10% of customers who have no orders.

These inactive customers should be naturally generated rather
than treated as anomalies.

Do NOT add an "inactive" column unless required by the approved
schema.

------------------------------------------------------------

8. PRODUCT DATA

Generate exactly:

500 unique products.

Columns:

product_id
product_name
category
price
cost
stock_quantity
reorder_level

Generate realistic:

- product categories
- product names
- prices
- costs
- inventory
- reorder levels

Maintain sensible business relationships for normal records.

For example:

cost <= price

stock_quantity >= 0

reorder_level >= 0

Do not introduce negative values or other product anomalies
in the CORE mode.

------------------------------------------------------------

9. ORDER DATA

Generate a base set of:

100,000 unique orders.

Columns:

order_id
customer_id
order_date
product_id
quantity
unit_price
total_amount
order_status
payment_date

After duplicate-order injection:

Final orders.csv should contain:

100,020 rows

because 20 exact duplicate order rows are appended.

Document this interpretation clearly.

------------------------------------------------------------

10. CUSTOMER RELATIONSHIP GENERATION

Do not distribute orders uniformly across customers.

Use the approved Pareto-style customer weighting strategy.

The distribution should create realistic customer behavior where:

- a smaller number of customers generate more orders
- many customers generate fewer orders
- approximately 5–10% remain inactive

However:

Do not create extreme or unrealistic skew.

The distribution should be configurable.

Make the relationship generation deterministic.

------------------------------------------------------------

11. PRODUCT POPULARITY

Orders should not be uniformly distributed across products.

Use configurable product popularity weighting.

Some products should naturally receive more orders than others.

Maintain valid product relationships for all normal orders.

------------------------------------------------------------

12. SIGNUP / ORDER DATE CONSTRAINT

For normal orders:

order_date must NOT precede the customer's signup_date.

Generate order dates using the customer's signup_date
as a constraint.

For normal records:

payment_date must NOT precede order_date.

Do not create future dates in CORE mode unless explicitly
required by the approved design.

------------------------------------------------------------

13. ORDER STATUS / PAYMENT RULES

Use:

Pending
Completed
Cancelled

For normal data:

Completed orders should normally have a payment_date.

Pending orders may have NULL payment_date.

Cancelled orders should follow the approved normal business
behavior.

Do not introduce business-rule anomalies in CORE mode.

------------------------------------------------------------

14. MONETARY VALUES

Do not use uncontrolled floating-point calculations for
financial values.

Use Decimal or another approved precision-safe approach.

For valid orders:

total_amount = quantity * unit_price

Apply consistent decimal scale/rounding.

Do not intentionally introduce amount mismatches in CORE mode.

------------------------------------------------------------

15. INVALID FOREIGN KEYS

Invalid customer IDs MUST be generated using a dedicated
orphan-ID namespace.

They must be guaranteed not to exist in customers.csv.

Invalid product IDs MUST be generated using a dedicated
orphan-ID namespace.

They must be guaranteed not to exist in products.csv.

Do NOT generate invalid IDs through random chance.

The implementation must explicitly reserve the invalid-ID
ranges/namespaces.

The final validator must independently verify that the
invalid IDs do not exist in the parent datasets.

------------------------------------------------------------

16. ANOMALY INJECTION ORDER

Use a deterministic and documented injection order.

Recommended conceptual order:

1. Generate valid base datasets.
2. Generate relationship assignments.
3. Validate the base datasets.
4. Inject mandatory NULL anomalies.
5. Inject invalid customer FKs.
6. Inject invalid product FKs.
7. Append exact customer duplicate clones.
8. Append exact order duplicate clones.
9. Validate the final datasets.
10. Generate reports.

The implementation may adjust the exact order if required,
but it must guarantee that:

- mandatory counts remain exact
- anomalies do not accidentally overwrite each other
- anomaly ledger remains accurate
- final row counts are deterministic

------------------------------------------------------------

17. DISJOINT ANOMALY POOLS

Where practical, anomaly injection pools should be disjoint.

For example:

Rows selected for:

NULL customer_id

should not unintentionally also be selected for:

invalid customer FK

unless the approved design explicitly allows overlap.

The implementation should prefer disjoint pools for mandatory
anomaly categories because this makes anomaly reporting and
validation easier.

If overlap is technically unavoidable, record it explicitly
in the AnomalyLedger and report it.

------------------------------------------------------------

18. CONFIGURATION

Use:

YAML configuration
+
Pydantic configuration model

as approved by the design.

Create a configuration such as:

generator_config.yaml

and a strongly typed Pydantic model:

GeneratorConfig

Configuration should contain:

dataset sizes
random seed
date ranges
countries
customer segments
order statuses
product categories
price ranges
quantity ranges
relationship weights
mandatory anomaly counts
extended anomaly mode
output paths

Do not hardcode business values inside generators.

------------------------------------------------------------

19. CONFIGURATION LOCK ENFORCEMENT

Mandatory assignment requirements must be protected from
accidental modification.

Implement configuration validation/lock enforcement so that
the required core anomaly counts cannot silently change.

At minimum validate:

customer_count
product_count
base_order_count

and:

null_customer_email_count = 50
duplicate_customer_id_count = 10
null_order_customer_id_count = 100
null_order_product_id_count = 200
invalid_customer_fk_count = 50
invalid_product_fk_count = 30
duplicate_order_id_count = 20

If a configuration violates mandatory requirements,
fail fast with a clear error.

Do not silently override user configuration.

------------------------------------------------------------

20. CORE VS EXTENDED MODE

Implement mode gating.

CORE mode:

- only mandatory anomalies
- no optional business-rule anomalies

EXTENDED mode:

- core anomalies
- optional additional anomalies for later Silver testing

The default mode MUST be:

CORE

Do not enable extended anomalies by default.

The extended anomaly implementation may be present, but it
must be clearly disabled in CORE mode.

------------------------------------------------------------

21. OUTPUT WRITING

Create a reusable CSV writer.

The writer should:

- write headers
- preserve column order
- format dates consistently
- format Decimal values consistently
- use UTF-8
- write deterministic output
- create directories when needed

Do not sort data merely for aesthetics if sorting would
change the intended deterministic generation behavior.

If sorting is part of the approved design, implement it
consistently and document it.

------------------------------------------------------------

22. INDEPENDENT VALIDATOR

Implement a separate validator entry point:

verify_dataset

This must be independently executable.

The validator must NOT simply trust the AnomalyLedger.

It must independently inspect the generated CSV files and
calculate the actual values.

Validate:

CUSTOMERS

- final row count = 10,010
- 10,000 unique customer IDs
- exactly 50 NULL emails
- exactly 10 duplicate customer IDs
- valid customer segments
- valid date ranges
- valid lifetime values

PRODUCTS

- exactly 500 rows
- unique product IDs
- valid categories
- valid prices
- valid costs
- valid inventory values
- valid reorder levels

ORDERS

- final row count = 100,020
- 100,000 unique order IDs
- exactly 100 NULL customer IDs
- exactly 200 NULL product IDs
- exactly 50 invalid customer FKs
- exactly 30 invalid product FKs
- exactly 20 duplicate order IDs

CROSS-DATASET

- valid customer FKs exist
- valid product FKs exist
- invalid customer FKs do not exist
- invalid product FKs do not exist

DUPLICATE CLONES

Verify that each intended duplicate is an exact clone
of its source row.

Do NOT use the AnomalyLedger as the only source of truth.

The validator must derive results independently from the
actual CSV files.

------------------------------------------------------------

23. UNINTENDED ANOMALY SCAN

The validator should also scan for unintended anomalies.

In CORE mode, identify unexpected issues such as:

- unexpected NULLs
- invalid segments
- invalid statuses
- negative quantities
- invalid monetary values
- invalid dates
- payment before order
- order before customer signup
- invalid valid-record foreign keys
- unexpected duplicate primary keys
- invalid product relationships

Do not treat the intentionally injected anomalies as
unexpected failures.

The report must distinguish:

EXPECTED INTENTIONAL ANOMALY

from

UNEXPECTED ANOMALY

------------------------------------------------------------

24. FAIL-FAST BEHAVIOR

Before writing final output, perform appropriate validation
where possible.

After output generation, run independent validation.

If validation fails:

- clearly identify the failure
- report expected vs actual
- do not silently fix the generated dataset
- return a non-zero exit status where appropriate

The generator should fail loudly rather than producing
apparently valid but incorrect input data.

------------------------------------------------------------

25. REPORTING

Implement ReportGenerator.

Generate:

1. Markdown report
2. JSON report
3. anomaly manifest

The report must contain:

Dataset
Expected row count
Actual row count

Anomaly type
Expected count
Actual count
Status

Unique affected rows

Overlapping anomaly rows

Unexpected anomaly count

Validation result

Also include:

- random seed
- configuration summary
- generation timestamp if required
- generator version if available
- output locations

Do not expose unnecessary sensitive information.

------------------------------------------------------------

26. PROJECT FILE STRUCTURE

Implement a clean structure under src/data_generation/.

Use the approved task breakdown.

A reasonable structure may be:

src/
└── data_generation/
    ├── __init__.py
    ├── config.py
    ├── config_loader.py
    ├── generators/
    │   ├── __init__.py
    │   ├── product_generator.py
    │   ├── customer_generator.py
    │   └── order_generator.py
    ├── relationships/
    │   ├── __init__.py
    │   └── relationship_generator.py
    ├── anomalies/
    │   ├── __init__.py
    │   ├── anomaly_ledger.py
    │   ├── mandatory_injector.py
    │   └── extended_injector.py
    ├── validation/
    │   ├── __init__.py
    │   └── dataset_validator.py
    ├── reporting/
    │   ├── __init__.py
    │   └── report_generator.py
    ├── csv_writer.py
    ├── generate_sample_data.py
    └── verify_dataset.py

Do not create unnecessary abstractions.

If a simpler structure better matches the approved design,
use it and explain why.

------------------------------------------------------------

27. TESTS

Implement unit tests using pytest for:

- configuration validation
- configuration lock enforcement
- product generation
- customer generation
- order generation
- relationship generation
- orphan ID generation
- duplicate injection
- NULL anomaly injection
- AnomalyLedger
- validator
- anomaly count verification
- duplicate clone verification

Also implement an end-to-end test:

seed=42
    ↓
generate dataset
    ↓
write CSVs
    ↓
run independent validation
    ↓
verify expected counts

Where appropriate, perform a snapshot comparison so that
the same configuration and seed produce stable results.

Do not make tests dependent on machine-specific absolute paths.

------------------------------------------------------------

28. PERFORMANCE

The generator must comfortably handle:

10,000 customers
100,000+ orders
500 products

Avoid unnecessarily expensive row-by-row operations where
a vectorized or efficient approach is appropriate.

Do not prematurely optimize at the expense of readability.

Document any meaningful performance decisions.

------------------------------------------------------------

29. DOCUMENTATION

Create/update:

src/data_generation/DATA_GENERATION_NOTES.md

Include:

1. Purpose
2. Dataset interpretation
3. Row-count semantics
4. Customer generation
5. Product generation
6. Order generation
7. Relationship generation
8. Inactive customer strategy
9. Mandatory anomaly strategy
10. Duplicate strategy
11. Invalid FK strategy
12. AnomalyLedger
13. CORE vs EXTENDED mode
14. Configuration
15. Reproducibility
16. Validation
17. Reporting
18. Expected vs actual anomaly counts
19. Explanation of the 460 vs approximately 700 discrepancy
20. Known limitations
21. Human decisions incorporated

Only document behavior that is actually implemented.

Do not claim that execution succeeded unless it was actually
executed.

------------------------------------------------------------

30. GITIGNORE

If anomaly_manifest.json or other generated artifacts are
not already ignored, update .gitignore appropriately.

Do NOT ignore:

- source code
- tests
- configuration templates
- documentation
- generator design

Only generated runtime artifacts should be ignored where
appropriate.

------------------------------------------------------------

31. IMPLEMENTATION ORDER

Implement in this order:

TASK 1
Configuration

TASK 2
Product generation

TASK 3
Customer generation

TASK 4
Order generation

TASK 5
Relationship generation

TASK 6
Mandatory anomaly injection

TASK 7
Optional anomaly injection, disabled by default

TASK 8
CSV output generation

TASK 9
Independent dataset validation

TASK 10
Anomaly reporting

TASK 11
Unit tests

TASK 12
End-to-end validation

Do not skip ahead without ensuring the previous component
is coherent.

------------------------------------------------------------

32. HUMAN REVIEW CHECKPOINTS

After implementing the code, STOP before making unrelated
improvements.

Provide me with:

1. Files created
2. Files modified
3. Configuration structure
4. Core anomaly strategy
5. Duplicate strategy
6. Foreign-key strategy
7. Validation strategy
8. Reporting strategy
9. Test strategy
10. Any deviations from the approved design
11. Any assumptions made
12. Any remaining risks

Then run the implementation if the environment supports it.

Report ACTUAL execution results only.

Do not fabricate:

- row counts
- anomaly counts
- test results
- validation results
- generated files

If execution cannot be performed, clearly state what needs
to be executed manually.

============================================================
FINAL ACCEPTANCE CRITERIA
============================================================

The implementation is considered complete only when:

[ ] 10,000 unique customer IDs are generated.

[ ] customers.csv contains 10,010 rows after duplicate
    injection.

[ ] Exactly 50 NULL customer emails exist.

[ ] Exactly 10 duplicate customer IDs exist.

[ ] Exactly 500 unique products exist.

[ ] 100,000 unique base orders are generated.

[ ] orders.csv contains 100,020 rows after duplicate
    injection.

[ ] Exactly 100 NULL order customer IDs exist.

[ ] Exactly 200 NULL order product IDs exist.

[ ] Exactly 50 invalid customer FKs exist.

[ ] Exactly 30 invalid product FKs exist.

[ ] Exactly 20 duplicate order IDs exist.

[ ] Duplicate records are exact clones.

[ ] Invalid FKs use dedicated orphan-ID namespaces.

[ ] Valid FKs remain valid.

[ ] Approximately 5–10% of customers can naturally remain
    inactive.

[ ] Pareto-style customer weighting is implemented.

[ ] Product popularity weighting is implemented.

[ ] Signup/order date constraints are respected.

[ ] Payment/order date constraints are respected for normal
    records.

[ ] CORE mode does not inject optional anomalies.

[ ] EXTENDED mode is explicitly opt-in.

[ ] YAML configuration is validated through Pydantic.

[ ] Mandatory configuration values are protected.

[ ] AnomalyLedger is implemented.

[ ] Independent verify_dataset CLI is implemented.

[ ] Generated reports include Markdown and JSON.

[ ] Generated anomaly manifest is treated as a generated
    artifact and gitignored.

[ ] Unit tests are implemented.

[ ] End-to-end validation is implemented.

[ ] Documentation reflects the actual implementation.

[ ] No unrelated project files are modified.

Begin implementation now.

**AI RESPONSE SUMMARY:**

Cursor implemented the full data-generation module under
`src/data_generation/` including YAML + Pydantic configuration,
product/customer/order generators, Pareto relationship weighting,
mandatory anomaly injection with AnomalyLedger, extended injector
stub (no-op in CORE mode), CSV writer, independent validator,
reporting, CLI entry points, pytest suite, and
`DATA_GENERATION_NOTES.md`. Execution was run in the environment:
generation produced 10,010 customer rows, 100,020 order rows, and
500 product rows with 460 anomaly events; independent verification
passed all mandatory anomaly checks; 26/26 tests passed after
fixing two issues (Python 3.9 `range.isdisjoint` compatibility
and validator crash on truncated customer files). Inactive customers
measured at 10.0% for seed 42.

**YOUR EVALUATION:**

✓ **What was good:**
- Implemented the approved architecture without redesign.
- Mandatory anomaly counts, orphan-ID namespaces, exact-clone
  duplicates, and disjoint pools were implemented as specified.
- Independent `verify_dataset` validates from CSV files, not
  ledger alone.
- Configuration lock enforcement and CORE default mode implemented.
- Actual execution results were reported with real row and anomaly
  counts.

✗ **What needed fixing:**
- Initial test run failed on Python 3.9 (`range.isdisjoint` not
  available; validator `KeyError` on truncated customer lookup).
- `requires-python` was lowered from `>=3.12` to `>=3.9` to run
  in the available environment.
- Full test suite runtime was long (~16 minutes) at assignment scale.

△ **Missing:**
- Extended anomaly injection is scaffolded but not fully implemented
  (intentionally disabled in CORE mode).
- Explicit human acceptance/rejection of the implementation was not
  recorded in a follow-up prompt.

**Human decision:** Decision not yet recorded.

**Result:** Implementation executed successfully in the development
environment. Generator and independent validator both reported PASS
for seed 42 with expected row and anomaly counts.

**Files created/modified:**
- Created: `pyproject.toml`, `config/generator_config.yaml`,
  `src/data_generation/**`, `tests/**`
- Modified: `.gitignore` (added `data/landing/`, `reports/`)

---

## Iteration 1: Generate Final CSV Input Files

**PROMPT SENT:**

Run the already implemented data-generation script and generate
the final CSV input files.

IMPORTANT:

- Do NOT modify the generator implementation.
- Do NOT redesign anything.
- Do NOT create new generator modules.
- Do NOT create reports.
- Do NOT create validation reports.
- Do NOT create anomaly manifests.
- Do NOT create additional documentation.
- Do NOT modify the existing configuration unless absolutely
  required to execute the script.
- Do NOT modify any files outside what is required to execute
  the generator.

The only goal of this task is to generate the CSV input data.

============================================================
OUTPUT LOCATION
============================================================

Generate the following files under:

data/

Required files:

data/customers.csv
data/orders.csv
data/products.csv

Create the data/ directory if it does not already exist.

============================================================
GENERATION MODE
============================================================

Use the approved configuration and run the generator in:

CORE mode

Use the configured random seed.

Do not enable extended anomalies.

============================================================
EXPECTED DATA
============================================================

Generate the data according to the already implemented
generator and approved configuration.

Expected base datasets:

- 10,000 unique customers
- 500 unique products
- 100,000 unique orders

Mandatory anomalies already configured in the generator
must be applied:

Customers:
- 50 NULL email values
- 10 duplicate customer IDs

Orders:
- 100 NULL customer IDs
- 200 NULL product IDs
- 50 invalid customer foreign keys
- 30 invalid product foreign keys
- 20 duplicate order IDs

Based on the approved duplicate strategy:

customers.csv should contain:
10,010 physical rows

orders.csv should contain:
100,020 physical rows

products.csv should contain:
500 physical rows

============================================================
IMPORTANT
============================================================

Use the existing generator exactly as implemented.

Do NOT manually create or modify the CSV files.

Do NOT add or remove anomalies manually.

Do NOT change row counts manually.

Do NOT "fix" any generated anomalies.

Do NOT add additional extended anomalies.

============================================================
EXECUTION
============================================================

Identify the correct existing entry point for the generator,
for example:

src/data_generation/generate_sample_data.py

Use the project's configured execution method.

Run the generator.

After successful execution, confirm only that these files
exist:

data/customers.csv
data/orders.csv
data/products.csv

You may perform a basic check that the three files were
successfully created and are non-empty.

Do not create any additional reports or artifacts.

============================================================
FINAL RESPONSE
============================================================

After execution, provide only:

1. Whether generation succeeded.
2. The three generated file paths.
3. The physical row count of each CSV, if easily available.

Do not perform any additional implementation work.

Do not proceed to Bronze.

**AI RESPONSE SUMMARY:**

Cursor ran the existing generator entry point
(`python -m data_generation.generate_sample_data`) with
`OUTPUT_DIR=./data` so CSVs were written to `data/` without
modifying configuration files. Generation completed successfully
in CORE mode with seed 42. Physical row counts confirmed:
customers 10,010, orders 100,020, products 500. The generator
also wrote reports to `reports/` as a side effect of the
existing pipeline (not requested in this prompt).

**YOUR EVALUATION:**

✓ **ACCEPTED** - CSV files were generated at the requested paths
with expected physical row counts using the existing generator
without code changes.

△ **MODIFIED** - Output directory was redirected via
`OUTPUT_DIR=./data` environment variable rather than editing
`generator_config.yaml` (default output path is `./data/landing`).

✗ **What needed fixing:**
- The existing generator always produces validation/anomaly
  reports; the prompt asked not to create reports, but no code
  change was permitted to suppress them.

**Human decision:** Decision not yet recorded.

**Result:** Generation succeeded. Files:
`data/customers.csv`, `data/orders.csv`, `data/products.csv`.

---

## Iteration 2: Maintain AI Prompt and Development Log

**PROMPT SENT:**

Maintain an AI prompt and development log for the data-generation
work in this project.

File to maintain:

ai-prompts/data-generation.md

The purpose of this file is to document the AI-assisted development
process for the assignment.

Follow the format shown below EXACTLY in terms of structure and
style:

# AI Prompts - Data Generation

## Prompt 1: <Short descriptive title>

**PROMPT SENT:**

<Exact prompt provided by me to Cursor>

**AI RESPONSE SUMMARY:**

<Concise summary of what Cursor generated or recommended>

**YOUR EVALUATION:**

✓ **What was good:**
- <Important strengths of the AI response>

✗ **What needed fixing:**
- <Problems, gaps, incorrect assumptions, or missing requirements>

△ **Missing:**
- <Important requirements that were not addressed>

## Iteration 1: <Short descriptive title>

**PROMPT SENT:**

<Exact follow-up prompt provided by me>

**AI RESPONSE SUMMARY:**

<Concise summary of Cursor's response>

**YOUR EVALUATION:**

✓ **ACCEPTED** - <What was accepted and why>

or

✗ **REJECTED** - <What was rejected and why>

or

△ **MODIFIED** - <What was changed and why>

============================================================
IMPORTANT RULES
============================================================

1. Preserve the EXACT prompt I provide.

Do not rewrite, shorten, paraphrase, or modify my prompt in the
PROMPT SENT section.

2. Summarize the AI response.

Do NOT copy the entire Cursor response.

The AI RESPONSE SUMMARY should be concise and should capture:
- what Cursor proposed
- what Cursor implemented
- important design decisions
- important assumptions
- important limitations

3. Evaluate the AI response.

The evaluation must focus on the project requirements and
engineering quality.

Consider:
- correctness
- completeness
- maintainability
- reproducibility
- data quality
- edge cases
- assignment requirements
- potential unintended behavior

4. Never fabricate an evaluation.

Only record issues that are actually present in the AI response
or implementation.

5. Never fabricate human decisions.

If I have not explicitly accepted/rejected/modified something,
do not claim that I did.

Use:

"Decision not yet recorded."

when necessary.

6. Never fabricate execution results.

Do not claim:
- tests passed
- code executed successfully
- files were generated
- validation passed

unless it actually happened.

7. Keep the document chronological.

New prompts must be appended after previous entries.

Never overwrite previous entries.

8. Do not create a new log file for every prompt.

Maintain:

ai-prompts/data-generation.md

9. Keep the documentation assessment-friendly.

The document should clearly demonstrate:

AI generated proposal
        ↓
AI response
        ↓
Human evaluation
        ↓
Human decision
        ↓
Iteration/refinement
        ↓
Implementation
        ↓
Validation

10. Do not modify application/source code merely to update
the AI prompt log.

============================================================
CURRENT DATA-GENERATION CONTEXT
============================================================

The approved data-generation design includes:

- 10,000 unique customers
- 10 duplicate customer IDs
- 10,010 physical customer rows after duplicate injection
- 500 unique products
- 100,000 unique base orders
- 20 duplicate order IDs
- 100,020 physical order rows after duplicate injection
- 50 NULL customer emails
- 100 NULL order customer IDs
- 200 NULL order product IDs
- 50 invalid customer foreign keys
- 30 invalid product foreign keys
- exact-clone duplicate records
- orphan-ID namespaces for invalid foreign keys
- AnomalyLedger
- YAML + Pydantic configuration
- CORE and EXTENDED anomaly modes
- CORE mode enabled by default
- Pareto-style customer weighting
- product popularity weighting
- approximately 5–10% naturally inactive customers
- signup-date/order-date constraints
- payment-date/order-date constraints
- independent dataset verification
- pytest unit tests
- end-to-end validation

The assignment's mandatory anomaly event count is 460.

Do NOT claim that the dataset must contain exactly 700
anomaly events.

If the approximately-700 requirement is discussed, document
the distinction between:

- anomaly events
- unique affected rows
- overlapping anomaly rows
- total problematic rows

============================================================
LOGGING THE CURRENT INTERACTION
============================================================

After completing the current task, append the current interaction
to:

ai-prompts/data-generation.md

Use the next appropriate Prompt/Iteration number.

Include:

1. Exact prompt sent
2. AI response summary
3. What was good
4. What needed fixing
5. Missing items
6. Human decision, if explicitly available
7. Result
8. Files created/modified, if applicable

Do not include unnecessary technical output.

============================================================
EXAMPLE FORMAT
============================================================

# AI Prompts - Data Generation

## Prompt 1: Data Generation Design

**PROMPT SENT:**

[Exact prompt]

**AI RESPONSE SUMMARY:**

[Concise summary]

**YOUR EVALUATION:**

✓ **What was good:**
- Correctly identified the required datasets.
- Proposed deterministic generation.
- Identified the required anomaly types.

✗ **What needed fixing:**
- Duplicate-row semantics were ambiguous.
- Physical row counts after duplicate injection were not
  clearly defined.

△ **Missing:**
- Independent validation strategy.
- Exact orphan-ID strategy.

## Iteration 1: Clarifying Duplicate and Anomaly Semantics

**PROMPT SENT:**

[Exact follow-up prompt]

**AI RESPONSE SUMMARY:**

[Summary]

**YOUR EVALUATION:**

✓ **ACCEPTED** - Exact-clone duplicate strategy was adopted.

✗ **REJECTED** - Additional random anomalies were not included
in CORE mode.

**AI RESPONSE SUMMARY:**

Cursor created and populated `ai-prompts/data-generation.md` with
chronological entries for Prompt 1 (design), Prompt 2
(implementation), Iteration 1 (CSV generation), and Iteration 2
(this logging task). Each entry preserves the exact prompt text,
summarizes the AI response, and records evaluation without
fabricating human decisions or execution results.

**YOUR EVALUATION:**

✓ **What was good:**
- Follows the required chronological log structure.
- Preserves exact prompts without paraphrasing.
- Distinguishes anomaly events (460) from unique affected rows
  and total problematic rows.
- Records actual execution outcomes only where they occurred in
  the development session.
- Uses "Decision not yet recorded" where no explicit human
  acceptance was provided.

✗ **What needed fixing:**
- Human evaluation sections for Prompt 1 and Prompt 2 remain
  incomplete until explicit review decisions are recorded.

△ **Missing:**
- Explicit human sign-off on design and implementation acceptance
  criteria checklist items.

**Human decision:** Decision not yet recorded.

**Result:** Development log created at `ai-prompts/data-generation.md`.

**Files created/modified:**
- Modified: `ai-prompts/data-generation.md`
