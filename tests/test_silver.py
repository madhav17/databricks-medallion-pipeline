"""Silver layer validation tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import shutil
from pathlib import Path

import pytest
import yaml
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from bronze.ingestion_utils import _configure_local_spark_runtime
from bronze.schemas import CUSTOMERS_SCHEMA, ORDERS_SCHEMA, PRODUCTS_SCHEMA
from silver.create_silver_tables import run_silver_pipeline
from silver.silver_utils import SilverError


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    _configure_local_spark_runtime()
    session = (
        SparkSession.builder.master("local[1]")
        .appName("silver-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture
def silver_test_paths(tmp_path: Path, spark: SparkSession) -> dict[str, Path]:
    bronze_root = tmp_path / "bronze"
    silver_root = tmp_path / "silver"
    bronze_root.mkdir()
    silver_root.mkdir()

    customers_rows = [
        (1, "Alice", "alice@example.com", "US", date(2020, 1, 1), "Premium", Decimal("100.00")),
        (1, "Alice", "alice@example.com", "US", date(2020, 1, 1), "Premium", Decimal("100.00")),
        (2, "Bob", None, "CA", date(2021, 1, 1), "Standard", Decimal("50.00")),
    ]
    orders_rows = [
        (10, 1, date(2022, 1, 1), 1, 2, Decimal("10.00"), Decimal("20.00"), "Completed", date(2022, 1, 2)),
        (10, None, date(2022, 1, 2), 1, 1, Decimal("10.00"), Decimal("10.00"), "Pending", None),
        (12, 99999, date(2022, 1, 3), 2, 1, Decimal("5.00"), Decimal("5.00"), "Completed", date(2022, 1, 4)),
        (13, 1, date(2022, 1, 4), 99999, 1, Decimal("9.00"), Decimal("9.00"), "Completed", date(2022, 1, 5)),
        (14, 2, date(2022, 1, 5), None, 1, Decimal("9.00"), Decimal("9.00"), "Completed", date(2022, 1, 5)),
        (15, 1, date(2022, 1, 6), 1, 2, Decimal("10.00"), Decimal("99.00"), "Completed", date(2022, 1, 7)),
    ]
    products_rows = [
        (1, "Widget", "Electronics", Decimal("19.99"), Decimal("10.00"), 100, 20),
        (2, "Gadget", "Home", Decimal("9.99"), Decimal("5.00"), 20, 5),
    ]

    customers_df = spark.createDataFrame(customers_rows, schema=CUSTOMERS_SCHEMA)
    orders_df = spark.createDataFrame(orders_rows, schema=ORDERS_SCHEMA)
    products_df = spark.createDataFrame(products_rows, schema=PRODUCTS_SCHEMA)

    customers_df.write.mode("overwrite").parquet(str(bronze_root / "customers"))
    orders_df.write.mode("overwrite").parquet(str(bronze_root / "orders"))
    products_df.write.mode("overwrite").parquet(str(bronze_root / "products"))

    config_path = tmp_path / "silver_config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "bronze_root": str(bronze_root),
                    "silver_root": str(silver_root),
                },
                "spark": {"app_name": "SilverTests", "local_master": "local[1]"},
                "write": {"mode": "overwrite"},
                "table_registration": {
                    "enabled": False,
                    "catalog": None,
                    "database": None,
                },
            }
        ),
        encoding="utf-8",
    )

    return {
        "bronze_root": bronze_root,
        "silver_root": silver_root,
        "config_path": config_path,
    }


def test_silver_pipeline_flags_expected_quality_issues(
    spark: SparkSession,
    silver_test_paths: dict[str, Path],
) -> None:
    summary = run_silver_pipeline(str(silver_test_paths["config_path"]))
    assert summary["customers_rows"] == 3
    assert summary["orders_rows"] == 6
    assert summary["products_rows"] == 2

    silver_root = silver_test_paths["silver_root"]
    customers_df = spark.read.parquet(str(silver_root / "customers"))
    orders_df = spark.read.parquet(str(silver_root / "orders"))
    products_df = spark.read.parquet(str(silver_root / "products"))
    metrics_df = spark.read.parquet(str(silver_root / "quality_metrics"))

    assert customers_df.count() == 3
    assert orders_df.count() == 6
    assert products_df.count() == 2

    assert "quality_check_result" in customers_df.columns
    assert "quality_check_reason" in customers_df.columns
    assert "quality_check_result" in orders_df.columns
    assert "quality_check_reason" in orders_df.columns

    assert customers_df.filter(F.col("email").isNull()).filter(
        F.col("quality_check_reason").contains("COMPLETENESS: email is NULL")
    ).count() == 1

    assert customers_df.filter(F.col("customer_id") == 1).filter(
        F.col("quality_check_reason").contains("UNIQUENESS: duplicate customer_id")
    ).count() == 2

    assert orders_df.filter(F.col("customer_id").isNull()).filter(
        F.col("quality_check_reason").contains("COMPLETENESS: customer_id is NULL")
    ).count() == 1
    assert orders_df.filter(F.col("product_id").isNull()).filter(
        F.col("quality_check_reason").contains("COMPLETENESS: product_id is NULL")
    ).count() == 1

    assert orders_df.filter(F.col("customer_id") == 99999).filter(
        F.col("quality_check_reason").contains(
            "REFERENTIAL_INTEGRITY: customer_id not found in customers"
        )
    ).count() == 1
    assert orders_df.filter(F.col("product_id") == 99999).filter(
        F.col("quality_check_reason").contains(
            "REFERENTIAL_INTEGRITY: product_id not found in products"
        )
    ).count() == 1

    assert orders_df.filter(F.col("order_id") == 10).filter(
        F.col("quality_check_reason").contains("UNIQUENESS: duplicate order_id")
    ).count() == 2

    multi_fail_row = orders_df.filter(F.col("order_id") == 10).filter(
        F.col("customer_id").isNull()
    )
    assert multi_fail_row.filter(
        F.col("quality_check_reason").contains("COMPLETENESS: customer_id is NULL")
    ).count() == 1
    assert multi_fail_row.filter(
        F.col("quality_check_reason").contains("UNIQUENESS: duplicate order_id")
    ).count() == 1

    assert orders_df.filter(F.col("order_id") == 15).filter(
        F.col("quality_check_reason").contains(
            "BUSINESS_LOGIC: total_amount != quantity * unit_price"
        )
    ).count() == 1

    assert metrics_df.count() == 11
    check_names = {
        row.check_name
        for row in metrics_df.select("check_name").distinct().collect()
    }
    assert "business_logic" in check_names
    orders_ref_metric = metrics_df.filter(
        (F.col("dataset_name") == "orders")
        & (F.col("check_name") == "referential_integrity")
    ).collect()[0]
    assert orders_ref_metric.total_rows == 6
    assert orders_ref_metric.failed_rows == 2
    assert orders_ref_metric.passed_rows == 4
    assert abs(orders_ref_metric.fail_percentage - 33.333333) < 1e-5


def test_type_validation_detects_missing_required_column(
    spark: SparkSession,
    silver_test_paths: dict[str, Path],
) -> None:
    bronze_root = silver_test_paths["bronze_root"]
    broken_orders = spark.read.parquet(str(bronze_root / "orders")).drop("unit_price")
    temp_orders_path = bronze_root / "orders_broken"
    broken_orders.write.mode("overwrite").parquet(str(temp_orders_path))
    shutil.rmtree(bronze_root / "orders")
    shutil.move(str(temp_orders_path), str(bronze_root / "orders"))

    with pytest.raises(SilverError, match="missing required columns"):
        run_silver_pipeline(str(silver_test_paths["config_path"]))

