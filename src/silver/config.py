"""Pydantic configuration models for Silver layer processing."""

from __future__ import annotations

from typing import Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator


class SilverPathsConfig(BaseModel):
    bronze_root: str = "./data/bronze"
    silver_root: str = "./data/silver"


class SparkConfig(BaseModel):
    app_name: str = "SilverLayer"
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


class TableRegistrationConfig(BaseModel):
    enabled: bool = False
    catalog: Optional[str] = None
    database: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("database", "schema"),
    )


class SilverConfig(BaseModel):
    paths: SilverPathsConfig = Field(default_factory=SilverPathsConfig)
    spark: SparkConfig = Field(default_factory=SparkConfig)
    write: WriteConfig = Field(default_factory=WriteConfig)
    table_registration: TableRegistrationConfig = Field(
        default_factory=TableRegistrationConfig
    )

    def bronze_path(self, dataset_name: str) -> str:
        return f"{self.paths.bronze_root.rstrip('/')}/{dataset_name}"

    def silver_path(self, dataset_name: str) -> str:
        return f"{self.paths.silver_root.rstrip('/')}/{dataset_name}"

    def metrics_path(self) -> str:
        return f"{self.paths.silver_root.rstrip('/')}/quality_metrics"

