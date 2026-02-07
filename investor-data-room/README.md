# Investor Data Room — Series A Diligence Package

Automated metrics export for Series A due diligence.

## Endpoints

| Endpoint | Format | Description |
|----------|--------|-------------|
| `GET /investors/full-metrics` | JSON | Complete diligence package |
| `GET /investors/full-metrics.csv` | CSV | Spreadsheet export |
| `GET /investors/metrics` | JSON | Core metrics (M5) |
| `GET /investors/metrics.csv` | CSV | Core metrics CSV |

## Data Room Contents

### Financials
- MRR, ARR, MRR growth MoM, gross margin, COGS estimation
- MRR history (12 months)

### Customers
- Total tenants, paying subscribers (PRO/TEAM/ENTERPRISE)
- Cohort retention matrix

### Unit Economics
- ARPU, LTV, CAC, LTV:CAC ratio, monthly churn, payback months

### Platform
- Active API keys, API active tenants, marketplace blueprints
- Active installations, active webhooks, integrator count

### Verticals
- ARR breakdown by vertical (job-app, staffing-agency, grant, etc.)
- Enterprise count per vertical

### Staffing Agency Vertical
- Total batches, candidates submitted, success rate, revenue
- Unique agencies

### University Partnerships
- Partner count, total students, PRO upgrade conversions

### Marketplace Economics
- Paid blueprints, gross revenue, platform take, author payouts
- Top 5 blueprints by revenue

## Usage

```bash
# Full data room (JSON)
curl -H "Authorization: Bearer $TOKEN" https://api.sorce.app/investors/full-metrics | jq .

# CSV for Google Sheets
curl -H "Authorization: Bearer $TOKEN" https://api.sorce.app/investors/full-metrics.csv -o data_room.csv

# Refresh views first
curl -X POST -H "Authorization: Bearer $TOKEN" https://api.sorce.app/admin/m6-platform/refresh
```

## M6 Target Metrics

| Metric | Target | Endpoint Field |
|--------|--------|---------------|
| Enterprise ≥$50k ACV | 1 signed | `m6_targets.enterprise_max_acv` |
| Adjacent Vertical MRR | $10k+ | `m6_targets.staffing_mrr_current` |
| 3rd-party Integrators | ≥3 | `m6_targets.integrators_current` |
| ARR Run-rate | $2M+ | `m6_targets.arr_current` |
