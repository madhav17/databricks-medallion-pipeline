"""Tests for dataset generators."""

from __future__ import annotations

from decimal import Decimal

from data_generation.generators.customer_generator import generate_customers
from data_generation.generators.order_generator import generate_orders
from data_generation.generators.product_generator import generate_products
from data_generation.relationships.relationship_generator import build_relationship_model


def test_product_generation(config):
    products = generate_products(config)
    assert len(products) == 500
    ids = [p["product_id"] for p in products]
    assert len(set(ids)) == 500
    for p in products:
        assert p["cost"] <= p["price"]
        assert p["stock_quantity"] >= 0
        assert p["reorder_level"] >= 0


def test_customer_generation(config):
    customers = generate_customers(config)
    assert len(customers) == 10_000
    ids = [c["customer_id"] for c in customers]
    assert ids == list(range(1, 10_001))
    emails = [c["email"] for c in customers]
    assert len(set(emails)) == 10_000
    for c in customers:
        assert c["customer_segment"] in ("Premium", "Standard", "Basic")
        assert c["email"] is not None


def test_order_generation(config):
    products = generate_products(config)
    customers = generate_customers(config)
    model = build_relationship_model(config, customers, products)
    orders = generate_orders(config, customers, products, model)

    assert len(orders) == 100_000
    customer_lookup = {c["customer_id"]: c for c in customers}

    for o in orders:
        assert o["customer_id"] in customer_lookup
        assert o["product_id"] in range(1, 501)
        assert o["order_date"] >= customer_lookup[o["customer_id"]]["signup_date"]
        expected_total = (o["unit_price"] * o["quantity"]).quantize(Decimal("0.01"))
        assert o["total_amount"] == expected_total
        if o["order_status"] == "Completed":
            assert o["payment_date"] is not None
            assert o["payment_date"] >= o["order_date"]
        else:
            assert o["payment_date"] is None


def test_small_dataset_generation(small_config):
    products = generate_products(small_config)
    customers = generate_customers(small_config)
    model = build_relationship_model(small_config, customers, products)
    orders = generate_orders(small_config, customers, products, model)

    assert len(products) == 50
    assert len(customers) == 100
    assert len(orders) == 500
