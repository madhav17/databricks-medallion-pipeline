"""Mandatory anomaly injection for core dataset requirements."""

from __future__ import annotations

import copy
import random
from typing import Any

from data_generation.anomalies.anomaly_ledger import AnomalyLedger
from data_generation.config import GeneratorConfig
from data_generation.utils import seeded_rng


STAGE_MANDATORY = "mandatory"


def inject_mandatory_anomalies(
    config: GeneratorConfig,
    customers: list[dict],
    orders: list[dict],
    ledger: AnomalyLedger,
) -> tuple[list[dict], list[dict]]:
    """
    Inject mandatory anomalies in deterministic order with disjoint pools.

    Injection order:
    1. NULL email (customers)
    2. NULL customer_id (orders)
    3. NULL product_id (orders)
    4. Invalid customer FK (orders)
    5. Invalid product FK (orders)
    6. Append customer duplicate clones
    7. Append order duplicate clones
    """
    rng = seeded_rng(config.reproducibility.random_seed, "mandatory_anomalies")
    anomaly_cfg = config.mandatory_anomalies

    customers = _inject_null_emails(
        customers, anomaly_cfg.customers.null_email_count, ledger, rng,
    )

    used_order_indices: set[int] = set()

    orders, used_order_indices = _inject_null_customer_ids(
        orders, anomaly_cfg.orders.null_customer_id_count, ledger, rng, used_order_indices,
    )
    orders, used_order_indices = _inject_null_product_ids(
        orders, anomaly_cfg.orders.null_product_id_count, ledger, rng, used_order_indices,
    )
    orders, used_order_indices = _inject_invalid_customer_fks(
        orders, config, anomaly_cfg.orders.invalid_customer_fk_count,
        ledger, rng, used_order_indices,
    )
    orders, used_order_indices = _inject_invalid_product_fks(
        orders, config, anomaly_cfg.orders.invalid_product_fk_count,
        ledger, rng, used_order_indices,
    )

    customers = _append_duplicate_customers(
        customers, anomaly_cfg.customers.duplicate_customer_id_count, ledger, rng,
    )
    orders = _append_duplicate_orders(
        orders, anomaly_cfg.orders.duplicate_order_id_count, ledger, rng,
    )

    return customers, orders


def _select_indices(
    rng: random.Random,
    pool_size: int,
    count: int,
    excluded: set[int],
) -> list[int]:
    """Select distinct indices without replacement, excluding already-used indices."""
    available = [i for i in range(pool_size) if i not in excluded]
    if count > len(available):
        raise ValueError(
            f"Cannot select {count} indices from pool of {len(available)} "
            f"(pool_size={pool_size}, excluded={len(excluded)})"
        )
    return rng.sample(available, count)


def _inject_null_emails(
    customers: list[dict],
    count: int,
    ledger: AnomalyLedger,
    rng: random.Random,
) -> list[dict]:
    indices = _select_indices(rng, len(customers), count, set())
    for idx in indices:
        old_value = customers[idx]["email"]
        customers[idx]["email"] = None
        ledger.record(
            dataset="customers",
            anomaly_type="null_email",
            row_identifier=idx,
            primary_key=customers[idx]["customer_id"],
            affected_column="email",
            injection_stage=STAGE_MANDATORY,
            old_value=old_value,
            new_value=None,
        )
    return customers


def _inject_null_customer_ids(
    orders: list[dict],
    count: int,
    ledger: AnomalyLedger,
    rng: random.Random,
    excluded: set[int],
) -> tuple[list[dict], set[int]]:
    indices = _select_indices(rng, len(orders), count, excluded)
    for idx in indices:
        old_value = orders[idx]["customer_id"]
        orders[idx]["customer_id"] = None
        ledger.record(
            dataset="orders",
            anomaly_type="null_customer_id",
            row_identifier=idx,
            primary_key=orders[idx]["order_id"],
            affected_column="customer_id",
            injection_stage=STAGE_MANDATORY,
            old_value=old_value,
            new_value=None,
        )
        excluded.add(idx)
    return orders, excluded


def _inject_null_product_ids(
    orders: list[dict],
    count: int,
    ledger: AnomalyLedger,
    rng: random.Random,
    excluded: set[int],
) -> tuple[list[dict], set[int]]:
    indices = _select_indices(rng, len(orders), count, excluded)
    for idx in indices:
        old_value = orders[idx]["product_id"]
        orders[idx]["product_id"] = None
        ledger.record(
            dataset="orders",
            anomaly_type="null_product_id",
            row_identifier=idx,
            primary_key=orders[idx]["order_id"],
            affected_column="product_id",
            injection_stage=STAGE_MANDATORY,
            old_value=old_value,
            new_value=None,
        )
        excluded.add(idx)
    return orders, excluded


def _inject_invalid_customer_fks(
    orders: list[dict],
    config: GeneratorConfig,
    count: int,
    ledger: AnomalyLedger,
    rng: random.Random,
    excluded: set[int],
) -> tuple[list[dict], set[int]]:
    indices = _select_indices(rng, len(orders), count, excluded)
    orphan_ids = list(config.orphan_customer_id_range())
    rng.shuffle(orphan_ids)
    for idx, orphan_id in zip(indices, orphan_ids):
        old_value = orders[idx]["customer_id"]
        orders[idx]["customer_id"] = orphan_id
        ledger.record(
            dataset="orders",
            anomaly_type="invalid_customer_fk",
            row_identifier=idx,
            primary_key=orders[idx]["order_id"],
            affected_column="customer_id",
            injection_stage=STAGE_MANDATORY,
            old_value=old_value,
            new_value=orphan_id,
        )
        excluded.add(idx)
    return orders, excluded


def _inject_invalid_product_fks(
    orders: list[dict],
    config: GeneratorConfig,
    count: int,
    ledger: AnomalyLedger,
    rng: random.Random,
    excluded: set[int],
) -> tuple[list[dict], set[int]]:
    indices = _select_indices(rng, len(orders), count, excluded)
    orphan_ids = list(config.orphan_product_id_range())
    rng.shuffle(orphan_ids)
    for idx, orphan_id in zip(indices, orphan_ids):
        old_value = orders[idx]["product_id"]
        orders[idx]["product_id"] = orphan_id
        ledger.record(
            dataset="orders",
            anomaly_type="invalid_product_fk",
            row_identifier=idx,
            primary_key=orders[idx]["order_id"],
            affected_column="product_id",
            injection_stage=STAGE_MANDATORY,
            old_value=old_value,
            new_value=orphan_id,
        )
        excluded.add(idx)
    return orders, excluded


def _append_duplicate_customers(
    customers: list[dict],
    count: int,
    ledger: AnomalyLedger,
    rng: random.Random,
) -> list[dict]:
    """Append exact clones for duplicate customer_id anomalies."""
    source_indices = rng.sample(range(len(customers)), count)
    for source_idx in source_indices:
        clone = copy.deepcopy(customers[source_idx])
        new_row_id = len(customers)
        customers.append(clone)
        ledger.record(
            dataset="customers",
            anomaly_type="duplicate_customer_id",
            row_identifier=new_row_id,
            primary_key=clone["customer_id"],
            affected_column="customer_id",
            injection_stage=STAGE_MANDATORY,
            source_record_identifier=source_idx,
        )
    return customers


def _append_duplicate_orders(
    orders: list[dict],
    count: int,
    ledger: AnomalyLedger,
    rng: random.Random,
) -> list[dict]:
    """Append exact clones for duplicate order_id anomalies."""
    source_indices = rng.sample(range(len(orders)), count)
    for source_idx in source_indices:
        clone = copy.deepcopy(orders[source_idx])
        new_row_id = len(orders)
        orders.append(clone)
        ledger.record(
            dataset="orders",
            anomaly_type="duplicate_order_id",
            row_identifier=new_row_id,
            primary_key=clone["order_id"],
            affected_column="order_id",
            injection_stage=STAGE_MANDATORY,
            source_record_identifier=source_idx,
        )
    return orders
