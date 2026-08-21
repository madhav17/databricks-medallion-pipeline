"""Business logic checks for Silver layer.

Rules are aligned with the e-commerce data model documented in
``src/data_generation/DATA_GENERATION_NOTES.md`` and validated independently in
``src/data_generation/validation/dataset_validator.py``.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from silver.silver_utils import append_quality_reason

# Matches ``config/generator_config.yaml`` business_parameters.date_range.end_date.
DATE_RANGE_END_STR = "2025-06-30"

VALID_SEGMENTS = ("Premium", "Standard", "Basic")
VALID_STATUSES = ("Pending", "Completed", "Cancelled")


def _date_range_end():
    return F.to_date(F.lit(DATE_RANGE_END_STR))


def _apply_customer_business_logic(customers_df: DataFrame) -> DataFrame:
    date_range_end = _date_range_end()
    invalid_segment = F.col("customer_segment").isNotNull() & (
        ~F.col("customer_segment").isin(*VALID_SEGMENTS)
    )
    negative_lifetime_value = F.col("lifetime_value").isNotNull() & (
        F.col("lifetime_value") < F.lit(0)
    )
    future_signup_date = F.col("signup_date").isNotNull() & (
        F.col("signup_date") > date_range_end
    )

    customers_out = customers_df
    customers_out = append_quality_reason(
        customers_out,
        invalid_segment,
        "BUSINESS_LOGIC: customer_segment not in Premium/Standard/Basic",
    )
    customers_out = append_quality_reason(
        customers_out,
        negative_lifetime_value,
        "BUSINESS_LOGIC: lifetime_value is negative",
    )
    customers_out = append_quality_reason(
        customers_out,
        future_signup_date,
        "BUSINESS_LOGIC: signup_date after configured end date",
    )
    customers_out = customers_out.withColumn(
        "check_business_logic_failed",
        invalid_segment | negative_lifetime_value | future_signup_date,
    )
    return customers_out


def _apply_product_business_logic(products_df: DataFrame) -> DataFrame:
    negative_price = F.col("price").isNotNull() & (F.col("price") < F.lit(0))
    negative_cost = F.col("cost").isNotNull() & (F.col("cost") < F.lit(0))
    negative_stock = F.col("stock_quantity").isNotNull() & (
        F.col("stock_quantity") < F.lit(0)
    )
    negative_reorder = F.col("reorder_level").isNotNull() & (
        F.col("reorder_level") < F.lit(0)
    )

    products_out = products_df
    products_out = append_quality_reason(
        products_out,
        negative_price,
        "BUSINESS_LOGIC: price is negative",
    )
    products_out = append_quality_reason(
        products_out,
        negative_cost,
        "BUSINESS_LOGIC: cost is negative",
    )
    products_out = append_quality_reason(
        products_out,
        negative_stock,
        "BUSINESS_LOGIC: stock_quantity is negative",
    )
    products_out = append_quality_reason(
        products_out,
        negative_reorder,
        "BUSINESS_LOGIC: reorder_level is negative",
    )
    products_out = products_out.withColumn(
        "check_business_logic_failed",
        negative_price | negative_cost | negative_stock | negative_reorder,
    )
    return products_out


def _apply_order_business_logic(
    orders_df: DataFrame,
    customers_df: DataFrame,
) -> DataFrame:
    customer_signup = customers_df.select("customer_id", "signup_date").dropDuplicates(
        ["customer_id"]
    )

    orders_with_signup = (
        orders_df.alias("o")
        .join(
            F.broadcast(customer_signup.alias("c")),
            F.col("o.customer_id") == F.col("c.customer_id"),
            "left",
        )
        .select(
            "o.*",
            F.col("c.signup_date").alias("customer_signup_date"),
        )
    )

    date_range_end = _date_range_end()
    invalid_quantity = F.col("quantity").isNotNull() & (F.col("quantity") <= F.lit(0))
    negative_unit_price = F.col("unit_price").isNotNull() & (
        F.col("unit_price") < F.lit(0)
    )
    invalid_status = F.col("order_status").isNotNull() & (
        ~F.col("order_status").isin(*VALID_STATUSES)
    )
    future_order_date = F.col("order_date").isNotNull() & (
        F.col("order_date") > date_range_end
    )
    order_before_signup = (
        F.col("customer_id").isNotNull()
        & F.col("customer_signup_date").isNotNull()
        & F.col("order_date").isNotNull()
        & (F.col("order_date") < F.col("customer_signup_date"))
    )
    payment_before_order = (
        F.col("payment_date").isNotNull()
        & F.col("order_date").isNotNull()
        & (F.col("payment_date") < F.col("order_date"))
    )
    completed_without_payment = (F.col("order_status") == F.lit("Completed")) & (
        F.col("payment_date").isNull()
    )
    expected_total = F.round(
        F.col("quantity").cast("decimal(10,2)") * F.col("unit_price"),
        2,
    )
    incorrect_total_amount = (
        F.col("quantity").isNotNull()
        & F.col("unit_price").isNotNull()
        & F.col("total_amount").isNotNull()
        & (F.col("total_amount") != expected_total)
    )

    orders_out = orders_with_signup
    rules = [
        (invalid_quantity, "BUSINESS_LOGIC: quantity must be positive"),
        (negative_unit_price, "BUSINESS_LOGIC: unit_price is negative"),
        (invalid_status, "BUSINESS_LOGIC: order_status not in Pending/Completed/Cancelled"),
        (future_order_date, "BUSINESS_LOGIC: order_date after configured end date"),
        (order_before_signup, "BUSINESS_LOGIC: order_date before customer signup_date"),
        (payment_before_order, "BUSINESS_LOGIC: payment_date before order_date"),
        (
            completed_without_payment,
            "BUSINESS_LOGIC: Completed order missing payment_date",
        ),
        (
            incorrect_total_amount,
            "BUSINESS_LOGIC: total_amount != quantity * unit_price",
        ),
    ]

    for condition, reason in rules:
        orders_out = append_quality_reason(orders_out, condition, reason)

    orders_out = orders_out.withColumn(
        "check_business_logic_failed",
        invalid_quantity
        | negative_unit_price
        | invalid_status
        | future_order_date
        | order_before_signup
        | payment_before_order
        | completed_without_payment
        | incorrect_total_amount,
    ).drop("customer_signup_date")

    return orders_out


def apply_business_logic_checks(
    customers_df: DataFrame,
    orders_df: DataFrame,
    products_df: DataFrame,
) -> tuple[DataFrame, DataFrame, DataFrame]:
    customers_out = _apply_customer_business_logic(customers_df)
    products_out = _apply_product_business_logic(products_df)
    orders_out = _apply_order_business_logic(orders_df, customers_df)
    return customers_out, orders_out, products_out
