"""Customer-product relationship weighting for order generation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from data_generation.config import GeneratorConfig
from data_generation.utils import seeded_rng


@dataclass
class RelationshipModel:
    """Precomputed weights for customer and product assignment."""

    customer_weights: dict[int, float]
    product_weights: dict[int, float]
    inactive_customer_ids: set[int] = field(default_factory=set)
    active_customer_ids: set[int] = field(default_factory=set)

    def sample_customer_id(self, rng: random.Random) -> int:
        ids = list(self.customer_weights.keys())
        weights = [self.customer_weights[i] for i in ids]
        return rng.choices(ids, weights=weights, k=1)[0]

    def sample_product_id(self, rng: random.Random) -> int:
        ids = list(self.product_weights.keys())
        weights = [self.product_weights[i] for i in ids]
        return rng.choices(ids, weights=weights, k=1)[0]


def build_relationship_model(
    config: GeneratorConfig,
    customers: list[dict],
    products: list[dict],
) -> RelationshipModel:
    """
    Build Pareto-style customer weights and product popularity weights.

    Approximately 5-10% of customers are designated inactive (zero orders).
    """
    rng = seeded_rng(config.reproducibility.random_seed, "relationships")
    rel_cfg = config.business_parameters.relationship

    all_customer_ids = [c["customer_id"] for c in customers]
    inactive_pct = rng.uniform(
        rel_cfg.inactive_customer_pct_min,
        rel_cfg.inactive_customer_pct_max,
    )
    inactive_count = max(1, int(len(all_customer_ids) * inactive_pct))
    inactive_ids = set(rng.sample(all_customer_ids, inactive_count))
    active_ids = [cid for cid in all_customer_ids if cid not in inactive_ids]

    customer_weights = _pareto_weights(rng, active_ids, rel_cfg.pareto_alpha)
    product_weights = _product_popularity_weights(
        rng, products, rel_cfg.product_popularity_skew,
    )

    return RelationshipModel(
        customer_weights=customer_weights,
        product_weights=product_weights,
        inactive_customer_ids=inactive_ids,
        active_customer_ids=set(active_ids),
    )


def _pareto_weights(
    rng: random.Random, customer_ids: list[int], alpha: float,
) -> dict[int, float]:
    """Assign Pareto-distributed weights to active customers."""
    weights: dict[int, float] = {}
    for cid in customer_ids:
        u = rng.random()
        u = max(u, 1e-10)
        weights[cid] = 1.0 / (u ** (1.0 / alpha))
    return weights


def _product_popularity_weights(
    rng: random.Random, products: list[dict], skew: float,
) -> dict[int, float]:
    """Assign popularity weights with category-based baseline."""
    category_boost = {
        "Electronics": 1.3,
        "Clothing": 1.2,
        "Home": 1.0,
        "Sports": 0.9,
        "Books": 0.7,
    }
    weights: dict[int, float] = {}
    for product in products:
        boost = category_boost.get(product["category"], 1.0)
        u = max(rng.random(), 1e-10)
        weights[product["product_id"]] = boost * (1.0 / (u ** (1.0 / skew)))
    return weights


def count_inactive_customers(
    customers: list[dict], orders: list[dict],
) -> tuple[int, float]:
    """Count customers with zero orders and return (count, percentage)."""
    customers_with_orders = {o["customer_id"] for o in orders if o["customer_id"] is not None}
    all_ids = {c["customer_id"] for c in customers}
    inactive = all_ids - customers_with_orders
    pct = len(inactive) / len(all_ids) if all_ids else 0.0
    return len(inactive), pct
