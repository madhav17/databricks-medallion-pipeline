"""Bronze ingestion entry point for orders."""

from __future__ import annotations

import sys
import uuid

from bronze.config_loader import default_config_path, load_config
from bronze.ingestion_utils import (
    BronzeIngestionError,
    configure_logging,
    get_spark_session,
    ingest_orders,
    write_ingestion_metadata,
)


def main() -> int:
    configure_logging()
    config = load_config(default_config_path())
    spark = get_spark_session(config)
    run_id = str(uuid.uuid4())

    result = ingest_orders(spark, config, run_id)
    write_ingestion_metadata(spark, config, [result])

    if result.status != "SUCCESS":
        raise BronzeIngestionError(result.error_message or "Order ingestion failed")

    print(
        f"orders ingestion succeeded: "
        f"source_rows={result.source_row_count}, "
        f"bronze_rows={result.bronze_row_count}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BronzeIngestionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
