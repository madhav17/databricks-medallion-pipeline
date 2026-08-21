"""Dashboard query validation tests."""

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
from dashboard.dashboard_utils import (
    DashboardError,
    execute_dashboard_query,
    load_dashboard_queries,
    register_gold_views,
    validate_dashboard_queries,
)
from gold.create_gold_tables import run_gold_pipeline
from silver.create_silver_tables import run_silver_pipeline


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    _configure_local_spark_runtime()
    session = (
        SparkSession.builder.master("local[1]")
        .appName("dashboard-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture
def dashboard_test_paths(tmp_path: Path, spark: SparkSession) -> dict[str, Path]:
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
    ]
    products_rows = [
        (1, "Widget", "Electronics", Decimal("19.99"), Decimal("10.00"), 100, 20),
        (2, "Gadget", "Home", Decimal("9.99"), Decimal("5.00"), 20, 5),
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
                "spark": {"app_name": "DashboardSilverTests", "local_master": "local[1]"},
                "write": {"mode": "overwrite"},
                "table_registration": {"enabled": False},
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
                "spark": {"app_name": "DashboardGoldTests", "local_master": "local[1]"},
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

    run_silver_pipeline(str(silver_config_path))
    run_gold_pipeline(str(gold_config_path))

    return {
        "gold_config_path": gold_config_path,
        "gold_root": gold_root,
    }


def test_top_10_products_are_ordered_by_revenue_descending(
    spark: SparkSession,
    dashboard_test_paths: dict[str, Path],
) -> None:
    from gold.config_loader import load_config

    config = load_config(dashboard_test_paths["gold_config_path"])
    register_gold_views(spark, config)
    queries = load_dashboard_queries()
    top_products = execute_dashboard_query(spark, queries["top_10_products_by_revenue"])

    assert top_products.count() <= 10
    rows = top_products.collect()
    revenues = [row.total_revenue for row in rows]
    assert revenues == sorted(revenues, reverse=True)


def test_customer_revenue_query_has_unique_customer_id(
    spark: SparkSession,
    dashboard_test_paths: dict[str, Path],
) -> None:
    from gold.config_loader import load_config

    config = load_config(dashboard_test_paths["gold_config_path"])
    register_gold_views(spark, config)
    queries = load_dashboard_queries()
    customer_revenue = execute_dashboard_query(
        spark, queries["customer_revenue_distribution"]
    )

    assert customer_revenue.count() > 1
    assert (
        customer_revenue.select("customer_id").distinct().count()
        == customer_revenue.count()
    )


def test_customer_segmentation_has_expected_segment_types(
    spark: SparkSession,
    dashboard_test_paths: dict[str, Path],
) -> None:
    from gold.config_loader import load_config

    config = load_config(dashboard_test_paths["gold_config_path"])
    register_gold_views(spark, config)
    queries = load_dashboard_queries()
    segmentation = execute_dashboard_query(spark, queries["customer_segmentation"])

    segment_types = {
        row.segment_type for row in segmentation.select("segment_type").collect()
    }
    assert "High-Value" in segment_types
    assert "Inactive" in segment_types
    assert segment_types.issubset({"High-Value", "Repeat", "One-Time", "Inactive"})


def test_segmentation_revenue_reconciles_with_customer_revenue(
    spark: SparkSession,
    dashboard_test_paths: dict[str, Path],
) -> None:
    from gold.config_loader import load_config

    config = load_config(dashboard_test_paths["gold_config_path"])
    register_gold_views(spark, config)
    queries = load_dashboard_queries()

    customer_revenue = execute_dashboard_query(
        spark, queries["customer_revenue_distribution"]
    )
    segmentation = execute_dashboard_query(spark, queries["customer_segmentation"])

    customer_total = customer_revenue.agg(F.sum("total_revenue")).collect()[0][0]
    segment_total = segmentation.agg(F.sum("total_revenue")).collect()[0][0]
    assert Decimal(str(customer_total)) == Decimal(str(segment_total))


def test_dashboard_validation_runs_against_local_gold_data(
    dashboard_test_paths: dict[str, Path],
) -> None:
    from gold.config_loader import load_config

    config = load_config(dashboard_test_paths["gold_config_path"])
    summary = validate_dashboard_queries(config, sample_rows=0)

    assert summary["top_10_products_rows"] <= 10
    assert summary["customer_revenue_rows"] == 4
    assert summary["customer_segmentation_rows"] == 4
    assert summary["total_revenue_kpi"] == pytest.approx(1220.0)


def test_dashboard_validation_fails_when_gold_input_missing(tmp_path: Path) -> None:
    from gold.config_loader import load_config

    gold_config_path = tmp_path / "gold_config.yaml"
    gold_config_path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "silver_root": str(tmp_path / "silver"),
                    "gold_root": str(tmp_path / "missing_gold"),
                },
                "spark": {"app_name": "DashboardMissing", "local_master": "local[1]"},
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
    config = load_config(gold_config_path)

    with pytest.raises(DashboardError, match="Gold input missing"):
        validate_dashboard_queries(config, sample_rows=0)
