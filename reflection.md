# Reflection

## What I Built

- A complete local Databricks-style medallion pipeline for synthetic e-commerce data:
  **CSV → Bronze → Silver → Gold → Dashboard SQL**.
- **Data generation** — reproducible customers (10K), orders (100K), and products (500)
  CSVs with intentional quality anomalies (~460 documented issues).
- **Bronze** — raw CSV ingestion to Parquet with explicit schemas, structural validation,
  and ingestion metadata; no business cleansing.
- **Silver** — five quality checks (completeness, uniqueness, type/schema validation,
  referential integrity, business logic), row-level `quality_check_result` flagging,
  and a metrics report (`quality_metrics` Parquet).
- **Gold** — four aggregation datasets: sales by product, revenue by customer,
  daily/weekly trends, and customer segmentation.
- **Dashboard** — four SQL queries (three required visualizations + optional KPI) with
  local validation via pytest.
- **Tests and docs** — 51 pytest tests, lifecycle artifacts, AI prompt history, and
  database setup documentation.

## How I Used AI (Across the Lifecycle)

1. **Requirement analysis** — used Cursor to read the assignment PDF, map ambiguities
   (Silver check count, Gold aggregation count), and compare against repository evidence.
2. **Architecture design** — enforced medallion boundaries through persistent Cursor
   rules (`.cursor/rules/*.mdc`) and design notes before writing code.
3. **Implementation** — built each layer incrementally (Data Gen → Bronze → Silver →
   Gold → Dashboard), reusing existing patterns (YAML + Pydantic config, shared utils).
4. **Testing** — generated and refined pytest fixtures; used AI to add integration and
   end-to-end tests after core layers were stable.
5. **Debugging** — used AI to diagnose decimal casting, SQL parsing, and reconciliation
   issues; recorded fixes in `debugging-notes.md`.
6. **Documentation** — AI drafted layer notes, lifecycle docs, and prompt history;
   human review removed fabricated claims and marked unverified items explicitly.
7. **Gap remediation** — final compliance audit identified the missing fourth Gold
   aggregation (`03_daily_weekly_trends.sql`) and implemented only that gap without
   rebuilding working layers.

## What AI Helped With Most

- **Scaffolding** — quickly producing module structure, config loaders, and test
  fixtures that matched existing project conventions.
- **Gap analysis** — systematically comparing assignment requirements to repository
  artifacts and producing actionable remediation lists.
- **Documentation drafts** — accelerating layer notes, data model docs, and prompt
  history organization by activity.
- **Test generation** — creating deterministic pytest cases for quality checks,
  Gold reconciliation, and dashboard SQL validation.

## What AI Got Wrong

- **Scope creep** — sometimes proposed extra aggregations, quality rules, or refactors
  beyond assignment requirements; required human pruning.
- **Stale context** — early Cursor rules still said "Silver is next" after Silver was
  implemented; rules needed manual updates as stages completed.
- **Ambiguity handling** — initially excluded `daily_weekly_trends` based on Core
  Acceptance Criteria alone; compliance audit corrected this after comparing Common
  Technical Requirements and Required Repository Structure.
- **Environment claims** — AI cannot verify Databricks workspace execution without
  actual access; those items must remain marked "not verified."
- **Historical prompts** — without explicit recording during early sessions, some
  bronze/debugging prompt text is summarized rather than verbatim.

## How I Validated AI Output

- **pytest** — primary acceptance gate; full suite currently **51 passed**.
- **Pipeline CLI runs** — layer entry points (`ingest_all.py`, `create_silver_tables.py`,
  `create_gold_tables.py`, `validate_dashboard_queries.py`) exercised locally.
- **Reconciliation checks** — Gold pipeline validates that product, customer, and
  segmentation revenue totals match eligible Silver order revenue.
- **Quality metrics** — Silver tests verify intentional anomalies are flagged and
  metrics report pass/fail percentages.
- **No fabrication policy** — `.cursor/rules/09-ai-assisted-development.mdc` and
  project guardrails require reporting actual test outcomes and marking unverified
  Databricks steps explicitly.

## What I Would Improve Next

- Run the full pipeline on **Databricks Community Edition** earlier and capture
  execution evidence (screenshots, job logs, table row counts).
- Create the **Databricks SQL Dashboard UI** (3 tiles) and document the final dashboard URL.
- Complete **candidate-info.md** personal submission fields before final hand-in.
- Backfill **verbatim prompt history** for bronze and debugging sessions where only
  summaries exist today.
- Simplify the **CSV path convention** (`data/landing/` vs `data/`) into one documented
  workflow to reduce setup confusion.

## Reusable Workflow

1. **Set persistent context first** — `.cursor/rules/*.mdc` + `requirements-analysis.md`
   before asking for code.
2. **Implement one medallion layer at a time** — do not mix Silver logic into Bronze or
   Gold logic into Silver.
3. **Validate before accepting** — run pytest and a CLI smoke test after each AI change.
4. **Record decisions immediately** — update `ai-prompts/<layer>.md` with prompt, AI
   summary, what was accepted/rejected, and why.
5. **Resolve assignment ambiguities explicitly** — prefer mandatory Common Technical
   Requirements and Required Repository Structure over narrower acceptance-criteria wording.
6. **Keep paths configuration-driven** — same Python entry points for local and
   Databricks; override via YAML or environment variables.
7. **Treat Databricks-only steps as manual verification** — do not claim dashboard or
   workspace execution without evidence.

This workflow is also summarized in `tool-workflow.md` and
`tool-specific/cursor-workflow/cursor-rules-or-instructions.md`.
