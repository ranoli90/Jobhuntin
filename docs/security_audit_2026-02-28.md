# JobHuntin (Sorce) Backend — Comprehensive Security Audit Report

**Date:** 2026-02-28
**Scope:** `/workspace/apps/api/`, `/workspace/apps/api_v2/`, `/workspace/packages/backend/`, `/workspace/packages/shared/`
**Auditor:** Cursor Cloud Agent

---

## Executive Summary

The codebase demonstrates a security-conscious approach in many areas (parameterized queries, PII masking, CSRF protection, security headers, rate limiting). However, there are **critical** and **high-severity** findings that must be addressed before production hardening is complete.

---

## Finding #1 — Magic Link JWT Has No Single-Use Enforcement
- **File:** `apps/api/auth.py`, lines 178-207
- **Current behavior:**
  ```python
  payload = {
      "sub": str(user_id),
      "email": email,
      "aud": "authenticated",
      "exp": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
  }
  token = jwt.encode(payload, secret, algorithm="HS256")
  ```
  Magic link tokens are reusable until they expire (default 1 hour). No `jti` (JWT ID) claim is generated, and no server-side record marks the token as consumed.
- **Recommended fix:** Add a unique `jti` claim, store it in a Redis/DB "used tokens" set, and reject any token whose `jti` has already been seen.
- **Severity:** **Critical**

---

## Finding #2 — Magic Link Token Has No `iat` or `nbf` Claim
- **File:** `apps/api/auth.py`, lines 179-184
- **Current behavior:** Only `sub`, `email`, `aud`, `exp` are set. Missing `iat` (issued-at) and `nbf` (not-before) makes it harder to detect token replay or enforce time-of-issuance checks.
- **Recommended fix:** Add `"iat": datetime.now(timezone.utc)` and `"nbf": datetime.now(timezone.utc)`.
- **Severity:** **Medium**

---

## Finding #3 — JWT Token Decoding Leaks Exception Details to Client
- **File:** `apps/api/main.py`, lines 708-711
- **Current behavior:**
  ```python
  except pyjwt.PyJWTError as exc:
      raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")
  except Exception as exc:
      raise HTTPException(status_code=401, detail=f"Token error: {exc}")
  ```
  The full exception message is returned to the client, potentially leaking information about the JWT library version, algorithm, or key configuration.
- **Recommended fix:** Return a generic `"Invalid or expired token"` message. Log the details server-side.
- **Severity:** **Medium**

---

## Finding #4 — MFA Not Enforced on Login / Magic Link Flow
- **File:** `apps/api/auth.py` (entire file) + `apps/api/main.py`, line 691
- **Current behavior:** The magic link endpoint generates a full JWT and returns it in a link. The `get_current_user_id` dependency only validates the JWT — it never checks if the user has MFA enrolled and whether they completed the MFA challenge. A user with TOTP enabled can be fully authenticated without entering their TOTP code.
- **Recommended fix:** After token validation, check `user_mfa_enrollments`. If MFA is enabled, issue a partial-auth token and require `/auth/mfa/totp/challenge` before upgrading to a full session.
- **Severity:** **Critical**

---

## Finding #5 — MFA Disable Endpoint Has No Re-Authentication
- **File:** `apps/api/mfa.py`, lines 204-219
- **Current behavior:**
  ```python
  @router.delete("/disable")
  async def disable_mfa(
      body: DisableMFARequest | None = None,
      db: asyncpg.Pool = Depends(_get_pool),
      user_id: str = Depends(_get_user_id),
  ) -> dict[str, str]:
  ```
  MFA can be disabled with just a valid JWT. The optional `code` field in `DisableMFARequest` is never validated. An attacker with a stolen JWT can silently disable MFA.
- **Recommended fix:** Require a valid TOTP code or recovery code in the `DisableMFARequest.code` field, and validate it before allowing MFA to be disabled.
- **Severity:** **Critical**

---

## Finding #6 — TOTP Secret Returned in API Response (Enrollment)
- **File:** `apps/api/mfa.py`, lines 89-105
- **Current behavior:**
  ```python
  secret = config.get("secret", "")
  return TOTPEnrollResponse(
      enrollment_id=enrollment_id,
      provisioning_uri=uri,
      secret=secret,
  )
  ```
  The raw TOTP secret is returned in the JSON response alongside the provisioning URI. While the URI already contains the secret, explicitly returning it as a separate field increases the risk of the secret being logged by intermediate proxies.
- **Recommended fix:** Remove the `secret` field from `TOTPEnrollResponse`. The `provisioning_uri` already contains the secret for QR code generation.
- **Severity:** **Low**

---

## Finding #7 — TOTP Enrollment Not Scoped to Requesting User
- **File:** `apps/api/mfa.py`, lines 108-123 (`verify_totp_enrollment`)
- **Current behavior:** The `body.enrollment_id` is looked up without verifying it belongs to the authenticated `user_id`. An attacker could provide another user's enrollment ID to verify their enrollment.
- **Corresponding domain code** in `packages/backend/domain/mfa.py`, line 241: `WHERE id = $1 AND mfa_type = 'totp' AND is_verified = false` — no `user_id` filter.
- **Recommended fix:** Add `AND user_id = $2` to the enrollment lookup query, passing the authenticated `user_id`.
- **Severity:** **High**

---

## Finding #8 — `serve_storage_file` Endpoint Has No Authentication
- **File:** `apps/api/main.py`, lines 1292-1317
- **Current behavior:**
  ```python
  @app.get("/api/storage/{bucket}/{path:path}")
  async def serve_storage_file(
      bucket: str,
      path: str,
  ):
  ```
  This endpoint serves files from storage (resumes, avatars) with **no authentication**. Anyone who guesses or discovers the path can download user resumes.
- **Recommended fix:** Require authentication (via `Depends(get_current_user_id)`) and verify the requesting user owns the file, or use signed URLs with expiration.
- **Severity:** **Critical**

---

## Finding #9 — Storage Path Traversal Not Prevented
- **File:** `apps/api/main.py`, lines 1300-1301
- **Current behavior:**
  ```python
  storage_path = f"{bucket}/{path}"
  data = await storage.download_file(storage_path)
  ```
  The `path` parameter accepts FastAPI's `{path:path}` catch-all, but no validation prevents `../` traversal in the bucket or path components.
- **Recommended fix:** Validate that neither `bucket` nor `path` contain `..`, `//`, or absolute path prefixes. Normalize the path and verify it stays within the storage root.
- **Severity:** **High**

---

## Finding #10 — CCPA Request Processing Endpoint Lacks Admin Authorization
- **File:** `apps/api/ccpa.py`, lines 216-236
- **Current behavior:**
  ```python
  @router.post("/ccpa/requests/{request_id}/process")
  async def process_ccpa_request(
      request_id: str,
      db: asyncpg.Pool = Depends(_get_pool),
      user_id: str = Depends(_get_user_id),  # SECURITY: Require authentication
  ) -> dict[str, Any]:
      # SECURITY: This endpoint should be admin-only in production
      # For now, we require authentication but allow any authenticated user
      # TODO: Add admin role check for production
  ```
  The code's own comment acknowledges this is insecure. Any authenticated user can process any CCPA request, including deleting other users' data.
- **Recommended fix:** Add `require_system_admin` or `require_role(ctx, "OWNER", "ADMIN")` check.
- **Severity:** **Critical**

---

## Finding #11 — GDPR Deletion Endpoint Uses Manual Transaction Management
- **File:** `apps/api/gdpr.py`, lines 241-266
- **Current behavior:**
  ```python
  await conn.execute("BEGIN")
  try:
      for table, user_col in TABLES_FOR_DELETION:
          result = await conn.execute(f"DELETE FROM {table} WHERE {user_col} = $1", user_id)
      await conn.execute("COMMIT")
  except Exception as e:
      await conn.execute("ROLLBACK")
  ```
  While table names are whitelisted (line 128-133), using `f"DELETE FROM {table} WHERE {user_col} = $1"` is fragile. Manual `BEGIN/COMMIT/ROLLBACK` instead of using `db_transaction()` is error-prone.
- **Recommended fix:** Use the existing `db_transaction()` context manager.
- **Severity:** **Medium**

---

## Finding #12 — GDPR Export Generates Download URL But Never Stores Export Data
- **File:** `apps/api/gdpr.py`, lines 195-205
- **Current behavior:**
  ```python
  json.dumps(export_data, indent=2, default=str)  # result is discarded
  return DataExportResponse(
      export_id=export_id,
      status="completed",
      download_url=f"/gdpr/download/{export_id}",
  ```
  The export data is serialized to JSON and immediately discarded. The returned `download_url` (`/gdpr/download/{export_id}`) has no corresponding endpoint, so the user can never actually download their data.
- **Recommended fix:** Either store the export to persistent storage and serve it, or return the data inline.
- **Severity:** **High**

---

## Finding #13 — GDPR Deletion Returns Internal Error Details
- **File:** `apps/api/gdpr.py`, line 268
- **Current behavior:**
  ```python
  raise HTTPException(status_code=500, detail=f"Deletion failed: {e}")
  ```
  Full exception text from database errors is returned to the client.
- **Recommended fix:** Return generic error; log details server-side.
- **Severity:** **Medium**

---

## Finding #14 — Session Cleanup Endpoint Has No Authentication
- **File:** `apps/api/sessions.py`, lines 171-180
- **Current behavior:**
  ```python
  @router.post("/cleanup", response_model=RevokeResponse)
  async def cleanup_expired_sessions(
      db: asyncpg.Pool = Depends(_get_pool),
  ) -> RevokeResponse:
  ```
  This endpoint deletes expired sessions across ALL users with no auth required. An attacker could trigger mass session cleanup as a DoS vector.
- **Recommended fix:** Require system admin authentication, or move cleanup to a scheduled background task.
- **Severity:** **High**

---

## Finding #15 — Session Revocation Not Scoped to Requesting User
- **File:** `apps/api/sessions.py`, lines 94-122
- **Current behavior:** The `revoke_session` endpoint accepts any `session_id` and revokes it. It depends on `ctx` (TenantContext) for the user, but calls `manager.revoke_session(session_id, ...)` without verifying the session belongs to `ctx.user_id`.
- **Recommended fix:** Pass `ctx.user_id` to `revoke_session` and verify ownership in the query: `WHERE session_id = $1 AND user_id = $2`.
- **Severity:** **High**

---

## Finding #16 — Stripe Webhook Missing Signature Validation Fallback
- **File:** `apps/api/billing.py`, lines 264-274
- **Current behavior:**
  ```python
  stripe_signature: str = Header(None),
  ```
  The `stripe_signature` parameter defaults to `None`. If no signature header is sent, `construct_event` is called with `None`, and the behavior depends on the Stripe library version — some versions may accept `None`.
- **Recommended fix:** Return 400 immediately if `stripe_signature` is `None` or empty.
- **Severity:** **High**

---

## Finding #17 — Stripe Error Details Leaked to Client
- **File:** `apps/api/billing.py`, line 192 and 229
- **Current behavior:**
  ```python
  raise HTTPException(status_code=502, detail=f"Payment provider error: {str(e)}")
  ```
  Stripe exception details (which may include account IDs, API version info) are returned to the client.
- **Recommended fix:** Return generic "Payment processing failed" message.
- **Severity:** **Medium**

---

## Finding #18 — Checkout `success_url` / `cancel_url` Not Validated
- **File:** `apps/api/billing.py`, lines 38-41
- **Current behavior:**
  ```python
  class CheckoutRequest(BaseModel):
      success_url: str
      cancel_url: str
  ```
  These URLs are passed directly to `stripe.checkout.Session.create()` without any validation. An attacker could set `success_url` to a malicious domain to phish users after payment.
- **Recommended fix:** Validate that `success_url` and `cancel_url` belong to allowed domains (e.g., `jobhuntin.com`, `localhost` for dev).
- **Severity:** **High**

---

## Finding #19 — Webhook URL Not Validated for SSRF
- **File:** `apps/api/developer.py`, line 153 and `apps/api_v2/router.py`, line 303
- **Current behavior:**
  ```python
  class CreateWebhookRequest(BaseModel):
      url: str
  ```
  The webhook URL is stored and later receives HTTP POST requests from the server. No validation prevents internal URLs like `http://localhost`, `http://169.254.169.254` (cloud metadata), or `http://127.0.0.1`.
- **Recommended fix:** Validate that webhook URLs use HTTPS, resolve to public IP addresses, and don't point to private/reserved ranges.
- **Severity:** **High**

---

## Finding #20 — OG Image Endpoint Has No Rate Limiting or Auth
- **File:** `apps/api/og.py`, entire file
- **Current behavior:** The `GET /api/og` endpoint generates PNG images on every request with CPU-intensive Pillow operations and external font downloads. No auth or rate limiting.
- **Recommended fix:** Add aggressive rate limiting (by IP), cache generated images, and add a simple API key or HMAC signature.
- **Severity:** **Medium**

---

## Finding #21 — External Font Fetching is SSRF-Adjacent
- **File:** `apps/api/og.py`, lines 17-18, 32-33
- **Current behavior:**
  ```python
  FONT_URL_BOLD = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf"
  resp = httpx.get(url, timeout=10)
  ```
  Hardcoded URLs to GitHub are fetched on first request. If these URLs ever change or are compromised, malicious content could be loaded. Also a latency/reliability risk.
- **Recommended fix:** Bundle fonts locally in the Docker image/repo.
- **Severity:** **Low**

---

## Finding #22 — Rate Limiter Memory Leak (In-Process Dict Growth)
- **File:** `apps/api/user.py`, lines 56-77
- **Current behavior:**
  ```python
  _profile_limiters: dict[str, RateLimiter] = {}
  _upload_limiters: dict[str, RateLimiter] = {}
  ```
  Per-user rate limiters are stored in unbounded dictionaries. In production with thousands of users, these grow without limit and are never evicted.
- **Affected files:** Also `apps/api/auth.py` line 43 (has eviction), `apps/api/export.py` line 31 (unbounded `defaultdict`).
- **Recommended fix:** Use TTL-based eviction (like `auth.py` does) or switch to Redis-backed rate limiting.
- **Severity:** **Medium**

---

## Finding #23 — API v2 Rate Limiting is In-Memory Only
- **File:** `apps/api_v2/auth.py`, lines 22-23, 69-83
- **Current behavior:**
  ```python
  _rate_buckets: dict[str, tuple[int, float]] = {}
  ```
  Rate limits are per-process, in-memory. With multiple instances/workers, limits are not shared, effectively multiplying the actual rate limit by the number of instances.
- **Recommended fix:** Use Redis-backed rate limiting for distributed deployments.
- **Severity:** **Medium**

---

## Finding #24 — `CreateApplicationBody.decision` Not Constrained
- **File:** `apps/api/user.py`, lines 154-156
- **Current behavior:**
  ```python
  class CreateApplicationBody(BaseModel):
      job_id: str
      decision: str  # ACCEPT | REJECT
  ```
  The `decision` field accepts any string. Only "ACCEPT" is handled explicitly (line 169); everything else falls through to the rejection path silently.
- **Recommended fix:** Use `Literal["ACCEPT", "REJECT"]` or a Pydantic validator.
- **Severity:** **Low**

---

## Finding #25 — `SnoozeBody.hours` Has No Upper Bound
- **File:** `apps/api/user.py`, lines 370-371
- **Current behavior:**
  ```python
  class SnoozeBody(BaseModel):
      hours: int = 24
  ```
  No upper limit. A user could snooze for `hours=999999999`, effectively hiding the application forever.
- **Recommended fix:** Add `Field(ge=1, le=720)` (max 30 days).
- **Severity:** **Low**

---

## Finding #26 — `job_id` Not Validated as UUID in Several Endpoints
- **File:** `apps/api/user.py`, line 164 (`create_application`)
- **Current behavior:** The `body.job_id` is used directly in SQL queries without UUID validation. Compare with `undo_application` (line 254) which does validate.
- **Recommended fix:** Add `validate_uuid(body.job_id, "job_id")` before use.
- **Severity:** **Low**

---

## Finding #27 — Placeholder Webhook Secrets in Config Defaults
- **File:** `packages/shared/config.py`, lines 148, 165
- **Current behavior:**
  ```python
  stripe_webhook_secret: str = "dev-placeholder-webhook-secret"
  webhook_signing_secret: str = "dev-placeholder-webhook-signing"
  ```
  These placeholder values could end up in production if environment variables are misconfigured. `validate_critical()` only checks if `stripe_webhook_secret` is empty when `stripe_secret_key` is set.
- **Recommended fix:** Treat the placeholder strings as equivalent to empty in `validate_critical()`.
- **Severity:** **High**

---

## Finding #28 — SSO Session Token Secret Default Empty
- **File:** `packages/shared/config.py`, line 187
- **Current behavior:**
  ```python
  sso_session_secret: str = ""
  ```
  The SSO session secret defaults to empty string and is explicitly excluded from the `validate_critical()` check (lines 317-319, commented out). If SSO is enabled for an ENTERPRISE tenant without this secret being set, tokens would be signed with an empty key.
- **Recommended fix:** If SSO is enabled on any tenant, require `sso_session_secret` to be set.
- **Severity:** **High**

---

## Finding #29 — `get_client_ip` Trusts X-Forwarded-For Without Validation
- **File:** `packages/shared/middleware.py`, lines 162-178
- **Current behavior:**
  ```python
  def get_client_ip(request: Request) -> str:
      forwarded = request.headers.get("x-forwarded-for")
      if forwarded:
          return forwarded.split(",")[0].strip()
  ```
  `X-Forwarded-For` is easily spoofable. Rate limits, IP allowlists, and audit logs all use this function. An attacker can bypass IP-based rate limiting by setting a fake `X-Forwarded-For` header.
- **Recommended fix:** Use a configurable "trusted proxy" count. Only trust the Nth-from-right entry in the XFF chain (where N = number of trusted proxies).
- **Severity:** **High**

---

## Finding #30 — CSRF Exempt Paths Are Too Broad
- **File:** `packages/shared/middleware.py`, lines 74-89
- **Current behavior:**
  ```python
  EXEMPT_PATHS = [
      "/health", "/healthz",
      "/auth/magic-link", "/auth/",
      "/api/v2/webhook", "/billing/webhook",
      "/sso/saml/acs", "/og/",
      "/profile", "/profile/resume", "/profile/avatar",
      "/me/skills", "/me/work-style",
      "/ai/",
  ]
  ```
  `/profile`, `/profile/resume`, `/profile/avatar`, `/me/skills`, `/me/work-style`, and the entire `/ai/` prefix are exempt from CSRF. These are state-changing POST/PATCH/DELETE endpoints that modify user data.
- **Recommended fix:** Only exempt truly public/webhook endpoints. Remove `/profile`, `/me/skills`, `/me/work-style`, and `/ai/` from the CSRF exempt list.
- **Severity:** **High**

---

## Finding #31 — CORS Allows All Methods Including DELETE
- **File:** `apps/api/main.py`, lines 304-312
- **Current behavior:**
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
  ```
  Allowing DELETE in CORS increases the attack surface for CSRF-like attacks, especially for endpoints without CSRF protection.
- **Recommended fix:** Only allow the methods actually needed by the frontend.
- **Severity:** **Low**

---

## Finding #32 — Error Handler Leaks Exception Details in Non-Prod
- **File:** `apps/api/main.py`, lines 662-683
- **Current behavior:**
  ```python
  if _settings.env == Environment.LOCAL:
      msg = f"Internal Server Error: {str(exc)}"
  else:
      msg = "Internal Server Error"
  ```
  Good for prod, but `Environment.LOCAL` is the default (line 37 in config.py). If the env var is not set, full stack traces are returned. Additionally, the `STAGING` environment gets the generic message, which is correct.
- **Recommended fix:** This is acceptable but worth noting that `LOCAL` is the default env.
- **Severity:** **Low**

---

## Finding #33 — Email Address Logged in Multiple Places
- **File:** `apps/api/auth.py`, lines 133, 146, 162, 196
- **Current behavior:**
  ```python
  logger.info("[MAGIC_LINK] Starting generation", extra={"email": email, ...})
  logger.info("[MAGIC_LINK] Creating new user", extra={"email": email})
  ```
  Email addresses (PII) are logged in structured log fields across the magic link flow. These logs may be sent to third-party logging services.
- **Recommended fix:** Hash or truncate emails in logs: `email[:3] + "***@" + email.split("@")[1]`.
- **Severity:** **Medium**

---

## Finding #34 — User ID Logged as PII in Profile Endpoints
- **File:** `apps/api/user.py`, line 634
- **Current behavior:**
  ```python
  incr("profile.update.rate_limited", {"user_id": ctx.user_id})
  ```
  User IDs are sent as metric tags. Depending on the metrics backend, these could be stored indefinitely and constitute PII tracking.
- **Recommended fix:** Use hashed user IDs in metric tags, or omit them.
- **Severity:** **Low**

---

## Finding #35 — Sentry DSN Logged in Plaintext
- **File:** `apps/api/main.py`, line 91
- **Current behavior:**
  ```python
  logger.info(f"Sentry initialized for {_settings.env.value}")
  ```
  While the DSN itself isn't logged here, the `sentry_sdk.init(dsn=_settings.sentry_dsn, ...)` is called with the DSN. The DSN contains a project key — if any debug logging captures it, it could be exposed.
- **Recommended fix:** Ensure Sentry DSN is never logged. This is currently OK but fragile.
- **Severity:** **Low**

---

## Finding #36 — No Brute-Force Protection on TOTP Verification
- **File:** `apps/api/mfa.py`, lines 125-135 and `packages/backend/domain/mfa.py`, lines 298-334
- **Current behavior:** The TOTP challenge endpoint (`/auth/mfa/totp/challenge`) has no rate limiting. An attacker can try all 1,000,000 6-digit codes (or 10,000 with windowed verification).
- **Recommended fix:** Rate limit to 5 attempts per 5 minutes per user. Lock account after 10 consecutive failures.
- **Severity:** **High**

---

## Finding #37 — Recovery Code Verification Has No Rate Limiting
- **File:** `apps/api/mfa.py`, lines 138-148
- **Current behavior:** No rate limit on recovery code verification. With only 8 recovery codes of 8 hex chars each (4 bytes = ~4 billion possibilities), this is less critical than TOTP, but brute-force is still a concern.
- **Recommended fix:** Rate limit recovery code attempts (3 per 15 minutes).
- **Severity:** **Medium**

---

## Finding #38 — Database Connection Pool Allows Degraded Mode
- **File:** `apps/api/main.py`, lines 566-572
- **Current behavior:**
  ```python
  # Do not raise RuntimeError, allow app to start in degraded mode
  # raise RuntimeError("Failed to initialize database pool")
  ```
  After 3 failed DB connection attempts, the app starts without a database. All endpoints will fail with 503. This is intentional for zero-downtime deploys but means a misconfigured app serves errors instead of failing fast.
- **Recommended fix:** In production, fail startup. In staging, allow degraded mode.
- **Severity:** **Medium**

---

## Finding #39 — DB SSL Context Hardcoded to None
- **File:** `apps/api/main.py`, lines 619-624
- **Current behavior:**
  ```python
  @staticmethod
  def _get_ssl_config(settings: Any) -> Any:
      return None
  ```
  Despite the `db_ssl_ca_cert_path` setting existing in config (line 101-102), it is never used. SSL verification is delegated entirely to the DSN's `sslmode=require`, which does NOT verify the server certificate (no MITM protection).
- **Recommended fix:** When `db_ssl_ca_cert_path` is set, create an `ssl.SSLContext` with `load_verify_locations()` and pass it to the pool.
- **Severity:** **Medium**

---

## Finding #40 — Healthz Endpoint Exposes Internal Metrics
- **File:** `apps/api/main.py`, lines 1258-1286
- **Current behavior:**
  ```python
  return {
      "status": status,
      "env": s.env.value,
      "db": "ok" if db_ok else "unreachable",
      "circuit_breakers": cb_status,
      "metrics": metrics_dump(),
  }
  ```
  The `/healthz` endpoint exposes environment name, database connectivity, circuit breaker states, and full metrics dump. This requires authentication (`Depends(get_pool)`) but not admin auth — any authenticated user can see infrastructure details.
- **Recommended fix:** Restrict `/healthz` to system admins or internal-only networks. Serve a lightweight public health check on `/health`.
- **Severity:** **Medium**

---

## Finding #41 — Slack Integration Stores Access Token in Database
- **File:** `apps/api/integrations.py`, lines 63-78
- **Current behavior:**
  ```python
  class SlackConnectRequest(BaseModel):
      team_id: str
      access_token: str
      bot_user_id: str | None = None
  ```
  The Slack OAuth access token is accepted directly and stored in the database. It should be encrypted at rest.
- **Recommended fix:** Encrypt OAuth tokens using application-level encryption before storage.
- **Severity:** **High**

---

## Finding #42 — Notion Access Token Stored in Plaintext
- **File:** `apps/api/integrations.py`, lines 153-156, 176-180
- **Current behavior:** Same pattern as Slack — Notion access tokens stored directly in database without encryption.
- **Recommended fix:** Encrypt at rest using envelope encryption.
- **Severity:** **High**

---

## Finding #43 — Google Drive Tokens Stored in Plaintext
- **File:** `apps/api/integrations.py`, lines 276-278, 293-299
- **Current behavior:** Google Drive access tokens and refresh tokens stored directly in database.
- **Recommended fix:** Encrypt at rest.
- **Severity:** **High**

---

## Finding #44 — SSO OIDC Client Secret Stored in Config Model
- **File:** `apps/api/sso.py`, lines 60-66
- **Current behavior:**
  ```python
  class SSOConfigRequest(BaseModel):
      oidc_client_secret: str = ""
  ```
  The OIDC client secret is accepted in API requests and stored alongside other SSO config. No encryption at rest.
- **Recommended fix:** Encrypt secrets before storage.
- **Severity:** **High**

---

## Finding #45 — SAML Response Parsed Without Certificate on First Pass
- **File:** `apps/api/sso.py`, lines 121-125
- **Current behavior:**
  ```python
  if not tenant_id:
      claims = parse_saml_response(str(saml_response), "")
      if claims and claims.get("email"):
          domain = claims["email"].split("@")[-1]
  ```
  The first parse of the SAML response uses an empty certificate string. This means the response is parsed without signature verification to extract the email domain for tenant lookup. An attacker could craft a SAML response with any email to trigger tenant auto-discovery.
- **Recommended fix:** Never parse SAML without certificate verification. Use RelayState or a separate tenant lookup mechanism.
- **Severity:** **Critical**

---

## Finding #46 — API Key Displayed Once But Persisted in Response
- **File:** `apps/api/developer.py`, line 104
- **Current behavior:**
  ```python
  return {**dict(row), "raw_key": raw_key}
  ```
  The raw API key is returned in the response. This is the intended "show once" pattern, but ensure response logging doesn't capture it.
- **Recommended fix:** Verify that structured logging or Sentry doesn't capture response bodies for this endpoint.
- **Severity:** **Low**

---

## Finding #47 — Webhook Secret Returned in Response
- **File:** `apps/api/developer.py`, line 169 and `apps/api_v2/router.py`, line 308
- **Current behavior:**
  ```python
  return {**dict(row), "secret": secret}
  ```
  Same "show once" pattern as API keys. Acceptable but must ensure no response logging.
- **Severity:** **Low**

---

## Finding #48 — `SnoozeBody` Default Instance Shared Across Requests
- **File:** `apps/api/user.py`, line 377
- **Current behavior:**
  ```python
  body: SnoozeBody = SnoozeBody(),
  ```
  The default `SnoozeBody()` is a single shared instance. In Python/FastAPI with Pydantic, this is generally safe since Pydantic models are immutable, but it's a known anti-pattern.
- **Recommended fix:** Use `Body(default_factory=SnoozeBody)` or `None` with fallback.
- **Severity:** **Low**

---

## Finding #49 — Bulk Campaign Query Uses Dynamic String Concatenation
- **File:** `apps/api/bulk.py`, lines 148-159
- **Current behavior:**
  ```python
  query = """SELECT id FROM public.jobs WHERE (tenant_id = $1 OR tenant_id IS NULL)"""
  if title_filter:
      params.append(f"%{title_filter}%")
      query += f" AND title ILIKE ${len(params)}"
  ```
  While the values are parameterized (safe from SQL injection), the dynamic query construction pattern is fragile and could introduce injection if parameter indexing goes wrong.
- **Recommended fix:** Use a query builder or the null-check pattern (like audit log queries in admin.py which use `$N::text IS NULL OR ...`).
- **Severity:** **Low**

---

## Finding #50 — AI Endpoints Expose Internal Errors
- **File:** `apps/api/ai.py`, lines 288, 484, 1048, 1098
- **Current behavior:**
  ```python
  raise HTTPException(status_code=500, detail=f"AI generation failed: {exc}")
  raise HTTPException(status_code=500, detail=f"AI scoring failed: {exc}")
  ```
  Full exception details from LLM calls (which may include API keys, model names, request IDs) are returned to clients.
- **Recommended fix:** Return generic "AI service temporarily unavailable" messages.
- **Severity:** **Medium**

---

## Finding #51 — Match Feedback Summary Endpoint Has No Auth
- **File:** `apps/api/ai.py`, lines 1437-1461
- **Current behavior:**
  ```python
  @router.get("/match-feedback/summary", response_model=MatchFeedbackSummaryResponse)
  async def get_match_feedback_summary(
      days: int = 30,
      tenant_id: str | None = Depends(_get_tenant_id),
      db: asyncpg.Pool = Depends(_get_pool),
  ```
  No `user_id` dependency. Any authenticated user (via tenant context) can see aggregate feedback, which may be acceptable. However, the `_get_tenant_id` dependency may be `None`, allowing cross-tenant data access.
- **Recommended fix:** Ensure tenant_id is required (not None) for aggregate queries.
- **Severity:** **Medium**

---

## Finding #52 — Job Feedback Stats Endpoint Missing Auth
- **File:** `apps/api/ai.py`, lines 1464-1486
- **Current behavior:**
  ```python
  @router.get("/match-feedback/job/{job_id}/stats")
  async def get_job_feedback_stats(
      job_id: str,
      db: asyncpg.Pool = Depends(_get_pool),
  ):
  ```
  No authentication at all. Anyone with the database pool (which always resolves) can query feedback stats for any job.
- **Recommended fix:** Add `user_id: str = Depends(_get_user_id)`.
- **Severity:** **High**

---

## Finding #53 — LLM Metrics Endpoints Not Restricted to Admin
- **File:** `apps/api/ai.py`, lines 1494-1567
- **Current behavior:** `/ai/llm/metrics`, `/ai/llm/health`, `/ai/llm/semantic-cache/stats` only require basic authentication. These expose internal infrastructure details (model names, latency, error rates, cache sizes) to any authenticated user.
- **Recommended fix:** Restrict to admin role or system admin.
- **Severity:** **Medium**

---

## Finding #54 — No Content-Type Validation on SAML ACS POST
- **File:** `apps/api/sso.py`, lines 91-96
- **Current behavior:** The SAML ACS endpoint accepts the SAML response from form data without validating `Content-Type`. While FastAPI/Starlette handle form parsing, explicit content type enforcement is a defense-in-depth measure.
- **Severity:** **Low**

---

## Finding #55 — Audit Log Query Uses ILIKE with User-Supplied Pattern
- **File:** `apps/api/admin.py`, line 413
- **Current behavior:**
  ```python
  f"%{action}%" if action else None,
  ```
  The `action` parameter is wrapped in wildcards for ILIKE. While parameterized, special LIKE/ILIKE characters (`%`, `_`) in the user input are not escaped, allowing pattern manipulation.
- **Recommended fix:** Escape `%` and `_` in the user input: `action.replace('%', '\\%').replace('_', '\\_')`.
- **Severity:** **Low**

---

## Finding #56 — `validate_critical()` Uses `sys.exit(1)` Instead of Exception
- **File:** `packages/shared/config.py`, line 353
- **Current behavior:**
  ```python
  if missing:
      logger.critical(...)
      sys.exit(1)
  ```
  Using `sys.exit()` prevents graceful shutdown and makes testing difficult.
- **Recommended fix:** Raise `RuntimeError` or a custom `ConfigurationError`.
- **Severity:** **Low**

---

## Finding #57 — JWT Only Uses HS256 (Symmetric Algorithm)
- **File:** `apps/api/main.py`, line 704 and `apps/api/auth.py`, line 194
- **Current behavior:**
  ```python
  payload = pyjwt.decode(token, s.jwt_secret, algorithms=["HS256"], audience="authenticated")
  token = jwt.encode(payload, secret, algorithm="HS256")
  ```
  HS256 requires the signing secret to be shared with any service that validates tokens. If Supabase or any third party also validates tokens, the secret must be shared, increasing exposure.
- **Recommended fix:** Consider RS256 (asymmetric) for production, especially if tokens are validated by multiple services.
- **Severity:** **Medium**

---

## Finding #58 — No Token Revocation Mechanism for JWTs
- **File:** `apps/api/main.py`, lines 691-711
- **Current behavior:** JWT tokens are validated purely by signature and expiration. There is no token blocklist/revocation mechanism. If a JWT is compromised, it remains valid until expiration.
- **Recommended fix:** Implement a Redis-backed token blocklist, or use short-lived JWTs with refresh tokens.
- **Severity:** **Medium**

---

## Finding #59 — File Upload Missing Magic Byte Validation
- **File:** `apps/api/user.py`, lines 796-797 and `apps/api/main.py`, lines 1069-1070
- **Current behavior:**
  ```python
  if file.content_type not in ("application/pdf", "application/octet-stream"):
      raise HTTPException(status_code=400, detail="Only PDF files are accepted")
  ```
  Only the `Content-Type` header is checked. An attacker can upload any file type (e.g., executable, HTML with XSS) with a faked `Content-Type: application/pdf`.
- **Recommended fix:** Read the first few bytes and verify the PDF magic number (`%PDF`). For avatar images, verify image magic bytes.
- **Severity:** **High**

---

## Finding #60 — Avatar Upload Missing Magic Byte Validation
- **File:** `apps/api/user.py`, lines 859-866
- **Current behavior:** Only `Content-Type` header is checked for avatar uploads. No magic byte validation.
- **Recommended fix:** Validate image magic bytes (PNG: `\x89PNG`, JPEG: `\xFF\xD8\xFF`, WebP: `RIFF...WEBP`).
- **Severity:** **Medium**

---

## Finding #61 — Admin Job Sync Endpoints in User Router
- **File:** `apps/api/user.py`, lines 920-950
- **Current behavior:**
  ```python
  @router.get("/admin/jobs/sync/status")
  async def get_job_sync_status(
      ctx: TenantContext = Depends(_get_tenant_ctx),
  ```
  Admin endpoints are defined in the user router instead of the admin router. The `ctx.is_admin` check is correct, but this is a structural concern — it's easy to miss these endpoints during security reviews.
- **Recommended fix:** Move admin endpoints to `admin.py` or a dedicated admin router.
- **Severity:** **Low**

---

## Finding #62 — `application/octet-stream` Accepted for Resume Upload
- **File:** `apps/api/main.py`, line 1069
- **Current behavior:**
  ```python
  if file.content_type not in ("application/pdf", "application/octet-stream"):
  ```
  Accepting `application/octet-stream` means any file type can be uploaded if the browser/client doesn't set a specific content type.
- **Recommended fix:** Only accept `application/pdf`. Validate magic bytes.
- **Severity:** **Medium**

---

## Finding #63 — S3 Signed URL Uses SHA-1 (Deprecated)
- **File:** `packages/shared/storage.py`, lines 214-216
- **Current behavior:**
  ```python
  signature = base64.b64encode(
      hmac.new(self.secret_key.encode(), string_to_sign.encode(), hashlib.sha1).digest()
  )
  ```
  SHA-1 is deprecated for cryptographic use. The signed URL implementation uses V2 signing (SHA-1) instead of V4 signing (SHA-256) for the pre-signed URL generation.
- **Recommended fix:** Use V4 signing (already used for uploads in the same class).
- **Severity:** **Medium**

---

## Finding #64 — HSTS Only Set in Production
- **File:** `packages/shared/middleware.py`, lines 212-215
- **Current behavior:**
  ```python
  if s.env.value == "prod":
      response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
  ```
  HSTS is not set in staging, which means staging environments could be subject to protocol downgrade attacks.
- **Recommended fix:** Enable HSTS for staging as well.
- **Severity:** **Low**

---

## Finding #65 — No `preload` Directive in HSTS Header
- **File:** `packages/shared/middleware.py`, line 214
- **Current behavior:**
  ```python
  "max-age=31536000; includeSubDomains"
  ```
  Missing `preload` directive means browsers won't add the domain to the HSTS preload list.
- **Recommended fix:** Add `; preload` and submit to the HSTS preload list.
- **Severity:** **Low**

---

## Finding #66 — CSP Policy Is Minimal
- **File:** `packages/shared/middleware.py`, lines 202-204
- **Current behavior:**
  ```python
  response.headers.setdefault(
      "Content-Security-Policy",
      "default-src 'self'; frame-ancestors 'none'; object-src 'none'",
  )
  ```
  The CSP is minimal (which is good for an API). However, `script-src` and `style-src` are not explicitly restricted, inheriting from `default-src 'self'`, which could allow script injection if the API ever serves HTML.
- **Recommended fix:** Add `script-src 'none'; style-src 'none'` for the API.
- **Severity:** **Low**

---

## Finding #67 — Data Export Stream May Leak Other Users' Application Data
- **File:** `apps/api/export.py`, lines 84-93
- **Current behavior:**
  ```python
  rows = await ApplicationRepo.list_for_tenant(
      conn, ctx.tenant_id, limit=batch_size, offset=offset,
  )
  for row in rows:
      if str(row.get("user_id")) != ctx.user_id:
          continue
  ```
  The query fetches ALL tenant applications and filters client-side. This is inefficient and could expose timing information about the number of applications in the tenant.
- **Recommended fix:** Filter by `user_id` in the SQL query directly.
- **Severity:** **Medium**

---

## Finding #68 — No Permissions-Policy Header
- **File:** `packages/shared/middleware.py`
- **Current behavior:** No `Permissions-Policy` header is set. While less critical for an API, it's a defense-in-depth measure.
- **Recommended fix:** Add `Permissions-Policy: camera=(), microphone=(), geolocation=()`.
- **Severity:** **Low**

---

## Finding #69 — Zapier Webhook URL Not Validated
- **File:** `apps/api/integrations.py`, lines 383-407
- **Current behavior:**
  ```python
  class ZapierSubscribeRequest(BaseModel):
      webhook_url: str
  ```
  Same SSRF risk as Finding #19 — Zapier webhook URLs are not validated.
- **Recommended fix:** Validate against internal/reserved IPs.
- **Severity:** **Medium**

---

## Finding #70 — Google Drive Backup Content Has No Size Limit
- **File:** `apps/api/integrations.py`, lines 325-351
- **Current behavior:**
  ```python
  class GoogleDriveBackupRequest(BaseModel):
      file_name: str = "resume.pdf"
      content_base64: str
  ```
  The `content_base64` field has no size limit. Base64 encoding inflates size by ~33%, and a large payload could cause memory exhaustion.
- **Recommended fix:** Add `max_length` constraint (e.g., 20MB base64 encoded).
- **Severity:** **Medium**

---

## Finding #71 — Profile Completeness Score Unbounded
- **File:** `apps/api/main.py`, lines 914-921 and 998-1003
- **Current behavior:**
  ```python
  await conn.execute(
      """UPDATE public.users SET profile_completeness =
         COALESCE(profile_completeness, 0) +
         CASE WHEN ... THEN 20 ELSE 10 END
         WHERE id = $1""",
  ```
  The profile completeness score is only ever incremented, never capped. Repeated calls could push it above 100.
- **Recommended fix:** Cap at 100: `LEAST(COALESCE(profile_completeness, 0) + 20, 100)`.
- **Severity:** **Low**

---

---

## Summary by Severity

| Severity | Count | Finding IDs |
|----------|-------|-------------|
| **Critical** | 6 | #1, #4, #5, #8, #10, #45 |
| **High** | 15 | #7, #9, #12, #14, #15, #16, #18, #19, #27, #28, #29, #30, #36, #41-44, #52, #59 |
| **Medium** | 22 | #2, #3, #11, #13, #17, #20, #22, #23, #33, #37, #38, #39, #40, #50, #51, #53, #57, #58, #60, #62, #63, #67, #69, #70 |
| **Low** | 18 | #6, #21, #24, #25, #26, #31, #32, #34, #35, #46, #47, #48, #49, #54, #55, #56, #61, #64, #65, #66, #68, #71 |

---

## Top 5 Immediate Actions

1. **Enforce single-use magic link tokens** (Finding #1) — Prevents token replay attacks.
2. **Add MFA enforcement to login flow** (Finding #4) — TOTP is implemented but never required.
3. **Authenticate the storage file serving endpoint** (Finding #8) — Resumes are publicly downloadable.
4. **Fix SAML response parsing without certificate** (Finding #45) — SSO authentication bypass risk.
5. **Add admin check to CCPA processing endpoint** (Finding #10) — Any user can process deletion requests.
