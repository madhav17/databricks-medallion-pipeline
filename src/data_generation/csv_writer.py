"""CSV output writer with deterministic formatting."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any


DATE_FORMAT = "%Y-%m-%d"


def write_csv(
    path: Path,
    rows: list[dict],
    columns: list[str],
) -> None:
    """Write rows to a UTF-8 CSV file with headers and consistent formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter=",",
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({col: _format_value(row.get(col)) for col in columns})


def _format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.strftime(DATE_FORMAT)
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, float):
        return f"{Decimal(str(value)):.2f}"
    return str(value)


def write_json(path: Path, data: dict) -> None:
    """Write JSON data to a file."""
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, default=str)


def write_text(path: Path, content: str) -> None:
    """Write plain text/markdown to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
