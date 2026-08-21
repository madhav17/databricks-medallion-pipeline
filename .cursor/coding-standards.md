# Coding Standards

Persistent standards are enforced via `.cursor/rules/*.mdc`. Summary:

## General

- Prefer simple, readable, maintainable code over unnecessary abstraction.
- Follow existing module structure and naming patterns.
- Avoid new dependencies unless clearly required.
- Keep behavior configuration-driven, not hardcoded to a specific environment.

## Python

- Use clear function names and small, focused modules.
- Use type hints where appropriate and consistent with existing code.
- Prefer explicit data structures over hidden side effects.
- Keep comments concise and only where they add clarity.

## PySpark

- Use explicit schemas where required by stage behavior.
- Avoid implicit behavior that can drift across environments.
- Keep local and Databricks execution paths unified where possible.
- Avoid embedding environment-specific paths in code.

## Configuration

- Use YAML + Pydantic validation pattern already present in the project.
- Fail fast on invalid configuration.
- Preserve locked/mandatory constraints where implemented.

## Logging and Errors

- Log operational milestones and dataset-level status (not full dataset dumps).
- Raise/propagate actionable exceptions with dataset/path context.
- Do not silently skip required dataset failures.

## Testing

- Add/update tests when behavior changes.
- Keep tests deterministic and fixture-driven where possible.
- Validate row counts, schema behavior, and preservation requirements.
- Do not fabricate pass results; report actual outcomes and blockers.
