"""YAML configuration loader for Gold layer processing."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import yaml

from gold.config import GoldConfig


def load_config(path: str | Path) -> GoldConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Gold configuration file not found: {config_path}")

    with config_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if raw is None:
        raise ValueError(f"Gold configuration file is empty: {config_path}")

    config = GoldConfig.model_validate(raw)
    return _apply_env_overrides(config)


def _apply_env_overrides(config: GoldConfig) -> GoldConfig:
    updates: dict = {}

    if silver_root := os.environ.get("GOLD_SILVER_ROOT"):
        updates.setdefault("paths", {})["silver_root"] = silver_root

    if gold_root := os.environ.get("GOLD_ROOT"):
        updates.setdefault("paths", {})["gold_root"] = gold_root

    if threshold := os.environ.get("HIGH_VALUE_REVENUE_THRESHOLD"):
        updates.setdefault("business_rules", {})["high_value_revenue_threshold"] = Decimal(
            threshold
        )

    if statuses := os.environ.get("GOLD_ELIGIBLE_ORDER_STATUSES"):
        updates.setdefault("business_rules", {})["eligible_order_statuses"] = [
            status.strip() for status in statuses.split(",") if status.strip()
        ]

    if catalog := os.environ.get("GOLD_CATALOG"):
        updates.setdefault("table_registration", {})["catalog"] = catalog

    if database := os.environ.get("GOLD_SCHEMA"):
        updates.setdefault("table_registration", {})["database"] = database

    if enabled := os.environ.get("GOLD_TABLE_REGISTRATION_ENABLED"):
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
    return GoldConfig.model_validate(data)


def default_config_path() -> Path:
    candidates = [
        Path("config/gold_config.yaml"),
        Path("gold_config.yaml"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
