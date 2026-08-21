# Project Context (Cursor)

How project context is provided to Cursor for this repository.

## Primary Context Sources

1. **Persistent rules** — `.cursor/rules/*.mdc` (loaded automatically every session)
2. **This folder** — `tool-specific/cursor-workflow/` (assignment submission artifacts)
3. **Layer notes and configs** — `src/*/NOTES.md`, `config/*.yaml`
4. **Assignment reference** — `ai-prompts/DE_C1_Coding_Evaluation.pdf`

## Purpose

Databricks Medallion Architecture assessment for synthetic e-commerce data:

```text
CSV → Bronze → Silver → Gold → Databricks SQL Dashboard
```

## Current Project Status

| Layer | Location | Status |
|-------|----------|--------|
| Data Generation | `src/data_generation/` | Complete |
| Bronze | `src/bronze/` | Complete (frozen) |
| Silver | `src/silver/` | Complete |
| Gold | `src/gold/` | Complete |
| Dashboard | `src/dashboard/` | Complete (SQL + local validation) |

## Key Conventions Shared With Cursor

- **Configuration-driven paths** — YAML + Pydantic per layer; no hardcoded machine paths
- **Local + Databricks compatible** — same Python entry points; SparkSession reused on Databricks
- **Medallion boundaries** — Bronze preserves raw anomalies; Silver flags; Gold aggregates PASS rows only
- **No fabrication** — test results and Databricks execution must be marked honestly

## Silver Quality Checks

Five checks implemented (assignment requires at least four):

1. Completeness
2. Uniqueness
3. Type/schema validation
4. Referential integrity
5. Business logic

Metrics written to `{silver_root}/quality_metrics`.

## Gold Aggregations

Four datasets implemented:

1. `sales_by_product`
2. `revenue_by_customer`
3. `daily_weekly_trends`
4. `customer_segmentation`

## How Context Is Refreshed Each Session

- Cursor loads `.cursor/rules/*.mdc` via `alwaysApply: true`
- User prompts reference specific files (`@config/bronze_config.yaml`, layer notes, tests)
- Completed layers marked frozen in rules to prevent unnecessary rewrites
- Decisions recorded in `ai-prompts/<activity>.md` and lifecycle docs

## Remaining Manual Steps

- Complete personal fields in `candidate-info.md`
- Verify Databricks execution (`database/setup-notes.md`)
- Create Databricks SQL Dashboard UI (`src/dashboard/DASHBOARD_GUIDE.md`)

## Related Files

| File | Role |
|------|------|
| `spec.md` | Functional specification for Cursor tasks |
| `cursor-rules-or-instructions.md` | Rule inventory and usage |
| `task-breakdown.md` | Phase delivery tracker |
| `.cursor/project-context.md` | Working copy used during development |
