# Investor Overview

## Metrics API

JobHuntin exposes automated metrics endpoints for due diligence and investor updates.

### Endpoints

| Endpoint | Format | Description |
|----------|--------|-------------|
| `GET /investors/metrics` | JSON | Core metrics (MRR, ARR, customers, unit economics) |
| `GET /investors/metrics.csv` | CSV | Spreadsheet export |
| `GET /investors/full-metrics` | JSON | Full data room package |
| `GET /investors/full-metrics.csv` | CSV | Full data room CSV |

**Authentication**: Bearer token (admin/investor scope).

### Metrics Included

- **Financials**: MRR, ARR, MRR growth MoM, gross margin
- **Customers**: Total tenants, paying subscribers (PRO/TEAM/ENTERPRISE)
- **Unit Economics**: ARPU, LTV, CAC, LTV:CAC ratio, churn, payback
- **Product**: Applications sent, success rate, marketplace blueprints
- **MRR History**: Last 12 months

### Usage

```bash
# Core metrics (JSON)
curl -H "Authorization: Bearer $TOKEN" https://api.jobhuntin.com/investors/metrics | jq .

# Full data room (CSV)
curl -H "Authorization: Bearer $TOKEN" https://api.jobhuntin.com/investors/full-metrics.csv -o data_room.csv
```

### Refresh Views

Before exporting, refresh materialized views:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" https://api.jobhuntin.com/admin/m5-dashboard/refresh
```

## Documentation

- [investor-metrics/](../investor-metrics/README.md) – Metrics API details
- [investor-data-room/](../investor-data-room/README.md) – Full diligence package, M6 targets
