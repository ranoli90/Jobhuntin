# M1 Closed Beta — Launch Checklist

Complete every item before opening the beta to users.

---

## Infrastructure (Week -2)

- [ ] **Supabase project created** (prod instance, not local)
  - Project URL and anon key saved to `mobile/.env.production`
  - Service role key saved to backend `.env`
- [ ] **All migrations applied** in order:
  ```bash
  supabase db push   # or apply 001–009 manually
  ```
- [ ] **Backend deployed** (Railway / Render / Fly.io)
  - `ENV=prod` set
  - `DATABASE_URL` pointing to Supabase pooler
  - `LLM_API_KEY` set (OpenAI)
  - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET` set
  - Health check: `curl https://api.sorce.app/healthz` returns `200`
- [ ] **Worker deployed** (separate process on same host or dedicated)
  - Playwright + Chromium installed in container
  - `AGENT_ENABLED=true`
  - Verify: check logs for "Agent started – polling every 5s"
- [ ] **Sentry configured**
  - `SENTRY_DSN` set on both API and worker
  - Test error captured in Sentry dashboard

## Stripe (Week -2)

- [ ] **Stripe account activated** (not test mode)
- [ ] **Product + Price created** in Stripe Dashboard:
  - Product: "Sorce PRO"
  - Price: $29/month, recurring
  - Copy Price ID → `STRIPE_PRO_PRICE_ID` env var
- [ ] **Webhook endpoint registered** in Stripe Dashboard:
  - URL: `https://api.sorce.app/billing/webhook`
  - Events to listen for:
    - `customer.subscription.created`
    - `customer.subscription.updated`
    - `customer.subscription.deleted`
    - `invoice.payment_failed`
    - `checkout.session.completed`
  - Copy webhook signing secret → `STRIPE_WEBHOOK_SECRET` env var
- [ ] **Customer Portal configured** in Stripe Dashboard:
  - Enable subscription cancellation
  - Enable plan switching (if multiple prices)
- [ ] **Test checkout flow end-to-end**:
  1. Call `POST /billing/checkout` → get URL
  2. Complete payment with Stripe test card 4242...
  3. Verify webhook fires → tenant plan updates to PRO
  4. Verify `GET /billing/usage` shows PRO limits
  5. Cancel via portal → verify plan reverts to FREE

## Mobile App (Week -1)

- [ ] **EAS project linked**:
  ```bash
  cd mobile
  npx eas-cli init
  # Update app.json → extra.eas.projectId
  ```
- [ ] **iOS build (TestFlight)**:
  ```bash
  npx eas-cli build --platform ios --profile production
  npx eas-cli submit --platform ios --profile production
  ```
  - App appears in TestFlight → invite beta testers
- [ ] **Android build (internal)**:
  ```bash
  npx eas-cli build --platform android --profile production
  ```
  - Distribute APK via Firebase App Distribution or direct link
- [ ] **Deep links working**: `sorce://billing/success` opens correct screen
- [ ] **Push notifications**: test that "application submitted" push arrives

## Data & Content (Week -1)

- [ ] **Seed jobs**:
  ```bash
  python scripts/seed_beta.py --jobs-count 100
  ```
- [ ] **Adzuna job feed connected** (or alternative source piping jobs into DB)
- [ ] **Test resume parsed** for 3+ different resume formats (PDF)
- [ ] **Test HOLD flow**: upload resume → swipe right → agent hits HOLD → answer questions → agent completes
- [ ] **Dashboard views refreshed**:
  ```bash
  # Via API:
  curl -X POST https://api.sorce.app/admin/m1-dashboard/refresh -H "Authorization: Bearer $ADMIN_TOKEN"
  ```

## Smoke Test (Day -1)

- [ ] **Run smoke test**:
  ```bash
  python scripts/smoke_test.py --api-url https://api.sorce.app
  ```
  - All checks pass ✅

## GTM (Day 0)

- [ ] **Landing page live** at sorce.app
  - Waitlist email capture
  - 60-second demo video embedded
  - "Join the beta" CTA
- [ ] **Support email configured**: `support@sorce.app` → shared inbox
- [ ] **Social accounts created**: Twitter/X, LinkedIn
- [ ] **First 100 invites sent**:
  - 30 from personal network (email + text)
  - 25 from Reddit post (r/cscareerquestions)
  - 20 from Hacker News "Show HN"
  - 10 from Twitter thread
  - 10 from Discord job search servers
  - 5 from cold LinkedIn DMs to active job seekers

## Monitoring (Day 0+)

- [ ] **Daily check ritual** (founder, every morning):
  1. Open M1 Dashboard (`/admin/m1-dashboard`) or DashboardScreen in app
  2. Check agent success rate (target ≥75%)
  3. Check top failure reasons — file issues for recurring ones
  4. Check Sentry for new errors
  5. Check Stripe dashboard for new subscribers
  6. Reply to all support emails within 12h
- [ ] **Weekly metrics email** (manual for now):
  - MAU, apps processed, success rate, MRR, signups
  - Top 3 user complaints
  - Top 3 agent failures
  - Publish in `#metrics` Slack/Discord channel

---

## Rollback Plan

If critical issues are discovered post-launch:

1. **Agent broken**: Set `AGENT_ENABLED=false`, restart worker. Users can still browse jobs but applications won't process.
2. **API down**: Check Sentry, check database connectivity, restart API process.
3. **Billing broken**: Manually update tenant plans via SQL while debugging:
   ```sql
   UPDATE tenants SET plan = 'PRO' WHERE id = '<tenant_id>';
   ```
4. **Mobile crash loop**: Push OTA update via EAS Update (no App Store review needed):
   ```bash
   npx eas-cli update --branch production --message "hotfix: crash fix"
   ```

---

## Success Criteria Tracking

| Metric | Target | How to Check |
|--------|--------|-------------|
| Active users | 500 MAU | Dashboard → active_users.mau |
| Apps processed | 10,000 total | Dashboard → total_applications |
| Agent success rate | ≥75% | Dashboard → agent_success.success_rate_30d |
| Critical bugs | <5% unresolved P0/P1 | Sentry + GitHub Issues |
| PRO subscribers | First 10 | Stripe Dashboard |
