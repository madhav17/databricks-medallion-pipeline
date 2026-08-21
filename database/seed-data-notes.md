# Seed Data Notes

## Source CSV Files

| File | Config path | Purpose |
|------|-------------|---------|
| `customers.csv` | `config/generator_config.yaml` → `output.customers_file` | Customer dimension landing data |
| `orders.csv` | `config/generator_config.yaml` → `output.orders_file` | Order fact landing data |
| `products.csv` | `config/generator_config.yaml` → `output.products_file` | Product dimension landing data |

Default generator output directory: `./data/landing`

Bronze ingestion reads from `./data/` using `config/bronze_config.yaml`:

- `source_root`: `./data`
- `source_files`: `customers.csv`, `orders.csv`, `products.csv`

Sample CSV copies are also tracked at `./data/*.csv` for submission review.

## How Data Is Created

```bash
uv sync
PYTHONPATH=src python src/data_generation/generate_sample_data.py
```

Or:

```bash
generate-sample-data
```

Generation is deterministic (`random_seed: 42`) and configured by
`config/generator_config.yaml`.

Independent validation:

```bash
verify-dataset
```

## Approximate Expected Row Counts (CORE mode, seed 42)

| Dataset | Unique PK count | Final CSV rows |
|---------|-----------------|----------------|
| customers | 10,000 | 10,010 |
| orders | 100,000 | 100,020 |
| products | 500 | 500 |

Exact counts are verified by `verify-dataset` and recorded in
`reports/validation_report.json` after generation.

## Intentional Anomalies (460 total events)

| Anomaly | Count |
|---------|-------|
| NULL email (customers) | 50 |
| Duplicate customer_id | 10 |
| NULL customer_id (orders) | 100 |
| NULL product_id (orders) | 200 |
| Invalid customer FK | 50 |
| Invalid product FK | 30 |
| Duplicate order_id | 20 |

Details: `src/data_generation/DATA_GENERATION_NOTES.md`

## Regenerating Seed Data

1. Ensure `config/generator_config.yaml` is unchanged unless intentionally modified.
2. Run `generate-sample-data`.
3. Copy or symlink landing CSVs to `./data/` if Bronze is configured to read from that root.
4. Run `verify-dataset` and inspect `reports/validation_report.json`.
5. Re-run Bronze → Silver → Gold → Dashboard validation after pipeline outputs are refreshed.

All generated values are synthetic. No real customer PII is used.
