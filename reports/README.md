# Reports Directory

This directory stores validation and anomaly reports produced by the data
generation module.

## Tracked Submission Artifacts

| File | Produced by | Purpose |
|------|-------------|---------|
| `validation_report.json` | `verify-dataset` | Independent dataset validation summary |
| `anomaly_report.md` | `generate-sample-data` | Human-readable anomaly summary |
| `anomaly_manifest.json` | `generate-sample-data` | Machine-readable anomaly ledger export |

## Regeneration

From project root:

```bash
generate-sample-data
verify-dataset
```

Reports are regenerated from `config/generator_config.yaml` output paths.

## Related Pipeline Metrics

Silver quality metrics are written separately to:

`{silver_root}/quality_metrics` (default: `./data/silver/quality_metrics`)

That Parquet dataset contains per-check pass/fail statistics including
completeness, uniqueness, referential integrity, and business logic.
