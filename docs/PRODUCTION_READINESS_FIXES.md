# Production Readiness Fixes — Summary

**Date:** March 2025

## Completed Fixes

### 1. Config & Secrets (F24, F26)
- **shared/config.py**: Reject dev defaults (`dev-`, `change-in-production`) for CSRF_SECRET and JWT_SECRET in prod/staging
- **shared/api_auth_middleware.py**: AuthMiddleware reads JWT_SECRET from env; fails in prod if weak default

### 2. Auth (OB-002, OB-005)
- **auth.py**: Redis required for token replay in prod/staging (no in-memory fallback)
- **auth.py**: Magic link verification uses `INSERT ... ON CONFLICT` for race safety

### 3. User API (OB-003, OB-004)
- **user.py**: Preferences model validates salary_min/max (0–10M, min ≤ max)
- **user.py**: update_profile uses transaction for atomic ProfileRepo.upsert + UPDATE users

### 4. Onboarding (A4, F1)
- **api.ts**: On 401, call `flushOnboardingBeforeRedirect()` before redirect; 600ms delay on onboarding path
- **useOnboarding.ts**: Already has QuotaExceededError handling and sessionStorage fallback
- **browserCache.ts**: Already has try/catch for localStorage

### 5. Job Sync & JobSpy
- **proxy_fetcher.py**: Added `validate_proxy()`; optional validation before use
- **proxy_fetcher.py**: Added GitHub proxy list sources (TheSpeedX, ShiftyTR)
- **jobspy_client.py**: Added `daily` salary interval (×260)
- **config.py**: Added `jobspy_validate_proxies`

### 6. Agent (F15, F16)
- **agent.py**: OAuth: warn when credentials missing; only attempt flow when credentials present
- **agent.py**: submit_form: when navigation times out, check for success indicators before returning True; otherwise return False

### 7. Job Search & Repo (F1, F2, F3)
- **job_search.py**: Query uses COALESCE for legacy + JobSpy schema
- **job_search.py**: _map_job_row handles both column sets
- **repositories.py**: JobRepo.get_by_id simplified; no companies join; works with JobSpy schema

### 8. Migration
- **migrations/020_jobspy_schema_columns.sql**: Adds application_url, is_remote, date_posted, job_level, etc. with backfill from legacy columns

### 9. Resume (OB-001)
- **resume.py**: Compensating delete of orphaned file on DB upsert failure (already present)

### 10. GDPR/Privacy (PRIV-005, PRIV-007, PRIV-008)
- **apps/api/gdpr.py**: Replaced legacy `input_answers` with `application_inputs` (export via application_id, delete via subquery) and `answer_memory` (user_id). Export and deletion now align with actual schema.
- **packages/backend/domain/ccpa.py**: Same alignment; custom delete for application_inputs before applications.
- **packages/backend/domain/gdpr.py**: Added answer_memory to export and deletion.
- **PRIV-007**: data_retention.py — Applications now archived to applications_archive before DELETE; migration 032_applications_archive.sql.
- **PRIV-008**: gdpr.py — Export uploads to storage, returns download_url/expires_at; no raw data in response; GET /gdpr/export/{id}/download for secure fetch; Redis fallback when storage unavailable.

### 11. Admin RBAC (Item 23)
- **api/dependencies.py**: Added `require_admin_user_id` — returns user_id only if tenant OWNER/ADMIN or system admin; raises 403 otherwise.
- **api/main.py**: Admin endpoints (admin, analytics, dashboard, growth, dlq) now use `require_admin_user_id` instead of `get_current_user_id`.
- **api/user.py**: Profile includes `role` (user/admin/superadmin) for AdminGuard; derived from tenant_members and users.is_system_admin.

### 12. Security Headers / XSS (Items 42–44)
- **Security headers**: Already in setup_security_headers (CSP, X-Frame-Options, HSTS, etc.)
- **Rate limiting**: Already in rate_limiting_middleware (100/min unauthenticated, tier-based for tenants)
- **Input sanitization**: ProfileUpdate now sanitizes headline and bio via sanitize_text_input (Item 44)

### 13. Security
- **update-render-env.sh**: Stripe keys loaded from env; no hardcoding
- **sync_render_env_from_dotenv.py**: Fixed get_env_vars for Render API response formats

### 14. Audit Fixes (Section 3.6)
- **test_ionos_api.py**: Removed hardcoded IONOS_SECRET; credentials from IONOS_PUBLIC_PREFIX and IONOS_SECRET env vars
- **job_sync_service.py**: Cleanup: log on failure, don't abort sync; log parse errors instead of swallowing
- **localStorage QuotaExceededError**: safeSetStorage/safeGetStorage in utils.ts; useOnboarding, useFeatureFlags use it; sessionStorage fallback

### 15. Session Fixes (Production Readiness Branch)
- **Redis**: Key collisions, TTL gaps, serialization fixes
- **Security**: CORS, CSP hardening; setup_security_headers in middleware
- **Communication**: Notification preferences get/update; support ticket, service suspension TODOs
- **DLQ**: oldest_item_age_hours from oldest_item in health check
- **Scripts**: Maintenance audit — hardcoded values, error handling, shell safety
- **Tests**: Flaky tests, missing cleanup, env leaks
- **Migrations**: FK gaps, missing indexes, migration order
- **Web**: Routing, 401 handling, returnTo whitelist
- **Worker**: SSL, statement_cache_size=0 for DB pools; asyncio.Lock for sync_all_sources; jobspy_timeout_seconds
- **Tenant/RBAC**: Multi-tenant isolation, require_admin_user_id
- **Job search**: ILIKE injection, sort injection, filter bypass fixed
- **Config**: Remove hardcoded secrets, validation, reject dev defaults in prod
- **DLQ/feedback/agent**: IDOR, auth, error handling
- **AI**: Prompt injection, input validation, cost controls
- **Resume**: Upload, storage, file handling hardening
- **Magic link/Resend**: Template injection, redirects, headers
- **Onboarding/settings/export**: PII, 401, validation, state
- **Auth**: Token handling, session revocation, replay hardening
- **Billing**: Exponential backoff polling (Item 21); return_url validation
- **Concurrent tracker**: Deadlock fix; ctx.user_id for tenant ownership
- **VACUUM**: table_name validation before database_stats, index_analyzer
- **Web-admin**: sessionStorage try/catch, ErrorBoundary, 401 handling
- **ErrorBoundary/Sentry**: RouteErrorBoundary on all routes; Sentry.captureException (Items 33–34)

### 16. ATS Integration (Section 3.3 High)
- **agent.py**: Wired `ats_handlers.py` into the agent flow
  - `_detect_and_prepare_ats()`: detect ATS platform after navigation, run `pre_fill_hook` (e.g. Lever "Apply" click)
  - `fill_form_from_mapping`: added `skip_selectors` for ATS-specific fields to skip (referral, source)
  - `click_next_button`: custom next selectors from ATS handlers (Greenhouse, Lever, Workday, SmartRecruiters)
  - `submit_form`: merge ATS submit selectors with blueprint selectors
  - Greenhouse/Lever/Workday/SmartRecruiters handlers now used for pre-fill, custom selectors, skip selectors

## Environment Checklist for Production

| Variable | Required |
|----------|----------|
| DATABASE_URL | Yes |
| REDIS_URL | Yes |
| JWT_SECRET | Yes (not dev default) |
| CSRF_SECRET | Yes (not dev default) |
| LLM_API_KEY | Yes |
| APP_BASE_URL | Yes |
| RESEND_API_KEY | Yes (for magic links) |
| STRIPE_* | If using Stripe |
| API_PUBLIC_URL | Yes (magic link redirect) |

## Run Migration

```bash
# Apply migration 020 for JobSpy schema
psql $DATABASE_URL -f migrations/020_jobspy_schema_columns.sql
```

## Sync Render Env

```bash
export RENDER_API_KEY=rnd_xxx  # or in .env
python scripts/maintenance/sync_render_env_from_dotenv.py
```
