"""Type/schema validation checks for Silver layer."""

from __future__ import annotations

from pyspark.sql import DataFrame

from bronze.schemas import DATASET_SCHEMAS
from silver.silver_utils import SilverError


def validate_type_schemas(
    customers_df: DataFrame,
    orders_df: DataFrame,
    products_df: DataFrame,
) -> dict[str, bool]:
    checks = {
        "customers": _matches_expected_schema(customers_df, "customers"),
        "orders": _matches_expected_schema(orders_df, "orders"),
        "products": _matches_expected_schema(products_df, "products"),
    }
    return checks


def _matches_expected_schema(df: DataFrame, dataset_name: str) -> bool:
    expected_fields = DATASET_SCHEMAS[dataset_name].fields
    actual_fields = df.schema.fields

    expected_names = [field.name for field in expected_fields]
    actual_names = [field.name for field in actual_fields]
    if expected_names != actual_names:
        raise SilverError(
            f"Schema column mismatch for dataset '{dataset_name}'. "
            f"Expected columns {expected_names}, found {actual_names}"
        )

    for expected, actual in zip(expected_fields, actual_fields):
        if expected.dataType != actual.dataType:
            raise SilverError(
                f"Schema type mismatch for dataset '{dataset_name}' "
                f"column '{expected.name}': expected {expected.dataType}, "
                f"found {actual.dataType}"
            )

    return True

