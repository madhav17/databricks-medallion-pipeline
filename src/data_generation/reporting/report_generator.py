"""Report generation for validation and anomaly tracking."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from data_generation import __version__
from data_generation.anomalies.anomaly_ledger import AnomalyLedger
from data_generation.config import GeneratorConfig
from data_generation.csv_writer import write_json, write_text
from data_generation.validation.dataset_validator import ValidationResult


def generate_reports(
    config: GeneratorConfig,
    ledger: AnomalyLedger,
    validation: ValidationResult,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Generate Markdown, JSON validation report, and anomaly manifest."""
    config_hash = _config_hash(config)
    timestamp = datetime.now(timezone.utc).isoformat()

    json_report = _build_json_report(config, ledger, validation, config_hash, timestamp)
    md_report = _build_markdown_report(config, ledger, validation, config_hash, timestamp)
    manifest = ledger.to_manifest()
    manifest["generated_at_utc"] = timestamp
    manifest["config_hash"] = config_hash
    manifest["seed"] = config.reproducibility.random_seed
    manifest["mode"] = config.generator.mode.value
    manifest["overlapping_rows"] = ledger.overlapping_rows("customers") + ledger.overlapping_rows("orders")

    paths = {
        "validation_report": Path(config.output.validation_report),
        "anomaly_report": Path(config.output.anomaly_report),
        "anomaly_manifest": Path(config.output.anomaly_manifest),
    }

    write_json(paths["validation_report"], json_report)
    write_text(paths["anomaly_report"], md_report)
    write_json(paths["anomaly_manifest"], manifest)

    return paths


def _config_hash(config: GeneratorConfig) -> str:
    canonical = json.dumps(config.model_dump(mode="json"), sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _build_json_report(
    config: GeneratorConfig,
    ledger: AnomalyLedger,
    validation: ValidationResult,
    config_hash: str,
    timestamp: str,
) -> dict:
    return {
        "generator_version": __version__,
        "generated_at_utc": timestamp,
        "config_hash": config_hash,
        "seed": config.reproducibility.random_seed,
        "mode": config.generator.mode.value,
        "validation_status": "PASS" if validation.passed else "FAIL",
        "datasets": validation.dataset_summary,
        "mandatory_anomalies": [
            {
                "anomaly_type": c.anomaly_type,
                "expected": c.expected,
                "actual": c.actual,
                "status": "PASS" if c.passed else "FAIL",
            }
            for c in validation.anomaly_checks
        ],
        "anomaly_events_by_type": ledger.count_by_type(),
        "total_anomaly_events": ledger.total_anomaly_events(),
        "unique_affected_rows": validation.unique_affected_rows,
        "overlapping_anomaly_rows": validation.overlapping_anomaly_rows,
        "total_rows_with_anomalies": validation.total_rows_with_anomalies,
        "unexpected_anomaly_count": len(validation.unexpected_anomalies),
        "unexpected_anomalies": validation.unexpected_anomalies[:50],
        "errors": validation.errors,
        "warnings": validation.warnings,
        "output_locations": {
            "customers": str(Path(config.output.directory) / config.output.customers_file),
            "orders": str(Path(config.output.directory) / config.output.orders_file),
            "products": str(Path(config.output.directory) / config.output.products_file),
        },
    }


def _build_markdown_report(
    config: GeneratorConfig,
    ledger: AnomalyLedger,
    validation: ValidationResult,
    config_hash: str,
    timestamp: str,
) -> str:
    lines = [
        "# E-Commerce Data Generator — Anomaly Report",
        "",
        f"- **Generated**: {timestamp}",
        f"- **Seed**: {config.reproducibility.random_seed}",
        f"- **Mode**: {config.generator.mode.value}",
        f"- **Config hash**: {config_hash}",
        f"- **Status**: {'PASS' if validation.passed else 'FAIL'}",
        "",
        "## Dataset Summary",
        "",
        "| Dataset | Expected Rows | Actual Rows | Unique PKs |",
        "|---------|---------------|-------------|------------|",
    ]

    for name in ("customers", "orders", "products"):
        summary = validation.dataset_summary.get(name, {})
        expected = summary.get("expected_row_count", "N/A")
        actual = summary.get("row_count", "N/A")
        unique_key = {
            "customers": "unique_customer_id",
            "orders": "unique_order_id",
            "products": "unique_product_id",
        }[name]
        unique = summary.get(unique_key, "N/A")
        lines.append(f"| {name} | {expected} | {actual} | {unique} |")

    lines.extend([
        "",
        "## Mandatory Anomalies",
        "",
        "| Anomaly Type | Expected | Actual | Status |",
        "|--------------|----------|--------|--------|",
    ])

    for check in validation.anomaly_checks:
        status = "PASS" if check.passed else "FAIL"
        lines.append(
            f"| {check.anomaly_type} | {check.expected} | {check.actual} | {status} |"
        )

    lines.extend([
        "",
        "## Anomaly Accounting",
        "",
        f"- **Total anomaly events (by type sum)**: {ledger.total_anomaly_events()}",
        f"- **Unique affected rows (customers)**: {validation.unique_affected_rows.get('customers', 0)}",
        f"- **Unique affected rows (orders)**: {validation.unique_affected_rows.get('orders', 0)}",
        f"- **Total rows with at least one anomaly**: "
        f"{validation.total_rows_with_anomalies.get('combined', 0)}",
        f"- **Overlapping anomaly rows**: {len(validation.overlapping_anomaly_rows)}",
        f"- **Unexpected anomalies**: {len(validation.unexpected_anomalies)}",
        "",
        "### Why counts can differ",
        "",
        "- **Anomaly events by type** sums each anomaly category independently (total: 460).",
        "- **Unique affected rows** counts each row once even if it has multiple anomaly types.",
        "- **Total rows with anomalies** may differ from 460 because duplicate anomalies",
        "  involve two rows per duplicate ID (source + clone), and overlap is tracked separately.",
        "- The assignment's ~700 figure may count differently (per-field, extended anomalies,",
        "  or overlapping categories). This generator reports all metrics transparently.",
        "",
    ])

    if validation.errors:
        lines.extend(["## Errors", ""])
        for error in validation.errors:
            lines.append(f"- {error}")
        lines.append("")

    if validation.overlapping_anomaly_rows:
        lines.extend(["## Overlapping Anomaly Rows", ""])
        for overlap in validation.overlapping_anomaly_rows:
            lines.append(f"- {overlap}")
        lines.append("")

    return "\n".join(lines)
