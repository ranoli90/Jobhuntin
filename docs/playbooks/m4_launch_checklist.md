# M4 Scale to $100K MRR — Launch Checklist

Complete every item before enabling enterprise billing, SSO, and scaled infrastructure.

---

## Pre-Launch: Database Migrations (Week -2)

- [ ] **Migration 015 applied**: SSO config, priority_score, enterprise_settings, audit_log, bulk_campaigns
  ```bash
  supabase db push  # applies 015_m4_enterprise.sql
  ```
- [ ] **Migration 016 applied**: M4 materialized views (MRR cohorts, NRR, churn prediction, pipeline)
  ```bash
  supabase db push  # applies 016_m4_dashboard_views.sql
  ```

## Stripe Enterprise Configuration

- [ ] **Create Stripe Products**:
  - Product: "Sorce ENTERPRISE"
    - Price: $999/month (base) → set as `STRIPE_ENTERPRISE_PRICE_ID`
  - Existing PRO ($29) and TEAM ($199 + $49/seat) unchanged

- [ ] **Env vars on API server**:
  ```
  STRIPE_ENTERPRISE_PRICE_ID=price_xxx
  ```

- [ ] **Webhook handles ENTERPRISE**: verify `checkout.session.completed` with `metadata.plan=ENTERPRISE`:
  - Sets `tenants.plan = 'ENTERPRISE'`
  - Sets `tenants.max_seats` from metadata
  - Creates `enterprise_settings` row

## SSO Configuration

- [ ] **SSO env vars**:
  ```
  SSO_SP_ENTITY_ID=https://api.sorce.app/sso/saml/metadata
  SSO_SP_ACS_URL=https://api.sorce.app/sso/saml/acs
  SSO_SESSION_SECRET=<random-64-char-string>
  ```

- [ ] **Test SAML flow**:
  1. Enterprise admin configures IdP in `POST /sso/config`
  2. SP metadata available at `GET /sso/saml/metadata`
  3. IdP sends assertion to `POST /sso/saml/acs`
  4. User authenticated and redirected with session token
  5. Audit log entry: `sso.login`

- [ ] **OIDC discovery**: `GET /sso/.well-known/openid-configuration` returns valid JSON

## Priority Queue Verification

- [ ] **Priority scoring works**:
  - FREE application: `priority_score = 0`
  - PRO application: `priority_score = 10`
  - TEAM application: `priority_score = 20`
  - ENTERPRISE application: `priority_score = 100`

- [ ] **Worker claims by priority**:
  - Queue 1 FREE + 1 ENTERPRISE task
  - Worker claims ENTERPRISE first
  - Verify via `claim_next_prioritized()` function

## Web Admin Enterprise Console

- [ ] **Deploy updated web-admin**:
  ```bash
  cd web-admin
  npm install && npm run build
  npx vercel --prod
  ```

- [ ] **Verify all new pages**:
  - [ ] `/enterprise` — Enterprise dashboard with MRR, contract info
  - [ ] `/sso` — SSO configuration form with SP metadata display
  - [ ] `/audit-log` — Paginated audit log with CSV export
  - [ ] `/bulk-campaigns` — Create, start, and track bulk campaigns

- [ ] **Security headers**: verify `vercel.json` SOC 2 headers (CSP, HSTS, X-Frame-Options)

## Worker Horizontal Scaling

- [ ] **Scale workers**:
  ```bash
  python -m worker.scaling --instances 10
  ```
  Verify: 10 workers polling, connection pools sized correctly

- [ ] **Read replica** (if available):
  ```
  READ_REPLICA_URL=postgresql://...
  ```

- [ ] **Enterprise dedicated pool**:
  ```
  ENTERPRISE_DB_POOL_MIN=2
  ENTERPRISE_DB_POOL_MAX=10
  ```

## Load Testing

- [ ] **Install Artillery**:
  ```bash
  npm install -g artillery artillery-plugin-expect
  ```

- [ ] **Run smoke test**:
  ```bash
  cd scripts/load-test
  API_URL=https://api.sorce.app TEST_TOKEN=xxx bash run.sh --quick
  ```

- [ ] **Run full load test**:
  ```bash
  API_URL=https://api.sorce.app TEST_TOKEN=xxx bash run.sh
  ```
  Targets: p99 < 5s, p95 < 2s, >95% success rate at 50 rps

## Sentry & Observability

- [ ] **Set Sentry DSN**:
  ```
  SENTRY_DSN=https://xxx@o123.ingest.sentry.io/456
  SENTRY_ENVIRONMENT=production
  SENTRY_TRACES_SAMPLE_RATE=0.1
  ```

- [ ] **Verify error capture**: trigger a test error, confirm it appears in Sentry with `tenant_id` and `plan` tags

- [ ] **Automated alerts active**:
  - Agent success rate < 85% → warning, < 70% → critical
  - Stripe payment failures ≥ 3/hour → warning
  - Queue depth ≥ 100 → warning, ≥ 500 → critical
  - Enterprise SLA breach (task waiting > 5 min) → critical

## M4 Analytics Verification

- [ ] **M4 dashboard returns data**:
  ```bash
  curl -H "Authorization: Bearer $ADMIN_TOKEN" https://api.sorce.app/admin/m4-dashboard
  ```
  Verify: `mrr_cohorts`, `churn_prediction`, `nrr_monthly`, `enterprise_pipeline`, `ltv_cac`, `m4_targets`

- [ ] **Refresh views**:
  ```bash
  curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" https://api.sorce.app/admin/m4-dashboard/refresh
  ```

- [ ] **M4 targets tracking**:
  - 30k MAU target
  - $100k MRR target
  - 2,000 subscribers target
  - 50 team accounts target
  - 3 enterprise pilots target
  - NRR ≥ 110% target

## Enterprise Onboarding Flow

- [ ] **First enterprise pilot**:
  1. Create ENTERPRISE subscription via `POST /billing/enterprise-checkout`
  2. Configure SSO via `POST /sso/config`
  3. Set custom domain in `enterprise_settings`
  4. Invite team members (bulk invite)
  5. Verify priority queue: their tasks process first
  6. Verify audit log captures all actions

## Go-Live Sequence

1. Deploy migrations 015 → 016
2. Set all new env vars (Stripe, SSO, Sentry, worker scaling)
3. Deploy API with SSO router, enterprise billing, M4 dashboard, observability
4. Deploy updated web-admin with enterprise pages
5. Scale workers to 10+ instances
6. Run load test to verify capacity
7. Deploy mobile update with EnterpriseAdminScreen
8. Enable ENTERPRISE price in Stripe
9. Onboard first 3 enterprise pilots

## Week 1 Monitoring

- [ ] **Daily checks**:
  - Enterprise task SLA (< 5 min queue time)
  - Agent success rate (target: > 90%)
  - MRR trending toward $100k
  - NRR ≥ 110%
  - Churn prediction: reach out to high-risk accounts

- [ ] **Enterprise onboarding**:
  - Each pilot gets dedicated Slack channel
  - Weekly check-in calls for first month
  - Track: tasks per seat, SSO adoption, feature usage

- [ ] **Scale readiness**:
  - Monitor worker pool utilization
  - Database connection pool saturation
  - p99 response times under load
  - Queue depth during peak hours
