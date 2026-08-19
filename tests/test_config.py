"""Tests for configuration validation and lock enforcement."""

from __future__ import annotations

import pytest

from data_generation.config import GeneratorConfig, MANDATORY_ANOMALY_COUNTS


def test_load_default_config(config):
    assert config.dataset_sizes.customer_count == 10_000
    assert config.dataset_sizes.order_count == 100_000
    assert config.dataset_sizes.product_count == 500
    assert config.generator.mode.value == "core"
    assert config.is_core_mode is True


def test_expected_row_counts(config):
    assert config.expected_customer_row_count == 10_010
    assert config.expected_order_row_count == 100_020


def test_orphan_id_namespaces(config):
    assert set(config.orphan_customer_id_range()) == set(range(10_001, 10_051))
    assert set(config.orphan_product_id_range()) == set(range(501, 531))
    assert set(config.orphan_customer_id_range()).isdisjoint(config.valid_customer_ids())
    assert set(config.orphan_product_id_range()).isdisjoint(config.valid_product_ids())


def test_lock_enforcement_rejects_modified_counts(config):
    data = config.model_dump()
    data["mandatory_anomalies"]["customers"]["null_email_count"] = 49
    with pytest.raises(ValueError, match="locked"):
        GeneratorConfig.model_validate(data)


def test_lock_enforcement_rejects_modified_dataset_sizes(config):
    data = config.model_dump()
    data["dataset_sizes"]["customer_count"] = 9999
    with pytest.raises(ValueError, match="locked"):
        GeneratorConfig.model_validate(data)


def test_unlocked_config_allows_modification(config):
    data = config.model_dump()
    data["mandatory_anomalies"]["locked"] = False
    data["dataset_sizes"]["customer_count"] = 100
    cfg = GeneratorConfig.model_validate(data)
    assert cfg.dataset_sizes.customer_count == 100


def test_core_mode_disables_extended(config):
    data = config.model_dump()
    data["extended_anomalies"]["enabled"] = True
    cfg = GeneratorConfig.model_validate(data)
    assert cfg.extended_anomalies.enabled is False


def test_mandatory_anomaly_counts(config):
    assert config.mandatory_anomalies.customers.null_email_count == MANDATORY_ANOMALY_COUNTS["null_email_count"]
    assert config.mandatory_anomalies.orders.duplicate_order_id_count == 20
