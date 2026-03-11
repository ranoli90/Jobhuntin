# Self-Heal Loop Fixes Applied

## Summary

Applied fixes for auth and CSRF, plus a production-ready architecture (see `docs/PRODUCTION_AUTH_CSRF.md`).

## Fixes Applied

### 1. AuthContext – Include Authorization on Initial Fetch
**File:** `apps/web/src/context/AuthContext.tsx`

The initial profile fetch used a direct `fetch()` without `getAuthHeaders()`, so the Bearer token was never sent. **Fix:** Call `getAuthHeaders()` and merge into the initial fetch headers.

### 2. API Client – Ensure CSRF Before Mutations
**File:** `apps/web/src/lib/api.ts`

- Added `ensureCsrfCookie()` that fetches `GET /csrf/prepare` before PATCH/POST/DELETE when no CSRF token is present.
- Added `VITE_ALLOW_LOCALSTORAGE_AUTH` for localhost E2E testing in preview mode.

### 3. CSRF Middleware – Production-Ready (sensitive_cookies)
**File:** `shared/middleware.py`

- **sensitive_cookies={"jobhuntin_auth"}**: CSRF is only enforced when the request includes the httpOnly auth cookie. Bearer-only requests skip CSRF per OWASP (browser cannot auto-send Authorization header). Scales to 1 or 500 users.
- **cookie_domain**: Auto-derived for local (localhost) and production cross-subdomain (e.g. `jobhuntin.com` for app.jobhuntin.com + api.jobhuntin.com).

### 4. Redis Fallback
**File:** `apps/api/dependencies.py`

When Redis is unavailable in local env, session revocation checks are skipped (auth still works).

## Local Dev Setup

1. **Backend:** `ENV=local DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/sorce uvicorn api.main:app --host 0.0.0.0 --port 8000`
2. **Frontend:** `cd apps/web && npx vite --host 0.0.0.0 --port 5173`
3. **Token:** Generate JWT with `jti` claim; set `localStorage.setItem('auth_token', '<token>')` in the browser console.
4. **Flow:** Bearer-only requests skip CSRF; onboarding works without proxy.

## Production

See `docs/PRODUCTION_AUTH_CSRF.md` for Render deployment options and architecture.
