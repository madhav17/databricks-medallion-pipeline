"""Focused tests for Bronze layer ingestion."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pyspark.sql import SparkSession

from bronze.config import BronzeConfig, BronzePathsConfig, BronzeSourceFilesConfig
from bronze.config_loader import load_config
from bronze.ingestion_utils import (
    BronzeIngestionError,
    _configure_local_spark_runtime,
    get_spark_session,
    ingest_dataset,
    read_bronze_parquet,
    read_source_csv,
    run_bronze_ingestion,
    validate_csv_structure,
)
from bronze.schemas import CUSTOMERS_SCHEMA, DATASET_SCHEMAS, ORDERS_SCHEMA


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    _configure_local_spark_runtime()
    session = (
        SparkSession.builder.master("local[1]")
        .appName("bronze-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture
def bronze_test_config(tmp_path: Path) -> BronzeConfig:
    fixture_dir = Path(__file__).resolve().parent / "fixtures" / "bronze"
    source_root = tmp_path / "source"
    bronze_root = tmp_path / "bronze"
    source_root.mkdir()
    bronze_root.mkdir()

    for file_name in ("customers.csv", "orders.csv", "products.csv"):
        shutil.copy(fixture_dir / file_name, source_root / file_name)

    return BronzeConfig(
        paths=BronzePathsConfig(
            source_root=str(source_root),
            bronze_root=str(bronze_root),
        ),
        source_files=BronzeSourceFilesConfig(),
    )


def test_local_configuration_loads(project_root: Path) -> None:
    config = load_config(project_root / "config" / "bronze_config.yaml")
    assert config.paths.source_root.endswith("data")
    assert config.paths.bronze_root.endswith("data/bronze")
    assert config.write.mode == "overwrite"


def test_missing_source_file_raises(spark: SparkSession, bronze_test_config: BronzeConfig) -> None:
    missing_path = Path(bronze_test_config.paths.source_root) / "customers.csv"
    missing_path.unlink()

    result = ingest_dataset(spark, bronze_test_config, "customers", "test-run")
    assert result.status == "FAILED"
    assert "does not exist" in (result.error_message or "")


def test_missing_required_column_raises(spark: SparkSession, bronze_test_config: BronzeConfig) -> None:
    customers_path = Path(bronze_test_config.paths.source_root) / "customers.csv"
    customers_path.write_text(
        "customer_id,customer_name,country\n1,Alice,US\n",
        encoding="utf-8",
    )

    result = ingest_dataset(spark, bronze_test_config, "customers", "test-run")
    assert result.status == "FAILED"
    assert "Missing required columns" in (result.error_message or "")


def test_schema_application(spark: SparkSession, bronze_test_config: BronzeConfig) -> None:
    source_path = bronze_test_config.source_path("customers")
    df = read_source_csv(spark, source_path, CUSTOMERS_SCHEMA, "customers")
    assert [field.name for field in df.schema.fields] == [
        field.name for field in CUSTOMERS_SCHEMA.fields
    ]
    assert str(df.schema["lifetime_value"].dataType) == "DecimalType(10,2)"


def test_source_and_bronze_row_counts_match(
    spark: SparkSession,
    bronze_test_config: BronzeConfig,
) -> None:
    results = run_bronze_ingestion(bronze_test_config)
    assert len(results) == 3
    for result in results:
        assert result.status == "SUCCESS"
        assert result.source_row_count == result.bronze_row_count

    assert results[0].source_row_count == 3
    assert results[1].source_row_count == 4
    assert results[2].source_row_count == 2


def test_null_preservation(spark: SparkSession, bronze_test_config: BronzeConfig) -> None:
    ingest_dataset(spark, bronze_test_config, "customers", "test-run")
    bronze_df = read_bronze_parquet(
        spark,
        bronze_test_config.bronze_path("customers"),
        "customers",
    )
    null_email_count = bronze_df.filter("email IS NULL").count()
    assert null_email_count == 1


def test_duplicate_preservation(spark: SparkSession, bronze_test_config: BronzeConfig) -> None:
    ingest_dataset(spark, bronze_test_config, "customers", "test-run")
    bronze_df = read_bronze_parquet(
        spark,
        bronze_test_config.bronze_path("customers"),
        "customers",
    )
    duplicate_count = bronze_df.filter("customer_id = 1").count()
    assert duplicate_count == 2

    ingest_dataset(spark, bronze_test_config, "orders", "test-run")
    orders_df = read_bronze_parquet(
        spark,
        bronze_test_config.bronze_path("orders"),
        "orders",
    )
    duplicate_order_count = orders_df.filter("order_id = 1").count()
    assert duplicate_order_count == 2


def test_invalid_foreign_key_preservation(
    spark: SparkSession,
    bronze_test_config: BronzeConfig,
) -> None:
    ingest_dataset(spark, bronze_test_config, "orders", "test-run")
    orders_df = read_bronze_parquet(
        spark,
        bronze_test_config.bronze_path("orders"),
        "orders",
    )

    invalid_customer_fk_count = orders_df.filter("customer_id = 99999").count()
    null_product_count = orders_df.filter("product_id IS NULL").count()
    assert invalid_customer_fk_count == 1
    assert null_product_count == 1


def test_parquet_read_back(spark: SparkSession, bronze_test_config: BronzeConfig) -> None:
    ingest_dataset(spark, bronze_test_config, "products", "test-run")
    bronze_df = read_bronze_parquet(
        spark,
        bronze_test_config.bronze_path("products"),
        "products",
    )
    assert bronze_df.count() == 2
    assert bronze_df.columns == [field.name for field in DATASET_SCHEMAS["products"].fields]


def test_idempotent_execution(spark: SparkSession, bronze_test_config: BronzeConfig) -> None:
    first = run_bronze_ingestion(bronze_test_config)
    second = run_bronze_ingestion(bronze_test_config)

    for first_result, second_result in zip(first, second):
        assert first_result.source_row_count == second_result.source_row_count
        assert first_result.bronze_row_count == second_result.bronze_row_count


def test_validate_csv_structure_detects_header(
    spark: SparkSession,
    bronze_test_config: BronzeConfig,
) -> None:
    required_columns = [field.name for field in ORDERS_SCHEMA.fields]
    validate_csv_structure(
        spark,
        bronze_test_config.source_path("orders"),
        required_columns,
        "orders",
    )


def test_get_spark_session_reuses_active_session(spark: SparkSession, bronze_test_config: BronzeConfig) -> None:
    reused = get_spark_session(bronze_test_config)
    assert reused is spark
