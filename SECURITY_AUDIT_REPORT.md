# Security Audit Report: Authentication & Authorization

**Date:** March 9, 2026  
**Scope:** Magic link authentication, session management, CSRF protection, rate limiting, input validation, security headers, and edge cases

---

## Executive Summary

This audit reviewed the authentication and security implementation for the magic link flow, session management, and related security controls. The codebase demonstrates **strong security practices** with comprehensive protections, but several **critical and high-severity issues** were identified that require immediate attention.

**Overall Security Posture:** Good foundation with critical gaps in production deployment requirements.

---

## Critical Findings

### CRITICAL-1: Redis Required for Production Token Replay Protection
**Severity:** Critical  
**CWE:** CWE-287 (Improper Authentication)  
**OWASP:** A02:2021 – Cryptographic Failures

**Location:** `apps/api/auth.py:95-139`

**Issue:**
- Token replay prevention uses in-memory dictionary (`_consumed_tokens`) when Redis is unavailable
- In production, this creates a **race condition** where tokens can be reused across multiple worker instances
- Code correctly fails fast in production (lines 112-121), but startup validation may not catch all deployment scenarios

**Current Protection:**
```python
if settings.env.value == "prod":
    raise RuntimeError("Redis required for production token replay protection")
```

**Risk:**
- Magic link tokens can be replayed across different server instances
- Attackers could authenticate multiple times with a single token
- Session hijacking if token is intercepted

**Remediation:**
1. ✅ **Already implemented:** Startup validation in `apps/api/main.py:128-137` checks Redis in production
2. **Enhancement:** Add health check endpoint that verifies Redis connectivity
3. **Enhancement:** Add monitoring alert if Redis connection drops during runtime
4. **Documentation:** Ensure deployment docs clearly state Redis is mandatory

**Status:** Partially mitigated (startup check exists, but runtime monitoring needed)

---

### CRITICAL-2: Session Token Replay Not Prevented After Initial Verification
**Severity:** Critical  
**CWE:** CWE-287 (Improper Authentication)  
**OWASP:** A02:2021 – Cryptographic Failures

**Location:** `apps/api/dependencies.py:179-217`

**Issue:**
- Session JWT tokens (set in `jobhuntin_auth` cookie) are **not checked for replay** after initial verification
- The `jti` (JWT ID) in session tokens is only validated during magic link verification
- Once a session token is issued, it can be reused indefinitely until expiration (7 days)

**Code Evidence:**
```python
# apps/api/dependencies.py:186-189
# NOTE: Token replay protection (jti check) is handled at the /auth/verify-magic
# endpoint level only. We do NOT check jti here because the httpOnly auth cookie
# reuses the same JWT for the entire session — consuming the jti on the first
# API call would block all subsequent calls.
```

**Risk:**
- If a session token is stolen (XSS, network interception), it can be used until expiration
- No mechanism to invalidate stolen tokens
- Long-lived sessions (7 days) increase exposure window

**Remediation:**
1. **Implement token rotation:** Issue new session tokens periodically (e.g., every 24 hours)
2. **Add token revocation:** Store active session tokens in Redis with ability to revoke
3. **Shorten session TTL:** Consider reducing from 7 days to 1-3 days
4. **Add device fingerprinting:** Bind sessions to device characteristics
5. **Implement refresh tokens:** Use short-lived access tokens with refresh mechanism

**Priority:** High - Implement token rotation and revocation

---

## High Severity Findings

### HIGH-1: IP Binding for Magic Links Disabled by Default
**Severity:** High  
**CWE:** CWE-306 (Missing Authentication for Critical Function)  
**OWASP:** A01:2021 – Broken Access Control

**Location:** `apps/api/auth.py:388-408`, `shared/config.py:104`

**Issue:**
- `magic_link_bind_to_ip` defaults to `False`
- When disabled, magic link tokens can be used from any IP address
- If a token is intercepted (email compromise, MITM), it can be used from attacker's location

**Current Implementation:**
```python
bind_to_ip = getattr(settings, "magic_link_bind_to_ip", False)
if bind_to_ip and client_ip:
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
    payload["ip_hash"] = ip_hash
```

**Risk:**
- Token theft via email compromise allows authentication from any location
- No protection against token interception in transit
- Users on shared networks (coffee shops, hotels) are vulnerable

**Remediation:**
1. **Enable by default in production:** Set `MAGIC_LINK_BIND_TO_IP=true` in production
2. **Add configuration validation:** Warn if disabled in production
3. **Consider user experience:** May block legitimate users on VPNs or mobile networks
4. **Alternative:** Use device fingerprinting instead of IP (more flexible)

**Priority:** Medium-High - Enable in production with monitoring

---

### HIGH-2: Insufficient Rate Limiting on Magic Link Requests
**Severity:** High  
**CWE:** CWE-307 (Improper Restriction of Excessive Authentication Attempts)  
**OWASP:** A07:2021 – Identification and Authentication Failures

**Location:** `apps/api/auth.py:563-578`, `shared/config.py:100-101`

**Issue:**
- Default rate limit: **20 requests per hour per email** (5-minute window)
- IP-based rate limit: **60 requests per hour** (line 976-992)
- These limits may be too permissive for abuse prevention

**Current Limits:**
```python
magic_link_requests_per_hour: int = 20
magic_link_rate_limit_window_seconds: int = 300  # 5 minutes
# IP limit: 60/hour
```

**Risk:**
- Attackers can enumerate valid email addresses (20/hour = 480/day per email)
- IP-based limit (60/hour) allows testing multiple emails from same IP
- No progressive rate limiting (temporary bans after repeated violations)

**Remediation:**
1. **Reduce per-email limit:** Consider 5-10 requests per hour
2. **Add progressive delays:** Exponential backoff after multiple requests
3. **Implement CAPTCHA requirement:** After 2-3 requests from same IP/email
4. **Add account lockout:** Temporary lockout after 5 failed attempts
5. **Monitor for enumeration:** Alert on patterns suggesting email enumeration

**Priority:** High - Reduce limits and add progressive restrictions

---

### HIGH-3: CAPTCHA Verification Not Enforced
**Severity:** High  
**CWE:** CWE-306 (Missing Authentication for Critical Function)  
**OWASP:** A07:2021 – Identification and Authentication Failures

**Location:** `apps/api/auth.py:972-974`

**Issue:**
- CAPTCHA token is **optional** in the request (`captcha_token: str | None = None`)
- Verification only occurs if token is provided
- No enforcement for high-risk scenarios (new IPs, high request rates)

**Code:**
```python
if body.captcha_token:
    if not await _verify_captcha(settings, body.captcha_token, client_ip):
        raise HTTPException(status_code=400, detail="Invalid CAPTCHA token")
# If no token provided, request proceeds without CAPTCHA
```

**Risk:**
- Automated bots can request magic links without CAPTCHA
- Email enumeration attacks are easier without CAPTCHA requirement
- No protection against scripted abuse

**Remediation:**
1. **Require CAPTCHA for:** New IPs, high request rates, disposable emails
2. **Enforce CAPTCHA after:** 2-3 requests from same email/IP
3. **Add CAPTCHA score threshold:** Reject low scores (< 0.5 is current, consider 0.7+)
4. **Frontend enforcement:** Ensure frontend always sends CAPTCHA token

**Priority:** High - Enforce CAPTCHA for high-risk scenarios

---

### HIGH-4: Missing Input Validation on Email Parameter
**Severity:** High  
**CWE:** CWE-20 (Improper Input Validation)  
**OWASP:** A03:2021 – Injection

**Location:** `apps/api/auth.py:142-145`, `apps/web/src/services/magicLinkService.ts:46`

**Issue:**
- Backend uses `EmailStr` from Pydantic (basic validation)
- Frontend sanitizes but may not catch all edge cases
- No length validation beyond RFC 320 character limit
- No protection against email header injection in email sending

**Current Validation:**
```python
class MagicLinkRequest(BaseModel):
    email: EmailStr  # Pydantic validation
    return_to: str | None = None
    captcha_token: str | None = None
```

**Risk:**
- Email header injection if email contains newlines/carriage returns
- Potential for email-based attacks (SMTP injection)
- Very long emails could cause issues in downstream systems

**Remediation:**
1. **Add strict email validation:** Reject emails with control characters
2. **Sanitize email before sending:** Strip/escape special characters
3. **Add length limits:** Enforce reasonable maximum (254 chars for domain + local)
4. **Validate email format strictly:** Use library like `email-validator` with strict mode
5. **Log suspicious patterns:** Alert on emails with unusual characters

**Priority:** Medium - Add strict validation

---

## Medium Severity Findings

### MEDIUM-1: Open Redirect Protection Has Minor Gaps
**Severity:** Medium  
**CWE:** CWE-601 (URL Redirection to Untrusted Site)  
**OWASP:** A01:2021 – Broken Access Control

**Location:** `apps/api/auth.py:210-262`, `apps/web/src/services/magicLinkService.ts:313-374`

**Issue:**
- Whitelist-based approach is good, but:
  - Query string is preserved without validation (line 261)
  - Frontend and backend whitelists must stay in sync (risk of divergence)
  - No validation of query parameters (could contain XSS payloads)

**Current Implementation:**
```python
# Re-append query string if present (safe: path is whitelisted)
return f"{path_only}?{query}" if query else path_only
```

**Risk:**
- Query parameters could contain XSS payloads if not sanitized by frontend
- If frontend whitelist diverges from backend, security could be bypassed
- No validation of query parameter values

**Remediation:**
1. **Validate query parameters:** Whitelist allowed query params per route
2. **Sanitize query values:** Remove/escape dangerous characters
3. **Sync mechanism:** Ensure frontend and backend whitelists are generated from same source
4. **Add tests:** Verify whitelist consistency between frontend and backend

**Priority:** Medium - Add query parameter validation

---

### MEDIUM-2: Session Cookie Security Settings
**Severity:** Medium  
**CWE:** CWE-614 (Sensitive Cookie in HTTPS Session Without 'Secure' Attribute)  
**OWASP:** A02:2021 – Cryptographic Failures

**Location:** `apps/api/auth.py:861-876`

**Issue:**
- Cookie `secure` flag only set in production/staging
- `samesite="none"` requires `secure=true`, but code handles this correctly
- `partitioned` attribute is good (CHIPS support) but only in production

**Current Implementation:**
```python
is_prod = settings.env.value in ("prod", "staging")
cookie_kwargs = dict(
    key=AUTH_COOKIE_NAME,
    value=session_token,
    max_age=SESSION_TTL_SECONDS,
    httponly=True,
    secure=is_prod,  # Only secure in prod
    samesite="none" if is_prod else "lax",
    path="/",
)
if is_prod:
    cookie_kwargs["partitioned"] = True
```

**Risk:**
- In development, cookies sent over HTTP could be intercepted
- `samesite="lax"` in dev is acceptable, but `secure=false` is risky if dev uses HTTPS

**Remediation:**
1. **Set secure based on URL scheme:** Check if `app_base_url` starts with `https://`
2. **Always use secure in staging:** Even if not "prod", use secure if HTTPS
3. **Add cookie security tests:** Verify secure flag is set correctly

**Priority:** Low-Medium - Improve secure flag detection

---

### MEDIUM-3: Error Messages May Leak Information
**Severity:** Medium  
**CWE:** CWE-209 (Information Exposure Through Error Message)  
**OWASP:** A01:2021 – Broken Access Control

**Location:** `apps/api/auth.py:730-777`

**Issue:**
- Most error cases correctly return generic `auth_failed` message
- However, some error paths may leak information through logs
- Disposable email rejection returns 429 (rate limit) which could be confusing

**Good Practice:**
```python
# SECURITY: Use generic error to prevent configuration enumeration
redirect_url = f"{settings.app_base_url.rstrip('/')}/login?error=auth_failed"
```

**Risk:**
- Timing attacks could reveal if email exists vs. doesn't exist
- Log messages might expose sensitive information
- Disposable email error masquerades as rate limit (good for privacy, but confusing)

**Remediation:**
1. **Consistent error messages:** Always use generic "auth_failed" for all failures
2. **Constant-time operations:** Ensure email lookup timing is consistent
3. **Sanitize logs:** Ensure no PII in error logs
4. **Add rate limiting to error responses:** Prevent enumeration via timing

**Priority:** Low - Already well implemented, minor improvements needed

---

### MEDIUM-4: Magic Link Token TTL May Be Too Long
**Severity:** Medium  
**CWE:** CWE-613 (Insufficient Session Expiration)  
**OWASP:** A07:2021 – Identification and Authentication Failures

**Location:** `shared/config.py:102`, `apps/api/auth.py:382`

**Issue:**
- Default TTL: **3600 seconds (1 hour)**
- This is reasonable, but no mechanism to shorten TTL for high-risk scenarios
- No user notification when link is about to expire

**Current:**
```python
magic_link_token_ttl_seconds: int = 3600  # 1 hour
```

**Risk:**
- Longer TTL increases window for token theft
- No way to enforce shorter TTL for suspicious requests
- Users may not realize link has expired until they click it

**Remediation:**
1. **Consider shorter TTL:** 15-30 minutes for most use cases
2. **Dynamic TTL:** Shorter TTL for new IPs, longer for known devices
3. **Expiration warnings:** Email reminder if link not used within X minutes
4. **User preference:** Allow users to request new link if expired

**Priority:** Low - Current TTL is reasonable, consider dynamic TTL

---

## Low Severity Findings

### LOW-1: Disposable Email Detection Could Be Bypassed
**Severity:** Low  
**CWE:** CWE-20 (Improper Input Validation)

**Location:** `apps/api/auth.py:152-208`

**Issue:**
- Static list of disposable email domains
- New disposable email services may not be in list
- No dynamic checking against disposable email APIs

**Risk:**
- Users can register with disposable emails not in the list
- Could be used for spam or abuse

**Remediation:**
1. **Use disposable email API:** Integrate with service like `disposable-email-detector`
2. **Regular list updates:** Keep static list updated
3. **Pattern matching:** Detect common disposable email patterns
4. **Monitor for abuse:** Track registration patterns

**Priority:** Low - Acceptable risk for most applications

---

### LOW-2: Frontend Rate Limiting Can Be Bypassed
**Severity:** Low  
**CWE:** CWE-602 (Client-Side Enforcement of Server-Side Security)

**Location:** `apps/web/src/services/magicLinkService.ts:23-35, 58-90`

**Issue:**
- Frontend implements client-side rate limiting and circuit breaker
- These can be bypassed by modifying client code or using API directly
- However, backend also implements rate limiting (defense in depth)

**Risk:**
- Attackers can bypass frontend limits by calling API directly
- Frontend limits provide UX benefit but not security

**Remediation:**
1. ✅ **Already mitigated:** Backend rate limiting is the real protection
2. **Documentation:** Clarify that frontend limits are UX-only
3. **Consider removing:** Frontend limits add complexity without security benefit

**Priority:** Very Low - Backend protection is sufficient

---

### LOW-3: Missing Security Headers on Some Responses
**Severity:** Low  
**CWE:** CWE-693 (Protection Mechanism Failure)

**Location:** `shared/middleware.py:188-251`

**Issue:**
- Security headers middleware is well implemented
- However, some redirect responses may not include all headers
- CSP nonce support exists but may not be used everywhere

**Current Headers:**
- ✅ X-Content-Type-Options: nosniff
- ✅ X-Frame-Options: DENY
- ✅ X-XSS-Protection: 1; mode=block
- ✅ Referrer-Policy: strict-origin-when-cross-origin
- ✅ Strict-Transport-Security (production)
- ✅ Content-Security-Policy (with nonce support)

**Remediation:**
1. **Verify redirect responses:** Ensure headers are set on all response types
2. **Test CSP nonce:** Ensure nonces are generated and used consistently
3. **Add Permissions-Policy header:** Restrict browser features (camera, microphone, etc.)

**Priority:** Very Low - Headers are well implemented

---

## Positive Security Practices

### ✅ Strong Security Implementations

1. **Token Replay Prevention:** Redis-based token consumption tracking (when available)
2. **CSRF Protection:** Comprehensive middleware with proper exemptions
3. **Security Headers:** Well-implemented middleware with CSP, HSTS, etc.
4. **Input Sanitization:** Whitelist-based return_to validation
5. **Error Message Obfuscation:** Generic error messages prevent enumeration
6. **HttpOnly Cookies:** Session tokens stored in httpOnly cookies (XSS protection)
7. **JWT Best Practices:** Proper audience validation, expiration, and signing
8. **Rate Limiting:** Multi-layer rate limiting (IP, email, tenant)
9. **IP Extraction:** Proper handling of X-Forwarded-For headers
10. **CAPTCHA Integration:** reCAPTCHA v3 support with score validation

---

## Recommendations Summary

### Immediate Actions (Critical/High)

1. **✅ Verify Redis is mandatory in production** (already enforced at startup)
2. **Implement session token rotation** (every 24 hours)
3. **Add session token revocation mechanism** (Redis-based)
4. **Enable IP binding for magic links in production** (`MAGIC_LINK_BIND_TO_IP=true`)
5. **Reduce magic link rate limits** (5-10 per hour per email)
6. **Enforce CAPTCHA for high-risk scenarios** (new IPs, high request rates)

### Short-Term Improvements (Medium)

1. **Add query parameter validation** for return_to URLs
2. **Improve cookie secure flag detection** (check URL scheme)
3. **Add progressive rate limiting** (exponential backoff)
4. **Implement account lockout** after repeated failures
5. **Add email validation enhancements** (control character rejection)

### Long-Term Enhancements (Low)

1. **Dynamic TTL based on risk** (shorter for new IPs)
2. **Disposable email API integration** (instead of static list)
3. **Device fingerprinting** (instead of IP binding)
4. **Refresh token mechanism** (short-lived access tokens)

---

## Testing Recommendations

1. **Token Replay Tests:** Verify tokens cannot be reused after consumption
2. **Rate Limiting Tests:** Verify limits are enforced correctly
3. **CSRF Tests:** Verify CSRF protection on all state-changing endpoints
4. **Open Redirect Tests:** Verify return_to validation prevents redirects
5. **Session Management Tests:** Verify session expiration and invalidation
6. **CAPTCHA Tests:** Verify CAPTCHA is required when appropriate
7. **Error Message Tests:** Verify no information leakage in errors
8. **Cookie Security Tests:** Verify secure, httpOnly, samesite flags

---

## Compliance Considerations

### GDPR/CCPA
- ✅ Email masking in logs (good practice)
- ⚠️ Session tokens stored in cookies (ensure consent for non-essential cookies)
- ✅ User data deletion support needed (verify implementation)

### OWASP Top 10 2021
- ✅ A01: Broken Access Control - Well protected (whitelist validation)
- ✅ A02: Cryptographic Failures - JWT properly signed, but session replay risk
- ✅ A03: Injection - Input validation present, but could be stricter
- ✅ A07: Identification Failures - Rate limiting present, but could be stricter
- ✅ A08: Software Integrity - Dependencies should be audited separately

---

## Conclusion

The authentication and security implementation demonstrates **strong foundational security practices** with comprehensive protections in place. However, **critical issues** around session token replay and production deployment requirements need immediate attention.

**Key Strengths:**
- Comprehensive CSRF protection
- Well-implemented security headers
- Good error message obfuscation
- Multi-layer rate limiting

**Key Weaknesses:**
- Session token replay not prevented after initial verification
- IP binding disabled by default
- Rate limits may be too permissive
- CAPTCHA not enforced for high-risk scenarios

**Overall Risk Level:** Medium-High (due to critical session token replay issue)

**Recommended Priority:** Address CRITICAL-2 and HIGH-1 through HIGH-4 before production launch.

---

## Appendix: Code References

- Magic Link Implementation: `apps/api/auth.py`
- Frontend Magic Link Service: `apps/web/src/services/magicLinkService.ts`
- CSRF Middleware: `shared/middleware.py:63-157`
- Security Headers: `shared/middleware.py:188-257`
- JWT Validation: `apps/api/dependencies.py:179-217`
- Rate Limiting: `apps/api/auth.py:563-1010`
- Configuration: `shared/config.py:100-105`
