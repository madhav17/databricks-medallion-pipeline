# AI Prompts — Bronze Layer

## Prompt 1: Bronze Layer Implementation

**PROMPT SENT:**

You are a Senior Data Engineer implementing the Bronze layer
of our Databricks Medallion Architecture assessment.

IMPORTANT:
Before making any changes, inspect the existing project structure,
existing data-generation implementation, configuration files,
documentation, .cursor instructions, and the generated CSV files.

Use the existing project conventions wherever possible.

Do not redesign the overall architecture.

============================================================
1. OBJECTIVE
============================================================

Implement the Bronze layer for the already-generated source data.

The source files are:

data/
├── customers.csv
├── orders.csv
└── products.csv

The Bronze layer must implement:

CSV
  ↓
PySpark
  ↓
Explicit Schema
  ↓
Basic Input Validation
  ↓
Parquet
  ↓
Bronze Dataset

The physical Bronze storage format MUST be Parquet.

Do NOT use Delta as the Bronze storage format for this
implementation.

Do NOT implement Silver, Gold, or Dashboard functionality.

[Prompt continued exactly in chat with sections 2 through 28, including assignment requirements, raw-data preservation rules, explicit schemas, validation expectations, local/Databricks compatibility, required structure/scripts/tests, documentation updates, acceptance criteria, and final response format.]

**AI RESPONSE SUMMARY:**

Implemented a Bronze ingestion module under `src/bronze/` using explicit PySpark schemas, structural CSV validation, CSV→Parquet ingestion, post-write schema and row-count verification, and separate ingestion metadata writing. Added dataset-specific scripts (`01_ingest_customers.py`, `02_ingest_orders.py`, `03_ingest_products.py`) and orchestrator (`ingest_all.py`). Added configurable path handling via YAML + Pydantic (`config/bronze_config.yaml`, `src/bronze/config.py`, `src/bronze/config_loader.py`) with local/Databricks compatibility and optional table registration. Added focused Bronze tests and Bronze notes documentation.

**YOUR EVALUATION:**

✓ **What was good:**
- Follows required Bronze-only scope and preserves raw data semantics.
- Uses explicit schemas with consistent decimal handling (`DecimalType(10,2)`).
- Implements structural input validation and fail-fast behavior in orchestrator.
- Stores ingestion metadata separately from business datasets.
- Uses overwrite mode for idempotent local reruns.

✗ **What needed fixing:**
- Local Spark execution in this environment is blocked by Java/Spark compatibility issues (`UnsupportedOperationException: getSubject is not supported` and initial stale `SPARK_HOME`), preventing successful local test/pipeline execution verification.
- Prompt history entry does not yet include the full exact prompt text verbatim; it references the exact prompt location in chat.

△ **Missing:**
- Verified passing runtime results for Bronze tests and full ingestion in this machine (blocked by environment-level Spark/JDK issue).
- Explicit human acceptance/rejection decision for this Bronze implementation.

**Human decision:** Decision not yet recorded.

**Result:** Bronze implementation completed; execution validation partially blocked by local Spark/JDK environment incompatibility.

**Files created/modified:**
- Created: `config/bronze_config.yaml`
- Created: `src/bronze/__init__.py`
- Created: `src/bronze/schemas.py`
- Created: `src/bronze/config.py`
- Created: `src/bronze/config_loader.py`
- Created: `src/bronze/ingestion_utils.py`
- Created: `src/bronze/01_ingest_customers.py`
- Created: `src/bronze/02_ingest_orders.py`
- Created: `src/bronze/03_ingest_products.py`
- Created: `src/bronze/ingest_all.py`
- Created: `src/bronze/BRONZE_LAYER_NOTES.md`
- Created: `tests/fixtures/bronze/customers.csv`
- Created: `tests/fixtures/bronze/orders.csv`
- Created: `tests/fixtures/bronze/products.csv`
- Created: `tests/test_bronze.py`
- Modified: `pyproject.toml`
- Modified: `ai-prompts/bronze-layer.md`
