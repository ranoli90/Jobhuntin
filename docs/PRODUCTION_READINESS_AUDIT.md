# Production Readiness & JobSpy Deep Audit

## 1. Mocks, Placeholders, Demo Data — Status

### Removed (Production Ready)
- **Admin Usage**: Mock fallback removed; shows error + Retry when API fails
- **Admin Matches**: Mock fallback removed; shows error + Retry when API fails  
- **SemanticMatcher**: Demo recommendations removed; calls `GET /communications/recommendations` (real API using jobs + user interest profiler)

### Intentional "Coming Soon" (Product Decision)
- **Billing**: Payment methods, Usage charts — EmptyState, not fake data
- **Social Login**: Google/LinkedIn — disabled, "Coming soon"
- **JobNiche**: Employer data — ComingSoonEmptyState when no majorEmployers

### Remaining (Internal / Non-User-Facing)
- Voice interviews: placeholder session data when DB retrieval fails (requires session persistence)
- Config: dev-placeholder-webhook-secret (validated in prod)
- Backend stubs: m4_metrics CAC, multi_resume offer_rate, etc. (internal calculations)

---

## 2. Production Readiness — First User

### Must-Have Before Launch
| # | Item | Status |
|---|------|--------|
| 1 | `REDIS_URL` | Required for magic link replay, session revocation |
| 2 | `RESEND_API_KEY`, `EMAIL_FROM` | Magic link delivery |
| 3 | `APP_BASE_URL`, `API_PUBLIC_URL` | Redirect URLs |
| 4 | `STRIPE_*` (if billing) | Live keys, prod price IDs |
| 5 | `JWT_SECRET`, `CSRF_SECRET` | Auth |

### Config Fixes Needed
- **EMAIL_FROM**: Replace `hello@skedaddle.app` with JobHuntin domain in deploy scripts
- **Stripe Price IDs**: Verify prod vs test in `set_render_env_*.py`

### Gaps
- No route-level ErrorBoundary (async errors can cause blank screens)
- Admin RBAC: server-side role checks for `/app/admin/*`
- Onboarding: `QuotaExceeded` in localStorage not handled
- Resume upload: not atomic (DB failure → orphaned file)

---

## 3. JobSpy Deep Dive

### Architecture
```
job_sync_worker (every 3–4h)
  → JobSyncService.sync_all_sources()
    → JobSpyClient.fetch_jobs() [ThreadPool, sync HTTP]
    → _apply_legitimacy_scores()
    → _sync_jobs_to_db()
  → public.jobs
    → GET /me/jobs (search_and_list_jobs)
      → Dashboard / JobsView
```

### Proxies (Quality: 6/10)
| Aspect | Status | Gap |
|--------|--------|-----|
| Config | `JOBSPY_PROXIES`, `jobspy_use_free_proxies` | Render job-sync has no proxy env in render.yaml |
| Free proxies | proxy_fetcher.py (GimmeProxy, PubProxy, GitHub) | Often unvalidated; many dead/slow |
| Rotation | Round-robin when `jobspy_proxy_rotation=True` | One proxy per fetch_jobs() call |
| Health | None | No blacklisting or health checks |
| Validation | Optional `jobspy_validate_proxies` | Off by default |

### Data Return (Quality: 8/10)
- Solid schema: application_url, is_remote, date_posted, job_level
- Dedup, legitimacy scoring
- Adzuna fallback when DB empty
- Pagination, filters

### AI Matching (Quality: 6/10)
| System | Used In | Model |
|--------|---------|-------|
| Rule-based | Main feed (GET /me/jobs) | score_job_match: skill 40%, location 15%, salary 15%, etc. |
| Semantic | AI endpoints only | text-embedding-3-small via OpenRouter |
| Precompute | match_scores table | May be unused |

**Gap**: Main feed uses rule-based only; semantic matching not in job feed.

### Auto-Apply (Quality: 7/10)
- Flow: User swipe → POST /me/applications → QUEUED → NOTIFY job_queue → Agent (Playwright/HTTP)
- HTTP-first for Greenhouse/Lever
- No success-rate tracking or dashboard
- Agent uses application_url from job row (JobSpy data)

### Recommendations
1. **Proxies**: Add `JOBSPY_PROXIES` to Render job-sync; enable `jobspy_validate_proxies`; add proxy health/blacklist
2. **AI matching**: Wire semantic precompute to main feed or add hybrid scoring
3. **Auto-apply**: Add success-rate aggregation and admin dashboard
