"""End-to-end integration test for the data generator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from data_generation.config_loader import load_config
from data_generation.generate_sample_data import generate
from data_generation.verify_dataset import verify


@pytest.fixture
def e2e_config_path(project_root, tmp_path):
    """Create a test config writing to tmp_path."""
    config_path = project_root / "config" / "generator_config.yaml"
    config = load_config(config_path)
    data = config.model_dump(mode="json")

    output_dir = tmp_path / "data" / "landing"
    reports_dir = tmp_path / "reports"
    data["output"]["directory"] = str(output_dir)
    data["output"]["validation_report"] = str(reports_dir / "validation_report.json")
    data["output"]["anomaly_report"] = str(reports_dir / "anomaly_report.md")
    data["output"]["anomaly_manifest"] = str(reports_dir / "anomaly_manifest.json")

    test_config = tmp_path / "generator_config.yaml"
    import yaml
    with test_config.open("w") as f:
        yaml.dump(data, f)
    return test_config


def test_e2e_generation_and_validation(e2e_config_path):
    exit_code = generate(e2e_config_path)
    assert exit_code == 0

    exit_code = verify(e2e_config_path)
    assert exit_code == 0


def test_e2e_deterministic_output(e2e_config_path, tmp_path):
    """Same seed produces identical CSV content."""
    generate(e2e_config_path)

    config = load_config(e2e_config_path)
    output_dir = Path(config.output.directory)

    hashes_run1 = {}
    for fname in ("customers.csv", "orders.csv", "products.csv"):
        content = (output_dir / fname).read_bytes()
        hashes_run1[fname] = hashlib.sha256(content).hexdigest()

    # Second run to same directory
    generate(e2e_config_path)

    for fname in ("customers.csv", "orders.csv", "products.csv"):
        content = (output_dir / fname).read_bytes()
        assert hashlib.sha256(content).hexdigest() == hashes_run1[fname]


def test_e2e_validation_report_contents(e2e_config_path):
    generate(e2e_config_path)
    config = load_config(e2e_config_path)

    report_path = Path(config.output.validation_report)
    assert report_path.exists()

    report = json.loads(report_path.read_text())
    assert report["validation_status"] == "PASS"
    assert report["seed"] == 42
    assert report["total_anomaly_events"] == 460
    assert report["datasets"]["customers"]["row_count"] == 10_010
    assert report["datasets"]["orders"]["row_count"] == 100_020
    assert report["datasets"]["products"]["row_count"] == 500
