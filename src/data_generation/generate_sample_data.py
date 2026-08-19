"""Main entry point for generating sample e-commerce datasets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data_generation.anomalies.anomaly_ledger import AnomalyLedger
from data_generation.anomalies.extended_injector import inject_extended_anomalies
from data_generation.anomalies.mandatory_injector import inject_mandatory_anomalies
from data_generation.config_loader import default_config_path, load_config
from data_generation.csv_writer import write_csv
from data_generation.generators.customer_generator import CUSTOMER_COLUMNS, generate_customers
from data_generation.generators.order_generator import ORDER_COLUMNS, generate_orders
from data_generation.generators.product_generator import PRODUCT_COLUMNS, generate_products
from data_generation.relationships.relationship_generator import build_relationship_model
from data_generation.reporting.report_generator import generate_reports
from data_generation.validation.dataset_validator import validate_dataset


def generate(config_path: str | Path | None = None) -> int:
    """Run the full data generation pipeline."""
    path = Path(config_path) if config_path else default_config_path()
    config = load_config(path)

    # Phase 1-3: Generate clean base datasets
    products = generate_products(config)
    customers = generate_customers(config)
    relationship_model = build_relationship_model(config, customers, products)
    orders = generate_orders(config, customers, products, relationship_model)

    # Phase 4-5: Anomaly injection
    ledger = AnomalyLedger()
    customers, orders = inject_mandatory_anomalies(config, customers, orders, ledger)
    customers, orders, products = inject_extended_anomalies(
        config, customers, orders, products, ledger,
    )

    # Phase 6: Write CSV output
    output_dir = Path(config.output.directory)
    customers_path = output_dir / config.output.customers_file
    orders_path = output_dir / config.output.orders_file
    products_path = output_dir / config.output.products_file

    write_csv(customers_path, customers, CUSTOMER_COLUMNS)
    write_csv(orders_path, orders, ORDER_COLUMNS)
    write_csv(products_path, products, PRODUCT_COLUMNS)

    # Phase 7: Independent validation
    validation = validate_dataset(config, customers_path, orders_path, products_path)
    if not validation.passed:
        _print_validation_errors(validation)
        return 1

    # Phase 8: Reports
    generate_reports(config, ledger, validation)

    print(f"Generation complete. Output: {output_dir}")
    print(f"  customers: {len(customers)} rows ({config.dataset_sizes.customer_count} unique IDs)")
    print(f"  orders:    {len(orders)} rows ({config.dataset_sizes.order_count} unique IDs)")
    print(f"  products:  {len(products)} rows")
    print(f"  anomaly events: {ledger.total_anomaly_events()}")
    print(f"  validation: PASS")

    return 0


def _print_validation_errors(validation) -> None:
    print("VALIDATION FAILED:", file=sys.stderr)
    for error in validation.errors:
        print(f"  - {error}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate e-commerce sample data for Databricks Medallion pipeline",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to generator_config.yaml (default: config/generator_config.yaml)",
    )
    args = parser.parse_args()
    sys.exit(generate(args.config))


if __name__ == "__main__":
    main()
