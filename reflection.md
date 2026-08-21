# Reflection

## What Worked

- **Layered architecture with strict boundaries** kept Bronze raw, Silver
  quality-focused, and Gold analytics-focused without cross-contamination.
- **Configuration-driven paths** allowed the same Python entry points for local
  and Databricks-oriented execution.
- **Deterministic data generation** with a documented anomaly ledger made Silver
  quality metrics explainable and testable.
- **Incremental delivery** (Data Gen → Bronze → Silver → Gold → Dashboard) matched
  assessment staging and simplified debugging.

## What Required Correction

- Gold decimal casting and reconciliation logic needed refinement after first
  pipeline run.
- Dashboard SQL parsing required a dedicated section parser.
- Final gap analysis identified missing submission artifacts (business logic check,
  database docs, lifecycle documentation) rather than core pipeline logic gaps.

## AI Strengths

- Rapid scaffolding following existing patterns (YAML + Pydantic, shared utils).
- Consistent test fixture generation and documentation drafts.
- Useful gap analysis and structured remediation plans.

## AI Weaknesses

- Occasionally proposed scope beyond assignment (e.g., extra aggregations, extra
  quality rules) requiring human pruning.
- Cannot verify Databricks workspace execution without actual environment access.
- Historical prompt/decision details incomplete unless explicitly recorded.

## Human Validation

- pytest served as the primary acceptance gate for each layer.
- Pipeline CLI smoke runs validated row counts and reconciliation.
- Architectural decisions (three Gold tables, no Daily/Weekly Trends, dashboard
  filter strategy) were enforced manually.

## Lessons Learned

1. Record human decisions in `ai-prompts/` evaluations as work progresses.
2. Add submission artifacts (database schema, sample CSV tracking, lifecycle docs)
   early, not only at the end.
3. Keep quality-check metrics aligned with assignment nomenclature (business logic
   vs internal type validation).

## What Would Be Improved

- Run Databricks verification earlier and capture execution evidence.
- Add full medallion integration test from the start (now added in gap remediation).
- Reduce duplication between `data/landing` and `data/` CSV paths with a single
  documented convention.
