# Task Breakdown

Tasks defined for Cursor-assisted delivery of the medallion pipeline.

## Phase Overview

| Phase | Status | Key deliverables | Primary paths |
|-------|--------|------------------|---------------|
| 1. Data Generation | Complete | CSV files, anomaly ledger, validation CLI | `src/data_generation/` |
| 2. Bronze | Complete | Parquet datasets, ingestion metadata | `src/bronze/` |
| 3. Silver | Complete | Quality flags, metrics report (5 checks) | `src/silver/` |
| 4. Gold | Complete | Four aggregation Parquet datasets | `src/gold/` |
| 5. Dashboard | Complete | SQL queries, validation CLI, setup guide | `src/dashboard/` |
| 6. Testing | Complete | Unit, integration, medallion e2e tests | `tests/` |
| 7. Lifecycle docs | Complete | Requirements, design, reflection, AI prompts | repo root, `ai-prompts/` |
| 8. Database artifacts | Complete | Schema SQL, seed/setup notes | `database/` |
| 9. Gap remediation | Complete | Business logic check, fourth Gold aggregation, docs | multiple |
| 10. Databricks verification | Not verified | Manual workspace run + SQL dashboard UI | `database/setup-notes.md` |

## Detailed Task List

### Phase 1 — Data Generation

- [x] Design deterministic generator with config + seed
- [x] Inject mandatory anomalies (NULL, duplicates, orphan FKs)
- [x] Write CSVs and validation reports
- [x] Document generation strategy (`DATA_GENERATION_NOTES.md`)

### Phase 2 — Bronze

- [x] Define explicit PySpark schemas
- [x] Implement per-dataset ingest scripts + orchestrator
- [x] Capture ingestion metadata (row counts, timestamps)
- [x] Preserve raw anomalies (no cleansing)
- [x] Add Bronze pytest coverage

### Phase 3 — Silver

- [x] Implement completeness, uniqueness, RI, business logic checks
- [x] Add type/schema validation gate
- [x] Flag rows with `quality_check_result` / `quality_check_reason`
- [x] Emit `quality_metrics` Parquet
- [x] Add Silver pytest coverage

### Phase 4 — Gold

- [x] Implement sales by product aggregation
- [x] Implement revenue by customer aggregation
- [x] Implement customer segmentation aggregation
- [x] Implement daily/weekly trends aggregation (`03_daily_weekly_trends.sql`)
- [x] Add revenue reconciliation validation
- [x] Add Gold pytest coverage

### Phase 5 — Dashboard

- [x] Author three required visualization queries + optional KPI
- [x] Document Databricks tile setup (`DASHBOARD_GUIDE.md`)
- [x] Add dashboard SQL validation tests

### Phase 6 — Testing and Validation

- [x] Layer unit/integration tests
- [x] Medallion end-to-end test (`test_medallion_e2e.py`)
- [x] Full pytest suite (51 tests passing locally)

### Phase 7 — Documentation and AI Artifacts

- [x] Layer notes (Bronze, Silver, Gold, Dashboard, Data Gen)
- [x] Lifecycle docs (requirements, design, reflection, tool-workflow)
- [x] AI prompt history by activity (`ai-prompts/`)
- [x] Cursor workflow folder (`tool-specific/cursor-workflow/`)

### Phase 8 — Submission Readiness

- [x] Final compliance audit against assignment PDF
- [ ] Complete `candidate-info.md` personal fields (candidate action)
- [ ] Run pipeline on Databricks Community Edition (manual)
- [ ] Create Databricks SQL Dashboard with 3+ tiles (manual)

## Cursor Usage Pattern Per Phase

1. Load context (rules + spec + relevant layer notes)
2. Prompt with bounded scope ("implement X in Silver only")
3. Run pytest / CLI validation
4. Record prompt + decision in `ai-prompts/<layer>.md`
5. Mark phase complete in rules and task breakdown

## Related Files

- `.cursor/task-breakdown.md` — working copy used during development
- `tool-workflow.md` — Part A workflow summary
- `final-ai-usage-summary.md` — AI usage across lifecycle
