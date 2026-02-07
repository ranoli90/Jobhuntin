# Sorce: Prototype → $1M ARR Execution Plan

---

## Part 1: Product Roadmap and Milestones

### M1: CLOSED BETA (Months 0–3)

**Success criteria:**
- 500 active users on TestFlight/internal APK
- 10,000 applications processed by the agent
- Agent success rate ≥75% (SUCCESS label in `agent_evaluations`)
- HOLD question resolution rate ≥85%
- <5% critical bugs (P0/P1) unresolved at end of milestone

**Key deliverables:**
- React Native app on TestFlight (iOS) + internal APK (Android)
- Stripe integration: FREE (25 apps/month) → PRO ($29/month, 200 apps/month)
- Resume upload + parse fully functional
- Swipe-to-apply feed with ≥3 job board sources (Adzuna + 2 scraped/API sources)
- In-app HOLD question modal working end-to-end
- Basic email support inbox (founder@sorce.app)
- Invite-only waitlist landing page with referral code

**Dependencies:**
- Existing prototype complete (✅)
- Apple Developer + Google Play Console accounts
- Stripe account + webhook integration
- 1 part-time backend contractor

---

### M2: OPEN BETA + FIRST REVENUE (Months 3–6)

**Success criteria:**
- 3,000 MAU (monthly active users)
- 100 paying PRO subscribers ($2,900 MRR)
- Agent success rate ≥82%
- FREE→PRO conversion rate ≥5%
- App Store rating ≥4.2 stars (50+ reviews)

**Key deliverables:**
- Public App Store + Google Play launch
- Onboarding flow: resume upload → profile review → first swipe in <3 minutes
- Push notifications: "Your application to [Company] was submitted ✅"
- Application history screen with status timeline
- User feedback widget on completed applications ("Was this correct? Yes/No")
- Product Hunt launch
- Referral program: "Give 5 free apps, get 5 free apps"
- Weekly email digest: "You applied to 12 jobs this week. 10 submitted, 2 need your input."

**Dependencies:**
- M1 complete
- Full-time senior engineer hired
- Part-time growth marketer hired
- $50k marketing budget allocated

---

### M3: TEAM FEATURES + VERTICAL EXPANSION (Months 6–10)

**Success criteria:**
- 10,000 MAU
- 500 paying subscribers across all tiers ($18k+ MRR)
- 10 team accounts (3+ seats each)
- ≥1 non-job-app blueprint live (grant applications or vendor onboarding)
- Agent success rate ≥87%
- Monthly churn <6%

**Key deliverables:**
- TEAM plan: shared job lists, team member management, admin dashboard
- Team billing: per-seat pricing via Stripe
- Admin panel (web): tenant management, usage reports, member invites
- Second blueprint shipped (grant applications — universities/nonprofits)
- Job source expansion: LinkedIn Easy Apply, Greenhouse, Lever ATS integration
- Application analytics dashboard in-app: success rate, avg time, top employers
- Smart profile pre-fill: learn from HOLD answers to reduce future holds
- GDPR/CCPA compliance: data export (already built), deletion endpoint, privacy policy

**Dependencies:**
- M2 complete
- 2nd full-time engineer hired
- PM hired (or founder acting as PM)
- $150k runway remaining or seed round closed

---

### M4: SCALE TO $100K MRR (Months 10–15)

**Success criteria:**
- 30,000 MAU
- $100k MRR ($1.2M ARR run-rate)
- 2,000+ paying subscribers
- 50+ team accounts
- 3+ enterprise pilots
- Net revenue retention ≥110%

**Key deliverables:**
- Enterprise tier: SSO (SAML/OIDC), dedicated support, custom SLAs, API access
- Web app (React) for team admins and enterprise users
- Bulk application campaigns: "Apply to all Data Analyst roles in NYC"
- AI cover letter generation per application
- ATS status tracking: detect "Application Received" confirmation emails
- White-label API: let career platforms embed Sorce's agent
- SOC 2 Type I compliance initiated
- Priority processing queue for PRO/ENTERPRISE tiers

**Dependencies:**
- M3 complete
- Seed round closed ($1.5–2.5M)
- Team at 6–8 people
- Sales lead hired for enterprise motion

---

### M5: $1M ARR (Months 15–20)

**Success criteria:**
- $83k+ MRR sustained for 3+ months ($1M ARR)
- 5,000+ paying subscribers
- 100+ team accounts, 5+ enterprise contracts
- LTV:CAC ratio ≥3:1
- Monthly churn <4%
- Agent success rate ≥90%

**Key deliverables:**
- Self-serve enterprise signup with annual billing discounts
- Marketplace: community-contributed blueprints (grant writing, vendor onboarding, scholarship apps)
- Mobile app v3: redesigned dashboard, dark mode, widget for "applications in progress"
- International expansion: EU job boards, multi-language profile parsing
- Automated A/B testing of prompts with auto-graduation (experimentation system v2)
- Customer success playbook for enterprise accounts

**Dependencies:**
- M4 complete
- Team at 10–12 people
- SOC 2 Type I certified
- Series A prep underway

---

### M6 (STRETCH): FIRST ENTERPRISE WIN + ADJACENT VERTICAL (Months 20–24)

**Success criteria:**
- 1 signed enterprise contract ≥$50k ACV
- 1 adjacent vertical generating ≥$10k MRR (grant applications or staffing agency automation)
- Platform used by ≥3 third-party integrators via API

**Key deliverables:**
- Staffing agency blueprint: bulk candidate submission to client job portals
- University career center partnership: white-labeled Sorce for students
- Enterprise admin console: usage dashboards, compliance reports, audit logs
- API v2: webhook callbacks, batch submission, status polling

**Dependencies:**
- M5 complete
- Dedicated enterprise AE
- Legal/compliance counsel (fractional)

---

### Technical Debt and Platform Work

**Allocation rule:** 20% of engineering capacity dedicated to platform/debt work at all times.

| Phase | Platform Focus |
|-------|---------------|
| M1 | Test coverage to ≥60%, CI/CD pipeline, staging environment |
| M2 | Database query optimization, connection pooling tuning, error monitoring (Sentry) |
| M3 | Worker horizontal scaling (multiple instances), job source adapter abstraction |
| M4 | SOC 2 prep, audit logging, secrets management (Vault/AWS SSM), load testing |
| M5 | Multi-region deployment, CDN for mobile assets, database read replicas |

**Platform day cadence:** Every other Friday is "Platform Friday" — no feature work, only debt reduction, dependency upgrades, monitoring improvements, and documentation.

---

### Success Metrics Dashboard

These 7 metrics are the north stars. All are computable from existing analytics tables.

| # | Metric | M1 Target | M2 Target | M3 Target | M4 Target | M5 Target | SQL Source |
|---|--------|-----------|-----------|-----------|-----------|-----------|------------|
| 1 | **MAU** | 500 | 3,000 | 10,000 | 30,000 | 50,000+ | `COUNT(DISTINCT user_id) FROM analytics_events WHERE created_at > now() - '30d'` |
| 2 | **Agent Success Rate** | ≥75% | ≥82% | ≥87% | ≥89% | ≥90% | `COUNT(*) FILTER (WHERE label='SUCCESS') / COUNT(*) FROM agent_evaluations WHERE source='SYSTEM'` |
| 3 | **MRR** | $0 | $2,900 | $18,000 | $100,000 | $83,000+ | Stripe MRR dashboard (or `SUM(plan_price) FROM tenants WHERE plan != 'FREE'`) |
| 4 | **FREE→PRO Conversion** | — | ≥5% | ≥7% | ≥8% | ≥10% | `COUNT(tenants WHERE plan='PRO') / COUNT(tenants WHERE created 30d+ ago)` |
| 5 | **Monthly Churn** | — | <8% | <6% | <5% | <4% | `churned_last_30d / active_start_of_month` |
| 6 | **Avg Hold Questions/App** | <4 | <3 | <2.5 | <2 | <1.5 | `AVG(hold_count)` from `eval_queries.get_avg_hold_questions()` |
| 7 | **NPS** | — | ≥30 | ≥40 | ≥45 | ≥50 | In-app survey (quarterly) |

---

## Part 2: Business Model and Monetization Phases

### Pricing Model Evolution

**Phase 1 — Beta (Months 0–6):**

| Tier | Price | Limits | Features |
|------|-------|--------|----------|
| FREE | $0 | 25 apps/month, 2 concurrent | Resume parsing, hold questions, swipe feed |
| PRO | $29/month | 200 apps/month, 10 concurrent | Priority processing, application analytics, email digest |

**Phase 2 — Growth (Months 6–12):**

| Tier | Price | Limits | Features |
|------|-------|--------|----------|
| FREE | $0 | 10 apps/month, 1 concurrent | Basic resume parsing, swipe feed |
| PRO | $49/month | 200 apps/month, 10 concurrent | Priority processing, analytics, cover letters, multi-source |
| TEAM | $199/month + $49/seat | Unlimited per seat, 20 concurrent | Shared job lists, admin dashboard, team analytics, API access |

**Phase 3 — Enterprise (Months 12+):**

| Tier | Price | Limits | Features |
|------|-------|--------|----------|
| ENTERPRISE | $999–5,000/month | Custom | SSO, dedicated support, SLA, custom blueprints, white-label, audit logs |

**Pricing rationale:**
- $29 PRO anchors below the "mental cost of 1 hour of manual applications"
- $49 at M6 justified by cover letters + expanded sources
- TEAM per-seat aligns with B2B SaaS norms; $199 base covers infra overhead
- FREE tier tightens at M6 to drive conversion (25→10 apps/month)

---

### Revenue Projections by Milestone

| Milestone | Month | Paying Users | MRR | ARR Run-Rate |
|-----------|-------|-------------|-----|-------------|
| M1 end | 3 | 0 (beta) | $0 | $0 |
| M2 end | 6 | 100 PRO | $2,900 | $35k |
| M3 end | 10 | 350 PRO + 10 TEAM (30 seats) | $18,580 | $223k |
| M4 end | 15 | 1,500 PRO + 50 TEAM (200 seats) + 3 Enterprise | $100,250 | $1.2M |
| M5 end | 20 | 3,000 PRO + 80 TEAM (350 seats) + 8 Enterprise | $175,000+ | $2.1M |

**Revenue composition at $1M ARR (M4):**
- Individual PRO: 1,500 × $49 = $73,500/month (73%)
- TEAM: 50 teams × ($199 base + 4 avg seats × $49) = $19,750/month (20%)
- Enterprise: 3 × $2,333 avg = $7,000/month (7%)

---

### Unit Economics

**Per active PRO user:**

| Metric | Value | Notes |
|--------|-------|-------|
| **Monthly revenue** | $49 | Phase 2 pricing |
| **LLM cost per app** | ~$0.03 | GPT-4o-mini: ~750 input + 500 output tokens per mapping call |
| **Infra cost per user** | ~$1.50/month | Supabase Pro ($25/mo shared) + compute + Playwright |
| **COGS per user** | ~$3.50/month | 60 avg apps × $0.03 + $1.50 infra |
| **Gross margin** | ~93% | ($49 - $3.50) / $49 |
| **Average lifespan** | 8 months | Job seekers churn after finding work; some return |
| **LTV** | $392 | $49 × 8 months |
| **Target CAC** | <$80 | For LTV:CAC ≥ 3:1 (later ≥ 5:1) |
| **Monthly churn** | <5% | Target: <4% by M5 |
| **Payback period** | <2 months | $80 CAC / $49 monthly |

**Per TEAM seat:**

| Metric | Value |
|--------|-------|
| Monthly revenue | $49/seat + $199 base (amortized ~$50/seat for 4-seat team) |
| Average lifespan | 14 months (stickier than individual) |
| LTV per seat | $1,386 |
| Target CAC per team | <$500 |

---

### Funding Needs

**Phase 1 — Bootstrap / Pre-Seed (Months 0–6):**
- Burn: $8–12k/month (founder salary + 1 contractor + infra)
- Total needed: $50–75k (personal savings or angel check)
- No formal round; SAFE notes from angels if needed

**Phase 2 — Seed Round (Months 4–8):**
- Raise: $1.5–2.5M on $8–12M post-money SAFE
- Use of funds: 18 months runway, hire to 8 people, marketing budget
- Trigger: 100+ paying users, $2k+ MRR, clear product-market signal
- Burn: $40–60k/month by M3

**Phase 3 — Series A Prep (Months 18–24):**
- Trigger: $100k+ MRR, growing 15%+ MoM
- Target: $5–10M on $40–60M valuation
- Use of funds: scale to 25+ people, international expansion, enterprise sales team

---

## Part 3: Team, Process, and Operations

### Hiring Plan by Milestone

**M1 (Months 0–3): 1–2 people**

| Role | Type | Focus | Comp Range |
|------|------|-------|------------|
| Founder/CTO | Full-time | Architecture, worker, agent, infra | Equity only |
| Backend engineer | Part-time contractor | Playwright stability, job source adapters, CI/CD | $60–80/hr, 20 hrs/week |

**M2 (Months 3–6): 3–4 people**

| Role | Type | Focus | Comp Range |
|------|------|-------|------------|
| Senior full-stack engineer | Full-time (hire #1) | Mobile app, API, Stripe, onboarding | $140–170k + 1–2% equity |
| Growth marketer | Part-time contractor | Product Hunt, Reddit, content, landing pages | $50–70/hr, 15 hrs/week |
| Customer support | Part-time contractor | Email triage, bug reports, user onboarding | $25–35/hr, 10 hrs/week |

**M3 (Months 6–10): 5–7 people**

| Role | Type | Focus | Comp Range |
|------|------|-------|------------|
| Full-stack engineer #2 | Full-time | Team features, admin panel, web app | $130–160k + 0.5–1% equity |
| Product manager | Full-time | Roadmap, user research, metrics | $130–150k + 0.5–1% equity |
| Growth marketer | Full-time (convert contractor) | Content, partnerships, paid acquisition | $100–130k + 0.25–0.5% |
| Customer success | Full-time | Onboarding, retention, team accounts | $60–80k + 0.1–0.25% |

**M4–M5 (Months 10–20): 8–12 people**

| Role | Type | Focus | Comp Range |
|------|------|-------|------------|
| ML/AI engineer | Full-time | Prompt optimization, agent intelligence, eval pipelines | $150–180k + 0.5% |
| Frontend engineer | Full-time | Web admin console, enterprise dashboard | $130–160k + 0.25% |
| Sales lead (enterprise) | Full-time | Enterprise pipeline, PoCs, partnerships | $120–140k base + commission + 0.5% |
| DevOps/SRE | Full-time | SOC 2, scaling, monitoring, multi-region | $140–170k + 0.25% |

---

### Team Structure and Ownership

```
CEO/Founder
├── CTO/Founder
│   ├── Senior Engineer (full-stack / mobile)
│   ├── Engineer #2 (backend / web)
│   ├── ML/AI Engineer
│   ├── Frontend Engineer
│   └── DevOps/SRE
├── Product Manager
│   └── Designer (contractor, M4+)
├── Growth Lead
│   ├── Content (contractor)
│   └── Community (contractor)
├── Sales Lead (M4+)
│   └── AE/BDR (M5+)
└── Customer Success
    └── Support (contractor)
```

**Ownership areas:**
- **CTO:** Worker/agent, LLM prompts, blueprints, infra, experiments
- **Senior Engineer:** Mobile app, API, billing, onboarding
- **Engineer #2:** Team features, admin panel, web app, ATS integrations
- **ML/AI Engineer:** Prompt optimization, eval pipelines, success rate improvements
- **PM:** Roadmap, metrics, user research, release notes, experiment reviews
- **Growth Lead:** All acquisition channels, content, partnerships, landing pages
- **Sales Lead:** Enterprise pipeline, pricing negotiations, PoC management

---

### Engineering Processes

**Code review:**
- All PRs require 1 approval (2 for worker/agent changes)
- CTO reviews all LLM prompt changes and agent logic changes
- Max PR size: 400 lines (larger → split into stacked PRs)

**Release cadence:**
- Mobile: weekly TestFlight builds, bi-weekly App Store releases
- Backend: continuous deployment to staging; production deploys 2–3x/week
- Worker: gated deploys — new agent behavior always behind experiments first

**Oncall:**
- M1–M2: CTO on call 24/7 (PagerDuty on worker failures)
- M3+: weekly rotation among engineers, 1-week shifts
- Oncall playbook: check Sentry → check `/healthz` → check agent metrics → check DB

**Experiment review:**
- Weekly 30-min "Agent Review" meeting
- Review: experiment results, top failure reasons, hold question frequency
- Decision: graduate/kill experiments, prioritize prompt fixes
- Uses the tuning cycle playbook (`docs/playbooks/tuning_cycle.md`)

**Incident management:**
- P0 (agent down / data loss): respond in 15 min, postmortem within 48h
- P1 (degraded success rate / billing bug): respond in 1h
- P2 (UI bug / cosmetic): next sprint
- All P0/P1 get written postmortems in `docs/incidents/`

---

### Support Model Evolution

| Phase | Channel | SLA | Owner |
|-------|---------|-----|-------|
| M1 (0–3mo) | `support@sorce.app` | 24h response | Founder |
| M2 (3–6mo) | Intercom live chat + email | 12h response | Support contractor |
| M3 (6–10mo) | Intercom + help center (FAQ) + in-app feedback | 4h (PRO), 12h (FREE) | Customer success + engineer rotation (1 day/sprint) |
| M4+ (10mo+) | Intercom + Slack Connect (enterprise) + phone | 1h (Enterprise), 4h (TEAM), 12h (PRO) | Dedicated CS + escalation to engineering |

---

## Part 4: Go-to-Market Execution Plan

### Channel Prioritization

**Month 1–3: Product-Led Growth (Budget: $5k)**

| Channel | Action | CAC Estimate | Target Users |
|---------|--------|-------------|-------------|
| Reddit | Daily posts in r/cscareerquestions, r/jobs, r/recruitinghell, r/datascience — genuine value-first answers with Sorce mention | $0 (time) | 200 |
| Twitter/X | Job search tips thread series → CTA to waitlist. Engage with #opentowork, #jobsearch, #techtwitter | $0 (time) | 100 |
| Product Hunt | Launch at M2 with pre-built upvote network. Target #1–3 Product of the Day | $500 (design assets) | 500 |
| University career centers | Cold email 20 career services directors with free pilot offer | $0 (time) | 100 |
| Hacker News | "Show HN: I built an AI that fills out job applications for you" | $0 (time) | 300 |
| Discord | Job search servers, tech career communities | $0 (time) | 50 |
| Referral program | "Invite friends, both get 5 free apps" | $2–5 effective CAC | 100 |

**Month 4–6: Content + Partnerships (Budget: $15k)**

| Channel | Action | CAC Estimate | Target Users |
|---------|--------|-------------|-------------|
| Newsletter | Weekly "Job Search Tactics" email — tips, Sorce success stories, industry data | $5–10 per subscriber via paid promotion | 2,000 subscribers |
| LinkedIn Ads | Targeting job seekers: "Active job search" + recent role change | $15–25 CAC | 200 |
| Blog/SEO | 10 long-form posts targeting "how to apply to more jobs", "job application automation" | $0 (time) + $2k for freelance writers | 1,000 organic/month |
| YouTube | 3 short demos: "Watch Sorce apply to 20 jobs in 10 minutes" | $500 production | 500 |
| University partnerships | 5 signed partnerships: free TEAM account for career center + student discount | $0 (barter) | 500 |

**Month 7–12: Paid Acquisition + Sales (Budget: $30k)**

| Channel | Action | CAC Estimate | Target Users |
|---------|--------|-------------|-------------|
| Google Ads | Intent keywords: "apply to jobs faster", "job application automation", "auto apply jobs" | $20–40 CAC | 500 |
| Meta/Instagram Ads | Retargeting website visitors + lookalike audiences | $15–30 CAC | 300 |
| LinkedIn Outbound | Sales lead targets HR directors and TA managers at staffing firms | $200–500 CAC (enterprise) | 20 enterprise leads |
| Affiliate program | Resume builders, career coaches get 20% recurring commission | $10–15 effective CAC | 200 |
| Conference sponsorship | 1–2 career fairs or HR tech events | $2–5k per event | 50 qualified leads |

---

### Content Flywheel

**Weekly content calendar (first 6 months):**

| Day | Content Type | Channel | Example |
|-----|-------------|---------|---------|
| Monday | Job search tip thread | Twitter/X | "5 mistakes that get your application auto-rejected (and how to fix them)" |
| Tuesday | Reddit value post | r/cscareerquestions | "I analyzed 500 job applications — here's what actually gets callbacks" |
| Wednesday | Newsletter issue | Email | "This week: 3 new job sources added, average success rate hit 85%" |
| Thursday | Blog/SEO article | sorce.app/blog | "The Complete Guide to Applying to 50+ Jobs Per Week Without Burnout" |
| Friday | User story / case study | LinkedIn + Twitter | "How Sarah landed a $120k role by automating her job search with Sorce" |

**Top 10 content pieces that drive signups:**

1. "I Applied to 100 Jobs in One Weekend Using AI — Here's What Happened" (blog + Reddit)
2. "Sorce vs. Manual Applications: A 30-Day Experiment" (blog + YouTube)
3. "The Hidden Cost of Applying to Jobs Manually" (infographic + LinkedIn)
4. "How to Write a Resume That AI Can Actually Parse" (SEO blog)
5. "Job Application Automation: Is It Ethical? A Founder's Perspective" (thought leadership)
6. "Watch Sorce Fill Out a Greenhouse Application in Real-Time" (screen recording + YouTube)
7. "From 5 Applications/Week to 50: One Student's Story" (case study)
8. "The Job Search Stack: Tools I Use to Land Interviews 3x Faster" (listicle + affiliate)
9. "Why Your Job Applications Keep Failing (And How an AI Agent Fixes It)" (newsletter)
10. "Sorce for Career Centers: How Universities Are Helping Students Apply Smarter" (whitepaper)

**Case study template:**
```
HEADLINE: How [Name] [achieved result] using Sorce
CONTEXT: [Background, job search pain]
BEFORE: [Manual process, time spent, results]
AFTER: [Sorce usage, time saved, outcome]
METRICS: [Applications submitted, success rate, time to offer]
QUOTE: "[Pull quote from user]"
CTA: Try Sorce free → [link]
```

---

### Sales Motion by Segment

**Individuals (80% of revenue through M4):**
```
Funnel: Content/Ad → Landing page → Sign up (FREE) → Resume upload → First swipe
        → HOLD question answered → "Wow, it worked" → PRO upgrade prompt
        → 7-day free trial of PRO → Convert to paid

Key conversion moments:
  1. First successful application (within 24h of signup)
  2. Push notification: "Your application to [Company] was submitted ✅"
  3. End of free tier: "You've used 10/10 free applications. Upgrade for $29/month."
  4. Trial end: "Your PRO trial ends tomorrow. Keep your momentum."
```

**Teams (15% of revenue at M4):**
```
Funnel: Content → "Sorce for Teams" landing page → Request demo → 15-min Zoom
        → 14-day team trial → Onboarding call → Convert to paid

Qualification: 3+ people actively job searching (bootcamp cohorts, laid-off teams,
               staffing agencies, career centers)

Sales cycle: 1–2 weeks
Closing: Founder or Growth Lead handles through M3; Sales Lead from M4
```

**Enterprise (5–10% of revenue at M4+):**
```
Funnel: Outbound (LinkedIn Sales Nav) + Inbound (whitepaper downloads)
        → Discovery call → Technical PoC (90 days, free) → Procurement → Close

Target profiles:
  - Staffing agencies (50–500 employees)
  - University career centers (state schools, bootcamps)
  - Outplacement firms
  - Large companies with internal mobility programs

Sales cycle: 60–120 days
Deal size: $12–60k ACV
Closing: Sales Lead + CTO for technical PoC support
```

---

### Partnership Strategy

| Partner Type | Target Partners | Value Prop | Deal Structure | Timeline |
|-------------|----------------|------------|---------------|----------|
| Job boards | Adzuna (existing), Indeed, ZipRecruiter | We drive application volume; they get completions | Revenue share or API access fee | M2–M3 |
| ATS platforms | Greenhouse, Lever, Workday | Our agent fills their forms correctly; reduces junk apps | Integration partnership, co-marketing | M3–M4 |
| Universities | Top 50 US career centers, coding bootcamps (Lambda, GA, Flatiron) | Free TEAM accounts; students get PRO discount | White-label or co-branded | M2–M4 |
| Resume builders | Resume.io, Zety, Canva | "Built your resume? Now auto-apply with Sorce" | Affiliate: 20% recurring commission | M3+ |
| Career coaches | Independent coaches + coaching platforms | Recommend Sorce to clients; track results | Affiliate: 20% recurring + co-branded landing pages | M3+ |
| Outplacement | RiseSmart, Randstad, LHH | Embed Sorce in outplacement packages | Enterprise license, white-label | M4+ |

**Affiliate program structure:**
- 20% recurring commission for 12 months
- Custom referral links + dashboard
- Minimum 5 conversions/month to stay active
- Monthly payouts via Stripe Connect
- Launched at M3

---

### Week 1 GTM Checklist

**Day 1 of closed beta — ship all of the following:**

**Landing page (sorce.app):**
- Hero: "Stop filling out job applications. Let AI do it."
- Sub: "Sorce auto-applies to jobs using your resume. You swipe right, we do the rest."
- Social proof: "500+ applications submitted in beta" (update live)
- CTA: "Join the beta — 25 free applications"
- Waitlist with email capture
- 60-second demo video (screen recording of swipe → agent fills → push notification)

**First 100 users acquisition plan:**

| # | Action | Target | Timeline |
|---|--------|--------|----------|
| 1 | Personal network blast: email + text + LinkedIn DM | 30 signups | Day 1–2 |
| 2 | Reddit post: "I built an AI agent that fills out job applications for you — looking for beta testers" in r/cscareerquestions | 25 signups | Day 1 |
| 3 | Hacker News "Show HN" post | 20 signups | Day 2 |
| 4 | Twitter thread: "I'm a CTO who spent 6 months building an AI that does job applications. Here's what I learned 🧵" | 10 signups | Day 3 |
| 5 | Cold DM 50 active job seekers on Twitter/LinkedIn with personalized invite | 10 signups | Day 3–5 |
| 6 | Post in 10 job search Discord servers | 5 signups | Day 4–5 |

**Total: ~100 beta users in first week with $0 spend.**

**Tracking setup (Day 1):**
- Analytics events flowing to `analytics_events` table
- Agent success rate visible in `/admin/agent-performance`
- Stripe test mode → live mode switch
- Sentry error tracking configured
- Weekly metrics email to founders (manual SQL → spreadsheet initially)

**Feedback loop (Week 1):**
- Every beta user gets a personal "How's it going?" email from the founder on Day 3
- In-app feedback widget active on all completed applications
- Slack channel `#beta-feedback` for real-time user messages
- End-of-week survey: "Would you pay $29/month for this? What's missing?"
