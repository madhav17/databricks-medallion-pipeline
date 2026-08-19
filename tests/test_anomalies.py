"""Tests for anomaly injection and ledger."""

from __future__ import annotations

import copy

from data_generation.anomalies.anomaly_ledger import AnomalyLedger
from data_generation.anomalies.mandatory_injector import inject_mandatory_anomalies
from data_generation.generators.customer_generator import generate_customers
from data_generation.generators.order_generator import generate_orders
from data_generation.generators.product_generator import generate_products
from data_generation.relationships.relationship_generator import build_relationship_model


def _generate_base(config):
    products = generate_products(config)
    customers = generate_customers(config)
    model = build_relationship_model(config, customers, products)
    orders = generate_orders(config, customers, products, model)
    return customers, orders


def test_mandatory_anomaly_counts(config):
    customers, orders = _generate_base(config)
    ledger = AnomalyLedger()
    customers, orders = inject_mandatory_anomalies(config, customers, orders, ledger)

    assert len(customers) == 10_010
    assert len(orders) == 100_020
    assert ledger.total_anomaly_events() == 460

    counts = ledger.count_by_type()
    assert counts["null_email"] == 50
    assert counts["duplicate_customer_id"] == 10
    assert counts["null_customer_id"] == 100
    assert counts["null_product_id"] == 200
    assert counts["invalid_customer_fk"] == 50
    assert counts["invalid_product_fk"] == 30
    assert counts["duplicate_order_id"] == 20


def test_null_email_injection(config):
    customers, orders = _generate_base(config)
    ledger = AnomalyLedger()
    customers, _ = inject_mandatory_anomalies(config, customers, orders, ledger)

    null_emails = sum(1 for c in customers if c["email"] is None)
    assert null_emails == 50


def test_orphan_customer_fks_not_in_valid_set(config):
    customers, orders = _generate_base(config)
    ledger = AnomalyLedger()
    _, orders = inject_mandatory_anomalies(config, customers, orders, ledger)

    valid_ids = config.valid_customer_ids()
    orphan_ids = set(config.orphan_customer_id_range())
    for o in orders:
        cid = o["customer_id"]
        if cid is not None and cid not in valid_ids:
            assert cid in orphan_ids


def test_duplicate_clones_are_exact(config):
    customers, orders = _generate_base(config)
    ledger = AnomalyLedger()
    customers, orders = inject_mandatory_anomalies(config, customers, orders, ledger)

    for rec in ledger.records:
        if rec.anomaly_type == "duplicate_customer_id":
            source = customers[rec.source_record_identifier]
            clone = customers[rec.row_identifier]
            assert source == clone
        if rec.anomaly_type == "duplicate_order_id":
            source = orders[rec.source_record_identifier]
            clone = orders[rec.row_identifier]
            assert source == clone


def test_disjoint_pools_no_overlap_in_ledger(config):
    customers, orders = _generate_base(config)
    ledger = AnomalyLedger()
    inject_mandatory_anomalies(config, customers, orders, ledger)

    order_null_cust = {
        r.row_identifier for r in ledger.records
        if r.anomaly_type == "null_customer_id"
    }
    order_null_prod = {
        r.row_identifier for r in ledger.records
        if r.anomaly_type == "null_product_id"
    }
    order_invalid_cust = {
        r.row_identifier for r in ledger.records
        if r.anomaly_type == "invalid_customer_fk"
    }
    order_invalid_prod = {
        r.row_identifier for r in ledger.records
        if r.anomaly_type == "invalid_product_fk"
    }

    assert order_null_cust.isdisjoint(order_null_prod)
    assert order_null_cust.isdisjoint(order_invalid_cust)
    assert order_null_prod.isdisjoint(order_invalid_prod)


def test_anomaly_ledger_manifest():
    ledger = AnomalyLedger()
    ledger.record(
        dataset="customers",
        anomaly_type="null_email",
        row_identifier=0,
        primary_key=1,
        affected_column="email",
        injection_stage="test",
    )
    manifest = ledger.to_manifest()
    assert manifest["total_anomaly_events"] == 1
    assert "null_email" in manifest["counts_by_type"]
