"""Independent dataset validation from CSV files."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from data_generation.config import GeneratorConfig, MANDATORY_ANOMALY_COUNTS
from data_generation.generators.customer_generator import CUSTOMER_COLUMNS
from data_generation.generators.order_generator import ORDER_COLUMNS
from data_generation.generators.product_generator import PRODUCT_COLUMNS

VALID_SEGMENTS = {"Premium", "Standard", "Basic"}
VALID_STATUSES = {"Pending", "Completed", "Cancelled"}
DATE_FORMAT = "%Y-%m-%d"


@dataclass
class AnomalyCheck:
    anomaly_type: str
    expected: int
    actual: int

    @property
    def passed(self) -> bool:
        return self.expected == self.actual


@dataclass
class ValidationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    anomaly_checks: list[AnomalyCheck] = field(default_factory=list)
    unexpected_anomalies: list[dict] = field(default_factory=list)
    dataset_summary: dict = field(default_factory=dict)
    overlapping_anomaly_rows: list[dict] = field(default_factory=list)
    unique_affected_rows: dict = field(default_factory=dict)
    total_rows_with_anomalies: dict = field(default_factory=dict)


def validate_dataset(
    config: GeneratorConfig,
    customers_path: Path,
    orders_path: Path,
    products_path: Path,
) -> ValidationResult:
    """Independently validate generated CSV files against requirements."""
    result = ValidationResult(passed=True)

    customers = _read_csv(customers_path)
    orders = _read_csv(orders_path)
    products = _read_csv(products_path)

    valid_customer_ids = config.valid_customer_ids()
    valid_product_ids = config.valid_product_ids()
    orphan_customer_ids = set(config.orphan_customer_id_range())
    orphan_product_ids = set(config.orphan_product_id_range())

    _validate_products(config, products, result)
    _validate_customers(config, customers, result)
    _validate_orders(config, orders, valid_customer_ids, valid_product_ids, result)

    anomaly_summary = _compute_anomaly_summary(
        customers, orders, valid_customer_ids, valid_product_ids,
        orphan_customer_ids, orphan_product_ids, config,
    )
    result.anomaly_checks = anomaly_summary["checks"]
    result.overlapping_anomaly_rows = anomaly_summary["overlaps"]
    result.unique_affected_rows = anomaly_summary["unique_affected"]
    result.total_rows_with_anomalies = anomaly_summary["total_rows_with_anomalies"]

    for check in result.anomaly_checks:
        if not check.passed:
            result.errors.append(
                f"Anomaly {check.anomaly_type}: expected {check.expected}, got {check.actual}"
            )

    _verify_duplicate_clones(customers, orders, result)
    _scan_unexpected_anomalies(
        config, customers, orders, products,
        valid_customer_ids, valid_product_ids,
        orphan_customer_ids, orphan_product_ids,
        anomaly_summary["intentional_row_keys"],
        result,
    )

    result.dataset_summary = {
        "customers": {
            "row_count": len(customers),
            "expected_row_count": config.expected_customer_row_count,
            "unique_customer_id": len({r["customer_id"] for r in customers}),
        },
        "orders": {
            "row_count": len(orders),
            "expected_row_count": config.expected_order_row_count,
            "unique_order_id": len({r["order_id"] for r in orders}),
        },
        "products": {
            "row_count": len(products),
            "expected_row_count": config.dataset_sizes.product_count,
            "unique_product_id": len({r["product_id"] for r in products}),
        },
    }

    if result.errors:
        result.passed = False

    return result


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [_parse_row(row) for row in reader]


def _parse_row(row: dict) -> dict:
    parsed: dict = {}
    for key, value in row.items():
        parsed[key] = _parse_value(key, value)
    return parsed


def _parse_value(key: str, value: str) -> Any:
    if value == "" or value is None:
        return None
    if key.endswith("_date") or key == "signup_date":
        return datetime.strptime(value, DATE_FORMAT).date()
    if key in ("customer_id", "order_id", "product_id", "quantity",
               "stock_quantity", "reorder_level"):
        return int(value)
    if key in ("lifetime_value", "price", "cost", "unit_price", "total_amount"):
        return Decimal(value)
    return value


def _validate_products(config: GeneratorConfig, products: list[dict], result: ValidationResult) -> None:
    expected = config.dataset_sizes.product_count
    if len(products) != expected:
        result.errors.append(f"products row count: expected {expected}, got {len(products)}")

    ids = [p["product_id"] for p in products]
    if len(set(ids)) != len(ids):
        result.errors.append("products: duplicate product_id values found")

    valid_categories = {c.name for c in config.business_parameters.product_categories}
    for i, p in enumerate(products):
        if p["category"] not in valid_categories:
            result.errors.append(f"products row {i}: invalid category '{p['category']}'")
        if p["price"] is not None and p["price"] < 0:
            result.errors.append(f"products row {i}: negative price")
        if p["cost"] is not None and p["cost"] < 0:
            result.errors.append(f"products row {i}: negative cost")
        if p["price"] is not None and p["cost"] is not None and p["cost"] > p["price"]:
            result.errors.append(f"products row {i}: cost > price")
        if p["stock_quantity"] is not None and p["stock_quantity"] < 0:
            result.errors.append(f"products row {i}: negative stock_quantity")
        if p["reorder_level"] is not None and p["reorder_level"] < 0:
            result.errors.append(f"products row {i}: negative reorder_level")


def _validate_customers(config: GeneratorConfig, customers: list[dict], result: ValidationResult) -> None:
    expected_rows = config.expected_customer_row_count
    if len(customers) != expected_rows:
        result.errors.append(
            f"customers row count: expected {expected_rows}, got {len(customers)}"
        )

    unique_ids = {c["customer_id"] for c in customers}
    if len(unique_ids) != config.dataset_sizes.customer_count:
        result.errors.append(
            f"customers unique IDs: expected {config.dataset_sizes.customer_count}, "
            f"got {len(unique_ids)}"
        )

    date_range = config.business_parameters.date_range
    for i, c in enumerate(customers):
        if c["customer_segment"] not in VALID_SEGMENTS:
            result.errors.append(f"customers row {i}: invalid segment")
        if c["signup_date"] and c["signup_date"] > date_range.end_date:
            result.errors.append(f"customers row {i}: future signup_date")


def _validate_orders(
    config: GeneratorConfig,
    orders: list[dict],
    valid_customer_ids: set[int],
    valid_product_ids: set[int],
    result: ValidationResult,
) -> None:
    expected_rows = config.expected_order_row_count
    if len(orders) != expected_rows:
        result.errors.append(f"orders row count: expected {expected_rows}, got {len(orders)}")

    unique_ids = {o["order_id"] for o in orders}
    if len(unique_ids) != config.dataset_sizes.order_count:
        result.errors.append(
            f"orders unique IDs: expected {config.dataset_sizes.order_count}, "
            f"got {len(unique_ids)}"
        )

    orphan_customer_ids = set(config.orphan_customer_id_range())
    orphan_product_ids = set(config.orphan_product_id_range())

    for i, o in enumerate(orders):
        cid = o["customer_id"]
        pid = o["product_id"]

        if cid is not None and cid in valid_customer_ids:
            pass  # valid FK
        elif cid is not None and cid in orphan_customer_ids:
            pass  # intentional invalid FK
        elif cid is not None:
            result.errors.append(f"orders row {i}: unexpected customer_id {cid}")

        if pid is not None and pid in valid_product_ids:
            pass
        elif pid is not None and pid in orphan_product_ids:
            pass
        elif pid is not None:
            result.errors.append(f"orders row {i}: unexpected product_id {pid}")


def _compute_anomaly_summary(
    customers: list[dict],
    orders: list[dict],
    valid_customer_ids: set[int],
    valid_product_ids: set[int],
    orphan_customer_ids: set[int],
    orphan_product_ids: set[int],
    config: GeneratorConfig,
) -> dict:
    null_emails = sum(1 for c in customers if c["email"] is None)
    customer_id_counts = Counter(c["customer_id"] for c in customers)
    duplicate_customer_ids = sum(1 for cid, cnt in customer_id_counts.items() if cnt > 1)

    null_customer_ids = sum(1 for o in orders if o["customer_id"] is None)
    null_product_ids = sum(1 for o in orders if o["product_id"] is None)
    invalid_customer_fks = sum(
        1 for o in orders
        if o["customer_id"] is not None and o["customer_id"] in orphan_customer_ids
    )
    invalid_product_fks = sum(
        1 for o in orders
        if o["product_id"] is not None and o["product_id"] in orphan_product_ids
    )
    order_id_counts = Counter(o["order_id"] for o in orders)
    duplicate_order_ids = sum(1 for oid, cnt in order_id_counts.items() if cnt > 1)

    checks = [
        AnomalyCheck("null_email", MANDATORY_ANOMALY_COUNTS["null_email_count"], null_emails),
        AnomalyCheck(
            "duplicate_customer_id",
            MANDATORY_ANOMALY_COUNTS["duplicate_customer_id_count"],
            duplicate_customer_ids,
        ),
        AnomalyCheck(
            "null_customer_id",
            MANDATORY_ANOMALY_COUNTS["null_customer_id_count"],
            null_customer_ids,
        ),
        AnomalyCheck(
            "null_product_id",
            MANDATORY_ANOMALY_COUNTS["null_product_id_count"],
            null_product_ids,
        ),
        AnomalyCheck(
            "invalid_customer_fk",
            MANDATORY_ANOMALY_COUNTS["invalid_customer_fk_count"],
            invalid_customer_fks,
        ),
        AnomalyCheck(
            "invalid_product_fk",
            MANDATORY_ANOMALY_COUNTS["invalid_product_fk_count"],
            invalid_product_fks,
        ),
        AnomalyCheck(
            "duplicate_order_id",
            MANDATORY_ANOMALY_COUNTS["duplicate_order_id_count"],
            duplicate_order_ids,
        ),
    ]

    customer_anomaly_rows: dict[int, set[str]] = defaultdict(set)
    for i, c in enumerate(customers):
        if c["email"] is None:
            customer_anomaly_rows[i].add("null_email")
    for cid, cnt in customer_id_counts.items():
        if cnt > 1:
            for i, c in enumerate(customers):
                if c["customer_id"] == cid:
                    customer_anomaly_rows[i].add("duplicate_customer_id")

    order_anomaly_rows: dict[int, set[str]] = defaultdict(set)
    for i, o in enumerate(orders):
        if o["customer_id"] is None:
            order_anomaly_rows[i].add("null_customer_id")
        if o["product_id"] is None:
            order_anomaly_rows[i].add("null_product_id")
        if o["customer_id"] in orphan_customer_ids:
            order_anomaly_rows[i].add("invalid_customer_fk")
        if o["product_id"] in orphan_product_ids:
            order_anomaly_rows[i].add("invalid_product_fk")
    for oid, cnt in order_id_counts.items():
        if cnt > 1:
            for i, o in enumerate(orders):
                if o["order_id"] == oid:
                    order_anomaly_rows[i].add("duplicate_order_id")

    overlaps = []
    for dataset_name, row_map in [("customers", customer_anomaly_rows), ("orders", order_anomaly_rows)]:
        for row_id, types in row_map.items():
            if len(types) > 1:
                overlaps.append({
                    "dataset": dataset_name,
                    "row_index": row_id,
                    "anomaly_types": sorted(types),
                })

    intentional_row_keys: set[tuple[str, int]] = set()
    for row_id in customer_anomaly_rows:
        intentional_row_keys.add(("customers", row_id))
    for row_id in order_anomaly_rows:
        intentional_row_keys.add(("orders", row_id))

    total_anomaly_events = sum(c.actual for c in checks)
    unique_customer_rows = len(customer_anomaly_rows)
    unique_order_rows = len(order_anomaly_rows)

    return {
        "checks": checks,
        "overlaps": overlaps,
        "unique_affected": {
            "customers": unique_customer_rows,
            "orders": unique_order_rows,
            "total": unique_customer_rows + unique_order_rows,
        },
        "total_rows_with_anomalies": {
            "customers": unique_customer_rows,
            "orders": unique_order_rows,
            "combined": unique_customer_rows + unique_order_rows,
        },
        "total_anomaly_events": total_anomaly_events,
        "intentional_row_keys": intentional_row_keys,
    }


def _verify_duplicate_clones(
    customers: list[dict], orders: list[dict], result: ValidationResult,
) -> None:
    """Verify duplicate rows are exact clones of their source counterparts."""
    customer_id_groups: dict[int, list[dict]] = defaultdict(list)
    for c in customers:
        customer_id_groups[c["customer_id"]].append(c)

    for cid, group in customer_id_groups.items():
        if len(group) > 1:
            reference = group[0]
            for duplicate in group[1:]:
                if not _rows_equal(reference, duplicate):
                    result.errors.append(
                        f"customers: duplicate customer_id {cid} is not an exact clone"
                    )

    order_id_groups: dict[int, list[dict]] = defaultdict(list)
    for o in orders:
        order_id_groups[o["order_id"]].append(o)

    for oid, group in order_id_groups.items():
        if len(group) > 1:
            reference = group[0]
            for duplicate in group[1:]:
                if not _rows_equal(reference, duplicate):
                    result.errors.append(
                        f"orders: duplicate order_id {oid} is not an exact clone"
                    )


def _rows_equal(a: dict, b: dict) -> bool:
    if set(a.keys()) != set(b.keys()):
        return False
    for key in a:
        if a[key] != b[key]:
            return False
    return True


def _scan_unexpected_anomalies(
    config: GeneratorConfig,
    customers: list[dict],
    orders: list[dict],
    products: list[dict],
    valid_customer_ids: set[int],
    valid_product_ids: set[int],
    orphan_customer_ids: set[int],
    orphan_product_ids: set[int],
    intentional_row_keys: set[tuple[str, int]],
    result: ValidationResult,
) -> None:
    """Scan for anomalies not part of the mandatory injection plan."""
    if not config.is_core_mode:
        return

    customer_lookup = {c["customer_id"]: c for c in customers}
    date_range = config.business_parameters.date_range

    for i, c in enumerate(customers):
        if ("customers", i) in intentional_row_keys:
            continue
        issues = []
        if c["email"] is None:
            issues.append("unexpected_null_email")
        if c["customer_name"] is None or str(c["customer_name"]).strip() == "":
            issues.append("missing_name")
        if c["customer_segment"] not in VALID_SEGMENTS:
            issues.append("invalid_segment")
        if c["lifetime_value"] is not None and c["lifetime_value"] < 0:
            issues.append("negative_lifetime_value")
        if c["signup_date"] and c["signup_date"] > date_range.end_date:
            issues.append("future_signup_date")
        if issues:
            result.unexpected_anomalies.append({
                "dataset": "customers", "row_index": i, "issues": issues,
            })

    for i, o in enumerate(orders):
        if ("orders", i) in intentional_row_keys:
            continue
        issues = []
        cid = o["customer_id"]
        pid = o["product_id"]

        if cid is not None and cid not in valid_customer_ids and cid not in orphan_customer_ids:
            issues.append("unexpected_invalid_customer_fk")
        if pid is not None and pid not in valid_product_ids and pid not in orphan_product_ids:
            issues.append("unexpected_invalid_product_fk")
        if o["quantity"] is not None and o["quantity"] <= 0:
            issues.append("invalid_quantity")
        if o["unit_price"] is not None and o["unit_price"] < 0:
            issues.append("negative_unit_price")
        if o["order_status"] not in VALID_STATUSES:
            issues.append("invalid_status")
        if o["order_date"] and o["order_date"] > date_range.end_date:
            issues.append("future_order_date")
        if cid is not None and cid in valid_customer_ids:
            customer = customer_lookup.get(cid)
            if customer and o["order_date"] and o["order_date"] < customer["signup_date"]:
                issues.append("order_before_signup")
        if o["payment_date"] and o["order_date"] and o["payment_date"] < o["order_date"]:
            issues.append("payment_before_order")
        if o["order_status"] == "Completed" and o["payment_date"] is None:
            issues.append("completed_without_payment")
        if o["quantity"] and o["unit_price"] and o["total_amount"]:
            expected = (o["unit_price"] * o["quantity"]).quantize(Decimal("0.01"))
            if o["total_amount"] != expected:
                issues.append("incorrect_total_amount")
        if issues:
            result.unexpected_anomalies.append({
                "dataset": "orders", "row_index": i, "issues": issues,
            })

    if result.unexpected_anomalies:
        result.errors.append(
            f"Found {len(result.unexpected_anomalies)} rows with unexpected anomalies"
        )
