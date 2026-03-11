# Self-Heal Loop Fixes Applied

## Summary

Applied fixes to enable full onboarding flow with token-based auth in local dev.

## Fixes Applied

### 1. AuthContext – Include Authorization on Initial Fetch
**File:** `apps/web/src/context/AuthContext.tsx`

The initial profile fetch used a direct `fetch()` without `getAuthHeaders()`, so the Bearer token was never sent. This caused 401s when using a localStorage token.

**Fix:** Call `getAuthHeaders()` and merge into the initial fetch headers.

### 2. API Client – Ensure CSRF Before Mutations
**File:** `apps/web/src/lib/api.ts`

- Added `ensureCsrfCookie()` that fetches `GET /csrf/prepare` before PATCH/POST/DELETE when no CSRF token is present.
- Call `ensureCsrfCookie()` before mutations in `apiFetch()`.
- Added `VITE_ALLOW_LOCALSTORAGE_AUTH` for localhost E2E testing in preview mode.

### 3. CSRF Middleware – Cookie Domain for Cross-Port
**File:** `shared/middleware.py`

For local dev with frontend (5173) and API (8000) on different ports, set `cookie_domain="localhost"` so the CSRF cookie is readable by JS on both origins.

### 4. Local Dev – Use Proxy for Same-Origin
**File:** `apps/web/.env`

For local dev, comment out `VITE_API_URL` so the frontend uses `http://localhost:5173/api` (Vite proxy). The proxy forwards to `localhost:8000`, keeping the same origin and making the CSRF cookie work.

## Recommended Local Dev Setup

1. **Backend:** `ENV=local DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/sorce uvicorn api.main:app --host 0.0.0.0 --port 8000`
2. **Frontend:** In `apps/web/.env`, comment out `VITE_API_URL` so the proxy is used.
3. **Token:** Generate JWT with `jti` claim and set `localStorage.setItem('auth_token', '<token>')` in the browser console.
4. **Flow:** Refresh, go to `/app/onboarding`, complete all steps.

## Known Issues

- **Backend crash on PATCH with /me exemption:** When `/me` is CSRF-exempt, PATCH `/me/profile` can trigger `TypeError: 'NoneType' object is not callable` in the middleware stack. Use proxy mode to avoid this.
- **Redis:** When Redis is unavailable, session revocation checks are skipped in local env (auth still works).
