# Investor Metrics — Series A Export

Automated metrics export for pitch deck and investor updates.

## Endpoints

| Endpoint | Format | Description |
|----------|--------|-------------|
| `GET /investors/metrics` | JSON | Full metrics payload |
| `GET /investors/metrics.csv` | CSV | Spreadsheet-friendly export |

## Metrics Included

- **Financials**: MRR, ARR, MRR growth MoM, gross margin, COGS
- **Customers**: Total tenants, paying subscribers (PRO/TEAM/ENTERPRISE)
- **Unit Economics**: ARPU, LTV, CAC, LTV:CAC ratio, monthly churn, payback months
- **Product**: Agent success rate, total applications, marketplace blueprints, platform revenue
- **MRR History**: Last 12 months of MRR data

## Usage

```bash
# JSON export
curl -H "Authorization: Bearer $ADMIN_TOKEN" https://api.sorce.app/investors/metrics | jq .

# CSV export (for Google Sheets / Excel)
curl -H "Authorization: Bearer $ADMIN_TOKEN" https://api.sorce.app/investors/metrics.csv -o metrics.csv

# Refresh all views first
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" https://api.sorce.app/admin/m5-dashboard/refresh
```

## Automation

Set up a weekly cron to refresh views and export:

```bash
# crontab: every Monday at 6am UTC
0 6 * * 1 curl -X POST -H "Authorization: Bearer $TOKEN" https://api.sorce.app/admin/m5-dashboard/refresh
```

## Target Metrics (Series A)

| Metric | Target | Source |
|--------|--------|--------|
| MRR | $83k+ sustained 3mo | `financials.mrr` |
| ARR | $1M+ | `financials.arr` |
| MRR Growth | ≥15% MoM | `financials.mrr_growth_mom_pct` |
| Gross Margin | ≥80% | `financials.gross_margin_pct` |
| Paying Subs | 5,000+ | `customers.paying_subscribers` |
| Enterprise | 5+ | `customers.enterprise` |
| LTV:CAC | ≥3:1 | `unit_economics.ltv_cac_ratio` |
| Churn | <4% monthly | `unit_economics.monthly_churn_pct` |
| NRR | ≥110% | `financials.net_revenue_retention_pct` |
