"""Silver layer orchestration for quality-flagged datasets."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from silver.config_loader import default_config_path, load_config
from silver.silver_utils import (
    SilverError,
    configure_logging,
    finalize_quality_columns,
    get_spark_session,
    read_bronze_dataset,
    validate_required_columns,
    write_silver_dataset,
)

completeness_module = importlib.import_module("silver.01_quality_completeness")
uniqueness_module = importlib.import_module("silver.02_quality_uniqueness")
type_validation_module = importlib.import_module("silver.03_quality_type_validation")
referential_module = importlib.import_module("silver.04_quality_referential_integrity")

apply_completeness_checks = completeness_module.apply_completeness_checks
apply_uniqueness_checks = uniqueness_module.apply_uniqueness_checks
validate_type_schemas = type_validation_module.validate_type_schemas
apply_referential_integrity_checks = referential_module.apply_referential_integrity_checks


@dataclass(frozen=True)
class MetricsRow:
    dataset_name: str
    check_name: str
    total_rows: int
    passed_rows: int
    failed_rows: int
    pass_percentage: float
    fail_percentage: float


METRICS_SCHEMA = StructType(
    [
        StructField("dataset_name", StringType(), nullable=False),
        StructField("check_name", StringType(), nullable=False),
        StructField("total_rows", LongType(), nullable=False),
        StructField("passed_rows", LongType(), nullable=False),
        StructField("failed_rows", LongType(), nullable=False),
        StructField("pass_percentage", DoubleType(), nullable=False),
        StructField("fail_percentage", DoubleType(), nullable=False),
    ]
)


def _metrics_row(
    dataset_name: str,
    check_name: str,
    total_rows: int,
    failed_rows: int,
) -> MetricsRow:
    passed_rows = total_rows - failed_rows
    pass_pct = (passed_rows / total_rows) * 100 if total_rows else 0.0
    fail_pct = (failed_rows / total_rows) * 100 if total_rows else 0.0
    return MetricsRow(
        dataset_name=dataset_name,
        check_name=check_name,
        total_rows=total_rows,
        passed_rows=passed_rows,
        failed_rows=failed_rows,
        pass_percentage=round(pass_pct, 6),
        fail_percentage=round(fail_pct, 6),
    )


def _count_rows(df: DataFrame) -> int:
    return int(df.count())


def _count_failed(df: DataFrame, condition) -> int:
    return int(df.filter(condition).count())


def _register_silver_table_if_enabled(config, spark, dataset_name: str) -> None:
    if not config.table_registration.enabled:
        return
    if not config.table_registration.catalog or not config.table_registration.database:
        raise SilverError(
            "Silver table registration enabled but catalog/database not configured"
        )
    table_name = (
        f"{config.table_registration.catalog}."
        f"{config.table_registration.database}.silver_{dataset_name}"
    )
    path = config.silver_path(dataset_name)
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        USING PARQUET
        LOCATION '{path}'
        """
    )


def run_silver_pipeline(config_path: str | None = None) -> dict[str, int]:
    configure_logging()
    config = load_config(config_path or default_config_path())
    spark = get_spark_session(config)

    customers_df = read_bronze_dataset(spark, config, "customers")
    orders_df = read_bronze_dataset(spark, config, "orders")
    products_df = read_bronze_dataset(spark, config, "products")

    validate_required_columns(customers_df, "customers")
    validate_required_columns(orders_df, "orders")
    validate_required_columns(products_df, "products")

    type_results = validate_type_schemas(customers_df, orders_df, products_df)

    from silver.silver_utils import init_quality_columns

    customers_df = init_quality_columns(customers_df)
    orders_df = init_quality_columns(orders_df)
    products_df = init_quality_columns(products_df)

    customers_df, orders_df, products_df = apply_completeness_checks(
        customers_df,
        orders_df,
        products_df,
    )
    customers_df, orders_df, products_df = apply_uniqueness_checks(
        customers_df,
        orders_df,
        products_df,
    )
    customers_df, orders_df, products_df = apply_referential_integrity_checks(
        customers_df,
        orders_df,
        products_df,
    )

    customers_total = _count_rows(customers_df)
    orders_total = _count_rows(orders_df)
    products_total = _count_rows(products_df)

    metrics_rows = [
        _metrics_row(
            "customers",
            "completeness",
            customers_total,
            _count_failed(customers_df, F.col("check_completeness_failed")),
        ),
        _metrics_row(
            "customers",
            "uniqueness",
            customers_total,
            _count_failed(customers_df, F.col("check_uniqueness_failed")),
        ),
        _metrics_row(
            "customers",
            "type_validation",
            customers_total,
            0 if type_results["customers"] else customers_total,
        ),
        _metrics_row(
            "orders",
            "completeness",
            orders_total,
            _count_failed(orders_df, F.col("check_completeness_failed")),
        ),
        _metrics_row(
            "orders",
            "uniqueness",
            orders_total,
            _count_failed(orders_df, F.col("check_uniqueness_failed")),
        ),
        _metrics_row(
            "orders",
            "type_validation",
            orders_total,
            0 if type_results["orders"] else orders_total,
        ),
        _metrics_row(
            "orders",
            "referential_integrity",
            orders_total,
            _count_failed(orders_df, F.col("check_referential_integrity_failed")),
        ),
        _metrics_row(
            "products",
            "type_validation",
            products_total,
            0 if type_results["products"] else products_total,
        ),
    ]

    customers_out = finalize_quality_columns(customers_df)
    orders_out = finalize_quality_columns(orders_df)
    products_out = finalize_quality_columns(products_df)

    bronze_customers_count = _count_rows(read_bronze_dataset(spark, config, "customers"))
    bronze_orders_count = _count_rows(read_bronze_dataset(spark, config, "orders"))
    bronze_products_count = _count_rows(read_bronze_dataset(spark, config, "products"))

    if customers_total != bronze_customers_count:
        raise SilverError(
            f"Row loss detected customers bronze={bronze_customers_count} silver={customers_total}"
        )
    if orders_total != bronze_orders_count:
        raise SilverError(
            f"Row loss detected orders bronze={bronze_orders_count} silver={orders_total}"
        )
    if products_total != bronze_products_count:
        raise SilverError(
            f"Row loss detected products bronze={bronze_products_count} silver={products_total}"
        )

    write_silver_dataset(customers_out, config, "customers")
    write_silver_dataset(orders_out, config, "orders")
    write_silver_dataset(products_out, config, "products")

    for dataset_name in ("customers", "orders", "products"):
        _register_silver_table_if_enabled(config, spark, dataset_name)

    metrics_df = spark.createDataFrame(
        [row.__dict__ for row in metrics_rows],
        schema=METRICS_SCHEMA,
    )
    metrics_df.write.mode(config.write.mode).parquet(config.metrics_path())

    return {
        "customers_rows": customers_total,
        "orders_rows": orders_total,
        "products_rows": products_total,
        "metrics_rows": len(metrics_rows),
    }


def main() -> int:
    summary = run_silver_pipeline()
    print("Silver pipeline summary:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SilverError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

