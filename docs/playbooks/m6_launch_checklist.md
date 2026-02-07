# M6 Platform Maturity — Launch Checklist

Complete every item before enabling API v2 platform, staffing vertical, and university partnerships.

**Success Criteria:** 1 enterprise contract ≥$50k ACV, 1 adjacent vertical ≥$10k MRR (staffing), ≥3 third-party integrators via API, $2M+ ARR run-rate, Series A closed.

---

## Pre-Launch: Database Migrations (Week -2)

- [ ] **Migration 019 applied**: platform tables (api_keys, webhooks, staffing, university, telemetry, renewals)
  ```bash
  supabase db push  # applies 019_m6_platform.sql
  ```
- [ ] **Migration 020 applied**: M6 telemetry materialized views
  ```bash
  supabase db push  # applies 020_m6_telemetry_views.sql
  ```
- [ ] **Verify views**: `SELECT * FROM mv_arr_by_vertical LIMIT 5;`

## Part 1: $50k Enterprise Contract — Staffing Agency

- [ ] **Register StaffingAgencyBlueprint** in `backend/blueprints/registry.py`:
  ```python
  from blueprints.staffing_agency import StaffingAgencyBlueprint
  register_blueprint("staffing-agency", StaffingAgencyBlueprint())
  ```
- [ ] **Staffing API endpoints deployed**:
  - `POST /api/v2/staffing/bulk-submit` — submit up to 25 candidates per batch
  - `GET /api/v2/staffing/status/{batch_id}` — real-time batch status
- [ ] **Pricing configured**:
  ```
  STAFFING_PRICE_PER_SUBMIT_CENTS=200    # $2 per successful submission
  STAFFING_BASE_MONTHLY_CENTS=200000     # $2k/month base
  ```
- [ ] **E2E test**: submit 5 test candidates → Greenhouse sandbox → verify status sync
- [ ] **Enterprise contract signed**: ≥$50k ACV (base + per-submission)

## Part 2: API v2 Platform for Integrators

- [ ] **OpenAPI spec deployed**: `api-v2/openapi.yaml` available at `/api/v2/docs`
- [ ] **API key management**:
  - `POST /developer/api-keys` — create key (returns raw key once)
  - `GET /developer/api-keys` — list keys
  - `DELETE /developer/api-keys/{id}` — revoke key
- [ ] **Rate limiting**: in-memory per-key RPM + monthly quota enforcement
- [ ] **Webhook system**:
  - `POST /developer/webhooks` — register endpoint
  - HMAC-SHA256 signature on every delivery
  - Automatic retry on failure (up to 3 attempts)
- [ ] **Stripe metering** (API PRO tier):
  ```
  API_V2_METERED_PRICE_ID=price_xxx    # $0.10/submission metered
  API_V2_PRO_PRICE_ID=price_xxx        # $99/mo PRO API tier
  ```
- [ ] **Developer portal pages**:
  - `/developer/api-keys` — key management + tier comparison
  - `/developer/webhooks` — endpoint config + delivery log
- [ ] **3 integrators onboarded**: ≥3 third-party API consumers with active usage

## Part 3: University Career Center Partnership

- [ ] **University partner API**:
  - `POST /partners/university/partners` — create partner
  - `POST /partners/university/import-students` — CSV bulk import
  - `GET /partners/university/roi-report` — career center dashboard
- [ ] **White-label config**: `bundle_id` + `branding` JSON on `university_partners`
- [ ] **CSV import E2E**:
  1. Upload CSV (email, first_name, last_name, major, graduation_year)
  2. Auto-provision FREE tenants
  3. Track via `platform_telemetry` for ROI attribution
- [ ] **Revenue share**: 50% of student PRO upgrades to university partner
- [ ] **ROI report**: "500 students applied to 3,472 jobs this semester"

## Part 4: Series A Data Room + Platform Telemetry

- [ ] **Investor data room endpoints**:
  - `GET /investors/full-metrics` — complete JSON diligence package
  - `GET /investors/full-metrics.csv` — spreadsheet export
  - Includes: financials, customers, unit economics, platform, verticals, staffing, university, marketplace
- [ ] **M6 platform dashboard**: `GET /admin/m6-platform`
  - ARR by vertical breakdown
  - API v2 usage analytics
  - Blueprint install heatmaps
  - Revenue per blueprint
  - Staffing agency performance
  - University ROI
  - Integrator stats
  - Contract renewals
- [ ] **Contract renewal automation**:
  - `POST /admin/renewal-cycle` — daily cron
  - Scans contracts within 90 days of expiry
  - Sends Slack notifications at 90/60/30 day marks
  - Auto-creates Stripe invoice on renewal
- [ ] **Data room export CLI**:
  ```bash
  python investor-data-room/export.py --api-url https://api.sorce.app --token $TOKEN
  ```

## Stripe Configuration

- [ ] **API metering price**: `API_V2_METERED_PRICE_ID` (usage-based, $0.10/submission)
- [ ] **API PRO price**: `API_V2_PRO_PRICE_ID` ($99/month)
- [ ] **Webhook signing secret**: `WEBHOOK_SIGNING_SECRET` (HMAC-SHA256)

## Go-Live Sequence

1. Deploy migrations 019 → 020
2. Set all new env vars (API metering, staffing pricing, webhook secret)
3. Register staffing-agency blueprint
4. Deploy API v2 + developer portal + university partner routes
5. Onboard first staffing agency client (target: $50k ACV)
6. Onboard first 3 API integrators
7. Sign first university partnership
8. Run data room export for investors
9. Schedule daily cron: `POST /admin/renewal-cycle`

## Week 1 Monitoring

- [ ] **Staffing agency**: batch submission success rate ≥90%
- [ ] **API v2**: latency p95 < 500ms, error rate < 1%
- [ ] **Integrators**: ≥3 with active API usage in last 7 days
- [ ] **University**: first CSV import successful, students onboarded
- [ ] **Renewals**: 90-day notifications sending to Slack
- [ ] **ARR**: tracking toward $2M run-rate

## Series A Readiness Checklist

- [ ] $2M+ ARR run-rate sustained (from `mv_arr_by_vertical`)
- [ ] ≥1 enterprise contract ≥$50k ACV signed
- [ ] Staffing vertical ≥$10k MRR
- [ ] ≥3 third-party API integrators active
- [ ] Cohort retention ≥60% at month 6
- [ ] Gross margin ≥80%
- [ ] NRR ≥110%
- [ ] LTV:CAC ≥3:1
- [ ] SOC 2 Type II in progress
- [ ] Data room export clean and current
