"""Optional extended anomaly injection (disabled in CORE mode)."""

from __future__ import annotations

from data_generation.anomalies.anomaly_ledger import AnomalyLedger
from data_generation.config import GeneratorConfig


def inject_extended_anomalies(
    config: GeneratorConfig,
    customers: list[dict],
    orders: list[dict],
    products: list[dict],
    ledger: AnomalyLedger,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Inject optional extended anomalies when mode=extended.

    In CORE mode this is a no-op.
    """
    if not config.extended_anomalies.enabled:
        return customers, orders, products

    # Extended anomaly implementation placeholder for future Silver testing.
    # Each extended anomaly type would use disjoint pools separate from mandatory.
    return customers, orders, products
