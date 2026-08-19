"""Tests for independent dataset validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from data_generation.anomalies.anomaly_ledger import AnomalyLedger
from data_generation.anomalies.mandatory_injector import inject_mandatory_anomalies
from data_generation.csv_writer import write_csv
from data_generation.generators.customer_generator import CUSTOMER_COLUMNS, generate_customers
from data_generation.generators.order_generator import ORDER_COLUMNS, generate_orders
from data_generation.generators.product_generator import PRODUCT_COLUMNS, generate_products
from data_generation.relationships.relationship_generator import build_relationship_model
from data_generation.validation.dataset_validator import validate_dataset


@pytest.fixture
def generated_csvs(config, tmp_path):
    products = generate_products(config)
    customers = generate_customers(config)
    model = build_relationship_model(config, customers, products)
    orders = generate_orders(config, customers, products, model)
    ledger = AnomalyLedger()
    customers, orders = inject_mandatory_anomalies(config, customers, orders, ledger)

    customers_path = tmp_path / "customers.csv"
    orders_path = tmp_path / "orders.csv"
    products_path = tmp_path / "products.csv"

    write_csv(customers_path, customers, CUSTOMER_COLUMNS)
    write_csv(orders_path, orders, ORDER_COLUMNS)
    write_csv(products_path, products, PRODUCT_COLUMNS)

    return customers_path, orders_path, products_path


def test_validator_passes_on_generated_data(config, generated_csvs):
    customers_path, orders_path, products_path = generated_csvs
    result = validate_dataset(config, customers_path, orders_path, products_path)
    assert result.passed, result.errors


def test_validator_detects_wrong_row_count(config, generated_csvs, tmp_path):
    customers_path, orders_path, products_path = generated_csvs
    # Truncate customers file
    lines = customers_path.read_text().splitlines()
    truncated = tmp_path / "customers_truncated.csv"
    truncated.write_text("\n".join(lines[:100]) + "\n")

    result = validate_dataset(config, truncated, orders_path, products_path)
    assert not result.passed
