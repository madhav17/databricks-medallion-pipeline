"""Referential integrity checks for Silver layer."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from silver.silver_utils import append_quality_reason


def apply_referential_integrity_checks(
    customers_df: DataFrame,
    orders_df: DataFrame,
    products_df: DataFrame,
) -> tuple[DataFrame, DataFrame, DataFrame]:
    valid_customer_ids = customers_df.select("customer_id").where(
        F.col("customer_id").isNotNull()
    ).distinct()
    valid_product_ids = products_df.select("product_id").where(
        F.col("product_id").isNotNull()
    ).distinct()

    orders_with_keys = (
        orders_df.alias("o")
        .join(
            F.broadcast(valid_customer_ids.alias("c")),
            F.col("o.customer_id") == F.col("c.customer_id"),
            "left",
        )
        .withColumn("customer_exists", F.col("c.customer_id").isNotNull())
        .drop(F.col("c.customer_id"))
        .join(
            F.broadcast(valid_product_ids.alias("p")),
            F.col("o.product_id") == F.col("p.product_id"),
            "left",
        )
        .withColumn("product_exists", F.col("p.product_id").isNotNull())
        .drop(F.col("p.product_id"))
    )

    invalid_customer_fk = F.col("customer_id").isNotNull() & (~F.col("customer_exists"))
    invalid_product_fk = F.col("product_id").isNotNull() & (~F.col("product_exists"))

    orders_out = (
        append_quality_reason(
            append_quality_reason(
                orders_with_keys,
                invalid_customer_fk,
                "REFERENTIAL_INTEGRITY: customer_id not found in customers",
            ),
            invalid_product_fk,
            "REFERENTIAL_INTEGRITY: product_id not found in products",
        )
        .withColumn("check_referential_invalid_customer_id", invalid_customer_fk)
        .withColumn("check_referential_invalid_product_id", invalid_product_fk)
        .withColumn(
            "check_referential_integrity_failed",
            invalid_customer_fk | invalid_product_fk,
        )
        .drop("customer_exists", "product_exists")
    )

    customers_out = customers_df.withColumn(
        "check_referential_integrity_failed",
        F.lit(False),
    )
    products_out = products_df.withColumn(
        "check_referential_integrity_failed",
        F.lit(False),
    )
    return customers_out, orders_out, products_out

