# AI Prompts - Debugging

Cross-layer debugging sessions documented in `debugging-notes.md`. This file
records AI-assisted debugging where verifiable from repository artifacts.

## Session: Local Spark / Java Runtime

**PROMPT SENT:**

Not recorded verbatim. Issue observed during Bronze/Silver local pytest runs with
Spark/Hadoop Java compatibility errors.

**AI RESPONSE SUMMARY:**

Recommended OpenJDK 17 and centralized local Spark runtime configuration in Bronze
ingestion utilities.

**YOUR EVALUATION:**

### What was good

- Identified environment root cause rather than changing pipeline business logic.

### What needed fixing

- Required explicit `JAVA_HOME` documentation for reproducible local runs.

### Missing

- Exact original prompt text: **Not verified from repository history.**

### Human decision

**ACCEPTED** — use OpenJDK 17 and `_configure_local_spark_runtime()`.

---

## Session: Gold Decimal Casting and Reconciliation

**PROMPT SENT:**

Not recorded verbatim. Gold tests/pipeline failed on schema mismatch and revenue
reconciliation.

**AI RESPONSE SUMMARY:**

Added explicit `DECIMAL(10,2)` casts in Gold SQL and semi-join filters to valid
PASS parent dimensions.

**YOUR EVALUATION:**

### What was good

- Fixes aligned with existing Gold design and test assertions.

### What needed fixing

- Initial Gold SQL assumed implicit decimal precision.

### Missing

- Full prompt transcript: **Not verified from repository history.**

### Human decision

**MODIFIED** — accepted reconciliation approach; kept three Gold aggregations only.

---

## Session: Dashboard SQL Parser

**PROMPT SENT:**

Not recorded verbatim. Dashboard query loader failed to parse sectioned SQL file.

**AI RESPONSE SUMMARY:**

Implemented regex section parser preserving titled query blocks.

**YOUR EVALUATION:**

### What was good

- Minimal change localized to `dashboard_utils.py`.

### What needed fixing

- Initial naive string split was insufficient.

### Missing

- Exact prompt: **Not verified from repository history.**

### Human decision

**ACCEPTED**

---

## Session: Silver Business Logic Gap Remediation

**PROMPT SENT:**

Final gap analysis task — implement missing `05_quality_business_logic.py` and
integrate into Silver orchestration/metrics without redesigning other layers.

**AI RESPONSE SUMMARY:**

Implemented business logic rules aligned with `dataset_validator.py`, integrated
into `create_silver_tables.py`, updated tests and documentation.

**YOUR EVALUATION:**

### What was good

- Reused existing quality framework conventions (`quality_check_reason`, metrics).

### What needed fixing

- Metrics and tests needed `business_logic` check rows.

### Missing

- N/A for this remediation session.

### Human decision

**ACCEPTED** — minimal targeted addition per gap analysis.
