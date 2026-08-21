# Cursor Rules and Instructions

This document describes the Cursor rules and instructions used for the medallion
pipeline project. It satisfies the assignment requirement for
`cursor-rules-or-instructions.md` under `tool-specific/cursor-workflow/`.

## Where Rules Live

Cursor persistent rules are stored as Markdown rule files with frontmatter:

```text
.cursor/rules/
├── 01-project-context.mdc
├── 02-requirements.mdc
├── 03-architecture.mdc
├── 04-coding-guidelines.mdc
├── 05-data-generation.mdc
├── 06-bronze-layer.mdc
├── 07-silver-layer.mdc
├── 08-testing.mdc
└── 09-ai-assisted-development.mdc
```

Each `.mdc` file includes:

```yaml
---
description: <short purpose>
alwaysApply: true
---
```

With `alwaysApply: true`, Cursor loads these rules automatically in every session
for this repository. This replaces a legacy single `.cursorrules` file.

## Supporting Cursor Artifacts

| File | Purpose |
|------|---------|
| `.cursor/project-context.md` | Short session primer; points to rules and current layer status |
| `.cursor/project-spec.md` | Functional requirements, non-goals, submission artifact list |
| `.cursor/task-breakdown.md` | Phase-by-phase delivery status |
| `.cursor/architecture.md` | High-level medallion flow pointer |
| `.cursor/coding-standards.md` | Summary of coding/testing standards (mirrors rule 04 and 08) |

Related workflow documentation:

- `tool-workflow.md` — Part A AI workflow summary (repo root)
- `ai-prompts/*.md` — prompt history organized by activity

## Rule Summary

### 01 — Project Context

- Defines assignment purpose, technology stack, and medallion flow.
- Requires local + Databricks-compatible execution.
- Tracks which layers are complete vs planned.

### 02 — Requirements Reference

- Points to authoritative artifacts: layer notes, configs, `ai-prompts/`, assignment PDF.
- Documents dataset sizes, anomaly strategy, Bronze/Silver/Gold expectations, and testing norms.

### 03 — Architecture

- Enforces medallion boundaries:
  - Bronze: raw ingest only
  - Silver: quality checks and flagging
  - Gold: business aggregations
  - Dashboard: reads Gold only
- Prohibits back-porting downstream logic into upstream layers.

### 04 — Coding Guidelines

- Prefer simple, maintainable, configuration-driven code.
- Use type hints, explicit PySpark schemas, actionable logging/errors.
- Update tests when behavior changes; do not fabricate results.

### 05 — Data Generation (Frozen)

- Data generation is complete and should not be modified unless explicitly requested.
- Preserves deterministic seed, anomaly ledger, and validation CLI behavior.

### 06 — Bronze Layer (Frozen)

- Bronze is complete and frozen by default.
- Documents raw-data preservation contract (no cleansing, dedup, or FK filtering).

### 07 — Silver Layer

- Silver consumes Bronze Parquet; implements quality checks and metrics.
- Separates valid/invalid handling via quality flags without deleting rows.

### 08 — Testing

- Unit, integration, and end-to-end test expectations.
- Deterministic fixtures; no machine-specific paths; report actual outcomes.

### 09 — AI-Assisted Development Principles

Key instructions enforced in every session:

1. Inspect the repository before making changes.
2. Do not modify completed stages unnecessarily.
3. Do not fabricate test results, execution results, or human decisions.
4. Preserve intentional data anomalies per stage contracts.
5. Identify assignment ambiguities explicitly instead of silently inventing requirements.
6. Record meaningful interactions under `ai-prompts/`.
7. Human decisions are authoritative over AI suggestions.

## How Rules Were Used in Practice

### Context setting

Before implementation prompts, rules ensured Cursor understood:

- current project stage and frozen layers
- medallion responsibilities
- local vs Databricks path configuration
- submission artifact expectations

### Iteration and rejection

Rules were used to **reject** AI suggestions that:

- added Silver cleansing into Bronze
- proposed optional stretch features not required by the assignment
- modified frozen Data Generation or Bronze without explicit request
- claimed Databricks execution without evidence

### Validation discipline

Rule 09 and rule 08 together required:

- pytest runs after behavioral changes
- explicit "not verified" markers for Databricks-only steps
- prompt history updates with accept/reject rationale

## Example Instruction Patterns That Worked

**Good (specific, bounded):**

> "Implement Silver completeness check for customers.email and orders.customer_id /
> orders.product_id. Flag rows with quality_check_result; do not delete Bronze rows.
> Match existing YAML + Pydantic config pattern."

**Weak (avoided):**

> "Write data quality code."

## Updating Rules

When a layer was completed, corresponding rules and `.cursor/project-context.md`
were updated to prevent Cursor from re-implementing finished stages. After the
final compliance audit, Gold scope was updated to include four aggregations
(including `daily_weekly_trends`).

## Related Assignment Files

| Assignment artifact | Repository location |
|--------------------|---------------------|
| `project-context.md` | `.cursor/project-context.md` and `tool-specific/cursor-workflow/project-context.md` (if present) |
| `spec.md` | `.cursor/project-spec.md` |
| `task-breakdown.md` | `.cursor/task-breakdown.md` |
| `cursor-rules-or-instructions.md` | this file |
