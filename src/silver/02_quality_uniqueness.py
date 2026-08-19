"""Uniqueness checks for Silver layer."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from silver.silver_utils import append_quality_reason


def apply_uniqueness_checks(
    customers_df: DataFrame,
    orders_df: DataFrame,
    products_df: DataFrame,
) -> tuple[DataFrame, DataFrame, DataFrame]:
    customer_window = Window.partitionBy("customer_id")
    customer_group_count = F.count("*").over(customer_window)
    customers_duplicate = F.col("customer_id").isNotNull() & (customer_group_count > 1)
    customers_out = (
        append_quality_reason(
            customers_df.withColumn("tmp_customer_group_count", customer_group_count),
            customers_duplicate,
            "UNIQUENESS: duplicate customer_id",
        )
        .withColumn("check_uniqueness_failed", customers_duplicate)
        .drop("tmp_customer_group_count")
    )

    order_window = Window.partitionBy("order_id")
    order_group_count = F.count("*").over(order_window)
    orders_duplicate = F.col("order_id").isNotNull() & (order_group_count > 1)
    orders_out = (
        append_quality_reason(
            orders_df.withColumn("tmp_order_group_count", order_group_count),
            orders_duplicate,
            "UNIQUENESS: duplicate order_id",
        )
        .withColumn("check_uniqueness_failed", orders_duplicate)
        .drop("tmp_order_group_count")
    )

    products_out = products_df.withColumn("check_uniqueness_failed", F.lit(False))
    return customers_out, orders_out, products_out

