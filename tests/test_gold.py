"""Gold layer validation tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from bronze.ingestion_utils import _configure_local_spark_runtime
from bronze.schemas import CUSTOMERS_SCHEMA, ORDERS_SCHEMA, PRODUCTS_SCHEMA
from gold.create_gold_tables import run_gold_pipeline
from gold.gold_utils import GoldError
from silver.create_silver_tables import run_silver_pipeline


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    _configure_local_spark_runtime()
    session = (
        SparkSession.builder.master("local[1]")
        .appName("gold-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture
def gold_test_paths(tmp_path: Path, spark: SparkSession) -> dict[str, Path]:
    bronze_root = tmp_path / "bronze"
    silver_root = tmp_path / "silver"
    gold_root = tmp_path / "gold"
    bronze_root.mkdir()
    silver_root.mkdir()
    gold_root.mkdir()

    customers_rows = [
        (1, "Alice", "alice@example.com", "US", date(2020, 1, 1), "Premium", Decimal("1000.00")),
        (2, "Bob", "bob@example.com", "US", date(2020, 2, 1), "Standard", Decimal("100.00")),
        (3, "Carol", "carol@example.com", "US", date(2020, 3, 1), "Basic", Decimal("50.00")),
        (4, "Dave", "dave@example.com", "US", date(2020, 4, 1), "Standard", Decimal("10.00")),
        (5, "Eve", None, "US", date(2020, 5, 1), "Basic", Decimal("10.00")),
    ]
    orders_rows = [
        (101, 1, date(2022, 1, 1), 1, 1, Decimal("600.00"), Decimal("600.00"), "Completed", date(2022, 1, 2)),
        (102, 1, date(2022, 1, 2), 2, 1, Decimal("500.00"), Decimal("500.00"), "Completed", date(2022, 1, 3)),
        (103, 2, date(2022, 1, 3), 1, 1, Decimal("50.00"), Decimal("50.00"), "Completed", date(2022, 1, 4)),
        (104, 3, date(2022, 1, 4), 2, 1, Decimal("30.00"), Decimal("30.00"), "Completed", date(2022, 1, 5)),
        (105, 3, date(2022, 1, 5), 3, 1, Decimal("40.00"), Decimal("40.00"), "Completed", date(2022, 1, 6)),
        (120, 2, date(2022, 1, 6), 1, 1, Decimal("50.00"), Decimal("50.00"), "Completed", date(2022, 1, 7)),
        (120, 2, date(2022, 1, 6), 1, 1, Decimal("50.00"), Decimal("50.00"), "Completed", date(2022, 1, 7)),
        (107, None, date(2022, 1, 7), 1, 1, Decimal("10.00"), Decimal("10.00"), "Completed", date(2022, 1, 8)),
        (108, 99999, date(2022, 1, 8), 1, 1, Decimal("20.00"), Decimal("20.00"), "Completed", date(2022, 1, 9)),
        (109, 1, date(2022, 1, 9), 2, 1, Decimal("99.00"), Decimal("99.00"), "Pending", None),
        (110, 2, date(2022, 1, 10), 2, 1, Decimal("88.00"), Decimal("88.00"), "Cancelled", None),
    ]
    products_rows = [
        (1, "Widget", "Electronics", Decimal("19.99"), Decimal("10.00"), 100, 20),
        (2, "Gadget", "Home", Decimal("9.99"), Decimal("5.00"), 20, 5),
        (2, "Gadget Duplicate", "Home", Decimal("9.99"), Decimal("5.00"), 20, 5),
        (3, "Tool", "Sports", Decimal("14.99"), Decimal("7.00"), 30, 10),
        (4, "Unused", "Books", Decimal("4.99"), Decimal("2.00"), 10, 2),
    ]

    spark.createDataFrame(customers_rows, schema=CUSTOMERS_SCHEMA).write.mode(
        "overwrite"
    ).parquet(str(bronze_root / "customers"))
    spark.createDataFrame(orders_rows, schema=ORDERS_SCHEMA).write.mode(
        "overwrite"
    ).parquet(str(bronze_root / "orders"))
    spark.createDataFrame(products_rows, schema=PRODUCTS_SCHEMA).write.mode(
        "overwrite"
    ).parquet(str(bronze_root / "products"))

    silver_config_path = tmp_path / "silver_config.yaml"
    silver_config_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "bronze_root": str(bronze_root),
                    "silver_root": str(silver_root),
                },
                "spark": {"app_name": "GoldSilverTests", "local_master": "local[1]"},
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

    gold_config_path = tmp_path / "gold_config.yaml"
    gold_config_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "silver_root": str(silver_root),
                    "gold_root": str(gold_root),
                },
                "spark": {"app_name": "GoldTests", "local_master": "local[1]"},
                "write": {"mode": "overwrite"},
                "business_rules": {
                    "high_value_revenue_threshold": "1000.00",
                    "eligible_order_statuses": ["Completed"],
                },
                "table_registration": {
                    "enabled": False,
                    "catalog": None,
                    "database": None,
                },
            }
        ),
        encoding="utf-8",
    )

    run_silver_pipeline(str(silver_config_path))

    return {
        "silver_root": silver_root,
        "gold_root": gold_root,
        "gold_config_path": gold_config_path,
    }


def _collect_map(df, key_col: str, value_cols: list[str]) -> dict:
    rows = df.collect()
    return {
        getattr(row, key_col): {col: getattr(row, col) for col in value_cols}
        for row in rows
    }


def test_gold_pipeline_produces_expected_aggregations(
    spark: SparkSession,
    gold_test_paths: dict[str, Path],
) -> None:
    summary = run_gold_pipeline(str(gold_test_paths["gold_config_path"]))

    assert summary["valid_customers_rows"] == 4
    assert summary["valid_orders_rows"] == 5
    assert summary["sales_by_product_rows"] == 4
    assert summary["revenue_by_customer_rows"] == 4
    assert summary["daily_weekly_trends_rows"] > 0
    assert summary["customer_segmentation_rows"] == 4
    assert summary["eligible_order_revenue"] == pytest.approx(1220.0)

    gold_root = gold_test_paths["gold_root"]
    sales_df = spark.read.parquet(str(gold_root / "sales_by_product"))
    revenue_df = spark.read.parquet(str(gold_root / "revenue_by_customer"))
    trends_df = spark.read.parquet(str(gold_root / "daily_weekly_trends"))
    segmentation_df = spark.read.parquet(str(gold_root / "customer_segmentation"))

    sales = _collect_map(
        sales_df,
        "product_id",
        ["total_orders", "total_revenue", "avg_order_value"],
    )
    assert sales[1]["total_orders"] == 2
    assert sales[1]["total_revenue"] == Decimal("650.00")
    assert sales[2]["total_orders"] == 2
    assert sales[2]["total_revenue"] == Decimal("530.00")
    assert sales[3]["total_orders"] == 1
    assert sales[3]["total_revenue"] == Decimal("40.00")
    assert sales[4]["total_orders"] == 0
    assert sales[4]["total_revenue"] == Decimal("0.00")
    assert sales[4]["avg_order_value"] is None

    revenue = _collect_map(
        revenue_df,
        "customer_id",
        ["total_orders", "total_revenue", "avg_order_value", "lifetime_value_actual"],
    )
    assert revenue[1]["total_orders"] == 2
    assert revenue[1]["total_revenue"] == Decimal("1100.00")
    assert revenue[1]["lifetime_value_actual"] == Decimal("1100.00")
    assert revenue[2]["total_orders"] == 1
    assert revenue[2]["total_revenue"] == Decimal("50.00")
    assert revenue[3]["total_orders"] == 2
    assert revenue[3]["total_revenue"] == Decimal("70.00")
    assert revenue[4]["total_orders"] == 0
    assert revenue[4]["total_revenue"] == Decimal("0.00")
    assert revenue[4]["avg_order_value"] is None
    assert revenue[4]["lifetime_value_actual"] == Decimal("0.00")

    segments = _collect_map(
        segmentation_df,
        "segment_type",
        ["customer_count", "avg_revenue", "total_revenue"],
    )
    assert segments["High-Value"]["customer_count"] == 1
    assert segments["High-Value"]["total_revenue"] == Decimal("1100.00")
    assert segments["One-Time"]["customer_count"] == 1
    assert segments["One-Time"]["total_revenue"] == Decimal("50.00")
    assert segments["Repeat"]["customer_count"] == 1
    assert segments["Repeat"]["total_revenue"] == Decimal("70.00")
    assert segments["Inactive"]["customer_count"] == 1
    assert segments["Inactive"]["total_revenue"] == Decimal("0.00")
    assert segments["Inactive"]["avg_revenue"] == Decimal("0.00")

    daily_trends = trends_df.filter(F.col("period_type") == "daily")
    weekly_trends = trends_df.filter(F.col("period_type") == "weekly")
    assert daily_trends.count() == 5
    assert weekly_trends.count() >= 1
    daily_revenue_total = daily_trends.agg(
        F.sum("total_revenue").alias("total_revenue")
    ).collect()[0].total_revenue
    assert daily_revenue_total == Decimal("1220.00")


def test_gold_pipeline_is_idempotent(
    spark: SparkSession,
    gold_test_paths: dict[str, Path],
) -> None:
    config_path = str(gold_test_paths["gold_config_path"])
    first = run_gold_pipeline(config_path)
    second = run_gold_pipeline(config_path)
    assert first["sales_by_product_rows"] == second["sales_by_product_rows"]
    assert first["revenue_by_customer_rows"] == second["revenue_by_customer_rows"]


def test_gold_pipeline_fails_when_silver_input_missing(
    tmp_path: Path,
) -> None:
    gold_config_path = tmp_path / "gold_config.yaml"
    gold_config_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "silver_root": str(tmp_path / "missing_silver"),
                    "gold_root": str(tmp_path / "gold"),
                },
                "spark": {"app_name": "GoldMissing", "local_master": "local[1]"},
                "write": {"mode": "overwrite"},
                "business_rules": {
                    "high_value_revenue_threshold": "1000.00",
                    "eligible_order_statuses": ["Completed"],
                },
                "table_registration": {"enabled": False},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(GoldError, match="Silver input missing"):
        run_gold_pipeline(str(gold_config_path))


def test_invalid_silver_orders_are_excluded_from_gold_totals(
    spark: SparkSession,
    gold_test_paths: dict[str, Path],
) -> None:
    silver_orders = spark.read.parquet(str(gold_test_paths["silver_root"] / "orders"))
    invalid_count = silver_orders.filter(F.col("quality_check_result") == "FAIL").count()
    assert invalid_count == 4

    summary = run_gold_pipeline(str(gold_test_paths["gold_config_path"]))
    assert summary["valid_orders_rows"] == 5
    assert summary["eligible_order_revenue"] == pytest.approx(1220.0)
