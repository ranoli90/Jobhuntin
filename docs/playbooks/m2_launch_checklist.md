# M2 Open Beta — Launch Checklist

Complete every item before the public App Store / Google Play launch.

---

## Pre-Launch: Infrastructure (Week -2)

- [ ] **Migration 010 applied**: `push_tokens`, `notification_log`, `referrals`, `email_digest_log`, `bonus_app_credits` column
  ```bash
  supabase db push  # applies 010_m2_growth.sql
  ```
- [ ] **Migration 011 applied**: conversion funnel + cohort materialized views
  ```bash
  supabase db push  # applies 011_m2_conversion_views.sql
  ```
- [ ] **New env vars set on API server**:
  ```
  EXPO_PUSH_ACCESS_TOKEN=...
  RESEND_API_KEY=...
  EMAIL_FROM=Sorce <noreply@sorce.app>
  REFERRAL_REWARD_APPS=5
  APP_STORE_URL=https://apps.apple.com/app/sorce/id...
  PLAY_STORE_URL=https://play.google.com/store/apps/details?id=app.sorce.mobile
  ```
- [ ] **Growth router verified**: `GET /referral`, `POST /push/register`, `POST /onboarding/complete` all return 200/401
- [ ] **Resend domain verified**: SPF/DKIM for `sorce.app`
- [ ] **Expo push credentials configured**: `npx eas-cli credentials` for both iOS (APNs) and Android (FCM)

## App Store Submission (Week -1)

- [ ] **iOS production build**:
  ```bash
  cd mobile
  npx eas-cli build --platform ios --profile production
  npx eas-cli submit --platform ios --profile production
  ```
- [ ] **Fill App Store Connect metadata** from `mobile/store-listing.json`:
  - Name, subtitle, description, keywords, promotional text
  - 6.5" and 5.5" screenshots (min 3 each)
  - App preview video (optional, recommended)
  - Category: Business, Secondary: Productivity
  - Privacy policy URL: `https://sorce.app/privacy`
  - Age rating: 4+
- [ ] **App Review notes**: "This app automates job applications using AI. Test account: test@sorce.app / TestPass123!"
- [ ] **Submit for review** (allow 24-48h)

- [ ] **Android production build**:
  ```bash
  npx eas-cli build --platform android --profile production
  npx eas-cli submit --platform android --profile production
  ```
- [ ] **Fill Google Play Console metadata** from `mobile/store-listing.json`:
  - Title, short/full description
  - Feature graphic (1024×500), screenshots
  - Content rating questionnaire
  - Privacy policy URL
- [ ] **Release to production track** (or staged rollout 20% → 100%)

## Product Hunt Launch (Day 0)

- [ ] **Product Hunt post scheduled** (Tuesday 12:01 AM PT for best results):
  - Tagline: "Swipe right on jobs. AI fills out the application for you."
  - Description: 3 paragraphs + demo GIF
  - First comment from maker: personal story + CTA to download
  - Topics: Artificial Intelligence, Productivity, Job Search
  - Link: `https://sorce.app/download?utm_source=producthunt&utm_medium=referral&utm_campaign=launch_day`

- [ ] **Landing page updated for launch day**:
  - Product Hunt badge embedded (see `mobile/src/lib/productHunt.ts` for HTML)
  - Download links to App Store + Google Play
  - "Featured on Product Hunt" banner
  - Social proof: "X applications submitted in beta"

- [ ] **Social media blitz** (Day 0, timed):
  - 6 AM: Twitter/X thread (founder story + demo video)
  - 8 AM: LinkedIn post
  - 10 AM: Reddit posts (r/cscareerquestions, r/jobs, r/SideProject)
  - 12 PM: Hacker News "Show HN"
  - 2 PM: Product Hunt first comment engagement
  - All day: Reply to every PH comment within 30 min

## Growth Features Verification (Week -1)

- [ ] **Push notifications end-to-end**:
  1. Register token: open app → permission prompt → token sent to backend
  2. Submit an application → receive "Application Submitted!" push within 60s
  3. HOLD flow → receive "Input Needed" push
  4. Verify on both iOS and Android devices

- [ ] **Referral program end-to-end**:
  1. User A: `GET /referral` → receives code `SORCE-XXXXXXXX`
  2. User A: shares via ReferralScreen share button
  3. User B: enters code during onboarding
  4. Verify: both A and B get `+5` bonus_app_credits on their tenant
  5. User A: receives "Referral Reward!" push notification

- [ ] **Email digest test**:
  1. Create some test applications
  2. Trigger: `POST /admin/trigger-digest` (admin auth)
  3. Check Resend dashboard for sent email
  4. Verify HTML renders correctly in Gmail + Apple Mail

- [ ] **Onboarding flow test**:
  1. New user signs up
  2. Welcome slide → Get Started
  3. Resume upload slide → upload PDF → success badge
  4. Referral code slide → enter code → "Start Swiping"
  5. Verify: `onboarding_completed_at` set on user row
  6. First swipe available immediately

- [ ] **Upgrade funnel test**:
  1. Use 20/25 free apps → verify 80% nudge appears (once per 24h)
  2. Use 25/25 free apps → verify hard paywall appears
  3. Complete 3rd app → verify "Go PRO" prompt
  4. After 7 days on FREE → verify retention nudge
  5. After 5th app → verify in-app review prompt (once per 90d)

## Analytics Verification

- [ ] **M2 dashboard returns data**:
  ```bash
  curl -H "Authorization: Bearer $ADMIN_TOKEN" https://api.sorce.app/admin/m2-dashboard
  ```
  Verify: `conversion_funnel`, `weekly_cohorts`, `referral_performance`, `signup_sources` present

- [ ] **UTM tracking works**:
  1. Open `https://sorce.app/download?utm_source=producthunt&utm_medium=referral&utm_campaign=launch_day`
  2. Install app → complete onboarding
  3. Refresh M2 dashboard → verify `signup_sources` shows `producthunt`

- [ ] **All new analytics events fire**:
  - `onboarding_started`, `onboarding_resume_uploaded`, `onboarding_completed`
  - `referral_shared`, `referral_redeemed`
  - `upgrade_prompt_shown`, `upgrade_started`, `upgrade_completed`
  - `push_token_registered`, `review_prompt_shown`

## Day 0 Monitoring

- [ ] **Founder dashboard check every 2 hours**:
  1. MAU trending toward 3,000 target
  2. Conversion funnel drop-off points
  3. Agent success rate ≥82%
  4. Sentry: no new P0/P1 errors
  5. Stripe: new subscribers appearing
  6. Product Hunt: upvote count + comment engagement

- [ ] **Emergency contacts**:
  - Agent down → set `AGENT_ENABLED=false`, post status to Twitter
  - App crash → push OTA update: `npx eas-cli update --branch production --message "hotfix"`
  - Billing broken → manual SQL: `UPDATE tenants SET plan = 'PRO' WHERE id = '...'`

## Week 1 Post-Launch

- [ ] **Daily metrics review** (first 7 days):
  - Signups per day (target: 100+/day from PH)
  - Onboarding completion rate (target: ≥60%)
  - FREE→PRO conversion (target: ≥5%)
  - App Store rating (target: ≥4.2)
  - Push notification opt-in rate (target: ≥60%)
- [ ] **Reply to every App Store review** within 24h
- [ ] **Send first weekly digest** on Day 7:
  ```bash
  curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" https://api.sorce.app/admin/trigger-digest
  ```
- [ ] **Write first case study** from a Day 1 user success story
