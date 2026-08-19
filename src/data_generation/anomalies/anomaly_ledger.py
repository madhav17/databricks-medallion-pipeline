"""Anomaly ledger for tracking intentionally injected data quality issues."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AnomalyRecord:
    dataset: str
    anomaly_type: str
    row_identifier: int | str
    primary_key: int | None
    affected_column: str | None
    injection_stage: str
    source_record_identifier: int | str | None = None
    old_value: Any = None
    new_value: Any = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnomalyLedger:
    """Tracks every intentionally injected anomaly."""

    records: list[AnomalyRecord] = field(default_factory=list)

    def record(
        self,
        *,
        dataset: str,
        anomaly_type: str,
        row_identifier: int | str,
        primary_key: int | None,
        affected_column: str | None,
        injection_stage: str,
        source_record_identifier: int | str | None = None,
        old_value: Any = None,
        new_value: Any = None,
    ) -> None:
        self.records.append(AnomalyRecord(
            dataset=dataset,
            anomaly_type=anomaly_type,
            row_identifier=row_identifier,
            primary_key=primary_key,
            affected_column=affected_column,
            injection_stage=injection_stage,
            source_record_identifier=source_record_identifier,
            old_value=old_value,
            new_value=new_value,
        ))

    def count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for rec in self.records:
            counts[rec.anomaly_type] = counts.get(rec.anomaly_type, 0) + 1
        return counts

    def rows_by_dataset(self, dataset: str) -> dict[int | str, list[str]]:
        """Map row identifiers to list of anomaly types affecting them."""
        result: dict[int | str, list[str]] = {}
        for rec in self.records:
            if rec.dataset != dataset:
                continue
            key = rec.row_identifier
            result.setdefault(key, []).append(rec.anomaly_type)
        return result

    def unique_affected_rows(self, dataset: str | None = None) -> int:
        keys: set[int | str] = set()
        for rec in self.records:
            if dataset is None or rec.dataset == dataset:
                keys.add((rec.dataset, rec.row_identifier))
        return len(keys)

    def overlapping_rows(self, dataset: str) -> list[dict]:
        """Return rows affected by more than one anomaly type."""
        row_types = self.rows_by_dataset(dataset)
        overlaps = []
        for row_id, types in row_types.items():
            if len(types) > 1:
                overlaps.append({"row_identifier": row_id, "anomaly_types": types})
        return overlaps

    def total_anomaly_events(self) -> int:
        return len(self.records)

    def to_manifest(self) -> dict:
        return {
            "total_anomaly_events": self.total_anomaly_events(),
            "counts_by_type": self.count_by_type(),
            "unique_affected_rows": self.unique_affected_rows(),
            "records": [r.to_dict() for r in self.records],
        }

    def affected_row_keys(self, dataset: str) -> set[int | str]:
        return {rec.row_identifier for rec in self.records if rec.dataset == dataset}
