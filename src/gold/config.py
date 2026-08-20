"""Pydantic configuration models for Gold layer processing."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator


class GoldPathsConfig(BaseModel):
    silver_root: str = "./data/silver"
    gold_root: str = "./data/gold"


class SparkConfig(BaseModel):
    app_name: str = "GoldLayer"
    local_master: str = "local[*]"


class WriteConfig(BaseModel):
    mode: str = "overwrite"

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        allowed = {"overwrite", "error", "ignore"}
        if value not in allowed:
            raise ValueError(
                f"Unsupported write mode '{value}'. Allowed values: {sorted(allowed)}"
            )
        return value


class BusinessRulesConfig(BaseModel):
    high_value_revenue_threshold: Decimal = Decimal("1000.00")
    eligible_order_statuses: list[str] = Field(
        default_factory=lambda: ["Completed"]
    )

    @field_validator("eligible_order_statuses")
    @classmethod
    def validate_statuses(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("eligible_order_statuses must contain at least one status")
        return value


class TableRegistrationConfig(BaseModel):
    enabled: bool = False
    catalog: Optional[str] = None
    database: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("database", "schema"),
    )


class GoldConfig(BaseModel):
    paths: GoldPathsConfig = Field(default_factory=GoldPathsConfig)
    spark: SparkConfig = Field(default_factory=SparkConfig)
    write: WriteConfig = Field(default_factory=WriteConfig)
    business_rules: BusinessRulesConfig = Field(default_factory=BusinessRulesConfig)
    table_registration: TableRegistrationConfig = Field(
        default_factory=TableRegistrationConfig
    )

    def silver_path(self, dataset_name: str) -> str:
        return f"{self.paths.silver_root.rstrip('/')}/{dataset_name}"

    def gold_path(self, dataset_name: str) -> str:
        return f"{self.paths.gold_root.rstrip('/')}/{dataset_name}"
