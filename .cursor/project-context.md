# Project Context (Cursor)

Persistent summary for AI-assisted sessions. Detailed rules live in
`.cursor/rules/*.mdc`.

## Purpose

Databricks Medallion Architecture assessment for synthetic e-commerce data:

CSV → Bronze → Silver → Gold → Databricks SQL Dashboard

## Completed Layers

- Data Generation (`src/data_generation/`)
- Bronze (`src/bronze/`)
- Silver (`src/silver/`) — four quality checks including business logic
- Gold (`src/gold/`) — four aggregations (including daily/weekly trends)
- Dashboard (`src/dashboard/`)

## Key Conventions

- YAML + Pydantic configuration per layer
- PySpark transformations; local and Databricks share business logic
- Silver flags invalid rows; does not delete Bronze records
- Gold consumes Silver PASS rows only

## Next Reviewer Actions

- Complete personal fields in `candidate-info.md`
- Verify Databricks execution manually (`database/setup-notes.md`)
