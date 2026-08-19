"""Independent dataset verification CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from data_generation.config_loader import default_config_path, load_config
from data_generation.validation.dataset_validator import validate_dataset


def verify(
    config_path: str | Path | None = None,
    customers_path: Path | None = None,
    orders_path: Path | None = None,
    products_path: Path | None = None,
) -> int:
    """Independently verify generated CSV files."""
    path = Path(config_path) if config_path else default_config_path()
    config = load_config(path)

    output_dir = Path(config.output.directory)
    customers = customers_path or output_dir / config.output.customers_file
    orders = orders_path or output_dir / config.output.orders_file
    products = products_path or output_dir / config.output.products_file

    for p, name in [(customers, "customers"), (orders, "orders"), (products, "products")]:
        if not p.exists():
            print(f"ERROR: {name} file not found: {p}", file=sys.stderr)
            return 1

    result = validate_dataset(config, customers, orders, products)

    print(json.dumps({
        "validation_status": "PASS" if result.passed else "FAIL",
        "datasets": result.dataset_summary,
        "anomaly_checks": [
            {"type": c.anomaly_type, "expected": c.expected, "actual": c.actual, "passed": c.passed}
            for c in result.anomaly_checks
        ],
        "unique_affected_rows": result.unique_affected_rows,
        "overlapping_anomaly_rows": result.overlapping_anomaly_rows,
        "unexpected_anomaly_count": len(result.unexpected_anomalies),
        "errors": result.errors,
    }, indent=2))

    if not result.passed:
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Independently verify generated e-commerce sample data",
    )
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--customers", type=str, default=None)
    parser.add_argument("--orders", type=str, default=None)
    parser.add_argument("--products", type=str, default=None)
    args = parser.parse_args()

    sys.exit(verify(
        config_path=args.config,
        customers_path=Path(args.customers) if args.customers else None,
        orders_path=Path(args.orders) if args.orders else None,
        products_path=Path(args.products) if args.products else None,
    ))


if __name__ == "__main__":
    main()
