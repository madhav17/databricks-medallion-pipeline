"""Orchestrate Bronze ingestion for all source datasets."""

from __future__ import annotations

import sys

from bronze.config_loader import default_config_path, load_config
from bronze.ingestion_utils import BronzeIngestionError, configure_logging, run_bronze_ingestion


def main() -> int:
    configure_logging()
    config = load_config(default_config_path())
    results = run_bronze_ingestion(config)

    print("Bronze ingestion summary:")
    for result in results:
        print(
            f"- {result.dataset_name}: status={result.status}, "
            f"source_rows={result.source_row_count}, "
            f"bronze_rows={result.bronze_row_count}, "
            f"duration_seconds={result.ingestion_duration_seconds:.3f}"
        )
    print(f"metadata_path={config.metadata_path()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BronzeIngestionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
