# M5 $1M ARR — Launch Checklist

Complete every item before enabling marketplace, self-serve enterprise, and investor metrics.

**Success Criteria:** $83k+ MRR sustained 3+ months, 5k+ paying subs, 100+ teams, 5+ enterprise, LTV:CAC ≥3:1, churn <4%, agent success ≥90%.

---

## Pre-Launch: Database Migrations (Week -2)

- [ ] **Migration 017 applied**: marketplace tables, contract fields, annual billing, answer_memory
  ```bash
  supabase db push  # applies 017_m5_marketplace.sql
  ```
- [ ] **Migration 018 applied**: M5 revenue intelligence views (P&L, marketplace rev, cohort retention)
  ```bash
  supabase db push  # applies 018_m5_revenue_intelligence.sql
  ```
- [ ] **Verify views**: `SELECT * FROM mv_m5_pnl LIMIT 1;`

## Stripe Configuration

- [ ] **Annual prices created**:
  - PRO Annual: $278/yr (20% off) → `STRIPE_PRO_ANNUAL_PRICE_ID`
  - TEAM Annual: $1,910/yr (20% off) → `STRIPE_TEAM_ANNUAL_PRICE_ID`
  - ENTERPRISE Annual: $9,590/yr (20% off) → `STRIPE_ENTERPRISE_ANNUAL_PRICE_ID`

- [ ] **Stripe Connect** (marketplace payouts):
  - Connect platform account activated
  - `STRIPE_CONNECT_CLIENT_ID` set
  - Payout schedule: weekly, 7-day rolling

- [ ] **Env vars deployed**:
  ```
  STRIPE_PRO_ANNUAL_PRICE_ID=price_xxx
  STRIPE_TEAM_ANNUAL_PRICE_ID=price_xxx
  STRIPE_ENTERPRISE_ANNUAL_PRICE_ID=price_xxx
  STRIPE_CONNECT_CLIENT_ID=ca_xxx
  MARKETPLACE_PLATFORM_FEE_PCT=30
  ```

## Self-Serve Enterprise Flow

- [ ] **Onboarding flow E2E**:
  1. `POST /billing/enterprise-self-serve` → checkout URL + onboarding record
  2. Stripe checkout → webhook sets plan=ENTERPRISE + enterprise_settings
  3. `GET /billing/onboarding` → step=sso
  4. Admin configures SSO → step=complete
  5. Team members SSO login → audit log entries

- [ ] **Annual billing E2E**:
  1. `POST /billing/annual-checkout` with plan=PRO/TEAM/ENTERPRISE
  2. Stripe creates yearly subscription with 20% discount
  3. Webhook sets `billing_interval=annual`

## Blueprint Marketplace

- [ ] **Deploy marketplace API**:
  - `GET /marketplace/blueprints` — browse (public, no auth)
  - `GET /marketplace/blueprints/{slug}` — detail
  - `GET /marketplace/categories` — category list
  - `POST /marketplace/blueprints/{id}/install` — install (auth required)
  - `POST /marketplace/blueprints/submit` — author submission
  - `GET /marketplace/author/blueprints` — author's blueprints
  - `GET /marketplace/author/earnings` — revenue share dashboard

- [ ] **Seed initial blueprints**:
  - `vendor-onboard` (community/vendor_onboard)
  - `scholarship` (community/scholarship)
  - `job-app` (built-in, auto-approved)
  - `grant` (built-in, auto-approved)

- [ ] **Admin review flow**:
  - `POST /marketplace/admin/blueprints/{id}/approve`
  - `POST /marketplace/admin/blueprints/{id}/reject`

- [ ] **Web admin marketplace pages**:
  - `/marketplace` — browse & install
  - `/marketplace/submit` — author submission form
  - `/marketplace/author` — earnings & analytics

## Mobile v3

- [ ] **Dashboard-first redesign**: `DashboardHome.tsx` as default screen
- [ ] **i18n**: EN/DE/FR/ES translations, locale persistence
- [ ] **Smart pre-fill**: `answer_memory` table + API endpoints
- [ ] **Widget data refresh**: `WidgetConfig.ts` persists to shared preferences
- [ ] **EU job boards**: StepStone DE, Indeed DE/FR in job browse

## Alerting v2

- [ ] **PagerDuty**:
  ```
  PAGERDUTY_API_KEY=xxx
  PAGERDUTY_SERVICE_ID=xxx
  ```
  Critical alerts auto-trigger PagerDuty incidents

- [ ] **Slack**:
  ```
  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
  SLACK_ENTERPRISE_CHANNEL=#enterprise-alerts
  SLACK_OPS_CHANNEL=#ops-alerts
  ```

- [ ] **Auto-rollback**: triggers if agent success < 60% (20+ samples/hour)
- [ ] **A/B test graduation**: auto-promotes winners after 7d + 200 samples + 5% delta

- [ ] **Run cycle**: `POST /admin/alerting-cycle` → dispatches all channels

## Revenue Intelligence

- [ ] **M5 dashboard**: `GET /admin/m5-dashboard`
  - P&L with COGS estimation
  - Cohort retention matrix
  - Marketplace revenue
  - Agent performance by blueprint
  - M5 target tracking ($83k MRR, 5k subs, etc.)

- [ ] **Investor metrics**: `GET /investors/metrics` (JSON)
  - `GET /investors/metrics.csv` (CSV export)
  - MRR, ARR, growth, churn, LTV:CAC, NRR, gross margin
  - Subscriber breakdown, agent performance, marketplace traction

- [ ] **Churn risk scoring**: `update_churn_risk_scores()` — run daily via cron

## Go-Live Sequence

1. Deploy migrations 017 → 018
2. Set all new env vars (annual prices, Stripe Connect, PagerDuty, Slack)
3. Deploy API with marketplace, annual billing, investor metrics, alerting v2
4. Seed marketplace with built-in + community blueprints
5. Deploy web-admin with marketplace pages
6. Deploy mobile v3 (dashboard-first, i18n, smart pre-fill)
7. Enable annual pricing toggle in UI
8. Open marketplace for community submissions
9. Publish investor metrics dashboard

## Week 1 Monitoring

- [ ] **Daily metrics review**:
  - MRR trending toward $83k
  - New annual subscriptions converting (target: 20% of new subs)
  - Marketplace installs growing
  - Churn rate < 4%
  - LTV:CAC ratio ≥ 3:1
  - Agent success rate ≥ 90%

- [ ] **Marketplace health**:
  - Blueprint submissions coming in
  - Review queue < 48h turnaround
  - No negative reviews on built-in blueprints
  - Author payouts processing correctly

- [ ] **Enterprise pipeline**:
  - Self-serve signups converting
  - SSO configurations completing
  - Contract values tracking
  - Renewal dates monitored (30-day alerts)

## Series A Readiness

- [ ] **Metrics clean**: `GET /investors/metrics` returns accurate data
- [ ] **3-month MRR trend**: $83k+ sustained (from `mv_m5_pnl`)
- [ ] **Cohort retention**: 60%+ at month 6 (from `mv_cohort_retention`)
- [ ] **Gross margin**: ≥80% (LLM costs controlled)
- [ ] **NRR**: ≥110% (expansion from seat additions + plan upgrades)
- [ ] **Growth rate**: ≥15% MoM
