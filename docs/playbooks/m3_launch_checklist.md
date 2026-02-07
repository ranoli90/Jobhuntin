# M3 Team Features + Vertical Expansion — Launch Checklist

Complete every item before enabling TEAM billing and the grant blueprint in production.

---

## Pre-Launch: Infrastructure (Week -2)

- [ ] **Migration 012 applied**: TEAM enum, team_invites, seat columns, shared job lists
  ```bash
  supabase db push  # applies 012_m3_teams.sql
  ```
- [ ] **Migration 013 applied**: grant_profiles, grant_portals, application.grant_profile_id
  ```bash
  supabase db push  # applies 013_m3_grant_blueprint.sql
  ```
- [ ] **Migration 014 applied**: M3 materialized views (team metrics, blueprint perf, churn risk)
  ```bash
  supabase db push  # applies 014_m3_dashboard_views.sql
  ```

## Stripe Configuration

- [ ] **Create Stripe Products**:
  - Product: "Sorce TEAM" 
    - Price 1: $199/month (base — includes 3 seats) → set as `STRIPE_TEAM_BASE_PRICE_ID`
    - Price 2: $49/month per unit (additional seats) → set as `STRIPE_TEAM_SEAT_PRICE_ID`
  - Verify existing PRO product ($29/month) still active

- [ ] **Stripe Customer Portal** — enable seat management:
  - Settings → Customer Portal → enable subscription updates
  - Allow quantity changes for the seat price
  - Allow plan switching (PRO ↔ TEAM)

- [ ] **New env vars on API server**:
  ```
  STRIPE_TEAM_BASE_PRICE_ID=price_xxx
  STRIPE_TEAM_SEAT_PRICE_ID=price_xxx
  TEAM_INCLUDED_SEATS=3
  ```

- [ ] **Webhook updated**: verify `checkout.session.completed` handles TEAM metadata:
  - Sets `tenants.plan = 'TEAM'`
  - Sets `tenants.max_seats` from checkout metadata
  - Stores `stripe_subscription_item_id` for seat line item

## Web Admin Deployment

- [ ] **Deploy web-admin to Vercel**:
  ```bash
  cd web-admin
  npm install
  npm run build  # verify no build errors
  npx vercel --prod
  ```

- [ ] **Set Vercel environment variables**:
  ```
  VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
  VITE_SUPABASE_ANON_KEY=your_anon_key
  VITE_API_URL=https://api.sorce.app
  ```

- [ ] **Custom domain**: Point `admin.sorce.app` to Vercel deployment

- [ ] **CORS**: Add `https://admin.sorce.app` to FastAPI CORS allowed origins

- [ ] **Verify all pages**:
  - [ ] Login with Supabase credentials
  - [ ] Dashboard: shows team stats, member activity table
  - [ ] Members: list, remove (non-owner)
  - [ ] Usage: quota bars, Stripe portal link, seat management
  - [ ] Invites: send invite, see pending/accepted/expired

## Team Billing End-to-End

- [ ] **TEAM checkout flow**:
  1. Owner calls `POST /billing/team-checkout` with `seats=5, team_name="Acme Corp"`
  2. Stripe Checkout opens with base ($199) + 2 additional seats ($98)
  3. Payment completes → webhook fires
  4. Verify: `tenants.plan = 'TEAM'`, `tenants.max_seats = 5`, `tenants.team_name = 'Acme Corp'`

- [ ] **Seat management**:
  1. Owner calls `POST /billing/add-seats` with `new_total_seats=7`
  2. Stripe subscription updates (prorated)
  3. Verify: `tenants.max_seats = 7`

- [ ] **Invite flow**:
  1. Admin calls `POST /billing/invite` with `email=new@company.com`
  2. Invite created with 7-day expiry token
  3. New user calls `POST /billing/invite/accept` with token
  4. Verify: user added to `tenant_members`, `tenants.seat_count` incremented

- [ ] **Member removal**:
  1. Admin calls `DELETE /billing/team/members/{user_id}`
  2. Verify: member removed, seat_count decremented
  3. Verify: OWNER cannot be removed (400 error)

- [ ] **Seat limit enforcement**:
  1. Fill all seats
  2. Try to invite → should get "Seat limit reached" error
  3. Add more seats → invite succeeds

## Grant Blueprint Verification

- [ ] **Blueprint registered**: On API startup, logs show `Registered blueprint: Grant Applications (v0.1.0) as 'grant'`

- [ ] **Grant profile parsing**:
  1. Upload an org document / grant narrative
  2. Parse returns `GrantApplicantProfile` with org name, EIN, project title, budget
  3. Verify all fields populated correctly

- [ ] **Grant DOM mapping**:
  1. Navigate agent to a test grant form
  2. Profile data maps to form fields correctly
  3. Unresolved required fields return clear questions

- [ ] **Grant application end-to-end**:
  1. Create application with `blueprint_key = 'grant'`
  2. Worker picks up task, dispatches to `GrantApplicationBlueprint`
  3. Agent navigates, fills form, submits
  4. Push notification: "Application Submitted!"
  5. Verify in `mv_blueprint_performance`: grant row appears

- [ ] **Grant portal registry**: `grant_portals` table has Grants.gov, Foundation Directory entries

## M3 Analytics Verification

- [ ] **M3 dashboard returns data**:
  ```bash
  curl -H "Authorization: Bearer $ADMIN_TOKEN" https://api.sorce.app/admin/m3-dashboard
  ```
  Verify all sections: `team_metrics`, `blueprint_performance`, `mrr_by_plan`, `churn_risk`, `m3_targets`

- [ ] **Refresh views**:
  ```bash
  curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" https://api.sorce.app/admin/m3-dashboard/refresh
  ```

- [ ] **MRR calculation correct**:
  - FREE: $0
  - PRO: $29 × count
  - TEAM: $199 + ($49 × extra seats) × count
  - Total matches Stripe dashboard

- [ ] **Churn risk list**: shows paying tenants inactive >7 days

- [ ] **Blueprint performance**: both `job-app` and `grant` rows with success rates

## Mobile TeamOwnerScreen

- [ ] **Screen accessible** for TEAM plan users
- [ ] **Stats grid**: members, seats, apps/month, pending invites
- [ ] **Quick invite**: send invite from mobile
- [ ] **Member list**: shows all members with roles and usage
- [ ] **Admin dashboard link**: opens `admin.sorce.app` in browser

## Go-Live Sequence

1. Deploy migrations 012 → 013 → 014
2. Set Stripe env vars
3. Deploy API with new billing + analytics endpoints
4. Deploy web-admin to Vercel
5. Deploy mobile update with TeamOwnerScreen
6. Enable TEAM plan in Stripe (make prices active)
7. Announce to existing PRO users via push + email

## Week 1 Monitoring

- [ ] **Daily checks**:
  - New TEAM signups (target: 2-3/week)
  - Seat expansion events
  - Grant blueprint success rate vs job-app rate
  - Churn risk list — reach out to at-risk teams
  - MRR trending toward $18k target

- [ ] **Team onboarding**:
  - First team signs up → personal welcome email from founder
  - First 10 teams → schedule 15-min onboarding call
  - Track: avg seats per team (target: 3+), apps per team member

- [ ] **Grant blueprint feedback**:
  - Monitor hold question rate (should be <30%)
  - Collect portal-specific field mapping improvements
  - Update `grant_portals` table with new portal configs
