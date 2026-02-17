# JobHuntin/Sorce - Project Memory Bank

## Company Identity

**Product Name:** JobHuntin (formerly Sorce)  
**Domain:** jobhuntin.com  
**Tagline:** "Stop filling out job applications. Let AI do it."  
**Core Value Prop:** Fully autonomous AI agent that discovers jobs, tailors resumes, and applies on your behalf - "Set it and forget it"

## Business Model

### Pricing Tiers (Phase 2 - Growth)
| Tier | Price | Limits | Features |
|------|-------|--------|----------|
| FREE | $0 | 10 apps/month | Basic resume parsing, swipe feed |
| PRO | $49/month | 200 apps/month | Priority processing, analytics, cover letters, multi-source |
| TEAM | $199/month + $49/seat | Unlimited per seat | Shared job lists, admin dashboard, API access |
| ENTERPRISE | $999-5,000/month | Custom | SSO, dedicated support, SLA, custom blueprints |

### Revenue Targets
- M2 (Month 6): $2,900 MRR (100 PRO users)
- M3 (Month 10): $18,000 MRR (500 subscribers)
- M4 (Month 15): $100,000 MRR ($1.2M ARR)
- M5 (Month 20): $83,000+ MRR ($1M ARR sustained)

### Unit Economics
- LTV (PRO): $392 (8 months avg lifespan)
- Target CAC: <$80
- Gross Margin: ~93%
- Monthly Churn Target: <4% by M5

## Competitive Landscape

### Top Direct Competitors
1. **JobRight.ai** ($7.7M Series A) - "Searchless" AI agent, vector matching
2. **Simplify.jobs** ($4.35M Seed) - Chrome extension, DOM autofill
3. **LazyApply** - High volume brute-force (up to 1,500 apps/day)
4. **LoopCV** - Pipeline campaign manager with email outreach
5. **AIApply** ($354K) - End-to-end suite with interview copilot
6. **Teal (TealHQ)** ($19M) - CRM-style job tracking
7. **ApplyPass** - Tech sector focused, vector-based matching
8. **JobCopilot** - Adaptive ML that learns from user edits
9. **Final Round AI** ($6.88M) - Apply bot + interview prep

### Four Strategic Archetypes
1. **Volume Maximizer** (LazyApply) - Brute force, diminishing returns
2. **Precision Matcher** (JobRight, ApplyPass) - Semantic matching, high relevance
3. **Workflow Orchestrator** (Teal, Careerflow) - CRM for job seekers
4. **Document Ecosystem** (Rezi, Kickresume) - Resume optimization

### JobHuntin Differentiators
- **Autopilot vs Copilot** - Fully autonomous, not just assistance
- **Stealth Mode** - Human-like browsing patterns, evades bot detection
- **Per-Application Resume Tailoring** - Every app gets custom resume
- **Background Operation** - No active browser tab needed
- **Explainable Matching** - Shows why each job was selected

## Architecture Overview

### Monorepo Structure
```
apps/
├── api/           FastAPI v1 (tenants, applications, webhooks)
├── api_v2/        Experimental routes, magic-link auth
├── web/           Vite/React UI + AI-powered SEO scripts
├── web-admin/     Operator dashboard for agencies
├── extension/     Chromium extension
├── worker/        Playwright FormAgent + ScalingManager
packages/
├── backend/       Domain models, repositories, LLM orchestration
├── blueprints/    Community + staffing-agency blueprints
├── partners/      University + enterprise adapters
├── shared/        Config, logging, metrics, redis, telemetry
```

### Tech Stack
- **Backend:** Python 3.12, FastAPI, asyncpg, Pydantic
- **Frontend:** React 18, Vite, Tailwind, TypeScript
- **Mobile:** Expo/React Native
- **Database:** PostgreSQL (Render)
- **LLM:** OpenRouter with google/gemini-2.0-flash (primary), openai/gpt-4o-mini (fallback)
- **Browser Automation:** Playwright
- **Infrastructure:** Render (API, workers, web)
- **Billing:** Stripe

### Key Domain Modules (backend/domain/)
- `models.py` - CanonicalProfile, Application, Job, Tenant
- `repositories.py` - ApplicationRepo, JobRepo, ProfileRepo
- `billing.py` - Stripe integration
- `quotas.py` - Rate limiting per plan
- `notifications.py` - Push/email alerts
- `analytics_events.py` - Usage tracking

### LLM Integration (backend/llm/)
- `client.py` - LLMClient with retry logic
- `prompt_registry.py` - Prompt templates
- `contracts.py` - Typed response schemas

## FormAgent (Worker)

### Flow
1. Poll PostgreSQL queue for pending applications
2. Fetch job URL and CanonicalProfile
3. Launch Playwright headless browser
4. Navigate to job application page
5. LLM maps DOM fields to profile fields
6. Fill form with human-like timing
7. Handle HOLD questions (user input needed)
8. Submit and record result
9. Emit metrics/telemetry

### Key Metrics
- **Agent Success Rate Target:** 90%+ by M5
- **HOLD Question Rate:** <1.5 per app by M5
- **Current Status:** 75%+ success in closed beta

## SEO Engine

### Location
`apps/web/scripts/seo/`

### Components
- `automated-ranking-engine.ts` - AI-powered content generation
- `submit-to-google.ts` - Google Indexing API integration
- `seo-monitoring-dashboard.ts` - Performance tracking
- `generate-competitor-content.ts` - Competitive content pages
- `generate-city-content.ts` - Location-based pages

### Target Keywords
- Role pages: "Software Engineer jobs", "Data Scientist career"
- Competitor comparisons: "JobHuntin vs LazyApply", "Jobright alternative"
- Location + role: "Software Engineer jobs San Francisco"

## Known Technical Debt (from Audit)

### P0 Blockers
1. ~~Missing Bot import in Login.tsx~~ (needs verification)
2. ~~useCoverLetter missing reset function~~ (needs verification)
3. ~~AI endpoints lack authentication~~ **RESOLVED** - JWT auth injected via `app.dependency_overrides`
4. Empty extension background worker
5. ~~Corrupted requirements.txt redis declaration~~ (needs verification)
6. LinkedIn URL not persisted in Onboarding

### P1 Issues
1. SignOut doesn't update local session
2. SSO user auto-provisioning incomplete
3. JobMatchScore interface mismatch
4. No versioned database migrations
5. ~~No rate limiting on API v1 endpoints~~ **RESOLVED** - middleware added in main.py

## Regulatory Considerations

### Compliance Requirements
- **CCPA/ADMT** (Jan 2027) - Automated decision-making transparency
- **GDPR Article 22** - Right to opt-out of automated processing
- **EU AI Act** - Employment AI classified as high-risk

### Mitigation Strategies
1. **Legal Bifurcation** - Agent acts on behalf of candidate, not as decision-maker
2. **Batch Review Mode** - User approves queued applications (HITL)
3. **Algorithmic Auditing** - Third-party bias audits bi-annually

## Partnership Targets

| Type | Targets | Value Prop |
|------|---------|------------|
| Job Boards | Adzuna, Indeed, ZipRecruiter | Drive application volume |
| ATS Platforms | Greenhouse, Lever, Workday | Verified Application Partner |
| Universities | Top 50 career centers, bootcamps | Free TEAM accounts |
| Resume Builders | Resume.io, Zety | Affiliate (20% recurring) |

## Development Commands

```bash
# Python
.venv/Scripts/pytest tests/           # Run tests
.venv/Scripts/ruff check backend/     # Lint
.venv/Scripts/mypy backend/           # Typecheck

# Web
cd apps/web && npm run dev            # Dev server
npm run seo:engine                    # SEO engine
npm run build                         # Production build

# API
set PYTHONPATH=apps;packages
.venv/Scripts/uvicorn api.main:app --reload

# Worker
python -m apps.worker.agent           # Single FormAgent
python -m apps.worker.scaling --instances 4
```

## Success Metrics Dashboard

| Metric | M1 | M2 | M3 | M4 | M5 |
|--------|----|----|----|----|----|
| MAU | 500 | 3,000 | 10,000 | 30,000 | 50,000+ |
| Agent Success | 75% | 82% | 87% | 89% | 90% |
| MRR | $0 | $2,900 | $18,000 | $100,000 | $83,000+ |
| Free→PRO Conv | - | 5% | 7% | 8% | 10% |
| Monthly Churn | - | <8% | <6% | <5% | <4% |
| Avg HOLDs/App | <4 | <3 | <2.5 | <2 | <1.5 |

---
Last Updated: 2026-02-12

## Production Readiness Roadmap (GLM-5 Analysis)

### Completed (M1-M3)
- [x] AI endpoints auth verification
- [x] Rate limiting middleware on API
- [x] Test suite passes (129 passed, 10 skipped)
- [x] Vector embedding service (packages/backend/domain/embeddings.py)
- [x] Semantic matching service (packages/backend/domain/semantic_matching.py)
- [x] Dynamic resume tailoring (packages/backend/domain/resume_tailoring.py)
- [x] ATS scoring pipeline (23 metrics)
- [x] Dealbreaker preferences backend + UI
- [x] /ai/semantic-match, /ai/semantic-match/batch endpoints
- [x] /ai/tailor-resume, /ai/ats-score endpoints
- [x] MatchExplanation UI component
- [x] ATS-specific handlers (Greenhouse, Lever, Workday, SmartRecruiters, iCIMS)
- [x] CAPTCHA detection

### MILESTONE 4: Production Hardening (COMPLETED)
- [x] ProductionMiddleware with error handling (packages/backend/domain/production.py)
- [x] AIEndpointError hierarchy (LLMError, EmbeddingError, RateLimitError, TenantIsolationError, ValidationError)
- [x] TenantRateLimiter with tier-based quotas (free: 20/min, pro: 100/min, team: 500/min, enterprise: 2000/min)
- [x] MatchMetrics for structured logging (semantic_match, resume_tailoring metrics)
- [x] GDPR endpoints (apps/api/gdpr.py) - Article 15 export, Article 17 deletion
- [x] Multi-tenant isolation migration (infra/supabase/migrations/025_tenant_isolation.sql)
- [x] GDPR audit log table with RLS
- [x] Production tests (18 tests)

### Key Files Created (M2-M4)
**Backend Domain:**
- packages/backend/domain/embeddings.py
- packages/backend/domain/semantic_matching.py
- packages/backend/domain/resume_tailoring.py
- packages/backend/domain/ats_handlers.py
- packages/backend/domain/production.py

**API Routes:**
- apps/api/gdpr.py

**Frontend:**
- apps/web/src/components/ui/MatchExplanation.tsx

**Migrations:**
- infra/supabase/migrations/024_embeddings.sql
- infra/supabase/migrations/025_tenant_isolation.sql

**Tests:**
- tests/test_semantic_matching.py (29 tests)
- tests/test_resume_tailoring.py (17 tests)
- tests/test_ats_handlers.py (25 tests)
- tests/test_production.py (18 tests)

### Production Readiness Summary
| Feature | Status |
|---------|--------|
| Vector semantic matching | ✅ |
| Explainable match scores | ✅ |
| 23-metric ATS scoring | ✅ |
| Dynamic resume tailoring | ✅ |
| Dealbreaker preferences | ✅ |
| Match explanation UI | ✅ |
| ATS platform handlers | ✅ |
| CAPTCHA detection | ✅ |
| Error handling middleware | ✅ |
| Multi-tenant isolation | ✅ |
| Per-tenant rate limiting | ✅ |
| Structured logging/metrics | ✅ |
| GDPR compliance | ✅ |
| Test coverage | 129 passing |
