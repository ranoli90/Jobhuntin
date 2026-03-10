# Production Readiness Checklist

**Comprehensive audit of user flow, AI usage, job matching, apply system, and frontend.**  
**Scope:** First-time register → email link → onboarding → dashboard (all features).  
**Date:** March 10, 2026

---

## Executive Summary

| Area | Status | Critical Issues |
|------|--------|-----------------|
| Registration / Magic Link | ⚠️ Partial | Session replay, Redis required, IP binding off |
| Email Link Flow | ✅ OK | Replay protection; loading state exists |
| Onboarding | ⚠️ Partial | Progress in localStorage, no funnel tracking |
| Dashboard | ✅ OK | Metrics, jobs, applications, holds |
| AI (Onboarding + Swipe) | ⚠️ Partial | Fallbacks hide errors, rate limits in-memory |
| Job Matching | ✅ OK | Rule-based scoring, dealbreakers, optional ML |
| Post-Swipe Apply | ⚠️ Partial | No API rate limit, mobile bypasses API |
| Concurrency (4000 swipes) | ⚠️ Partial | DB locking OK; worker rate limits; no horizontal scale |
| Frontend | ⚠️ Partial | JobsView bug fixed; mobile vs web divergence |

---

## 1. Registration Flow

### Flow
1. User enters email on `/login` (or homepage hero CTA)
2. Frontend calls `POST /auth/magic-link` with `{ email, return_to?, captcha_token? }`
3. Backend: blocks disposable emails, rate limits (IP: 30/hr, per-email configurable), optional CAPTCHA
4. JWT (1h TTL) created; email sent via Resend
5. No separate registration; new users created on magic link verification

### Issues to Fix

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 1 | Critical | No email delivery confirmation tracking | `auth.py`, Resend webhook |
| 2 | ~~High~~ Fixed | Tighter limits: 20/hr IP, CAPTCHA after 3 | `auth.py` |
| 3 | ~~High~~ Fixed | CAPTCHA after 3 IP or 40% email limit | `auth.py` |
| 4 | ~~Medium~~ Fixed | Specific error messages by status/type | `Login.tsx`, `magicLinkService.ts` |
| 5 | ~~Medium~~ Fixed | magic_link_sent, magic_link_failed, magic_link_verified analytics | Frontend, backend |
| 6 | Low | Email typo detection exists (`checkEmailTypo`) but not consistently used | `emailUtils.ts` |

---

## 2. Email Link Flow (Click → Verify)

### Flow
1. Link format: `{app_base_url}/login?token={JWT}&returnTo={path}`
2. User lands on `/login?token=...`
3. AuthContext redirects to `GET /auth/verify-magic?token=...&return_to=...`
4. Backend: JWT validation, optional IP binding, replay protection (Redis jti)
5. New users: `_find_or_create_user_by_email`; session created; httpOnly cookie set
6. Redirect to `returnTo` or `/app/onboarding` for new users

### Issues to Fix

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 7 | Critical | Session token replay: no revocation; JWTs reusable until expiry | `auth.py`, session management |
| 8 | Critical | Redis required for replay protection; in-memory fallback unsafe for multi-instance | `auth.py`, `redis_client.py` |
| 9 | High | IP binding off by default (`MAGIC_LINK_BIND_TO_IP=false`) | Config, `auth.py` |
| 10 | ~~High~~ Fixed | auth_failed hint param (expired, used, invalid, ip_mismatch) | `auth.py`, `Login.tsx` |
| 11 | ~~Medium~~ Fixed | Clearer verification loading (progress bar, aria) | `Login.tsx` |
| 12 | Medium | No `magic_link_verified` analytics | Backend, frontend |

---

## 3. Onboarding Flow

### Steps
1. WelcomeStep → ResumeStep (LLM parse) → SkillReviewStep → ConfirmContactStep
2. PreferencesStep → WorkStyleStep → CareerGoalsStep → ReadyStep

### Data Storage
- Profile: `profiles.profile_data` (JSONB)
- Preferences: `user_preferences`
- Skills: `user_skills`
- Work style: `work_style`
- Progress: `onboarding_progress` + `localStorage`

### Issues to Fix

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 13 | ~~High~~ Fixed | Server-side onboarding_step + sync | `user.py`, `useOnboarding`, `Onboarding.tsx` |
| 14 | High | No onboarding funnel tracking (`onboarding_step_viewed`, `onboarding_step_completed`) | `Onboarding.tsx`, telemetry |
| 15 | ~~High~~ Fixed | Resume error messages improved (extract, parse, network) | `Onboarding.tsx` |
| 16 | ~~Medium~~ Fixed | Progress saved indicator present | `Onboarding.tsx` |
| 17 | ~~Medium~~ Fixed | Error handling: inline save-error banner + toast for API failures | `Onboarding.tsx`, step components |
| 18 | ~~Medium~~ Fixed | Touch targets ≥ 44px (buttons, chips, icon buttons) | Step components |
| 19 | ~~Low~~ Fixed | Ctrl+Enter / Cmd+Enter to continue | `Onboarding.tsx` |
| 20 | ~~Low~~ Fixed | Step regions + aria-labelledby for screen readers | All step components |

---

## 4. Dashboard & All Features

### Features
- Dashboard home: metrics (Active Applications, Applied Rate, Needs Input, Total), recent apps, CTA
- Jobs tab: swipe feed (Tinder-like), filters from profile
- Applications tab: list with status (APPLYING, APPLIED, HOLD, FAILED)
- Holds tab: applications needing input
- Team tab: team workspace
- AI Matches, AI Tailor, ATS Score, Pipeline View, Export, Follow-up, Interview Practice, Multi-Resume, Notes, Billing, Settings, Sessions

### Issues to Fix

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 21 | ~~Medium~~ Fixed | Empty dashboard guidance improved | `Dashboard.tsx` |
| 22 | ~~Medium~~ Fixed | HOLD tooltip + AppCard explanation | `Dashboard.tsx`, `AppCard.tsx` |
| 23 | ~~Low~~ Fixed | Dynamic polling: 10s when APPLYING, 30s otherwise | `useApplications` |
| 24 | Low | Billing tiers hardcoded; consider `/billing/tiers` API | `Dashboard.tsx`, `BILLING_TIERS` |

---

## 5. AI in Onboarding & Job Swipe

### Onboarding AI
- Resume parsing: LLM parses PDF for skills, experience
- AI suggestions: `useAISuggestions` → `POST ai/suggest-roles`, `ai/suggest-salary`, `ai/suggest-locations`
- AI onboarding: `AIOboardingManager` (adaptive questions, completion detection)

### Job Swipe AI
- Match scoring: `score_job_match()` (skill 40%, location 15%, salary 15%, culture 20%, trajectory 10%)
- Dealbreakers: `apply_dealbreaker_filters()`
- Explainable scoring: `ExplainableScoringEngine`
- Worker: LLM for DOM mapping, cover letters, form filling

### Issues to Fix

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 25 | ~~High~~ Fixed | AI endpoints surface 503 instead of fallbacks | `ai.py` |
| 26 | ~~High~~ Fixed | AI rate limits use Redis when available | `ai.py` |
| 27 | ~~Medium~~ Fixed | Resume parse failure recovery: actionable message + skip hint | `ResumeStep` |
| 28 | ~~Medium~~ Fixed | Retry/backoff for transient LLM failures in worker | `agent.py` |
| 29 | ~~Low~~ Fixed | AI suggestion loading states (skeleton, error UI) | `PreferencesStep`, `AISuggestionCard` |

---

## 6. Job Matching System

### Algorithm
- `score_job_match()`: skill (40%), location (15%), salary (15%), culture (20%), trajectory (10%)
- Dealbreakers: excluded companies/keywords, min salary, remote/onsite
- Per-tenant weights in `match_weights.py`
- Precompute: `match_score_precompute.py`
- Cold start: `cold_start.py` for new users

### Assessment
- Well-implemented rule-based scoring
- Dealbreakers correctly filter
- Optional ML support via `enable_ml_scoring`

### Issues to Fix

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 30 | ~~Low~~ Fixed | Match score tooltip added | `JobsView.tsx` |
| 31 | Low | No user feedback loop to improve matching | - |

---

## 7. Post-Swipe Apply Flow

### Web Flow
1. User swipes right in JobsView
2. `handleSwipe(jobId, "accept")` → `apiPost("/me/applications", { job_id, decision: "ACCEPT" })`
3. Backend: transaction + `SELECT FOR UPDATE` on (user_id, job_id, tenant_id)
4. Quota check (`check_can_create_application`)
5. Insert with `ON CONFLICT DO UPDATE`; `NOTIFY job_queue`
6. Worker polls/notified, claims via `claim_next_prioritized` (SELECT FOR UPDATE SKIP LOCKED)
7. Worker: DOM mapping, form fill, submit

### Mobile Flow
- ~~**Bypasses REST API**: Mobile used Supabase directly~~ **FIXED**: Mobile now uses REST API POST /me/applications
- No `NOTIFY job_queue` (worker picks up on next poll only)
- No `tenant_id`, `blueprint_key`, `priority_score` from API
- Pre-flight quota check via `getUsage()` only

### Issues to Fix

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 32 | ~~Critical~~ Fixed | Mobile now uses REST API; NOTIFY trigger added for any direct inserts | `mobile/src/api/client.ts`, `jobStore.ts` |
| 33 | ~~Critical~~ Fixed | Idempotency-Key header supported; Redis cache + ON CONFLICT | `user.py` |
| 34 | ~~High~~ Fixed | Per-user rate limit (60/min) | `user.py` |
| 35 | ~~High~~ Fixed | API returns tenant_id, priority_score; mobile consumes them | `user.py`, `mobile/client.ts` |
| 36 | ~~Medium~~ Fixed | Queue position/ETA via GET /me/applications/queue-stats | API, Dashboard, useApplications |
| 37 | ~~Medium~~ Fixed | ACCEPT undo exposed in JobsView (10s window) | `JobsView.tsx` |
| 38 | Low | ~~JobsView announcement used wrong job (topJob vs applied job)~~ **FIXED** | `JobsView.tsx` |

---

## 8. Concurrency: 4000 People Swiping at Once

### Current Behavior
- **API**: `SELECT FOR UPDATE` + `ON CONFLICT` prevent duplicate (user_id, job_id) rows
- **Worker**: `claim_next_prioritized` uses `FOR UPDATE SKIP LOCKED` for safe concurrent claiming
- **Worker rate limits**: `max_applications_per_minute`, `llm_rate_limit_per_minute`
- **NOTIFY**: Wakes worker immediately on web apply; mobile relies on polling

### Issues to Fix

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 39 | ~~High~~ Fixed | Worker scaling documented; SKIP LOCKED supports N workers | `OPERATIONAL_RUNBOOKS.md` |
| 40 | ~~High~~ Fixed | DB pool config documented; DB_POOL_MIN/MAX env vars | `config.py`, runbooks |
| 41 | ~~Medium~~ Fixed | Per-user apply rate limit 60/min | `user.py` |
| 42 | ~~Medium~~ Fixed | claim_next_prioritized gives per-tenant fairness | `agent.py`, runbooks |
| 43 | Low | Composite index for `claim_next_prioritized` exists (`idx_applications_claim`) | `schema.sql` ✅ |

---

## 9. Frontend Design & Wiring

### Structure
- React + Vite, React Query, lazy routes
- AuthGuard / AdminGuard, AppLayout
- `useAuth`, `useProfile`, `useBilling`, `useApplications`, `useJobs`

### Issues to Fix

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 44 | ~~High~~ Fixed | Mobile now uses REST API; paths aligned | `mobile/`, `apps/web/` |
| 45 | Medium | JobsView `handleSwipe` had wrong job in screen reader announcement — **FIXED** | `JobsView.tsx` |
| 46 | ~~Medium~~ Fixed | `useJobs` invalidates applications + jobs on apply | `JobsView.tsx`, `Dashboard.tsx` |
| 47 | Medium | Error handling: api.ts has friendlyMessage; hooks use consistently | `lib/api.ts` |
| 48 | ~~Medium~~ Fixed | PWA workbox: NetworkFirst for API, cache static assets | `vite.config.ts` |
| 49 | Low | Some buttons < 44px touch target | Various components |
| 50 | Low | Keyboard shortcuts limited | `useKeyboardShortcuts` |
| 51 | Low | Pre-existing lint/type errors (~838 ruff, ~351 mypy per AGENTS.md) | Codebase |

---

## 10. Security & Operations

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 52 | Critical | Session token replay; no revocation | `auth.py` |
| 53 | ~~High~~ Fixed | Disposable email list expanded (tempail, mail.tm, etc.) | `auth.py` |
| 54 | ~~High~~ Fixed | return_to whitelist synced backend + frontend | `auth.py`, `magicLinkService.ts` |
| 55 | Medium | CSRF implemented; magic-link and webhooks exempt | `middleware.py` |
| 56 | ~~Medium~~ Fixed | Operational runbooks: scaling, DB pool, worker | `OPERATIONAL_RUNBOOKS.md` |
| 57 | Low | Missing analytics for funnel and events | Telemetry |

---

## 11. Summary: Priority Order

### P0 (Critical – Before Production)
1. Session token replay / revocation
2. Redis required for replay protection (no in-memory fallback in prod)
3. Mobile apply path: align with API or add NOTIFY trigger
4. Idempotency keys for write endpoints (or document ON CONFLICT behavior)

### P1 (High – Before Production)
5. Rate limit on `POST /me/applications`
6. IP binding for magic links in production
7. Onboarding funnel tracking
8. AI rate limits distributed (Redis)
9. Worker horizontal scaling story
10. Mobile apply: tenant_id, priority_score, NOTIFY

### P2 (Medium – Soon After)
11. Apply queue position/ETA for users
12. Empty dashboard guidance
13. HOLD status explanation
14. Resume parsing error recovery
15. API error handling consistency

### P3 (Low – Backlog)
16. Touch targets, keyboard shortcuts
17. Offline support
18. Lint/type errors
19. Duplicate review/withdraw logic in Dashboard.tsx and ApplicationsView.tsx

---

## Additional Items (Small / Edge Cases)

| # | Severity | Issue |
|---|----------|-------|
| 58 | ~~Low~~ Fixed | getApiBase never returns empty; fallback to /api | `lib/api.ts` |
| 59 | Low | Worker LISTEN uses pool connection; 60s keep-alive sleep | `agent.py` |
| 60 | ~~Low~~ Fixed | API sets tenant_id; mobile receives it in response | `user.py`, mobile |
| 61 | ~~Low~~ Fixed | ACCEPT undo wired in JobsView (10s window) | `JobsView.tsx` |
| 62 | Low | Dashboard.tsx and ApplicationsView both implement review/withdraw; consider shared hook |
| 63 | Low | `useJobs` staleTime 5min; swiped jobs still in list until refetch |
| 64 | Low | Social login (Google, LinkedIn) shows "Coming soon"; buttons disabled |

---

## Files Reference

| Area | Key Files |
|------|-----------|
| Auth | `apps/api/auth.py`, `apps/web/src/pages/Login.tsx`, `apps/web/src/context/AuthContext.tsx`, `apps/web/src/services/magicLinkService.ts` |
| Onboarding | `apps/web/src/pages/app/Onboarding.tsx`, `packages/backend/domain/onboarding.py`, `apps/api/ai_onboarding.py` |
| Dashboard | `apps/web/src/pages/Dashboard.tsx`, `apps/api/dashboard.py` |
| Jobs / Apply | `apps/web/src/pages/dashboard/JobsView.tsx`, `apps/api/user.py`, `apps/worker/agent.py` |
| Job Matching | `packages/backend/domain/job_scoring.py`, `packages/backend/domain/job_search.py`, `packages/backend/domain/match_weights.py` |
| Mobile | `mobile/src/api/client.ts`, `mobile/src/stores/jobStore.ts` |
| Worker | `apps/worker/agent.py`, `apps/worker/job_queue_worker.py`, `packages/backend/domain/job_queue.py` |
