"""Pydantic configuration models for the data generator."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

GENERATOR_VERSION = "1.0.0"

# Mandatory assignment values — protected when locked=True
MANDATORY_DATASET_SIZES = {
    "customer_count": 10_000,
    "order_count": 100_000,
    "product_count": 500,
}

MANDATORY_ANOMALY_COUNTS = {
    "null_email_count": 50,
    "duplicate_customer_id_count": 10,
    "null_customer_id_count": 100,
    "null_product_id_count": 200,
    "invalid_customer_fk_count": 50,
    "invalid_product_fk_count": 30,
    "duplicate_order_id_count": 20,
}


class GeneratorMode(str, Enum):
    CORE = "core"
    EXTENDED = "extended"


class GeneratorSection(BaseModel):
    version: str = GENERATOR_VERSION
    mode: GeneratorMode = GeneratorMode.CORE


class ReproducibilityConfig(BaseModel):
    random_seed: int = 42


class DatasetSizesConfig(BaseModel):
    customer_count: int = 10_000
    order_count: int = 100_000
    product_count: int = 500


class CustomerAnomalyConfig(BaseModel):
    null_email_count: int = 50
    duplicate_customer_id_count: int = 10


class OrderAnomalyConfig(BaseModel):
    null_customer_id_count: int = 100
    null_product_id_count: int = 200
    invalid_customer_fk_count: int = 50
    invalid_product_fk_count: int = 30
    duplicate_order_id_count: int = 20


class MandatoryAnomaliesConfig(BaseModel):
    locked: bool = True
    customers: CustomerAnomalyConfig = Field(default_factory=CustomerAnomalyConfig)
    orders: OrderAnomalyConfig = Field(default_factory=OrderAnomalyConfig)


class ExtendedAnomaliesConfig(BaseModel):
    enabled: bool = False
    customers: dict[str, int] = Field(default_factory=dict)
    orders: dict[str, int] = Field(default_factory=dict)
    products: dict[str, int] = Field(default_factory=dict)


class ProductCategoryConfig(BaseModel):
    name: str
    weight: float
    price_range: tuple[Decimal, Decimal]

    @field_validator("price_range", mode="before")
    @classmethod
    def parse_price_range(cls, value: Any) -> tuple[Decimal, Decimal]:
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return Decimal(str(value[0])), Decimal(str(value[1]))
        raise ValueError("price_range must be a two-element list of numbers")


class CountryConfig(BaseModel):
    name: str
    weight: float


class LifetimeValueRange(BaseModel):
    min: Decimal
    max: Decimal


class DateRangeConfig(BaseModel):
    start_date: date
    end_date: date
    min_days_between_signup_and_order: int = 0

    @model_validator(mode="after")
    def validate_date_order(self) -> DateRangeConfig:
        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        return self


class QuantityRangeConfig(BaseModel):
    min: int = 1
    max: int = 50
    weights: dict[str, float] = Field(
        default_factory=lambda: {"1-3": 0.70, "4-10": 0.25, "11-50": 0.05}
    )


class RelationshipConfig(BaseModel):
    inactive_customer_pct_min: float = 0.05
    inactive_customer_pct_max: float = 0.10
    pareto_alpha: float = 1.5
    product_popularity_skew: float = 2.0


class OutlierThresholds(BaseModel):
    excessive_lifetime_value: Decimal = Decimal("10000.00")
    large_quantity: int = 100
    large_transaction_value: Decimal = Decimal("50000.00")


class BusinessParametersConfig(BaseModel):
    customer_segments: dict[str, float]
    order_statuses: dict[str, float]
    product_categories: list[ProductCategoryConfig]
    date_range: DateRangeConfig
    quantity_range: QuantityRangeConfig = Field(default_factory=QuantityRangeConfig)
    price_variance_pct: float = 0.05
    countries: list[CountryConfig]
    lifetime_value: dict[str, LifetimeValueRange]
    relationship: RelationshipConfig = Field(default_factory=RelationshipConfig)
    outlier_thresholds: OutlierThresholds = Field(default_factory=OutlierThresholds)

    @model_validator(mode="after")
    def validate_weights_sum(self) -> BusinessParametersConfig:
        for name, weights in [
            ("customer_segments", self.customer_segments),
            ("order_statuses", self.order_statuses),
        ]:
            total = sum(weights.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(f"{name} weights must sum to approximately 1.0, got {total}")

        cat_total = sum(c.weight for c in self.product_categories)
        if abs(cat_total - 1.0) > 0.01:
            raise ValueError(
                f"product_categories weights must sum to approximately 1.0, got {cat_total}"
            )

        country_total = sum(c.weight for c in self.countries)
        if abs(country_total - 1.0) > 0.01:
            raise ValueError(
                f"countries weights must sum to approximately 1.0, got {country_total}"
            )
        return self


class OutputConfig(BaseModel):
    directory: str = "./data/landing"
    customers_file: str = "customers.csv"
    orders_file: str = "orders.csv"
    products_file: str = "products.csv"
    validation_report: str = "./reports/validation_report.json"
    anomaly_report: str = "./reports/anomaly_report.md"
    anomaly_manifest: str = "./reports/anomaly_manifest.json"


class GeneratorConfig(BaseModel):
    generator: GeneratorSection = Field(default_factory=GeneratorSection)
    reproducibility: ReproducibilityConfig = Field(default_factory=ReproducibilityConfig)
    dataset_sizes: DatasetSizesConfig = Field(default_factory=DatasetSizesConfig)
    mandatory_anomalies: MandatoryAnomaliesConfig = Field(
        default_factory=MandatoryAnomaliesConfig
    )
    extended_anomalies: ExtendedAnomaliesConfig = Field(
        default_factory=ExtendedAnomaliesConfig
    )
    business_parameters: BusinessParametersConfig
    output: OutputConfig = Field(default_factory=OutputConfig)

    @model_validator(mode="after")
    def enforce_mandatory_lock(self) -> GeneratorConfig:
        if not self.mandatory_anomalies.locked:
            return self

        errors: list[str] = []

        for key, expected in MANDATORY_DATASET_SIZES.items():
            actual = getattr(self.dataset_sizes, key)
            if actual != expected:
                errors.append(
                    f"dataset_sizes.{key}: expected {expected} (locked), got {actual}"
                )

        customer_anomalies = self.mandatory_anomalies.customers
        for key in ("null_email_count", "duplicate_customer_id_count"):
            expected = MANDATORY_ANOMALY_COUNTS[key]
            actual = getattr(customer_anomalies, key)
            if actual != expected:
                errors.append(
                    f"mandatory_anomalies.customers.{key}: "
                    f"expected {expected} (locked), got {actual}"
                )

        order_anomalies = self.mandatory_anomalies.orders
        for key in (
            "null_customer_id_count",
            "null_product_id_count",
            "invalid_customer_fk_count",
            "invalid_product_fk_count",
            "duplicate_order_id_count",
        ):
            expected = MANDATORY_ANOMALY_COUNTS[key]
            actual = getattr(order_anomalies, key)
            if actual != expected:
                errors.append(
                    f"mandatory_anomalies.orders.{key}: "
                    f"expected {expected} (locked), got {actual}"
                )

        if errors:
            raise ValueError(
                "Configuration violates locked mandatory requirements:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )
        return self

    @model_validator(mode="after")
    def enforce_extended_mode_gating(self) -> GeneratorConfig:
        if self.generator.mode == GeneratorMode.CORE:
            self.extended_anomalies.enabled = False
        elif self.generator.mode == GeneratorMode.EXTENDED:
            self.extended_anomalies.enabled = True
        return self

    @property
    def is_core_mode(self) -> bool:
        return self.generator.mode == GeneratorMode.CORE

    @property
    def expected_customer_row_count(self) -> int:
        return (
            self.dataset_sizes.customer_count
            + self.mandatory_anomalies.customers.duplicate_customer_id_count
        )

    @property
    def expected_order_row_count(self) -> int:
        return (
            self.dataset_sizes.order_count
            + self.mandatory_anomalies.orders.duplicate_order_id_count
        )

    def orphan_customer_id_range(self) -> range:
        """Reserved namespace for invalid customer FKs (not in customers.csv)."""
        start = self.dataset_sizes.customer_count + 1
        count = self.mandatory_anomalies.orders.invalid_customer_fk_count
        return range(start, start + count)

    def orphan_product_id_range(self) -> range:
        """Reserved namespace for invalid product FKs (not in products.csv)."""
        start = self.dataset_sizes.product_count + 1
        count = self.mandatory_anomalies.orders.invalid_product_fk_count
        return range(start, start + count)

    def valid_customer_ids(self) -> set[int]:
        return set(range(1, self.dataset_sizes.customer_count + 1))

    def valid_product_ids(self) -> set[int]:
        return set(range(1, self.dataset_sizes.product_count + 1))
