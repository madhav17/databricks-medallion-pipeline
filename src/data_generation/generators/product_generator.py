"""Product dataset generator."""

from __future__ import annotations

import random
from decimal import Decimal, ROUND_HALF_UP

from data_generation.config import GeneratorConfig
from data_generation.utils import seeded_rng, weighted_choice_from_list

PRODUCT_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "price",
    "cost",
    "stock_quantity",
    "reorder_level",
]

ADJECTIVES = [
    "Pro", "Elite", "Classic", "Essential", "Premium", "Compact",
    "Ultra", "Smart", "Eco", "Deluxe", "Standard", "Advanced",
]

CATEGORY_ITEMS: dict[str, list[str]] = {
    "Electronics": ["Laptop", "Headphones", "Tablet", "Monitor", "Keyboard", "Speaker", "Camera"],
    "Clothing": ["Jacket", "Shirt", "Jeans", "Dress", "Sneakers", "Hat", "Scarf"],
    "Home": ["Lamp", "Chair", "Desk", "Rug", "Blender", "Vacuum", "Mirror"],
    "Sports": ["Yoga Mat", "Dumbbell", "Bicycle", "Tennis Racket", "Running Shoes", "Helmet"],
    "Books": ["Novel", "Cookbook", "Biography", "Textbook", "Guide", "Atlas"],
}

BRANDS = [
    "Apex", "Nova", "Zenith", "Pulse", "Vertex", "Horizon",
    "Summit", "Crest", "Forge", "Lumen", "Stride", "Nest",
]


def generate_products(config: GeneratorConfig) -> list[dict]:
    """Generate clean product records with no anomalies."""
    rng = seeded_rng(config.reproducibility.random_seed, "products")
    params = config.business_parameters
    count = config.dataset_sizes.product_count

    categories = params.product_categories
    cat_names = [c.name for c in categories]
    cat_weights = [c.weight for c in categories]
    cat_price_map = {c.name: c.price_range for c in categories}

    products: list[dict] = []
    for product_id in range(1, count + 1):
        category = weighted_choice_from_list(rng, cat_names, cat_weights)
        price_min, price_max = cat_price_map[category]
        price = _random_decimal(rng, price_min, price_max)
        cost_ratio = Decimal(str(rng.uniform(0.40, 0.75)))
        cost = (price * cost_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        stock_quantity = max(0, int(rng.lognormvariate(5.0, 0.8)))
        reorder_level = max(0, int(stock_quantity * rng.uniform(0.10, 0.30)))

        item = rng.choice(CATEGORY_ITEMS.get(category, ["Item"]))
        brand = rng.choice(BRANDS)
        adjective = rng.choice(ADJECTIVES)
        product_name = f"{brand} {adjective} {item}"

        products.append({
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "price": price,
            "cost": cost,
            "stock_quantity": stock_quantity,
            "reorder_level": reorder_level,
        })

    return products


def _random_decimal(rng: random.Random, low: Decimal, high: Decimal) -> Decimal:
    """Generate a random Decimal in [low, high] with 2 decimal places."""
    span = float(high - low)
    value = float(low) + rng.random() * span
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
