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
