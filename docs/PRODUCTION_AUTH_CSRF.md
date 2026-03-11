# Production Auth & CSRF Architecture

## Overview

This document describes the production-ready authentication and CSRF strategy for JobHuntin, designed to scale from 1 to 500+ concurrent users on Render.

## Security Model

### OWASP-Aligned CSRF Strategy

**Key principle:** CSRF protection is only required when the browser automatically sends credentials (cookies). Bearer tokens in the `Authorization` header are **not** automatically sent—they must be explicitly added by JavaScript. Therefore, Bearer-only requests are **exempt from CSRF** per OWASP guidance.

### Implementation: `sensitive_cookies`

The backend uses starlette-csrf with `sensitive_cookies={"jobhuntin_auth"}`:

- **Bearer-only requests** (no `jobhuntin_auth` cookie): CSRF check **skipped**. Works for:
  - Dev/localStorage token
  - API clients
  - Any request with `Authorization: Bearer <token>` and no auth cookie

- **Cookie-based requests** (magic link flow): CSRF check **enforced**. The double-submit pattern protects users who authenticate via httpOnly cookie.

### Scaling Properties

- **Stateless**: JWT validation only; no server-side session lookup for auth
- **Horizontal scaling**: Works with multiple Render instances; no sticky sessions
- **1 or 500 users**: Same code path; no special handling

## Deployment on Render

### Option A: Custom Domain (Recommended)

Use `app.jobhuntin.com` (frontend) and `api.jobhuntin.com` (backend):

1. **CORS**: Allow `https://app.jobhuntin.com` in `CORS_ALLOWED_ORIGINS`
2. **Cookie domain**: Backend auto-derives `cookie_domain=jobhuntin.com` from `API_PUBLIC_URL` / `APP_BASE_URL`, so both subdomains share the CSRF cookie
3. **Magic link flow**: User clicks link → backend sets `jobhuntin_auth` cookie → redirects to app → subsequent requests use cookie + CSRF token
4. **Frontend**: Call `GET /csrf/prepare` before first mutation (with `credentials: "include"`) to obtain the CSRF cookie

### Option B: Render Default URLs (*.onrender.com)

With `jobhuntin-api.onrender.com` and `jobhuntin.onrender.com`:

- **No shared parent domain**: CSRF cookie cannot be read by the frontend (different subdomains)
- **Solution**: Use Bearer token flow. After magic link verify, redirect with token in URL fragment (or one-time code exchange). Frontend stores token and sends `Authorization: Bearer` on all requests. No CSRF needed.
- **Alternative**: Deploy frontend and backend as a single service (FastAPI serves static build + API) for same-origin.

### Option C: Same-Origin via Reverse Proxy

Deploy a single Web Service that:

1. Serves the React static build at `/`
2. Proxies `/api/*` to the FastAPI backend (or mounts it)

Result: `https://jobhuntin.com` and `https://jobhuntin.com/api` are same-origin. Cookies work naturally.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `APP_BASE_URL` | Frontend URL (e.g. `https://app.jobhuntin.com`) |
| `API_PUBLIC_URL` | Backend URL (e.g. `https://api.jobhuntin.com`) |
| `CSRF_SECRET` | Required in prod; used to sign CSRF tokens |
| `JWT_SECRET` | Required in prod; used to sign JWTs |

## Frontend Configuration

- **Bearer flow**: Set `Authorization: Bearer <token>` on all API requests. No CSRF token needed.
- **Cookie flow** (magic link): Call `GET /api/csrf/prepare` with `credentials: "include"` before first mutation. Include `x-csrftoken` header (from `document.cookie`) on PATCH/POST/DELETE.

## References

- [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Do I need CSRF token if I'm using Bearer JWT?](https://security.stackexchange.com/questions/170388/do-i-need-csrf-token-if-im-using-bearer-jwt)
- [starlette-csrf sensitive_cookies](https://github.com/frankie567/starlette-csrf)
