# AI Prompts — BI Dashboard

The dashboard is the final presentation layer of the Bronze → Silver → Gold →
Dashboard pipeline.

The dashboard consumes Gold datasets and provides business visualizations.

Required visualizations:

1. Top 10 Products by Revenue
2. Customer Revenue Distribution
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

Data Generation, Bronze, Silver, and Gold were completed before dashboard
implementation began.

---

## Prompt 1: BI Dashboard Requirements Analysis

**PROMPT SENT:**

Not performed as a separate prompt in recorded project history.

**AI RESPONSE SUMMARY:**

Not applicable. Dashboard requirements and design were provided directly as
part of the implementation prompt (Prompt 2).

**YOUR EVALUATION:**

✓ What was good:

- Dashboard requirements were explicitly detailed in the implementation prompt.
- Local vs Databricks responsibilities were clearly separated in the prompt.
- Gold-only consumption and filter requirements were specified up front.

✗ What needed fixing:

- A separate requirements-analysis-only prompt was not recorded.

△ Missing:

- No standalone human requirements review prompt before implementation.

**HUMAN DECISION:**

Decision not yet recorded.

---

## Prompt 2: BI Dashboard Implementation

**PROMPT SENT:**

You are a Senior Data Engineer completing the FINAL ANALYTICS
layer of our Databricks Medallion Architecture assessment.

The following stages have already been implemented:

1. Data Generation
2. Bronze Layer
3. Silver Layer
4. Gold Layer

The ONLY remaining core pipeline component is:

5. BI Dashboard

Your task is to implement the dashboard query layer,
dashboard documentation, validation, and Databricks dashboard
configuration guidance.

IMPORTANT:

Do NOT redesign or rewrite:

- data generation
- Bronze
- Silver
- Gold

Do NOT modify business logic in completed layers unless a
blocking defect is discovered.

First inspect the existing repository and understand the
existing implementation.

The complete Prompt 2 user message contained 32 numbered sections
(from repository inspection through final response requirements),
covering:

- dashboard requirements and 3+ tiles
- Gold-only input contract
- three mandatory visualizations plus optional KPI
- filter design
- `dashboard_queries.sql` and `DASHBOARD_GUIDE.md`
- local Spark validation (not Streamlit)
- Databricks SQL Dashboard configuration guidance
- testing and reconciliation requirements
- assignment gap scan
- deferral of `ai-prompts/dashboard.md` until a separate documentation prompt

The opening requirement block is recorded above; the remaining section text
matches the BI Dashboard implementation user query from this project session
in full.

**AI RESPONSE SUMMARY:**

Implemented a Gold-backed dashboard query layer with portable Spark SQL,
local validation, tests, and Databricks setup documentation.

**Files created:**

- `src/dashboard/__init__.py`
- `src/dashboard/dashboard_queries.sql`
- `src/dashboard/dashboard_utils.py`
- `src/dashboard/validate_dashboard_queries.py`
- `src/dashboard/DASHBOARD_GUIDE.md`
- `tests/test_dashboard.py`

**Files modified:**

- `pyproject.toml` (added `validate-dashboard-queries` script)
- `README.md` (added local dashboard validation instructions)

**Implementation highlights:**

- Four independently executable SQL queries in `dashboard_queries.sql`
- Local validation via Spark temp views registered from Gold Parquet:
  - `gold_sales_by_product`
  - `gold_revenue_by_customer`
  - `gold_customer_segmentation`
- Reconciliation checks ensuring dashboard queries do not alter Gold totals
- Filter guidance documented for Databricks (not embedded in base SQL)
- Databricks dashboard tile/visualization setup documented in `DASHBOARD_GUIDE.md`

**YOUR EVALUATION:**

✓ What was good:

- Dashboard consumes Gold only; no CSV/Bronze/Silver bypass.
- Same SQL used for local validation and Databricks dashboard tiles.
- Three mandatory visualizations supported with documented configuration.
- Optional fourth KPI tile added without expanding dashboard scope excessively.
- Local validation and tests verify business behavior, not just execution.
- Completed layers were not modified.

✗ What needed fixing:

- Initial SQL section parser split query titles from SQL bodies; corrected
  before tests passed.
- Filters are documented for Databricks but not implemented in base SQL
  (intentional, but requires clear guide/documentation).

**WHAT WAS ACCEPTED:**

- Gold-backed SQL query file as the single business-logic source.
- Local Spark validation CLI instead of a separate Streamlit UI.
- Reuse of existing Gold configuration (`config/gold_config.yaml`) for paths.
- Optional Total Revenue KPI as a fourth tile.
- Visualization-level filter design documented in `DASHBOARD_GUIDE.md`.
- Temp view naming aligned to Gold dataset names (`gold_sales_by_product`, etc.).

**WHAT WAS CHANGED:**

- SQL query loader/parser adjusted after title/SQL sections were parsed
  incorrectly on first attempt.
- Filter approach split into:
  - unfiltered base queries for local validation
  - Databricks parameter wrappers documented separately in the guide

**WHAT WAS REJECTED:**

- Streamlit or other local interactive dashboard UI (not required; Databricks SQL
  Dashboard is the intended presentation layer).
- Reading Bronze/Silver/CSV directly in dashboard queries.
- Date-based dashboard filters (Gold outputs do not expose an appropriate date
  field for dashboard filtering).
- Daily/Weekly Trends dashboard exposure (Gold dataset not implemented).

No other material AI-generated implementation was rejected.

**HUMAN DECISION:**

Decision not yet recorded.

---

## Top 10 Products by Revenue

**Gold source:** `gold_sales_by_product` (from `{gold_root}/sales_by_product`)

**SQL logic:**

- Selects product fields from Gold Sales by Product aggregation
- Orders by `total_revenue DESC, product_id ASC`
- Limits to 10 rows

**Why Gold, not Silver/Bronze:**

- Gold already provides business-valid, aggregated product revenue.
- Dashboard should not recompute revenue from raw or quality-flagged lower layers.

**Visualization:** Bar chart

- X-axis: `product_name`
- Y-axis: `total_revenue`

**Validation performed:**

- Row count `<= 10`
- Descending revenue sort verified
- No duplicate `product_id`
- Non-negative `total_revenue`
- Top 10 revenue sum `<=` total Gold product revenue

---

## Customer Revenue Distribution

**Gold source:** `gold_revenue_by_customer` (from `{gold_root}/revenue_by_customer`)

**SQL logic:**

- Returns one row per customer with `total_revenue`
- Uses actual aggregated customer revenue from Gold
- Does not use source `lifetime_value`

**Granularity:** customer-level (not aggregated to one summary row)

**Visualization:** Histogram

- Value field: `total_revenue`

**Validation performed:**

- `customer_id` uniqueness
- Multiple customer rows present in fixture/full-data runs
- Dashboard customer revenue total reconciles to Gold customer revenue total

**Important distinction:**

- `total_revenue` = actual realized revenue from valid orders
- `lifetime_value` / `lifetime_value_actual` are present in the query output but
  the histogram uses `total_revenue`, not estimated lifetime value

---

## Customer Segmentation

**Gold source:** `gold_customer_segmentation` (from `{gold_root}/customer_segmentation`)

**SQL logic:**

- Selects `segment_type`, `customer_count`, `avg_revenue`, `total_revenue`
- Orders by `segment_type`

**Expected segments:**

- High-Value
- Repeat
- One-Time
- Inactive

**Visualization:** Pie chart

- Category: `segment_type`
- Value: `customer_count`

**Validation performed:**

- `segment_type` uniqueness
- Segment types subset of expected values
- Non-negative `customer_count` and `total_revenue`
- Segmentation revenue and customer counts reconcile with Gold

---

## Filters

Filters were **documented for Databricks dashboard configuration** in
`DASHBOARD_GUIDE.md`. They were **not implemented in the base
`dashboard_queries.sql` file** used for local validation.

### Filter: Product Category

**Field:** `category`  
**Type:** single-select or multi-select (documented)  
**Visualization(s):** Top 10 Products by Revenue  
**Why it was selected:** Product category is available in Gold Sales by Product
and supports useful product ranking analysis.  
**How it was validated:** Documented as a Databricks query wrapper with
`:product_category` parameter; not executed as embedded base SQL locally.

### Filter: Customer Segment

**Field:** `customer_segment`  
**Type:** single-select or multi-select (documented)  
**Visualization(s):** Customer Revenue Distribution  
**Why it was selected:** Gold Revenue by Customer retains source customer
segment attribute for business filtering.  
**How it was validated:** Documented as a Databricks query wrapper with
`:customer_segment` parameter; not embedded in base local SQL.

### Filter: Segment Type

**Field:** `segment_type`  
**Type:** single-select or multi-select (documented)  
**Visualization(s):** Customer Segmentation  
**Why it was selected:** Matches the derived segmentation pie chart dimension.  
**How it was validated:** Documented as a Databricks query wrapper with
`:segment_type` parameter; not embedded in base local SQL.

### Filter: Revenue Range

**Field:** `total_revenue`  
**Type:** numeric range (documented)  
**Visualization(s):** Customer Revenue Distribution  
**Why it was selected:** Supports inspecting customer revenue bands in the
histogram visualization.  
**How it was validated:** Documented as optional `:min_revenue` / `:max_revenue`
wrappers; not embedded in base local SQL.

### Filter not added: Date

**Reason:** Gold dashboard inputs do not expose an appropriate date field; date
filtering was intentionally not invented.

---

## Local vs Databricks Design

**LOCAL:**

- Dashboard SQL executed/validated through Spark
- Gold Parquet registered as temp views
- Query results inspected via validation CLI and tests
- Business logic validated without building a local dashboard UI

**DATABRICKS:**

- Same base SQL queries used for dashboard tiles
- Visualizations configured in Databricks SQL Dashboard
- Filters applied via documented parameter wrappers at visualization level

**Design principle:**

SAME BUSINESS LOGIC  
DIFFERENT PRESENTATION / ENVIRONMENT CONFIGURATION

The interactive dashboard UI itself is Databricks-specific. No local Streamlit or
equivalent interactive dashboard was implemented.

**Databricks dashboard creation:** Not performed in Cursor.

---

## Prompt 3: Dashboard Testing and Validation

**PROMPT SENT:**

Not performed as a separate prompt in recorded project history.  
Testing and validation execution occurred during Prompt 2 implementation.

**AI RESPONSE SUMMARY:**

Created `tests/test_dashboard.py` and executed local validation against both
controlled fixtures and existing Gold outputs.

**YOUR EVALUATION:**

✓ What passed:

- `PYTHONPATH=src python3 -m pytest tests/test_dashboard.py -q`
  → **6 passed in 41.87s** (with OpenJDK 17)
- `PYTHONPATH=src python3 src/dashboard/validate_dashboard_queries.py`
  → success on existing Gold data

✗ What failed:

- Initial test run failed before SQL query parser fix (queries not loaded
  correctly from section headers)

**Actual results documented:**

| Check | Result |
|-------|--------|
| Top 10 ordering | Pass (descending by revenue) |
| Top 10 row limit | Pass (`<= 10` rows) |
| Customer uniqueness | Pass (`customer_id` unique) |
| Segmentation types | Pass (includes High-Value, Inactive; subset of expected set) |
| Segmentation reconciliation | Pass (segment revenue = customer revenue in tests) |
| Full-data customer revenue total | **85,064,788.93** |
| Full-data segmentation revenue total | **85,064,788.93** |
| Total Revenue KPI | **85,064,788.93** |
| Local SQL execution | Pass |
| Missing Gold input failure | Pass (`DashboardError` raised) |

**Full-data validation summary (local run):**

- `gold_sales_by_product_rows`: 500
- `gold_revenue_by_customer_rows`: 9940
- `gold_customer_segmentation_rows`: 4
- `top_10_products_rows`: 10
- `customer_revenue_rows`: 9940
- `customer_segmentation_rows`: 4
- `total_revenue_kpi`: 85064788.93

---

## Debugging and Corrections

### Issue 1

**Problem:**  
Dashboard query loader failed to associate SQL bodies with section titles.

**Root Cause:**  
Initial parser split on separator lines in a way that isolated title comments
from their query SQL blocks.

**AI Assistance:**  
Identified from failed query loading/tests and replaced parser with section regex
matching title block + SQL body together.

**Fix:**  
Updated `load_dashboard_queries()` in `dashboard_utils.py` to parse
`-- N. Title` sections with following SQL as one unit.

**Validation:**  
Dashboard tests passed after parser fix.

---

## Accept / Modify / Reject

### Accepted

- **Gold-only dashboard inputs** — reused existing business-ready aggregations
  without duplicating Gold logic in dashboard SQL.
- **Spark SQL query file + local validation CLI** — matched project conventions
  and supported Databricks portability.
- **Optional Total Revenue KPI** — satisfied 3+ tile requirement with minimal
  added complexity.
- **Reuse of Gold config/paths** — avoided introducing a second configuration
  framework.

### Modified

- **Filter implementation approach** — accepted filter requirement but implemented
  as documented Databricks visualization-level wrappers rather than embedding
  parameters in base local SQL, because local Spark does not use Databricks dashboard
  parameter syntax the same way.
- **SQL parser implementation** — adjusted after first loading approach failed.

### Rejected

- **Streamlit/local interactive dashboard** — rejected because assignment expects
  Databricks SQL Dashboard as the presentation layer and explicitly said not to
  build Streamlit unless required.
- **Bronze/Silver/CSV dashboard reads** — rejected because they violate medallion
  boundaries and would duplicate quality/eligibility logic already handled in
  Gold.
- **Date filters** — rejected because no appropriate Gold date dimension exists
  for dashboard filtering.
- **Daily/Weekly Trends tile** — rejected because corresponding Gold output was
  not implemented.

---

## Assignment Gap Scan

| Artifact | Status |
|----------|--------|
| Sample data generator | COMPLETED |
| Bronze ingestion | COMPLETED |
| Silver quality checks | COMPLETED |
| Gold aggregations | COMPLETED |
| Dashboard queries | COMPLETED |
| Dashboard documentation (`DASHBOARD_GUIDE.md`) | COMPLETED |
| Database schema/setup (`database/`) | MISSING |
| Seed/sample data | COMPLETED (`data/`, generated CSV + pipeline outputs) |
| Input validation | COMPLETED (layer-level validation exists) |
| Error handling | COMPLETED (layer-level error handling exists) |
| Data quality reporting | COMPLETED (Silver `quality_metrics`) |
| Tests | COMPLETED (includes `tests/test_dashboard.py`) |
| README | COMPLETED (partial; expanded for Gold/Dashboard execution) |
| Prompt history (`ai-prompts/`) | COMPLETED (this file completes dashboard prompt history) |
| Requirements analysis (`requirements-analysis.md`) | MISSING |
| Design notes (`design-notes.md`) | MISSING |
| Data model (`data-model.md`) | MISSING |
| Data quality strategy (`data-quality-strategy.md`) | MISSING |
| Debugging notes (`debugging-notes.md`) | MISSING |
| Reflection (`reflection.md`) | MISSING |
| Final AI usage summary (`final-ai-usage-summary.md`) | MISSING |
| Candidate info (`candidate-info.md`) | MISSING |
| Tool workflow (`tool-workflow.md`) | MISSING |
| Databricks Dashboard UI creation | NEEDS MANUAL ACTION |
| Silver `05_quality_business_logic.py` (fourth quality check file) | MISSING (pre-existing Silver gap; not modified during dashboard work) |

---

## Databricks Manual Step

Databricks Dashboard creation/configuration is a manual workspace step.

Cursor created:

- `src/dashboard/dashboard_queries.sql`
- local validation tooling
- `src/dashboard/DASHBOARD_GUIDE.md`

Cursor did **not** create the Databricks SQL Dashboard UI.

Manual steps (from `DASHBOARD_GUIDE.md`):

1. Ensure Gold datasets are available in Databricks.
2. Create SQL queries/tables referencing:
   - `gold_sales_by_product`
   - `gold_revenue_by_customer`
   - `gold_customer_segmentation`
3. Create dashboard **E-Commerce Sales Analytics Dashboard**.
4. Add tiles:
   - Top 10 Products by Revenue (bar chart)
   - Customer Revenue Distribution (histogram)
   - Customer Segmentation (pie chart)
   - Optional Total Revenue KPI
5. Configure visualization fields per guide.
6. Add visualization-level filters using documented parameter wrappers.
7. Save/publish dashboard.

---

## Final Evaluation

### What AI helped with most

- Translating assignment dashboard requirements into a Gold-backed SQL query
  structure quickly.
- Creating local Spark validation and pytest coverage aligned with existing layer
  patterns.
- Documenting Databricks tile/filter configuration without overbuilding a local UI.

### What AI got wrong

- Initial SQL section parsing logic did not correctly bind query titles to SQL
  bodies, causing early validation failure.

### What I changed

- Parser logic for loading dashboard SQL sections.
- Filter strategy split between base local SQL and documented Databricks wrappers.

### What I rejected

- Streamlit/local dashboard UI.
- Non-Gold data sources for dashboard queries.
- Date filters and Daily/Weekly Trends exposure without corresponding Gold outputs.

### How I validated AI output

- Ran `tests/test_dashboard.py` locally.
- Ran `validate_dashboard_queries.py` against existing Gold outputs.
- Verified reconciliation of customer/segmentation revenue totals with Gold.
- Confirmed dashboard SQL reads Gold temp views only.

### What I learned

- Dashboard layers should reuse Gold business semantics rather than recomputing
  from lower layers.
- Local validation can validate SQL/business logic without reproducing the
  Databricks UI.
- Filters should be documented honestly as visualization-level when they are not
  embedded in shared base SQL.

### What I would improve

- Add optional filtered-query variants as separate named queries if Databricks
  setup needs copy/paste-free deployment.
- Perform actual Databricks dashboard creation to validate tile/filter behavior
  in the target workspace.
- Complete missing assignment documentation artifacts outside the dashboard code
  path (requirements analysis, design notes, reflection, etc.).

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

- Decision not yet recorded (Prompt 1 requirements stage).
- Decision not yet recorded (Prompt 2 acceptance/sign-off).
- Databricks dashboard UI creation deferred as manual workspace action.

---

## Accuracy Notes

Documented from actual dashboard implementation artifacts, tests, and executed
local validation runs.

Not performed:

- Databricks SQL Dashboard UI creation
- Databricks filter/widget execution validation
- Dashboard screenshots

Not verified:

- Explicit human approval decisions beyond implementation-prompt guidance
