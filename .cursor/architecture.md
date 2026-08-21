# Architecture Summary

See also `.cursor/rules/03-architecture.mdc` and `design-notes.md`.

```text
CSV (data/*.csv)
  → Bronze (data/bronze/*.parquet)
  → Silver (data/silver/*.parquet + quality_metrics)
  → Gold (data/gold/*)
  → Dashboard SQL (Gold temp views)
```

Layer boundaries are strict: no business cleansing in Bronze, no aggregation in Silver.
