"""YAML configuration loader for Bronze layer ingestion."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from bronze.config import BronzeConfig


def load_config(path: str | Path) -> BronzeConfig:
    """Load and validate Bronze configuration from a YAML file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Bronze configuration file not found: {config_path}")

    with config_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if raw is None:
        raise ValueError(f"Bronze configuration file is empty: {config_path}")

    config = BronzeConfig.model_validate(raw)
    return _apply_env_overrides(config)


def _apply_env_overrides(config: BronzeConfig) -> BronzeConfig:
    """Apply optional environment variable overrides."""
    updates: dict = {}

    if source_root := os.environ.get("BRONZE_SOURCE_ROOT"):
        updates.setdefault("paths", {})["source_root"] = source_root

    if bronze_root := os.environ.get("BRONZE_ROOT"):
        updates.setdefault("paths", {})["bronze_root"] = bronze_root

    if catalog := os.environ.get("BRONZE_CATALOG"):
        updates.setdefault("table_registration", {})["catalog"] = catalog

    if schema := os.environ.get("BRONZE_SCHEMA"):
        updates.setdefault("table_registration", {})["database"] = schema

    if enabled := os.environ.get("BRONZE_TABLE_REGISTRATION_ENABLED"):
        updates.setdefault("table_registration", {})["enabled"] = enabled.lower() in {
            "1",
            "true",
            "yes",
        }

    if not updates:
        return config

    data = config.model_dump(mode="json")
    for section, values in updates.items():
        data[section].update(values)
    return BronzeConfig.model_validate(data)


def default_config_path() -> Path:
    """Return the default Bronze configuration file path."""
    candidates = [
        Path("config/bronze_config.yaml"),
        Path("bronze_config.yaml"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
