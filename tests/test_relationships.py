"""Tests for relationship generation."""

from __future__ import annotations

from data_generation.generators.customer_generator import generate_customers
from data_generation.generators.order_generator import generate_orders
from data_generation.generators.product_generator import generate_products
from data_generation.relationships.relationship_generator import (
    build_relationship_model,
    count_inactive_customers,
)


def test_inactive_customers_within_range(config):
    products = generate_products(config)
    customers = generate_customers(config)
    model = build_relationship_model(config, customers, products)
    orders = generate_orders(config, customers, products, model)

    inactive_count, inactive_pct = count_inactive_customers(customers, orders)
    assert 0.05 <= inactive_pct <= 0.10 + 0.01  # small tolerance for rounding


def test_inactive_customers_are_in_model(config):
    products = generate_products(config)
    customers = generate_customers(config)
    model = build_relationship_model(config, customers, products)

    assert len(model.inactive_customer_ids) > 0
    assert model.inactive_customer_ids.isdisjoint(model.active_customer_ids)


def test_relationship_model_deterministic(config):
    products = generate_products(config)
    customers = generate_customers(config)
    model1 = build_relationship_model(config, customers, products)
    model2 = build_relationship_model(config, customers, products)
    assert model1.inactive_customer_ids == model2.inactive_customer_ids
