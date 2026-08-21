"""End-to-end medallion pipeline integration test."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from bronze.ingestion_utils import _configure_local_spark_runtime, run_bronze_ingestion
from bronze.config_loader import load_config as load_bronze_config
from dashboard.dashboard_utils import validate_dashboard_queries
from gold.config_loader import load_config as load_gold_config
from gold.create_gold_tables import run_gold_pipeline
from silver.create_silver_tables import run_silver_pipeline


@pytest.fixture(scope="module")
def spark() -> SparkSession:
    _configure_local_spark_runtime()
    session = (
        SparkSession.builder.master("local[1]")
        .appName("medallion-e2e-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture
def medallion_paths(tmp_path: Path) -> dict[str, Path]:
    data_root = tmp_path / "data"
    data_root.mkdir()

    (data_root / "customers.csv").write_text(
        "\n".join(
            [
                "customer_id,customer_name,email,country,signup_date,customer_segment,lifetime_value",
                "1,Alice Smith,alice@example.com,United States,2020-01-01,Premium,100.00",
                "2,Bob Jones,bob@example.com,Canada,2021-05-10,Standard,50.00",
            ]
        ),
        encoding="utf-8",
    )
    (data_root / "products.csv").write_text(
        "\n".join(
            [
                "product_id,product_name,category,price,cost,stock_quantity,reorder_level",
                "1,Widget,Electronics,19.99,10.00,100,20",
                "2,Gadget,Home,29.99,15.00,50,10",
            ]
        ),
        encoding="utf-8",
    )
    (data_root / "orders.csv").write_text(
        "\n".join(
            [
                "order_id,customer_id,order_date,product_id,quantity,unit_price,total_amount,order_status,payment_date",
                "10,1,2022-01-01,1,2,10.00,20.00,Completed,2022-01-02",
                "11,2,2022-02-01,2,1,29.99,29.99,Completed,2022-02-02",
                "12,,2022-03-01,1,1,15.00,15.00,Pending,",
            ]
        ),
        encoding="utf-8",
    )

    bronze_root = tmp_path / "bronze"
    silver_root = tmp_path / "silver"
    gold_root = tmp_path / "gold"

    bronze_config_path = tmp_path / "bronze_config.yaml"
    bronze_config_path.write_text(
        yaml.safe_dump(
            {
                "paths": {"source_root": str(data_root), "bronze_root": str(bronze_root)},
                "source_files": {
                    "customers": "customers.csv",
                    "orders": "orders.csv",
                    "products": "products.csv",
                },
                "spark": {"app_name": "MedallionE2E", "local_master": "local[1]"},
                "write": {"mode": "overwrite"},
                "table_registration": {"enabled": False, "catalog": None, "database": None},
                "metadata": {"directory": "_metadata", "file_name": "ingestion_metadata.parquet"},
            }
        ),
        encoding="utf-8",
    )

    silver_config_path = tmp_path / "silver_config.yaml"
    silver_config_path.write_text(
        yaml.safe_dump(
            {
                "paths": {"bronze_root": str(bronze_root), "silver_root": str(silver_root)},
                "spark": {"app_name": "MedallionE2E", "local_master": "local[1]"},
                "write": {"mode": "overwrite"},
                "table_registration": {"enabled": False, "catalog": None, "database": None},
            }
        ),
        encoding="utf-8",
    )

    gold_config_path = tmp_path / "gold_config.yaml"
    gold_config_path.write_text(
        yaml.safe_dump(
            {
                "paths": {"silver_root": str(silver_root), "gold_root": str(gold_root)},
                "spark": {"app_name": "MedallionE2E", "local_master": "local[1]"},
                "write": {"mode": "overwrite"},
                "business_rules": {
                    "high_value_revenue_threshold": 1000.0,
                    "eligible_order_statuses": ["Completed"],
                },
                "table_registration": {"enabled": False, "catalog": None, "database": None},
            }
        ),
        encoding="utf-8",
    )

    return {
        "data_root": data_root,
        "bronze_root": bronze_root,
        "silver_root": silver_root,
        "gold_root": gold_root,
        "bronze_config_path": bronze_config_path,
        "silver_config_path": silver_config_path,
        "gold_config_path": gold_config_path,
    }


def test_medallion_pipeline_csv_to_dashboard(
    spark: SparkSession,
    medallion_paths: dict[str, Path],
) -> None:
    bronze_config = load_bronze_config(str(medallion_paths["bronze_config_path"]))
    bronze_results = run_bronze_ingestion(bronze_config)
    assert len(bronze_results) == 3
    assert all(result.status == "SUCCESS" for result in bronze_results)

    silver_summary = run_silver_pipeline(str(medallion_paths["silver_config_path"]))
    assert silver_summary["customers_rows"] > 0
    assert silver_summary["orders_rows"] > 0
    assert silver_summary["products_rows"] > 0

    metrics_df = spark.read.parquet(str(medallion_paths["silver_root"] / "quality_metrics"))
    required_checks = {
        "completeness",
        "uniqueness",
        "referential_integrity",
        "business_logic",
    }
    actual_checks = {
        row.check_name
        for row in metrics_df.select("check_name").distinct().collect()
    }
    assert required_checks.issubset(actual_checks)

    gold_summary = run_gold_pipeline(str(medallion_paths["gold_config_path"]))
    assert gold_summary["sales_by_product_rows"] > 0
    assert gold_summary["revenue_by_customer_rows"] > 0
    assert gold_summary["customer_segmentation_rows"] > 0

    gold_config = load_gold_config(str(medallion_paths["gold_config_path"]))
    dashboard_summary = validate_dashboard_queries(gold_config)
    assert dashboard_summary["top_10_products_rows"] > 0
    assert dashboard_summary["customer_revenue_rows"] > 0
    assert dashboard_summary["customer_segmentation_rows"] > 0

    silver_orders = spark.read.parquet(str(medallion_paths["silver_root"] / "orders"))
    assert silver_orders.filter(F.col("quality_check_result") == "FAIL").count() > 0
    assert silver_orders.filter(F.col("quality_check_result") == "PASS").count() > 0
