"""Explicit PySpark schemas for Bronze layer source datasets."""

from __future__ import annotations

from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

# Monetary fields use Decimal(10, 2) — two decimal places, matching the
# data generator's CSV formatting and sufficient for all assignment values.
MONETARY_DECIMAL = DecimalType(10, 2)

CUSTOMERS_SCHEMA = StructType(
    [
        StructField("customer_id", IntegerType(), nullable=True),
        StructField("customer_name", StringType(), nullable=True),
        StructField("email", StringType(), nullable=True),
        StructField("country", StringType(), nullable=True),
        StructField("signup_date", DateType(), nullable=True),
        StructField("customer_segment", StringType(), nullable=True),
        StructField("lifetime_value", MONETARY_DECIMAL, nullable=True),
    ]
)

ORDERS_SCHEMA = StructType(
    [
        StructField("order_id", IntegerType(), nullable=True),
        StructField("customer_id", IntegerType(), nullable=True),
        StructField("order_date", DateType(), nullable=True),
        StructField("product_id", IntegerType(), nullable=True),
        StructField("quantity", IntegerType(), nullable=True),
        StructField("unit_price", MONETARY_DECIMAL, nullable=True),
        StructField("total_amount", MONETARY_DECIMAL, nullable=True),
        StructField("order_status", StringType(), nullable=True),
        StructField("payment_date", DateType(), nullable=True),
    ]
)

PRODUCTS_SCHEMA = StructType(
    [
        StructField("product_id", IntegerType(), nullable=True),
        StructField("product_name", StringType(), nullable=True),
        StructField("category", StringType(), nullable=True),
        StructField("price", MONETARY_DECIMAL, nullable=True),
        StructField("cost", MONETARY_DECIMAL, nullable=True),
        StructField("stock_quantity", IntegerType(), nullable=True),
        StructField("reorder_level", IntegerType(), nullable=True),
    ]
)

DATASET_SCHEMAS: dict[str, StructType] = {
    "customers": CUSTOMERS_SCHEMA,
    "orders": ORDERS_SCHEMA,
    "products": PRODUCTS_SCHEMA,
}
