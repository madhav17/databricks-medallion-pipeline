"""Order dataset generator."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from data_generation.config import GeneratorConfig
from data_generation.relationships.relationship_generator import RelationshipModel
from data_generation.utils import seeded_rng, weighted_choice

ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "product_id",
    "quantity",
    "unit_price",
    "total_amount",
    "order_status",
    "payment_date",
]


def generate_orders(
    config: GeneratorConfig,
    customers: list[dict],
    products: list[dict],
    relationship_model: RelationshipModel,
) -> list[dict]:
    """Generate clean order records with valid FKs and business rules."""
    rng = seeded_rng(config.reproducibility.random_seed, "orders")
    params = config.business_parameters
    count = config.dataset_sizes.order_count

    customer_lookup = {c["customer_id"]: c for c in customers}
    product_lookup = {p["product_id"]: p for p in products}
    date_range = params.date_range

    orders: list[dict] = []
    for order_id in range(1, count + 1):
        customer_id = relationship_model.sample_customer_id(rng)
        product_id = relationship_model.sample_product_id(rng)

        customer = customer_lookup[customer_id]
        product = product_lookup[product_id]

        order_date = _random_date(
            rng, customer["signup_date"], date_range.end_date,
        )
        quantity = _sample_quantity(rng, params.quantity_range)
        unit_price = _compute_unit_price(
            rng, product["price"], params.price_variance_pct,
        )
        total_amount = (unit_price * quantity).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )
        order_status = weighted_choice(rng, params.order_statuses)
        payment_date = _compute_payment_date(rng, order_date, order_status)

        orders.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "order_date": order_date,
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "order_status": order_status,
            "payment_date": payment_date,
        })

    return orders


def _random_date(rng: random.Random, start: date, end: date) -> date:
    delta = (end - start).days
    if delta < 0:
        return start
    offset = rng.randint(0, delta)
    return start + timedelta(days=offset)


def _sample_quantity(rng: random.Random, quantity_range) -> int:
    bucket = weighted_choice(rng, quantity_range.weights)
    if bucket == "1-3":
        return rng.randint(1, 3)
    if bucket == "4-10":
        return rng.randint(4, 10)
    return rng.randint(11, min(quantity_range.max, 50))


def _compute_unit_price(
    rng: random.Random, base_price: Decimal, variance_pct: float,
) -> Decimal:
    variance = Decimal(str(rng.uniform(-variance_pct, variance_pct)))
    price = base_price * (Decimal("1") + variance)
    return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _compute_payment_date(
    rng: random.Random, order_date: date, order_status: str,
) -> date | None:
    if order_status == "Completed":
        delay = rng.randint(0, 3)
        return order_date + timedelta(days=delay)
    return None
