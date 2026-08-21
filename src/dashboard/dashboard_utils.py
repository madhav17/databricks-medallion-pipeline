"""Shared utilities for dashboard SQL execution and validation."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from gold.config import GoldConfig
from gold.gold_utils import GoldError, get_spark_session

logger = logging.getLogger(__name__)


class DashboardError(Exception):
    """Raised when dashboard query processing fails."""


GOLD_VIEW_NAMES = {
    "sales_by_product": "gold_sales_by_product",
    "revenue_by_customer": "gold_revenue_by_customer",
    "customer_segmentation": "gold_customer_segmentation",
}

EXPECTED_SEGMENT_TYPES = {
    "High-Value",
    "Inactive",
    "One-Time",
    "Repeat",
}


@dataclass(frozen=True)
class DashboardQuery:
    query_id: str
    title: str
    sql: str


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def dashboard_queries_path() -> Path:
    return Path(__file__).parent / "dashboard_queries.sql"


def load_dashboard_queries(path: Path | None = None) -> dict[str, DashboardQuery]:
    sql_path = path or dashboard_queries_path()
    if not sql_path.exists():
        raise DashboardError(f"Dashboard SQL file not found: {sql_path}")

    content = sql_path.read_text(encoding="utf-8")
    section_pattern = re.compile(
        r"-{10,}\s*\n--\s*(\d+[a-z]?)\.\s*(.+?)\s*\n-{10,}\s*\n(.*?)(?=\n-{10,}\s*\n--\s*\d|\Z)",
        re.DOTALL,
    )
    queries: dict[str, DashboardQuery] = {}

    for match in section_pattern.finditer(content):
        query_number, title, sql = match.groups()
        sql = sql.strip()
        if not sql:
            continue
        query_id = _query_id_from_number(query_number)
        queries[query_id] = DashboardQuery(
            query_id=query_id,
            title=title.strip(),
            sql=sql,
        )

    if len(queries) < 3:
        raise DashboardError(
            f"Expected at least 3 dashboard queries in {sql_path}, found {len(queries)}"
        )

    return queries


def _query_id_from_number(query_number: str) -> str:
    mapping = {
        "1": "top_10_products_by_revenue",
        "2": "customer_revenue_distribution",
        "3": "customer_segmentation",
        "4": "total_revenue_kpi",
    }
    return mapping.get(query_number, f"query_{query_number}")


def register_gold_views(spark: SparkSession, config: GoldConfig) -> dict[str, int]:
    counts: dict[str, int] = {}
    for dataset_name, view_name in GOLD_VIEW_NAMES.items():
        path = config.gold_path(dataset_name)
        is_uri_path = "://" in path
        if (not is_uri_path) and (not Path(path).exists()):
            raise DashboardError(
                f"Gold input missing for dataset '{dataset_name}' at path '{path}'"
            )
        try:
            df = spark.read.parquet(path)
        except Exception as exc:
            raise DashboardError(
                f"Failed to read Gold Parquet for dataset '{dataset_name}' at path '{path}'"
            ) from exc
        df.createOrReplaceTempView(view_name)
        counts[view_name] = df.count()
    return counts


def execute_dashboard_query(spark: SparkSession, query: DashboardQuery) -> DataFrame:
    try:
        return spark.sql(query.sql)
    except Exception as exc:
        raise DashboardError(
            f"Failed executing dashboard query '{query.query_id}'"
        ) from exc


def _decimal(value) -> Decimal:
    return Decimal(str(value))


def reconcile_dashboard_outputs(
    top_products_df: DataFrame,
    customer_revenue_df: DataFrame,
    segmentation_df: DataFrame,
    sales_by_product_df: DataFrame,
    revenue_by_customer_df: DataFrame,
    segmentation_source_df: DataFrame,
) -> None:
    top_product_revenue = top_products_df.agg({"total_revenue": "sum"}).collect()[0][0]
    gold_product_revenue = sales_by_product_df.agg({"total_revenue": "sum"}).collect()[0][0]
    if top_product_revenue is not None and _decimal(top_product_revenue) > _decimal(
        gold_product_revenue
    ):
        raise DashboardError(
            "Top 10 product revenue exceeds total Gold product revenue"
        )

    dashboard_customer_total = customer_revenue_df.agg({"total_revenue": "sum"}).collect()[
        0
    ][0]
    gold_customer_total = revenue_by_customer_df.agg({"total_revenue": "sum"}).collect()[0][
        0
    ]
    if _decimal(dashboard_customer_total) != _decimal(gold_customer_total):
        raise DashboardError(
            "Customer revenue distribution total does not match Gold revenue_by_customer"
        )

    dashboard_segment_revenue = segmentation_df.agg({"total_revenue": "sum"}).collect()[0][
        0
    ]
    gold_segment_revenue = segmentation_source_df.agg({"total_revenue": "sum"}).collect()[
        0
    ][0]
    if _decimal(dashboard_segment_revenue) != _decimal(gold_segment_revenue):
        raise DashboardError(
            "Customer segmentation revenue does not match Gold customer_segmentation"
        )

    dashboard_segment_customers = segmentation_df.agg({"customer_count": "sum"}).collect()[
        0
    ][0]
    gold_segment_customers = segmentation_source_df.agg({"customer_count": "sum"}).collect()[
        0
    ][0]
    if int(dashboard_segment_customers) != int(gold_segment_customers):
        raise DashboardError(
            "Customer segmentation customer_count does not match Gold customer_segmentation"
        )


def validate_dashboard_queries(
    config: GoldConfig,
    config_path: str | None = None,
    queries_path: Path | None = None,
    sample_rows: int = 5,
) -> dict[str, int | float | str]:
    configure_logging()
    spark = get_spark_session(config)
    view_counts = register_gold_views(spark, config)
    queries = load_dashboard_queries(queries_path)

    results: dict[str, DataFrame] = {}
    for query_id, query in queries.items():
        logger.info("Executing dashboard query: %s", query_id)
        results[query_id] = execute_dashboard_query(spark, query)

    top_products_df = results["top_10_products_by_revenue"]
    customer_revenue_df = results["customer_revenue_distribution"]
    segmentation_df = results["customer_segmentation"]

    sales_by_product_df = spark.table(GOLD_VIEW_NAMES["sales_by_product"])
    revenue_by_customer_df = spark.table(GOLD_VIEW_NAMES["revenue_by_customer"])
    segmentation_source_df = spark.table(GOLD_VIEW_NAMES["customer_segmentation"])

    _validate_top_products(top_products_df)
    _validate_customer_revenue(customer_revenue_df)
    _validate_segmentation(segmentation_df)
    reconcile_dashboard_outputs(
        top_products_df,
        customer_revenue_df,
        segmentation_df,
        sales_by_product_df,
        revenue_by_customer_df,
        segmentation_source_df,
    )

    summary = {
        "gold_sales_by_product_rows": view_counts[GOLD_VIEW_NAMES["sales_by_product"]],
        "gold_revenue_by_customer_rows": view_counts[GOLD_VIEW_NAMES["revenue_by_customer"]],
        "gold_customer_segmentation_rows": view_counts[
            GOLD_VIEW_NAMES["customer_segmentation"]
        ],
        "top_10_products_rows": top_products_df.count(),
        "customer_revenue_rows": customer_revenue_df.count(),
        "customer_segmentation_rows": segmentation_df.count(),
    }

    if "total_revenue_kpi" in results:
        kpi_value = results["total_revenue_kpi"].collect()[0]["total_revenue"]
        summary["total_revenue_kpi"] = float(kpi_value)
        gold_total = revenue_by_customer_df.agg({"total_revenue": "sum"}).collect()[0][0]
        if _decimal(kpi_value) != _decimal(gold_total):
            raise DashboardError("Total revenue KPI does not match Gold customer revenue")

    if sample_rows > 0:
        print("\nSample: Top 10 Products by Revenue")
        top_products_df.show(min(sample_rows, 10), truncate=False)
        print("\nSample: Customer Revenue Distribution")
        customer_revenue_df.show(sample_rows, truncate=False)
        print("\nSample: Customer Segmentation")
        segmentation_df.show(sample_rows, truncate=False)
        if "total_revenue_kpi" in results:
            print("\nSample: Total Revenue KPI")
            results["total_revenue_kpi"].show(truncate=False)

    return summary


def _validate_top_products(df: DataFrame) -> None:
    row_count = df.count()
    if row_count > 10:
        raise DashboardError(f"Top 10 products query returned {row_count} rows")

    if row_count == 0:
        return

    product_ids = df.select("product_id").distinct().count()
    if product_ids != row_count:
        raise DashboardError("Top 10 products query contains duplicate product_id values")

    revenues = [row.total_revenue for row in df.select("total_revenue").collect()]
    if any(revenue is not None and _decimal(revenue) < 0 for revenue in revenues):
        raise DashboardError("Top 10 products query contains negative total_revenue")

    ordered = df.orderBy(df["total_revenue"].desc(), df["product_id"].asc()).collect()
    actual = df.collect()
    for expected, actual_row in zip(ordered, actual):
        if expected.product_id != actual_row.product_id:
            raise DashboardError("Top 10 products query is not sorted by revenue descending")


def _validate_customer_revenue(df: DataFrame) -> None:
    row_count = df.count()
    if row_count == 0:
        return

    if row_count == 1 and "customer_id" not in df.columns:
        raise DashboardError(
            "Customer revenue distribution appears aggregated to a single summary row"
        )

    customer_ids = df.select("customer_id").distinct().count()
    if customer_ids != row_count:
        raise DashboardError("Customer revenue distribution contains duplicate customer_id")


def _validate_segmentation(df: DataFrame) -> None:
    row_count = df.count()
    if row_count == 0:
        return

    segment_types = {row.segment_type for row in df.select("segment_type").collect()}
    if not segment_types.issubset(EXPECTED_SEGMENT_TYPES):
        unexpected = segment_types - EXPECTED_SEGMENT_TYPES
        raise DashboardError(f"Unexpected segment types in dashboard query: {unexpected}")

    segments = df.select("segment_type").distinct().count()
    if segments != row_count:
        raise DashboardError("Customer segmentation query contains duplicate segment_type")

    for row in df.collect():
        if row.customer_count < 0:
            raise DashboardError("Customer segmentation contains negative customer_count")
        if row.total_revenue is not None and _decimal(row.total_revenue) < 0:
            raise DashboardError("Customer segmentation contains negative total_revenue")
