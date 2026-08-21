# Tool Workflow (Cursor AI-Assisted Development)

This documents the actual workflow evidenced by repository structure, layer notes,
and `ai-prompts/` history. Prompt text is preserved in layer-specific files; this
document summarizes process only.

## Workflow Stages

| Stage | Activity | Primary artifacts |
|-------|----------|-------------------|
| 1. Requirement analysis | Read assignment + define scope | `.cursor/rules/`, `requirements-analysis.md` |
| 2. Architecture design | Medallion layer boundaries | `design-notes.md`, `.cursor/rules/03-architecture.mdc` |
| 3. Data generation | Synthetic CSV + anomalies | `src/data_generation/`, `ai-prompts/data-generation.md` |
| 4. Bronze | CSV ingestion | `src/bronze/`, `ai-prompts/bronze-layer.md` |
| 5. Silver | Quality checks + metrics | `src/silver/`, `ai-prompts/silver-layer.md` |
| 6. Gold | Aggregations | `src/gold/`, `ai-prompts/gold-layer.md` |
| 7. Dashboard | SQL query layer | `src/dashboard/`, `ai-prompts/dashboard.md` |
| 8. Validation | pytest + CLI smoke runs | `tests/` |
| 9. Debugging | Fix runtime/test failures | `debugging-notes.md` |
| 10. Documentation | Layer notes + lifecycle docs | repo root, `database/`, `reports/` |

## How Cursor Was Used

1. **Persistent rules:** `.cursor/rules/*.mdc` encode project context, architecture
   boundaries, and coding standards for each session.
2. **Layer-by-layer implementation:** Each medallion stage implemented in separate
   focused sessions with dedicated `ai-prompts/<layer>.md` files.
3. **Read-before-write:** AI inspected existing modules before extending patterns
   (YAML + Pydantic config, shared utils, pytest fixtures).
4. **Human review:** Generated code validated with pytest and pipeline CLI runs
   before acceptance.
5. **Gap remediation:** Final gap analysis drove targeted additions (business logic
   check, database artifacts, lifecycle documentation) without redesigning
   completed layers.

## Human Decisions (Documented Where Known)

| Decision | Status | Reference |
|----------|--------|-----------|
| Gold includes four aggregations per Common Technical Requirements | ACCEPTED | `src/gold/GOLD_LAYER_NOTES.md`, `requirements-analysis.md` |
| Dashboard reads Gold, not Silver/Bronze | ACCEPTED | `src/dashboard/DASHBOARD_GUIDE.md` |
| Same business logic local and Databricks | ACCEPTED | Layer notes across Bronze–Dashboard |
| Separate `ai-prompts/` file per layer | ACCEPTED | `ai-prompts/` directory structure |
| Synthetic data only | ACCEPTED | `src/data_generation/DATA_GENERATION_NOTES.md` |

Decisions not recorded in repository history are marked explicitly in individual
`ai-prompts/*.md` evaluation sections.

## Part A Checklist (Assignment PDF §6)

| Topic | How it was addressed |
|-------|----------------------|
| Primary AI tool | Cursor (see `candidate-info.md`, `.cursor/rules/`) |
| Project context | Persistent `.cursor/rules/*.mdc`, `.cursor/project-spec.md` |
| Requirement analysis | `requirements-analysis.md`, assignment PDF cross-check |
| Pipeline design | `design-notes.md`, layer notes, architecture rules |
| Code generation | Layer-by-layer implementation with pytest validation |
| Validation of AI output | pytest suite, CLI smoke runs, reconciliation checks |
| Testing / debugging | `tests/`, `debugging-notes.md`, `ai-prompts/debugging.md` |
| Data quality checks | Silver metrics + `data-quality-strategy.md` |
| PII avoidance | Synthetic data only; no real customer PII in repo or prompts |
| Production reuse | Config-driven paths, shared local/Databricks logic, idempotent writes |
| Lessons learned | `reflection.md`, `final-ai-usage-summary.md` |

## Validation Discipline

- Do not fabricate test or execution results (`.cursor/rules/09-ai-assisted-development.mdc`)
- Run pytest after behavioral changes
- Record actual outcomes in layer notes and prompt evaluations where available
