"""Completeness checks for Silver layer."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from silver.silver_utils import append_quality_reason


def apply_completeness_checks(
    customers_df: DataFrame,
    orders_df: DataFrame,
    products_df: DataFrame,
) -> tuple[DataFrame, DataFrame, DataFrame]:
    customers_out = append_quality_reason(
        customers_df,
        F.col("email").isNull(),
        "COMPLETENESS: email is NULL",
    ).withColumn("check_completeness_failed", F.col("email").isNull())

    orders_customer_null = F.col("customer_id").isNull()
    orders_product_null = F.col("product_id").isNull()
    orders_out = (
        append_quality_reason(
            append_quality_reason(
                orders_df,
                orders_customer_null,
                "COMPLETENESS: customer_id is NULL",
            ),
            orders_product_null,
            "COMPLETENESS: product_id is NULL",
        )
        .withColumn("check_completeness_customer_id_null", orders_customer_null)
        .withColumn("check_completeness_product_id_null", orders_product_null)
        .withColumn(
            "check_completeness_failed",
            orders_customer_null | orders_product_null,
        )
    )

    products_out = products_df.withColumn("check_completeness_failed", F.lit(False))
    return customers_out, orders_out, products_out

