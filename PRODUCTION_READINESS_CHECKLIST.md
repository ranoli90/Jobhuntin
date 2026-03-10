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
| 2 | High | Magic link rate limits may be too permissive (enumeration risk) | `auth.py` |
| 3 | High | CAPTCHA only required after 5 IP requests or 50% of email limit | `auth.py` |
| 4 | Medium | Generic error messages ("Something went wrong") | `Login.tsx`, `magicLinkService.ts` |
| 5 | Medium | No `magic_link_sent` / `magic_link_failed` analytics | Frontend, backend |
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
| 10 | High | Generic `auth_failed` redirect with little user guidance | `auth.py`, `Login.tsx` |
| 11 | Medium | Loading state during verification exists but could be clearer | `Login.tsx` (isVerifying) |
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
| 13 | High | Progress in localStorage; no server-side resume from step | `Onboarding.tsx`, `useOnboarding` |
| 14 | High | No onboarding funnel tracking (`onboarding_step_viewed`, `onboarding_step_completed`) | `Onboarding.tsx`, telemetry |
| 15 | High | Resume upload retry exists but error messages unclear | `ResumeStep`, `resumeUploadRetry` |
| 16 | Medium | No "Your progress is saved automatically" indicator | `Onboarding.tsx` |
| 17 | Medium | Inconsistent error handling (toasts vs inline) across steps | Step components |
| 18 | Medium | Touch targets < 44px on some buttons | Step components |
| 19 | Low | No keyboard shortcuts (e.g. Ctrl+Enter to continue) | Step components |
| 20 | Low | Missing accessibility labels in some steps | Step components |

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
| 21 | Medium | Empty dashboard: no clear guidance for new users | `Dashboard.tsx` |
| 22 | Medium | HOLD / REQUIRES_INPUT status not clearly explained | `ApplicationsView`, `HoldsView` |
| 23 | Low | Applications polling every 15s; could use WebSocket or longer interval | `useApplications` |
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
| 25 | High | AI endpoints return fallback values instead of surfacing errors | `ai.py`, `batch_llm.py` |
| 26 | High | AI rate limits use in-memory `_user_rate_limits`; not distributed | `ai.py` |
| 27 | Medium | Resume parse failure recovery unclear to user | `ResumeStep`, `resume_parse` |
| 28 | Medium | No retry/backoff for transient LLM failures in worker | `agent.py` |
| 29 | Low | AI suggestion loading states could be clearer | `useAISuggestions`, step components |

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
| 30 | Low | Match score display: `<=1` vs `>1` logic may confuse (percent vs raw) | `JobsView.tsx` |
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
- **Bypasses REST API**: `supabase.from("applications").insert({ user_id, job_id, status: "QUEUED" })`
- No `NOTIFY job_queue` (worker picks up on next poll only)
- No `tenant_id`, `blueprint_key`, `priority_score` from API
- Pre-flight quota check via `getUsage()` only

### Issues to Fix

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 32 | Critical | Mobile inserts directly into Supabase; bypasses API validation, quota, NOTIFY | `mobile/src/api/client.ts`, `jobStore.ts` |
| 33 | Critical | No idempotency keys on `POST /me/applications`; retries can create duplicates (mitigated by ON CONFLICT) | `user.py` |
| 34 | High | No rate limit on `POST /me/applications` per user | `user.py`, middleware |
| 35 | High | Mobile applications lack `tenant_id`, `priority_score`; may not be processed correctly | Mobile client, worker |
| 36 | Medium | No queue position/ETA for users | Frontend |
| 37 | Medium | Undo only works for REJECT within 10s; ACCEPT undo exists but not exposed in JobsView | `user.py`, `JobsView.tsx` |
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
| 39 | High | Single-worker design; no horizontal scaling story | `agent.py`, `job_queue_worker.py` |
| 40 | High | DB connection pool may saturate under 4000 concurrent requests | `main.py`, pool config |
| 41 | Medium | No per-user apply rate limit; one user could spam 1000 applies | `user.py` |
| 42 | Medium | Worker `max_applications_per_minute` is global; no per-tenant fairness | `agent.py` |
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
| 44 | High | Mobile uses Supabase directly; web uses REST API — divergent paths | `mobile/`, `apps/web/` |
| 45 | Medium | JobsView `handleSwipe` had wrong job in screen reader announcement — **FIXED** | `JobsView.tsx` |
| 46 | Medium | `useJobs` doesn't invalidate on apply; applications count may be stale | `useJobs`, `useApplications` |
| 47 | Medium | Error handling inconsistent across API calls | `lib/api.ts`, various hooks |
| 48 | Medium | No offline support (service worker) | - |
| 49 | Low | Some buttons < 44px touch target | Various components |
| 50 | Low | Keyboard shortcuts limited | `useKeyboardShortcuts` |
| 51 | Low | Pre-existing lint/type errors (~838 ruff, ~351 mypy per AGENTS.md) | Codebase |

---

## 10. Security & Operations

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 52 | Critical | Session token replay; no revocation | `auth.py` |
| 53 | High | Disposable email list may need updates | `auth.py` |
| 54 | High | `return_to` sanitization; keep whitelist in sync with frontend | `auth.py`, `magicLinkService.ts` |
| 55 | Medium | CSRF implemented; magic-link and webhooks exempt | `middleware.py` |
| 56 | Medium | No operational runbooks | - |
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
| 58 | Low | Login: If `getApiBase()` empty, token-in-URL redirect to verify-magic may not happen |
| 59 | Low | Worker LISTEN uses pool connection; 60s keep-alive sleep may affect connection lifecycle |
| 60 | Low | `applications` table: mobile insert omits `tenant_id`; worker may need default tenant resolution |
| 61 | Low | JobsView undo only for REJECT; ACCEPT undo endpoint exists but not wired in UI |
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
