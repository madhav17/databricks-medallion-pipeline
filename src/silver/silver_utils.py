"""Shared utilities for Silver layer quality processing."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, StringType

from bronze.ingestion_utils import _configure_local_spark_runtime
from bronze.schemas import DATASET_SCHEMAS
from silver.config import SilverConfig

logger = logging.getLogger(__name__)


class SilverError(Exception):
    """Raised when Silver processing fails."""


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def get_spark_session(config: SilverConfig) -> SparkSession:
    active = SparkSession.getActiveSession()
    if active is not None:
        logger.info("Reusing active SparkSession")
        return active

    _configure_local_spark_runtime()
    logger.info("Creating local SparkSession with master=%s", config.spark.local_master)
    return (
        SparkSession.builder.master(config.spark.local_master)
        .appName(config.spark.app_name)
        .getOrCreate()
    )


def read_bronze_dataset(
    spark: SparkSession,
    config: SilverConfig,
    dataset_name: str,
) -> DataFrame:
    path = config.bronze_path(dataset_name)
    is_uri_path = "://" in path
    if (not is_uri_path) and (not Path(path).exists()):
        raise SilverError(
            f"Bronze input missing for dataset '{dataset_name}' at path '{path}'"
        )

    try:
        return spark.read.parquet(path)
    except Exception as exc:
        raise SilverError(
            f"Failed to read Bronze Parquet for dataset '{dataset_name}' at path '{path}'"
        ) from exc


def validate_required_columns(df: DataFrame, dataset_name: str) -> None:
    required_columns = [field.name for field in DATASET_SCHEMAS[dataset_name].fields]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise SilverError(
            f"Silver input missing required columns for dataset '{dataset_name}': {missing}"
        )


def init_quality_columns(df: DataFrame) -> DataFrame:
    return (
        df.withColumn(
            "quality_fail_reasons",
            F.array().cast(ArrayType(StringType())),
        )
    )


def append_quality_reason(df: DataFrame, condition, reason: str) -> DataFrame:
    return df.withColumn(
        "quality_fail_reasons",
        F.when(
            condition,
            F.array_union(
                F.col("quality_fail_reasons"),
                F.array(F.lit(reason)),
            ),
        ).otherwise(F.col("quality_fail_reasons")),
    )


def finalize_quality_columns(df: DataFrame) -> DataFrame:
    return (
        df.withColumn(
            "quality_check_result",
            F.when(F.size(F.col("quality_fail_reasons")) == 0, F.lit("PASS"))
            .otherwise(F.lit("FAIL")),
        )
        .withColumn(
            "quality_check_reason",
            F.when(
                F.size(F.col("quality_fail_reasons")) == 0,
                F.lit(""),
            ).otherwise(F.concat_ws("; ", F.col("quality_fail_reasons"))),
        )
    )


def write_silver_dataset(
    df: DataFrame,
    config: SilverConfig,
    dataset_name: str,
) -> None:
    path = config.silver_path(dataset_name)
    try:
        df.write.mode(config.write.mode).parquet(path)
    except Exception as exc:
        raise SilverError(
            f"Failed writing Silver dataset '{dataset_name}' to path '{path}'"
        ) from exc

