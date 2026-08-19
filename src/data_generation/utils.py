"""Deterministic random seed utilities."""

from __future__ import annotations

import hashlib
import random


def derive_seed(master_seed: int, phase: str) -> int:
    """Derive a deterministic sub-seed for a named generation phase."""
    digest = hashlib.sha256(f"{master_seed}:{phase}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def seeded_rng(master_seed: int, phase: str) -> random.Random:
    """Create a seeded Random instance for a named phase."""
    return random.Random(derive_seed(master_seed, phase))


def weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    """Select a key from a weight dictionary."""
    keys = list(weights.keys())
    values = [weights[k] for k in keys]
    return rng.choices(keys, weights=values, k=1)[0]


def weighted_choice_from_list(
    rng: random.Random, items: list, weights: list[float],
) -> object:
    """Select an item from a list using corresponding weights."""
    return rng.choices(items, weights=weights, k=1)[0]
