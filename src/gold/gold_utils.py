"""Shared utilities for Gold layer aggregation processing."""

from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from bronze.ingestion_utils import _configure_local_spark_runtime
from bronze.schemas import MONETARY_DECIMAL
from gold.config import GoldConfig

logger = logging.getLogger(__name__)


class GoldError(Exception):
    """Raised when Gold processing fails."""


QUALITY_RESULT_COLUMN = "quality_check_result"
QUALITY_PASS_VALUE = "PASS"

GOLD_DATASETS = (
    "sales_by_product",
    "revenue_by_customer",
    "daily_weekly_trends",
    "customer_segmentation",
)

SALES_BY_PRODUCT_SCHEMA = StructType(
    [
        StructField("product_id", IntegerType(), nullable=False),
        StructField("product_name", StringType(), nullable=True),
        StructField("category", StringType(), nullable=True),
        StructField("total_orders", LongType(), nullable=False),
        StructField("total_revenue", MONETARY_DECIMAL, nullable=False),
        StructField("avg_order_value", MONETARY_DECIMAL, nullable=True),
    ]
)

REVENUE_BY_CUSTOMER_SCHEMA = StructType(
    [
        StructField("customer_id", IntegerType(), nullable=False),
        StructField("customer_name", StringType(), nullable=True),
        StructField("customer_segment", StringType(), nullable=True),
        StructField("total_orders", LongType(), nullable=False),
        StructField("total_revenue", MONETARY_DECIMAL, nullable=False),
        StructField("avg_order_value", MONETARY_DECIMAL, nullable=True),
        StructField("lifetime_value_actual", MONETARY_DECIMAL, nullable=False),
    ]
)

DAILY_WEEKLY_TRENDS_SCHEMA = StructType(
    [
        StructField("period_type", StringType(), nullable=False),
        StructField("period_start", DateType(), nullable=False),
        StructField("total_orders", LongType(), nullable=False),
        StructField("total_revenue", MONETARY_DECIMAL, nullable=False),
        StructField("avg_order_value", MONETARY_DECIMAL, nullable=True),
    ]
)

CUSTOMER_SEGMENTATION_SCHEMA = StructType(
    [
        StructField("segment_type", StringType(), nullable=False),
        StructField("customer_count", LongType(), nullable=False),
        StructField("avg_revenue", MONETARY_DECIMAL, nullable=False),
        StructField("total_revenue", MONETARY_DECIMAL, nullable=False),
    ]
)

GOLD_SCHEMAS: dict[str, StructType] = {
    "sales_by_product": SALES_BY_PRODUCT_SCHEMA,
    "revenue_by_customer": REVENUE_BY_CUSTOMER_SCHEMA,
    "daily_weekly_trends": DAILY_WEEKLY_TRENDS_SCHEMA,
    "customer_segmentation": CUSTOMER_SEGMENTATION_SCHEMA,
}


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def get_spark_session(config: GoldConfig) -> SparkSession:
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


def read_silver_dataset(
    spark: SparkSession,
    config: GoldConfig,
    dataset_name: str,
) -> DataFrame:
    path = config.silver_path(dataset_name)
    is_uri_path = "://" in path
    if (not is_uri_path) and (not Path(path).exists()):
        raise GoldError(
            f"Silver input missing for dataset '{dataset_name}' at path '{path}'"
        )

    try:
        return spark.read.parquet(path)
    except Exception as exc:
        raise GoldError(
            f"Failed to read Silver Parquet for dataset '{dataset_name}' at path '{path}'"
        ) from exc


def _validate_quality_columns(df: DataFrame, dataset_name: str) -> None:
    if QUALITY_RESULT_COLUMN not in df.columns:
        raise GoldError(
            f"Silver dataset '{dataset_name}' missing required column "
            f"'{QUALITY_RESULT_COLUMN}'"
        )


def register_valid_silver_views(spark: SparkSession, config: GoldConfig) -> dict[str, int]:
    """Register business-eligible Silver temp views for Gold SQL execution."""
    customers_df = read_silver_dataset(spark, config, "customers")
    orders_df = read_silver_dataset(spark, config, "orders")
    products_df = read_silver_dataset(spark, config, "products")

    for dataset_name, df in (
        ("customers", customers_df),
        ("orders", orders_df),
        ("products", products_df),
    ):
        _validate_quality_columns(df, dataset_name)

    valid_customers = customers_df.filter(
        F.col(QUALITY_RESULT_COLUMN) == QUALITY_PASS_VALUE
    )
    # Products do not have Silver uniqueness checks; dedupe defensively for joins.
    valid_products = products_df.filter(
        F.col(QUALITY_RESULT_COLUMN) == QUALITY_PASS_VALUE
    ).dropDuplicates(["product_id"])

    valid_customer_ids = valid_customers.select("customer_id")
    valid_product_ids = valid_products.select("product_id")

    valid_orders = (
        orders_df.filter(F.col(QUALITY_RESULT_COLUMN) == QUALITY_PASS_VALUE)
        .filter(F.col("order_status").isin(config.business_rules.eligible_order_statuses))
        .join(valid_customer_ids, on="customer_id", how="left_semi")
        .join(valid_product_ids, on="product_id", how="left_semi")
    )

    valid_customers.createOrReplaceTempView("valid_silver_customers")
    valid_orders.createOrReplaceTempView("valid_silver_orders")
    valid_products.createOrReplaceTempView("valid_silver_products")

    return {
        "valid_customers_rows": valid_customers.count(),
        "valid_orders_rows": valid_orders.count(),
        "valid_products_rows": valid_products.count(),
    }


def load_sql(filename: str) -> str:
    sql_path = Path(__file__).parent / filename
    if not sql_path.exists():
        raise GoldError(f"Gold SQL file not found: {sql_path}")
    return sql_path.read_text(encoding="utf-8")


def render_sql(sql_template: str, config: GoldConfig) -> str:
    threshold = config.business_rules.high_value_revenue_threshold
    return sql_template.format(
        high_value_threshold=threshold,
    )


def validate_output_schema(df: DataFrame, dataset_name: str) -> None:
    expected = GOLD_SCHEMAS[dataset_name]
    actual = df.schema
    if len(actual.fields) != len(expected.fields):
        raise GoldError(
            f"Schema mismatch for Gold dataset '{dataset_name}': "
            f"expected {len(expected.fields)} columns, found {len(actual.fields)}"
        )

    for expected_field, actual_field in zip(expected.fields, actual.fields):
        if expected_field.name != actual_field.name:
            raise GoldError(
                f"Schema mismatch for Gold dataset '{dataset_name}': "
                f"expected column '{expected_field.name}', found '{actual_field.name}'"
            )
        if expected_field.dataType != actual_field.dataType:
            raise GoldError(
                f"Schema mismatch for Gold dataset '{dataset_name}' column "
                f"'{expected_field.name}': expected {expected_field.dataType}, "
                f"found {actual_field.dataType}"
            )


def validate_unique_keys(
    df: DataFrame,
    dataset_name: str,
    key_column: str | list[str],
) -> None:
    total_rows = df.count()
    key_columns = [key_column] if isinstance(key_column, str) else key_column
    distinct_keys = df.select(*key_columns).distinct().count()
    if total_rows != distinct_keys:
        key_label = ", ".join(key_columns)
        raise GoldError(
            f"Gold dataset '{dataset_name}' contains duplicate values in "
            f"'{key_label}': rows={total_rows}, distinct={distinct_keys}"
        )


def write_gold_dataset(
    df: DataFrame,
    config: GoldConfig,
    dataset_name: str,
) -> None:
    path = config.gold_path(dataset_name)
    try:
        df.write.mode(config.write.mode).parquet(path)
    except Exception as exc:
        raise GoldError(
            f"Failed writing Gold dataset '{dataset_name}' to path '{path}'"
        ) from exc


def register_gold_table_if_enabled(
    spark: SparkSession,
    config: GoldConfig,
    dataset_name: str,
) -> None:
    if not config.table_registration.enabled:
        return
    if not config.table_registration.catalog or not config.table_registration.database:
        raise GoldError(
            "Gold table registration enabled but catalog/database not configured"
        )
    table_name = (
        f"{config.table_registration.catalog}."
        f"{config.table_registration.database}.gold_{dataset_name}"
    )
    path = config.gold_path(dataset_name)
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        USING PARQUET
        LOCATION '{path}'
        """
    )


def eligible_order_revenue(spark: SparkSession) -> Decimal:
    row = spark.sql(
        """
        SELECT COALESCE(SUM(total_amount), CAST(0 AS DECIMAL(10, 2))) AS total_revenue
        FROM valid_silver_orders
        """
    ).collect()[0]
    return Decimal(str(row.total_revenue))


def reconcile_gold_outputs(spark: SparkSession) -> None:
    """Validate that Gold revenue totals reconcile to eligible Silver order revenue."""
    eligible_total = eligible_order_revenue(spark)

    product_total = Decimal(
        str(
            spark.sql(
                """
                SELECT COALESCE(SUM(total_revenue), CAST(0 AS DECIMAL(10, 2))) AS total_revenue
                FROM sales_by_product_gold
                """
            ).collect()[0].total_revenue
        )
    )
    customer_total = Decimal(
        str(
            spark.sql(
                """
                SELECT COALESCE(SUM(total_revenue), CAST(0 AS DECIMAL(10, 2))) AS total_revenue
                FROM revenue_by_customer_gold
                """
            ).collect()[0].total_revenue
        )
    )
    segment_total = Decimal(
        str(
            spark.sql(
                """
                SELECT COALESCE(SUM(total_revenue), CAST(0 AS DECIMAL(10, 2))) AS total_revenue
                FROM customer_segmentation_gold
                """
            ).collect()[0].total_revenue
        )
    )

    if product_total != eligible_total:
        raise GoldError(
            f"Reconciliation failed sales_by_product: gold={product_total}, "
            f"eligible_silver_orders={eligible_total}"
        )
    if customer_total != eligible_total:
        raise GoldError(
            f"Reconciliation failed revenue_by_customer: gold={customer_total}, "
            f"eligible_silver_orders={eligible_total}"
        )
    if segment_total != eligible_total:
        raise GoldError(
            f"Reconciliation failed customer_segmentation: gold={segment_total}, "
            f"eligible_silver_orders={eligible_total}"
        )
