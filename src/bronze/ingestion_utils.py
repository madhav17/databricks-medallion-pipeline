"""Shared utilities for Bronze CSV-to-Parquet ingestion."""

from __future__ import annotations

import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType, TimestampType

from bronze.config import BronzeConfig
from bronze.schemas import DATASET_SCHEMAS

logger = logging.getLogger(__name__)

INGESTION_ORDER = ("customers", "orders", "products")


INGESTION_METADATA_SCHEMA = StructType(
    [
        StructField("dataset_name", StringType(), nullable=False),
        StructField("source_file", StringType(), nullable=False),
        StructField("source_path", StringType(), nullable=False),
        StructField("bronze_path", StringType(), nullable=False),
        StructField("source_row_count", LongType(), nullable=False),
        StructField("bronze_row_count", LongType(), nullable=False),
        StructField("ingestion_timestamp", TimestampType(), nullable=False),
        StructField("status", StringType(), nullable=False),
        StructField("run_id", StringType(), nullable=False),
        StructField("ingestion_duration_seconds", DoubleType(), nullable=False),
        StructField("source_file_size_bytes", LongType(), nullable=True),
        StructField("error_message", StringType(), nullable=True),
    ]
)


class BronzeIngestionError(Exception):
    """Raised when Bronze ingestion fails for a dataset or the overall pipeline."""


@dataclass(frozen=True)
class IngestionResult:
    dataset_name: str
    source_file: str
    source_path: str
    bronze_path: str
    source_row_count: int
    bronze_row_count: int
    ingestion_timestamp: datetime
    status: str
    run_id: str
    ingestion_duration_seconds: float
    source_file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None

    def to_metadata_row(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "source_file": self.source_file,
            "source_path": self.source_path,
            "bronze_path": self.bronze_path,
            "source_row_count": self.source_row_count,
            "bronze_row_count": self.bronze_row_count,
            "ingestion_timestamp": self.ingestion_timestamp,
            "status": self.status,
            "run_id": self.run_id,
            "ingestion_duration_seconds": self.ingestion_duration_seconds,
            "source_file_size_bytes": self.source_file_size_bytes,
            "error_message": self.error_message,
        }


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def get_spark_session(config: BronzeConfig) -> SparkSession:
    """Reuse an active Spark session or create one for local execution."""
    active = SparkSession.getActiveSession()
    if active is not None:
        logger.info("Reusing active SparkSession")
        return active

    _configure_local_spark_runtime()

    logger.info(
        "Creating local SparkSession with master=%s",
        config.spark.local_master,
    )
    return (
        SparkSession.builder.master(config.spark.local_master)
        .appName(config.spark.app_name)
        .getOrCreate()
    )


def _configure_local_spark_runtime() -> None:
    """Configure local Spark/JDK env to use installed compatible runtimes."""
    spark_home = os.environ.get("SPARK_HOME")
    if not spark_home or not Path(spark_home, "bin", "spark-submit").exists():
        local_spark = _detect_local_spark_home()
        if local_spark is not None:
            os.environ["SPARK_HOME"] = str(local_spark)

    # Java 24+ can fail with Hadoop UGI Subject calls; prefer installed Java 17.
    java17 = Path("/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home")
    if java17.exists():
        os.environ["JAVA_HOME"] = str(java17)


def _detect_local_spark_home() -> Optional[Path]:
    candidates = sorted(Path("/opt/homebrew/Cellar/apache-spark").glob("*/libexec"))
    for candidate in reversed(candidates):
        if Path(candidate, "bin", "spark-submit").exists():
            return candidate
    return None


def validate_source_file(source_path: str) -> int:
    """Validate that the source CSV exists and is readable."""
    path = Path(source_path)
    if not path.exists():
        raise BronzeIngestionError(
            f"Source file does not exist for dataset ingestion: {source_path}"
        )
    if not path.is_file():
        raise BronzeIngestionError(
            f"Source path is not a file for dataset ingestion: {source_path}"
        )
    try:
        with path.open("r", encoding="utf-8") as handle:
            handle.read(1)
    except OSError as exc:
        raise BronzeIngestionError(
            f"Source file is not readable for dataset ingestion: {source_path}"
        ) from exc

    return path.stat().st_size


def validate_csv_structure(
    spark: SparkSession,
    source_path: str,
    required_columns: list[str],
    dataset_name: str,
) -> None:
    """Validate CSV header and required columns without business-quality checks."""
    try:
        header_df = (
            spark.read.option("header", True)
            .option("inferSchema", False)
            .csv(source_path)
            .limit(0)
        )
    except Exception as exc:
        raise BronzeIngestionError(
            f"Failed to read CSV header for dataset '{dataset_name}' "
            f"at path '{source_path}'"
        ) from exc

    actual_columns = header_df.columns
    if not actual_columns:
        raise BronzeIngestionError(
            f"CSV header is missing for dataset '{dataset_name}' at path '{source_path}'"
        )

    missing_columns = [
        column for column in required_columns if column not in actual_columns
    ]
    if missing_columns:
        raise BronzeIngestionError(
            f"Missing required columns for dataset '{dataset_name}' at path "
            f"'{source_path}': {missing_columns}"
        )


def read_source_csv(
    spark: SparkSession,
    source_path: str,
    schema: StructType,
    dataset_name: str,
) -> DataFrame:
    """Read a source CSV using an explicit schema and preserve empty-string nulls."""
    try:
        return (
            spark.read.option("header", True)
            .option("nullValue", "")
            .option("dateFormat", "yyyy-MM-dd")
            .schema(schema)
            .csv(source_path)
        )
    except Exception as exc:
        raise BronzeIngestionError(
            f"Spark failed to read source CSV for dataset '{dataset_name}' "
            f"at path '{source_path}'"
        ) from exc


def write_bronze_parquet(
    df: DataFrame,
    bronze_path: str,
    write_mode: str,
    dataset_name: str,
) -> None:
    """Write a Bronze dataset to Parquet without modifying business columns."""
    try:
        df.write.mode(write_mode).parquet(bronze_path)
    except Exception as exc:
        raise BronzeIngestionError(
            f"Failed to write Bronze Parquet for dataset '{dataset_name}' "
            f"to path '{bronze_path}'"
        ) from exc


def verify_bronze_schema(
    bronze_df: DataFrame,
    expected_schema: StructType,
    dataset_name: str,
) -> None:
    """Verify Bronze columns, data types, and ordering after read-back."""
    expected_fields = expected_schema.fields
    actual_fields = bronze_df.schema.fields

    if len(actual_fields) != len(expected_fields):
        raise BronzeIngestionError(
            f"Bronze schema column count mismatch for dataset '{dataset_name}': "
            f"expected {len(expected_fields)}, found {len(actual_fields)}"
        )

    for expected, actual in zip(expected_fields, actual_fields):
        if expected.name != actual.name:
            raise BronzeIngestionError(
                f"Bronze column order mismatch for dataset '{dataset_name}': "
                f"expected '{expected.name}', found '{actual.name}'"
            )
        if expected.dataType != actual.dataType:
            raise BronzeIngestionError(
                f"Bronze data type mismatch for dataset '{dataset_name}' "
                f"column '{expected.name}': expected {expected.dataType}, "
                f"found {actual.dataType}"
            )


def read_bronze_parquet(
    spark: SparkSession,
    bronze_path: str,
    dataset_name: str,
) -> DataFrame:
    """Read Bronze Parquet back for verification."""
    try:
        return spark.read.parquet(bronze_path)
    except Exception as exc:
        raise BronzeIngestionError(
            f"Failed to read Bronze Parquet for dataset '{dataset_name}' "
            f"from path '{bronze_path}'"
        ) from exc


def register_bronze_table(
    spark: SparkSession,
    config: BronzeConfig,
    dataset_name: str,
    bronze_path: str,
) -> None:
    """Optionally register a Bronze Parquet location as a table."""
    if not config.table_registration.enabled:
        return

    catalog = config.table_registration.catalog
    database = config.table_registration.database
    if not catalog or not database:
        raise BronzeIngestionError(
            "Table registration is enabled but catalog/database are not configured"
        )

    table_name = f"{catalog}.{database}.bronze_{dataset_name}"
    logger.info("Registering Bronze table %s at %s", table_name, bronze_path)
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        USING PARQUET
        LOCATION '{bronze_path}'
        """
    )


def ingest_dataset(
    spark: SparkSession,
    config: BronzeConfig,
    dataset_name: str,
    run_id: str,
) -> IngestionResult:
    """Ingest one dataset from CSV to Bronze Parquet with validation."""
    if dataset_name not in DATASET_SCHEMAS:
        raise BronzeIngestionError(f"Unsupported dataset '{dataset_name}'")

    schema = DATASET_SCHEMAS[dataset_name]
    source_file = getattr(config.source_files, dataset_name)
    source_path = config.source_path(dataset_name)
    bronze_path = config.bronze_path(dataset_name)
    required_columns = [field.name for field in schema.fields]
    started_at = time.perf_counter()
    ingestion_timestamp = datetime.now(timezone.utc)

    logger.info(
        "Bronze ingestion started for dataset=%s source_path=%s bronze_path=%s",
        dataset_name,
        source_path,
        bronze_path,
    )

    try:
        source_file_size = validate_source_file(source_path)
        validate_csv_structure(
            spark,
            source_path,
            required_columns,
            dataset_name,
        )

        source_df = read_source_csv(spark, source_path, schema, dataset_name)
        source_row_count = source_df.count()

        write_bronze_parquet(
            source_df,
            bronze_path,
            config.write.mode,
            dataset_name,
        )

        bronze_df = read_bronze_parquet(spark, bronze_path, dataset_name)
        verify_bronze_schema(bronze_df, schema, dataset_name)
        bronze_row_count = bronze_df.count()

        if source_row_count != bronze_row_count:
            raise BronzeIngestionError(
                f"Row count mismatch for dataset '{dataset_name}': "
                f"source={source_row_count}, bronze={bronze_row_count}, "
                f"source_path='{source_path}', bronze_path='{bronze_path}'"
            )

        register_bronze_table(spark, config, dataset_name, bronze_path)

        duration = time.perf_counter() - started_at
        result = IngestionResult(
            dataset_name=dataset_name,
            source_file=source_file,
            source_path=source_path,
            bronze_path=bronze_path,
            source_row_count=source_row_count,
            bronze_row_count=bronze_row_count,
            ingestion_timestamp=ingestion_timestamp,
            status="SUCCESS",
            run_id=run_id,
            ingestion_duration_seconds=duration,
            source_file_size_bytes=source_file_size,
        )

        logger.info(
            "Bronze ingestion completed for dataset=%s status=%s "
            "source_row_count=%s bronze_row_count=%s duration_seconds=%.3f",
            dataset_name,
            result.status,
            result.source_row_count,
            result.bronze_row_count,
            result.ingestion_duration_seconds,
        )
        return result

    except BronzeIngestionError as exc:
        duration = time.perf_counter() - started_at
        logger.error(
            "Bronze ingestion failed for dataset=%s source_path=%s error=%s",
            dataset_name,
            source_path,
            exc,
        )
        return IngestionResult(
            dataset_name=dataset_name,
            source_file=source_file,
            source_path=source_path,
            bronze_path=bronze_path,
            source_row_count=0,
            bronze_row_count=0,
            ingestion_timestamp=ingestion_timestamp,
            status="FAILED",
            run_id=run_id,
            ingestion_duration_seconds=duration,
            source_file_size_bytes=None,
            error_message=str(exc),
        )


def ingest_customers(
    spark: SparkSession,
    config: BronzeConfig,
    run_id: str,
) -> IngestionResult:
    return ingest_dataset(spark, config, "customers", run_id)


def ingest_orders(
    spark: SparkSession,
    config: BronzeConfig,
    run_id: str,
) -> IngestionResult:
    return ingest_dataset(spark, config, "orders", run_id)


def ingest_products(
    spark: SparkSession,
    config: BronzeConfig,
    run_id: str,
) -> IngestionResult:
    return ingest_dataset(spark, config, "products", run_id)


def write_ingestion_metadata(
    spark: SparkSession,
    config: BronzeConfig,
    results: list[IngestionResult],
) -> str:
    """Write ingestion metadata to a separate Bronze metadata location."""
    metadata_path = config.metadata_path()
    metadata_rows = [result.to_metadata_row() for result in results]
    metadata_df = spark.createDataFrame(metadata_rows, schema=INGESTION_METADATA_SCHEMA)
    metadata_df.write.mode(config.write.mode).parquet(metadata_path)
    logger.info("Wrote ingestion metadata to %s", metadata_path)
    return metadata_path


def run_bronze_ingestion(config: BronzeConfig) -> list[IngestionResult]:
    """Run all Bronze ingestions and write metadata."""
    configure_logging()
    run_id = str(uuid.uuid4())
    spark = get_spark_session(config)
    results: list[IngestionResult] = []

    logger.info("Bronze ingestion pipeline started run_id=%s", run_id)

    for dataset_name in INGESTION_ORDER:
        result = ingest_dataset(spark, config, dataset_name, run_id)
        results.append(result)
        if result.status != "SUCCESS":
            write_ingestion_metadata(spark, config, results)
            raise BronzeIngestionError(
                f"Bronze ingestion failed for dataset '{dataset_name}': "
                f"{result.error_message}"
            )

    write_ingestion_metadata(spark, config, results)
    logger.info("Bronze ingestion pipeline completed successfully run_id=%s", run_id)
    return results
