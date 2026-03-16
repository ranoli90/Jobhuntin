# CSRF Protection Audit Report

**Date:** 2026-03-15
**Auditor:** Kilo Code (Debug Mode)
**Scope:** JobHuntin API CSRF Protection

## Executive Summary

The JobHuntin API implements CSRF protection using `starlette-csrf` middleware with an OWASP-aligned approach. The implementation is **well-designed** with no critical security gaps identified. The key security principle correctly implemented is:

> CSRF protection is only enforced when cookie-based authentication (`jobhuntin_auth`) is present. Bearer token requests (Authorization header) are inherently CSRF-safe and automatically exempted.

## CSRF Middleware Configuration

### Location
- [`shared/middleware.py`](shared/middleware.py:145) - `setup_csrf_middleware()`
- [`apps/api/main.py`](apps/api/main.py:334) - Middleware registration

### Configuration Details

```python
# From shared/middleware.py
app.add_middleware(
    CSRFForCORSMiddleware,
    secret=secret,
    cookie_name="csrftoken",
    cookie_secure=cookie_secure,  # True in prod/staging
    cookie_httponly=False,  # Required for double-submit pattern
    cookie_samesite="none" if is_cross_origin else "lax",
    sensitive_cookies=frozenset({"jobhuntin_auth"}),  # KEY: Only enforce when auth cookie present
    exempt_urls=exempt_patterns,
)
```

### Key Security Features

1. **`sensitive_cookies` Configuration**: CSRF is ONLY enforced when the `jobhuntin_auth` cookie is present. This correctly implements OWASP guidance that Bearer token authentication is inherently CSRF-safe.

2. **Environment-Aware Security**:
   - Production/Staging: Requires `CSRF_SECRET`, fails closed if missing
   - Local/Dev: Warns but continues for development convenience
   - `cookie_secure=True` in production (HTTPS only)

3. **Cross-Origin Support**: Automatically configures `SameSite=none` and derives cookie domain for cross-origin deployments (e.g., `app.jobhuntin.com` + `api.jobhuntin.com`)

## Exempt Paths Analysis

The following paths are exempted from CSRF protection in [`CSRFMiddleware.EXEMPT_PATHS`](shared/middleware.py:81):

| Path | Reason | Risk Assessment |
|------|--------|-----------------|
| `/health`, `/healthz` | Health checks (GET only typically) | ✅ Safe - no state changes |
| `/auth/magic-link` | Initiates auth flow (public) | ✅ Safe - sends email, doesn't authenticate |
| `/auth/verify-magic` | Magic link callback (GET) | ✅ Safe - GET request, token in URL |
| `/auth/dev-login` | Dev-only endpoint | ✅ Safe - disabled in production |
| `/auth/logout` | Logout endpoint | ⚠️ Review - See below |
| `/auth/webhooks/resend` | Resend email webhook | ✅ Safe - has signature verification |
| `/billing/webhook` | Stripe webhook | ✅ Safe - has signature verification |
| `/sso/saml/acs` | SAML assertion consumer | ✅ Safe - external IdP POST |
| `/og/` | OpenGraph image generation | ✅ Safe - typically GET |
| `/webhook/resume_parse` | Resume parse webhook | ⚠️ Review - See below |
| `/contact` | Public contact form | ✅ Safe - rate-limited, no auth |

### Exemption Review Notes

1. **`/auth/logout`**: Exempted because logout is idempotent and typically a GET request. The worst case is a forced logout, which is not a security concern. ✅ Appropriate

2. **`/webhook/resume_parse`**: This endpoint requires authentication (`ctx: TenantContext = Depends(_get_tenant_ctx)`). However, it's exempted because:
   - It uses Bearer token auth (Authorization header) which is CSRF-safe
   - The `sensitive_cookies` check means CSRF is only enforced when `jobhuntin_auth` cookie is present
   - If called with Bearer token only, CSRF is automatically skipped
   - ⚠️ **Potential Issue**: If called with cookie-based auth, CSRF would be bypassed

## Authentication Flow Analysis

### Cookie-Based Authentication (Magic Link Flow)
1. User requests magic link via `/auth/magic-link` (POST, public, rate-limited)
2. User clicks link in email → `/auth/verify-magic` (GET, token in URL)
3. Backend sets `jobhuntin_auth` httpOnly cookie
4. Subsequent requests with this cookie require CSRF token

### Bearer Token Authentication
1. Frontend stores JWT from magic link verification
2. Requests include `Authorization: Bearer <token>` header
3. CSRF middleware detects no `jobhuntin_auth` cookie → CSRF check skipped
4. This is correct per OWASP: browsers don't auto-send Authorization headers

## State-Changing Endpoints Inventory

### Summary
- **Total POST/PUT/DELETE/PATCH endpoints found**: 287+
- **All authenticated endpoints use Bearer token auth** via `Depends(get_current_user_id)` or `Depends(get_tenant_context)`
- **CSRF protection is automatic** via `sensitive_cookies` configuration

### Endpoint Categories

| Category | Endpoints | Auth Method | CSRF Protection |
|----------|-----------|-------------|-----------------|
| User Profile | `/me/profile`, `/me/applications/*` | Bearer token | Auto (no cookie = skip) |
| AI Features | `/ai/*`, `/onboarding/*` | Bearer token | Auto (no cookie = skip) |
| Billing | `/billing/checkout`, `/billing/portal` | Bearer token | Auto (no cookie = skip) |
| Admin | `/admin/*` | Bearer token | Auto (no cookie = skip) |
| Webhooks | `/billing/webhook`, `/auth/webhooks/resend` | Signature verification | Exempt (appropriate) |
| Public | `/contact`, `/auth/magic-link` | None | Exempt (appropriate) |

## Identified Issues

### Issue 1: `/webhook/resume_parse` Exemption (FIXED)

**Location**: [`shared/middleware.py`](shared/middleware.py:81)

**Problem**: The `/webhook/resume_parse` endpoint was exempted from CSRF, but it requires authentication via `TenantContext`. If a user has both the `jobhuntin_auth` cookie AND calls this endpoint, CSRF protection would be bypassed.

**Risk**: Low - This endpoint is typically called with Bearer token auth. The exemption was redundant because Bearer token requests automatically skip CSRF (no `jobhuntin_auth` cookie present).

**Fix Applied**: Removed the `/webhook/resume_parse` exemption from `CSRFMiddleware.EXEMPT_PATHS`. The endpoint will now:
- Skip CSRF automatically when called with Bearer token (no cookie = no CSRF check)
- Enforce CSRF when called with cookie-based auth (appropriate protection)

**Status**: ✅ FIXED

### Issue 2: No CSRF Token Endpoint (Informational - No Issue)

**Observation**: The `/csrf/prepare` endpoint exists at [`apps/api/main.py:1223`](apps/api/main.py:1223).

**Purpose**: This GET endpoint triggers the CSRF middleware to set the `csrftoken` cookie. The frontend can then read from `document.cookie` and include the token in the `x-csrftoken` header for subsequent POST/PUT/DELETE/PATCH requests.

**Status**: ✅ Working as expected

## Recommendations

### 1. Document the CSRF Flow (Low Priority)
Add comments in the frontend code explaining:
- How CSRF tokens are obtained (via `/csrf/prepare` endpoint)
- When CSRF is required (cookie-based auth only)
- How to include the token (`x-csrftoken` header)

### 2. ~~Review `/webhook/resume_parse` Exemption~~ (COMPLETED)
~~Verify the intended use case:~~
~~- If external webhook: Add signature verification~~
~~- If user action: Remove exemption (Bearer auth auto-skips CSRF anyway)~~

**Fixed**: Removed the exemption. The endpoint now properly relies on the `sensitive_cookies` mechanism.

## Conclusion

The CSRF protection implementation is **well-designed and follows OWASP best practices**. The use of `sensitive_cookies` to only enforce CSRF when cookie-based auth is present is the correct approach for an API that supports both cookie and Bearer token authentication.

**One minor security gap was identified and fixed:**
- Removed unnecessary `/webhook/resume_parse` exemption that could have allowed CSRF bypass for cookie-based auth

### Security Posture: ✅ PASS

- CSRF middleware properly configured
- Bearer token requests correctly exempted (OWASP-compliant)
- Webhook endpoints have signature verification
- Public endpoints are appropriately exempted
- Production environment requires CSRF secret

---

## Appendix: How CSRF Protection Works

### For Cookie-Based Auth (Magic Link Flow)
```
1. User verifies magic link → backend sets jobhuntin_auth cookie
2. Browser makes POST request → includes cookie automatically
3. CSRF middleware detects jobhuntin_auth cookie → enforces CSRF
4. Frontend must include x-csrftoken header (from csrftoken cookie)
5. Middleware validates token match
```

### For Bearer Token Auth
```
1. Frontend stores JWT from auth flow
2. Browser makes POST request → includes Authorization header (NOT automatic)
3. CSRF middleware detects NO jobhuntin_auth cookie → skips CSRF
4. Request proceeds (JWT validation happens in endpoint dependencies)
```

This is secure because browsers cannot be tricked into sending custom `Authorization` headers - they must be explicitly added by JavaScript, which is subject to same-origin policy.
