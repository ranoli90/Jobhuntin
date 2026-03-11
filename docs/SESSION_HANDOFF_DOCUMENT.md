# Session Handoff Document — Full Context for New LLM

**Date:** March 2025  
**Purpose:** Zero-context handoff for a new session. Contains everything: what was done, what remains, coding standards, architecture, and instructions.

---

## 1. Project Overview

**Sorce/JobHuntin** — Job-hunting platform with:
- **Backend:** FastAPI (Python), PostgreSQL (Render), Redis
- **Frontend:** React + Vite (TypeScript)
- **Agent:** Playwright-based auto-apply for job applications
- **Job sync:** JobSpy (Indeed, LinkedIn, ZipRecruiter, Glassdoor) + Adzuna API
- **Deployment:** Render (web, API, workers, crons)

**Monorepo structure:**
- `apps/api/` — FastAPI routes
- `apps/web/` — React frontend
- `apps/worker/` — Background workers (job sync, agent, follow-up, etc.)
- `packages/backend/` — Domain logic, repositories, LLM
- `shared/` — Config, logging, storage, Redis
- `migrations/` — SQL migrations
- `docs/` — Audit findings, plans

**Key commands (from AGENTS.md):**
```bash
# Backend
source .venv/bin/activate
PYTHONPATH=apps:packages:. uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd apps/web && npx vite --host 0.0.0.0 --port 5173

# Tests
PYTHONPATH=apps:packages:. pytest tests/ -v -s --tb=short

# Lint (pre-existing ~838 ruff, ~351 mypy — don't block on these)
ruff check . --select E,W,F,I
PYTHONPATH=apps:packages:. mypy apps/api/ apps/worker/ packages/backend/ shared/ --ignore-missing-imports
```

---

## 2. What Was Done This Session

### 2.1 JobSpy Enhancements
- **Proxy rotation:** Round-robin over configured proxies; fetch from GimmeProxy/PubProxy when `JOBSPY_USE_FREE_PROXIES=true`
- **User-Agent rotation:** 8 realistic UAs, random per request
- **Free proxy sources:** GimmeProxy API, PubProxy API, GitHub proxy lists (TheSpeedX, ShiftyTR)
- **Proxy validation:** Optional `validate_proxy()` with httpbin health check; `jobspy_validate_proxies` config
- **Spam/quality:** Persist `is_scam`, `quality_score` at sync; filter `is_scam=true` in job search
- **Batch upsert:** 50 jobs per batch, `unnest` + `ON CONFLICT` for efficiency
- **Daily salary:** Added `daily` interval (×260) in `_parse_salary`
- **Migration 020:** `migrations/020_jobspy_schema_columns.sql` — adds JobSpy columns, backfills from legacy

### 2.2 Render & Env
- **sync_render_env_from_dotenv.py:** Syncs .env to all Render services; uses `RENDER_API_KEY` from .env
- **update-render-env.sh:** Stripe keys from env; no hardcoding
- **RENDER_API_KEY** added to .env (gitignored)

### 2.3 Production Readiness
- **Config:** Reject dev defaults for CSRF_SECRET, JWT_SECRET in prod/staging
- **api_auth_middleware:** Reads JWT from env; fails in prod if weak default
- **Auth:** Redis required for token replay in prod; magic link uses `INSERT ON CONFLICT`
- **Onboarding 401:** Call `flushOnboardingBeforeRedirect()` before redirect; 600ms delay
- **Agent:** OAuth warn when credentials missing; submit_form checks success indicators before returning True
- **Job search/repo:** COALESCE for legacy + JobSpy schema; JobRepo.get_by_id simplified

### 2.4 Audit Fixes (from prior audits)
- Email/Job/Privacy: COM-001–004, F001–009, PRIV-001–004, F006, F008
- Onboarding: OB-001, OB-003–OB-007, OB-009–OB-016, A4, F1, etc.
- Dashboard/API: C1, C2, H1–H3, API-3–6, FE-1, FE-2, M1–M6, L1–L4
- SEO: 60+ findings fixed
- Auth/Billing/Worker: AUTH-005, AUTH-006, AUTH-008, etc.

---

## 3. REMAINING / NOT FINISHED — Full List

### 3.1 Privacy (Email/Job/Privacy Audit)
| ID | File | Description | Priority |
|----|------|-------------|----------|
| PRIV-005 | gdpr.py | GDPR export vs deletion table mismatch (e.g. `input_answers` vs `application_inputs`/`answer_memory`) | fixed |
| PRIV-007 | data_retention.py | Applications hard-deleted, not archived; needs archive table | Deferred |
| PRIV-008 | gdpr.py | GDPR export returns raw data in response; needs secure download URLs | Deferred |
| F004 | match_score_precompute.py | Pre-computed scores never read (was deferred; may be fixed) | Check |

### 3.2 JobSpy / Job Sync
| ID | Description | Priority |
|----|-------------|----------|
| No JobSpy rate limiting | Only circuit breaker; no proactive throttling between fetches | Medium |
| Proxy rotation | Per-source proxy rotation; currently one proxy per fetch | Medium |
| Concurrent sync | `_running` not persisted; multiple workers could sync simultaneously | Medium |
| Job schema gaps | `emails`, `skills`, `benefits` not stored; `_normalize_job` exception handler may reference undefined `k` | Low |

### 3.3 Job Application (Agent)
| ID | Description | Priority |
|----|-------------|----------|
| Wire ExecutionEngine | Use `HumanBehaviorSimulator` and `AntiDetection` in agent | High |
| HTTP-first for Greenhouse/Lever | Try API apply before Playwright | High |
| Integrate ATS handlers | `ats_handlers.py` defines handlers but not used; pre-fill, custom selectors | High |
| CAPTCHA failure → REQUIRES_INPUT | Don't silently continue; escalate to user | High |
| Proxy rotation for agent | Add `agent_proxies`; rotate on 429/403 | Medium |
| OAuth session persistence | Store cookies per (user, domain) | Medium |
| Browserless as prod default | Remote browsers for scaling | Medium |
| Structured error classification | Add `error_type` to events/DLQ | Medium |
| ApplicationOrchestrator | Central strategy selection and retries | Medium |

### 3.4 Onboarding (Remaining)
| ID | Description | Priority |
|----|-------------|----------|
| A4 (full) | Full ReAuthModal: complex; flush + toast mitigates | Deferred |
| C1 | Two tabs submitting; last write wins; no optimistic locking | Medium |
| R1 (race) | Step 3 saved before step 2 completes; backend ordering | Medium |
| S3, S5, S2 | Various state sync edge cases | Low |

### 3.5 Production Readiness (Sprint Plan)
| # | Description | Priority |
|---|-------------|----------|
| 21 | Billing upgrade/portal: aggressive polling, no backoff | Medium |
| 22 | Admin sources: polls every 5s, no error boundary | Medium |
| 23 | Admin pages lack RBAC; any user can access | fixed |
| 24 | Admin sync "Trigger Sync" no confirmation modal | Medium |
| 25 | Admin alerts: mock fallback masks outages | High |
| 26 | Admin alerts acknowledge: optimistic update, no rollback | Medium |
| 27 | AI Tailor: no file size validation | Medium |
| 28 | ATS scoring runs twice per tailor (no dedup) | Medium |
| 29 | AI Tailor: generic "Parse Failed" toast | Medium |
| 30 | Magic link: no List-Unsubscribe, no plain-text fallback | Medium |
| 31 | Email typo: whitelist too small | Medium |
| 32 | No email analytics/open tracking | Medium |
| 33 | ErrorBoundary not wired at route level | done (RouteErrorBoundary on all routes) |
| 34 | ErrorBoundary reporting is console.log; no Sentry | done (Sentry.captureException in ErrorBoundary) |
| 35 | No global loading skeleton for route transitions | Medium |
| 36 | PWA manifest/service worker (may exist) | Medium |
| 37 | robots.txt conflicts | Low |
| 38 | No JSON-LD for jobs/organization | Medium |
| 39 | i18n: only en/fr; no locale detection | Medium |
| 40 | No lang/dir attributes on HTML | Medium |
| 41 | French translations incomplete | Medium |
| 42 | No CSP or security headers | done (setup_security_headers in middleware) |
| 43 | No rate limiting on public endpoints | done (rate_limiting_middleware) |
| 44 | No input sanitization libraries (XSS) | done (sanitize_text_input; added headline/bio) |

### 3.6 Audit Findings (from subagent)
| Area | File | Issue | Priority |
|------|------|-------|----------|
| Admin | dashboard.py | get_overview, get_metrics, get_config lacked auth | fixed |
| API | application_pipeline.py | sort_order SQL injection; company ILIKE escape | fixed |
| Auth | user.py | is_system_admin except pass → log | fixed |
| Auth | test_ionos_api.py | Hardcoded IONOS_SECRET | fixed (env vars) |
| Worker | job_sync_service.py | Swallowed exceptions in cleanup | fixed |
| Frontend | localStorage | QuotaExceededError handling | fixed |

### 3.7 Other
| Area | Description |
|------|-------------|
| Mypy | ~351 errors remaining (pre-existing) |
| Ruff | ~838 errors remaining (pre-existing) |
| npm audit | May have high/critical; run `npm audit fix` |

---

## 4. Coding Standards & Quality

### 4.1 General
- **Minimal, surgical fixes:** Don't refactor broadly; fix the specific issue
- **Tests:** Add or update tests when fixing critical paths; lock in behavior
- **Backwards compatibility:** Use COALESCE, ADD COLUMN IF NOT EXISTS for schema changes
- **No hardcoded secrets:** Never commit API keys, tokens; use env/.env

### 4.2 Python
- **Type hints:** Use them; `Optional[X]` or `X | None`
- **Async:** Use `await asyncpg`, `asyncio.to_thread` for blocking calls (e.g. Pinecone)
- **SQL:** Use parameterized queries; escape `%`, `_`, `\` for ILIKE; `_escape_ilike` helper exists
- **Transactions:** Wrap multi-step DB ops in `async with conn.transaction()`
- **Error handling:** Log and re-raise; don't swallow silently

### 4.3 Frontend
- **Null safety:** Use `?.`, `??`; avoid `!` unless certain
- **Storage:** Wrap `localStorage.setItem` in try/catch; handle QuotaExceededError; fallback to sessionStorage
- **401:** Preserve state before redirect; call `flushOnboardingBeforeRedirect()` when on onboarding
- **i18n:** Use `t()`, `formatT()`; add keys to EN and FR

### 4.4 Security
- **XSS:** Sanitize user input; `html.escape()` in templates; `sanitize_text_input` for free text
- **IDOR:** Validate ownership; `user_id` from JWT, not request body
- **Webhooks:** Verify signature before parsing; reject expired timestamps

---

## 5. Architecture Reference

### 5.1 Job Flow
```
User swipe → POST /me/applications (QUEUED)
         → Worker claims (FOR UPDATE SKIP LOCKED)
         → Playwright navigates to application_url
         → OAuth flow (if detected)
         → Extract form fields → LLM mapping → Fill → Submit
         → APPLIED or REQUIRES_INPUT or FAILED
```

### 5.2 Job Sync Flow
```
Worker/cron → JobSyncService.sync_all_sources()
         → _get_search_queries() (popular_searches, user_preferences, profiles, job_alerts)
         → JobSpyClient.fetch_jobs() per (term, location)
         → proxy_fetcher (GimmeProxy, PubProxy, GitHub lists)
         → _apply_legitimacy_scores() → _sync_jobs_to_db() (batch upsert)
         → cleanup_expired_jobs()
```

### 5.3 Key Files
| File | Purpose |
|------|---------|
| `apps/api/main.py` | FastAPI app, lifespan, routes |
| `apps/api/auth.py` | Magic link, Resend webhook |
| `apps/api/user.py` | Profile, applications, jobs |
| `apps/worker/agent.py` | FormAgent, claim, navigate, fill, submit |
| `apps/worker/scaling.py` | WorkerScaler, BrowserPoolManager |
| `packages/backend/domain/job_sync_service.py` | Job sync logic |
| `packages/backend/domain/jobspy_client.py` | JobSpy wrapper |
| `packages/backend/domain/job_search.py` | Search, filters, scoring |
| `packages/backend/domain/proxy_fetcher.py` | Free proxy fetch |
| `shared/config.py` | Settings, validate_critical |

---

## 6. Docs to Read

| Doc | Purpose |
|-----|---------|
| `AGENTS.md` | Services, gotchas, commands |
| `docs/PRODUCTION_READINESS_FIXES.md` | What was fixed for prod |
| `docs/JOB_APPLICATION_FLOW_AND_LOGIN.md` | Where we apply, login flow |
| `docs/JOB_APPLICATION_SELF_HEALING_IMPLEMENTATION.md` | Agent improvement plan |
| `docs/ONBOARDING_AUDIT_FINDINGS.md` | Full onboarding audit |
| `docs/AUDIT_FINDINGS_2025_03.md` | Latest bug audit |
| `docs/EMAIL_JOBSEARCH_PRIVACY_AUDIT_FINDINGS.md` | Email, job, privacy |
| `docs/DASHBOARD_API_AUDIT_FINDINGS.md` | Dashboard/API |
| `docs/reports/production_readiness_sprint_plan.md` | 44 items TODO |

---

## 7. Instructions for New LLM

1. **Read this document first** — then `AGENTS.md` and `docs/PRODUCTION_READINESS_FIXES.md`  
2. **Prioritize:** Critical > High > Medium > Low  
3. **Fix one thing at a time** — test, then commit  
4. **Don't break existing behavior** — run `pytest tests/` and `npx vite build` after changes  
5. **Use subagents** when exploring broad areas (e.g. `mcp_task` with `explore` or `generalPurpose`)  
6. **Document findings** in `docs/` before implementing  
7. **Pre-existing lint/type errors** — don't fix unless directly related to your change  
8. **Apply migration 020** if deploying: `psql $DATABASE_URL -f migrations/020_jobspy_schema_columns.sql`  
9. **Sync Render env** when needed: `python scripts/maintenance/sync_render_env_from_dotenv.py`

---

## 8. Trigger Prompt for New Session (Copy-Paste This)

```
Read docs/SESSION_HANDOFF_DOCUMENT.md in full. Then:

1. Prioritize and fix the highest-impact remaining items from Section 3 (REMAINING).
2. Start with PRIV-005 (GDPR export vs deletion mismatch), then Admin RBAC (item 23), then ErrorBoundary/Sentry (33–34), then CSP/security (42–44).
3. Use the coding standards in Section 4. Run tests after each fix.
4. Document what you fix in docs/PRODUCTION_READINESS_FIXES.md or create a new audit doc.
5. Commit and push when done.
```
