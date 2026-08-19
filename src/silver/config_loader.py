"""YAML configuration loader for Silver layer processing."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from silver.config import SilverConfig


def load_config(path: str | Path) -> SilverConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Silver configuration file not found: {config_path}")

    with config_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if raw is None:
        raise ValueError(f"Silver configuration file is empty: {config_path}")

    config = SilverConfig.model_validate(raw)
    return _apply_env_overrides(config)


def _apply_env_overrides(config: SilverConfig) -> SilverConfig:
    updates: dict = {}

    if bronze_root := os.environ.get("SILVER_BRONZE_ROOT"):
        updates.setdefault("paths", {})["bronze_root"] = bronze_root

    if silver_root := os.environ.get("SILVER_ROOT"):
        updates.setdefault("paths", {})["silver_root"] = silver_root

    if catalog := os.environ.get("SILVER_CATALOG"):
        updates.setdefault("table_registration", {})["catalog"] = catalog

    if database := os.environ.get("SILVER_SCHEMA"):
        updates.setdefault("table_registration", {})["database"] = database

    if enabled := os.environ.get("SILVER_TABLE_REGISTRATION_ENABLED"):
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
    return SilverConfig.model_validate(data)


def default_config_path() -> Path:
    candidates = [
        Path("config/silver_config.yaml"),
        Path("silver_config.yaml"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]

