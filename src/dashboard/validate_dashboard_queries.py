"""Local validation entry point for dashboard SQL queries."""

from __future__ import annotations

import sys

from dashboard.dashboard_utils import DashboardError, validate_dashboard_queries
from gold.config_loader import default_config_path, load_config


def main() -> int:
    config = load_config(default_config_path())
    summary = validate_dashboard_queries(config)
    print("Dashboard query validation summary:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DashboardError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
