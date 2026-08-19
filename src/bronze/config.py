"""Pydantic configuration models for Bronze layer ingestion."""

from __future__ import annotations

from typing import Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator


class BronzePathsConfig(BaseModel):
    source_root: str = "./data"
    bronze_root: str = "./data/bronze"


class BronzeSourceFilesConfig(BaseModel):
    customers: str = "customers.csv"
    orders: str = "orders.csv"
    products: str = "products.csv"


class SparkConfig(BaseModel):
    app_name: str = "BronzeIngestion"
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

    @field_validator("catalog", "database")
    @classmethod
    def strip_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class MetadataConfig(BaseModel):
    directory: str = "_metadata"
    file_name: str = "ingestion_metadata.parquet"


class BronzeConfig(BaseModel):
    paths: BronzePathsConfig = Field(default_factory=BronzePathsConfig)
    source_files: BronzeSourceFilesConfig = Field(default_factory=BronzeSourceFilesConfig)
    spark: SparkConfig = Field(default_factory=SparkConfig)
    write: WriteConfig = Field(default_factory=WriteConfig)
    table_registration: TableRegistrationConfig = Field(
        default_factory=TableRegistrationConfig
    )
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)

    def source_path(self, dataset_name: str) -> str:
        file_name = getattr(self.source_files, dataset_name)
        return f"{self.paths.source_root.rstrip('/')}/{file_name}"

    def bronze_path(self, dataset_name: str) -> str:
        return f"{self.paths.bronze_root.rstrip('/')}/{dataset_name}"

    def metadata_path(self) -> str:
        return (
            f"{self.paths.bronze_root.rstrip('/')}/"
            f"{self.metadata.directory.rstrip('/')}/{self.metadata.file_name}"
        )
