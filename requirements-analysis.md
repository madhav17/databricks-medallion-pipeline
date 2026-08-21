# Requirements Analysis

## Assignment Scope (As Implemented)

| Area | Requirement | Implementation |
|------|-------------|----------------|
| Data Generation | Reproducible synthetic CSV with controlled anomalies | `src/data_generation/` |
| Bronze | Raw CSV → Parquet, schema validation, metadata | `src/bronze/` |
| Silver | Four quality checks, flag invalid rows, metrics | `src/silver/` |
| Gold | Three business aggregations from valid Silver data | `src/gold/` |
| Dashboard | SQL queries over Gold outputs | `src/dashboard/` |
| Testing | Unit, integration, layer validation | `tests/` |
| Documentation | Layer notes, AI prompts, lifecycle docs | repo root + `ai-prompts/` |
| AI Workflow | Prompt history and human evaluation | `ai-prompts/`, `.cursor/rules/` |

## Silver Quality Checks (Required Four)

1. Completeness
2. Uniqueness
3. Referential Integrity
4. Business Logic

Additional structural type/schema validation runs before quality flagging and is
reported separately as `type_validation` in quality metrics.

## Gold Aggregations (Required Three)

1. Sales by Product
2. Revenue by Customer
3. Customer Segmentation

## Dashboard

- SQL queries consuming Gold datasets
- Databricks SQL Dashboard setup documented in `src/dashboard/DASHBOARD_GUIDE.md`
- Filters configured at dashboard UI level (documented, not embedded as fake SQL parameters)

## Testing Expectations

- Deterministic data generation validation
- Layer-specific pytest coverage
- End-to-end medallion integration test (`tests/test_medallion_e2e.py`)

## Known Ambiguities

| Topic | Resolution |
|-------|------------|
| Daily/Weekly Trends aggregation | **Not implemented.** Gold scope limited to three mandatory aggregations documented in `src/gold/GOLD_LAYER_NOTES.md`. Classified as P3 / out of scope unless acceptance criteria explicitly require it. |
| Invalid-record handling | Silver flags rows with `quality_check_result` PASS/FAIL; rows are not deleted. |
| Dashboard filters in SQL | Databricks dashboard filters are UI configuration; base SQL remains filter-free by design. |
| Databricks execution proof | Documented manual steps in `database/setup-notes.md`; not independently verified in this workspace. |
| Sample CSV location | Generator writes to `./data/landing`; Bronze reads `./data/*.csv`. Both paths documented in `database/seed-data-notes.md`. |

## Documentation Deliverables

Lifecycle artifacts at repository root:

- `candidate-info.md`
- `requirements-analysis.md` (this file)
- `design-notes.md`
- `data-model.md`
- `data-quality-strategy.md`
- `tool-workflow.md`
- `debugging-notes.md`
- `reflection.md`
- `final-ai-usage-summary.md`

Database artifacts under `database/`.
