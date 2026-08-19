"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from data_generation.config_loader import load_config


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def config_path(project_root: Path) -> Path:
    return project_root / "config" / "generator_config.yaml"


@pytest.fixture
def config(config_path: Path):
    return load_config(config_path)


@pytest.fixture
def small_config(config):
    """Return a config with smaller dataset sizes for fast tests."""
    data = config.model_dump()
    data["dataset_sizes"]["customer_count"] = 100
    data["dataset_sizes"]["order_count"] = 500
    data["dataset_sizes"]["product_count"] = 50
    data["mandatory_anomalies"]["locked"] = False
    data["mandatory_anomalies"]["customers"]["null_email_count"] = 5
    data["mandatory_anomalies"]["customers"]["duplicate_customer_id_count"] = 2
    data["mandatory_anomalies"]["orders"]["null_customer_id_count"] = 10
    data["mandatory_anomalies"]["orders"]["null_product_id_count"] = 20
    data["mandatory_anomalies"]["orders"]["invalid_customer_fk_count"] = 5
    data["mandatory_anomalies"]["orders"]["invalid_product_fk_count"] = 3
    data["mandatory_anomalies"]["orders"]["duplicate_order_id_count"] = 2

    from data_generation.config import GeneratorConfig
    return GeneratorConfig.model_validate(data)
