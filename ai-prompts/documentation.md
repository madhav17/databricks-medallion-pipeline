# AI Prompts - Documentation

Documentation work driven by assignment submission requirements and final gap
analysis remediation.

## Prompt: Lifecycle and Database Documentation

**PROMPT SENT:**

Final gap analysis — create missing lifecycle documents (`requirements-analysis.md`,
`design-notes.md`, `data-model.md`, `data-quality-strategy.md`, `tool-workflow.md`,
`debugging-notes.md`, `reflection.md`, `final-ai-usage-summary.md`,
`candidate-info.md`) and `database/` artifacts without fabricating history.

**AI RESPONSE SUMMARY:**

Created lifecycle docs from repository evidence (layer notes, tests, configs,
`ai-prompts/`). Marked unverified facts explicitly. Added `database/schema.sql`,
`seed-data-notes.md`, `setup-notes.md`, expanded `README.md`, and `reports/README.md`.

**YOUR EVALUATION:**

### What was good

- Documentation reflects implemented architecture rather than aspirational design.
- Ambiguities (Daily/Weekly Trends, Databricks verification) documented explicitly.

### What needed fixing

- Personal candidate fields remain for human completion in `candidate-info.md`.

### Missing

- Pre-gap-analysis documentation prompts: **Not verified from repository history.**

### Human decision

**ACCEPTED** — submission docs added with evidence-based content only.

---

## Prompt: Final Assignment Compliance Audit (2026-08-21)

**PROMPT SENT:**

Final assignment compliance audit against `ai-prompts/DE_C1_Coding_Evaluation.pdf`.
Compare PDF requirements to repository implementation; implement only genuine gaps;
run tests; produce compliance report. Resolve Silver/Gold count ambiguities from
PDF wording (Common Technical Requirements vs Core Acceptance Criteria vs Required
Repository Structure).

**AI RESPONSE SUMMARY:**

Audit identified one code gap: missing `03_daily_weekly_trends.sql` (Gold fourth
aggregation required by Common Technical Requirements and Required Repository
Structure). Implemented SQL, Gold orchestration, schema validation, tests, and
updated ambiguity documentation. Silver already exceeded four-check minimum (five
checks including type_validation and business_logic). Full pytest: 51 passed.

**YOUR EVALUATION:**

### What was good

- Gap limited to Gold fourth aggregation; no unnecessary rebuild of working layers.
- Ambiguity resolution documented in `requirements-analysis.md` and `GOLD_LAYER_NOTES.md`.

### What needed fixing

- Historical `ai-prompts/gold-layer.md` entries still describe trends as not implemented
  (prior session record; superseded by this implementation).

### Human decision

**ACCEPTED** — implement fourth Gold aggregation per Common Technical Requirements
and Required Repository Structure; preserve three core tables for acceptance criteria.

---

## Prompt: README End-to-End Setup

**PROMPT SENT:**

Expand README with full local runbook for all pipeline stages and testing.

**AI RESPONSE SUMMARY:**

README updated with prerequisites, staged commands, config references, and
documentation index.

**YOUR EVALUATION:**

### What was good

- Single entry point for reviewers to reproduce local pipeline.

### What needed fixing

- CSV path convention (landing vs Bronze source root) requires explicit note.

### Missing

- N/A

### Human decision

**ACCEPTED**

---

## Prompt: Reports and Sample CSV Tracking

**PROMPT SENT:**

Adjust `.gitignore` to track submission evidence (sample CSVs, validation reports)
while ignoring transient pipeline outputs.

**AI RESPONSE SUMMARY:**

Selective `.gitignore` rules for `data/*.csv` and key `reports/*` files; added
`reports/README.md`.

**YOUR EVALUATION:**

### What was good

- Avoids committing large Bronze/Silver/Gold Parquet outputs.

### What needed fixing

- Reviewer must still regenerate pipeline outputs locally for full E2E verification.

### Missing

- N/A

### Human decision

**ACCEPTED**
