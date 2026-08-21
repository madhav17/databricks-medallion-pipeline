# E-Commerce Data Generator — Anomaly Report

- **Generated**: 2026-08-18T09:29:42.412423+00:00
- **Seed**: 42
- **Mode**: core
- **Config hash**: 4bd8e0aca7a9d68f
- **Status**: PASS

## Dataset Summary

| Dataset | Expected Rows | Actual Rows | Unique PKs |
|---------|---------------|-------------|------------|
| customers | 10010 | 10010 | 10000 |
| orders | 100020 | 100020 | 100000 |
| products | 500 | 500 | 500 |

## Mandatory Anomalies

| Anomaly Type | Expected | Actual | Status |
|--------------|----------|--------|--------|
| null_email | 50 | 50 | PASS |
| duplicate_customer_id | 10 | 10 | PASS |
| null_customer_id | 100 | 100 | PASS |
| null_product_id | 200 | 200 | PASS |
| invalid_customer_fk | 50 | 50 | PASS |
| invalid_product_fk | 30 | 30 | PASS |
| duplicate_order_id | 20 | 20 | PASS |

## Anomaly Accounting

- **Total anomaly events (by type sum)**: 460
- **Unique affected rows (customers)**: 70
- **Unique affected rows (orders)**: 420
- **Total rows with at least one anomaly**: 490
- **Overlapping anomaly rows**: 0
- **Unexpected anomalies**: 0

### Why counts can differ

- **Anomaly events by type** sums each anomaly category independently (total: 460).
- **Unique affected rows** counts each row once even if it has multiple anomaly types.
- **Total rows with anomalies** may differ from 460 because duplicate anomalies
  involve two rows per duplicate ID (source + clone), and overlap is tracked separately.
- The assignment's ~700 figure may count differently (per-field, extended anomalies,
  or overlapping categories). This generator reports all metrics transparently.
