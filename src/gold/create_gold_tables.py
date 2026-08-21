"""Gold layer orchestration for business aggregation datasets."""

from __future__ import annotations

import sys

from pyspark.sql import DataFrame, SparkSession

from gold.config_loader import default_config_path, load_config
from gold.gold_utils import (
    GoldError,
    configure_logging,
    eligible_order_revenue,
    get_spark_session,
    load_sql,
    reconcile_gold_outputs,
    register_gold_table_if_enabled,
    register_valid_silver_views,
    render_sql,
    validate_output_schema,
    validate_unique_keys,
    write_gold_dataset,
)


GOLD_SQL_FILES = {
    "sales_by_product": "01_sales_by_product.sql",
    "revenue_by_customer": "02_revenue_by_customer.sql",
    "daily_weekly_trends": "03_daily_weekly_trends.sql",
    "customer_segmentation": "04_customer_segmentation.sql",
}


def _execute_gold_sql(
    spark: SparkSession,
    config,
    dataset_name: str,
) -> DataFrame:
    sql_template = load_sql(GOLD_SQL_FILES[dataset_name])
    sql = render_sql(sql_template, config)
    try:
        return spark.sql(sql)
    except Exception as exc:
        raise GoldError(
            f"Failed executing Gold SQL for dataset '{dataset_name}'"
        ) from exc


def _validate_dataset(df: DataFrame, dataset_name: str) -> None:
    validate_output_schema(df, dataset_name)
    if dataset_name == "sales_by_product":
        validate_unique_keys(df, dataset_name, "product_id")
    elif dataset_name == "revenue_by_customer":
        validate_unique_keys(df, dataset_name, "customer_id")
    elif dataset_name == "daily_weekly_trends":
        validate_unique_keys(df, dataset_name, ["period_type", "period_start"])
    elif dataset_name == "customer_segmentation":
        validate_unique_keys(df, dataset_name, "segment_type")


def run_gold_pipeline(config_path: str | None = None) -> dict[str, int | float | str]:
    configure_logging()
    config = load_config(config_path or default_config_path())
    spark = get_spark_session(config)

    view_counts = register_valid_silver_views(spark, config)

    gold_outputs: dict[str, DataFrame] = {}
    for dataset_name in GOLD_SQL_FILES:
        gold_df = _execute_gold_sql(spark, config, dataset_name)
        _validate_dataset(gold_df, dataset_name)
        gold_outputs[dataset_name] = gold_df

    for dataset_name, gold_df in gold_outputs.items():
        temp_view = f"{dataset_name}_gold"
        gold_df.createOrReplaceTempView(temp_view)

    reconcile_gold_outputs(spark)

    eligible_revenue = eligible_order_revenue(spark)

    for dataset_name, gold_df in gold_outputs.items():
        write_gold_dataset(gold_df, config, dataset_name)
        register_gold_table_if_enabled(spark, config, dataset_name)

    return {
        "valid_customers_rows": int(view_counts["valid_customers_rows"]),
        "valid_orders_rows": int(view_counts["valid_orders_rows"]),
        "valid_products_rows": int(view_counts["valid_products_rows"]),
        "sales_by_product_rows": gold_outputs["sales_by_product"].count(),
        "revenue_by_customer_rows": gold_outputs["revenue_by_customer"].count(),
        "daily_weekly_trends_rows": gold_outputs["daily_weekly_trends"].count(),
        "customer_segmentation_rows": gold_outputs["customer_segmentation"].count(),
        "eligible_order_revenue": float(eligible_revenue),
        "high_value_threshold": float(config.business_rules.high_value_revenue_threshold),
        "eligible_order_statuses": ",".join(config.business_rules.eligible_order_statuses),
    }


def main() -> int:
    summary = run_gold_pipeline()
    print("Gold pipeline summary:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GoldError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
