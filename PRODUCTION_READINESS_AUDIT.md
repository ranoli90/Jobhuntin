# Production Readiness Audit — JobHuntin (Sorce)

**Date:** 2026-02-28  
**Auditor:** Automated Cloud Agent  
**Scope:** 10 areas — Billing, Email, Analytics, Mobile, Extension, Admin, SEO, Legal, Error Pages, Multi-tenancy

---

## Summary

| Area | Findings | Critical | High | Medium | Low |
|------|----------|----------|------|--------|-----|
| 1. Billing / Stripe | 12 | 2 | 4 | 4 | 2 |
| 2. Email / Transactional | 8 | 1 | 3 | 3 | 1 |
| 3. Analytics / Tracking | 7 | 0 | 3 | 3 | 1 |
| 4. Mobile App | 9 | 1 | 3 | 3 | 2 |
| 5. Extension | 7 | 1 | 2 | 3 | 1 |
| 6. Admin Dashboard | 6 | 1 | 2 | 2 | 1 |
| 7. SEO | 5 | 0 | 1 | 3 | 1 |
| 8. Legal Compliance | 7 | 2 | 2 | 2 | 1 |
| 9. 404/Maintenance/Offline | 4 | 0 | 1 | 2 | 1 |
| 10. Team / Multi-user | 6 | 0 | 3 | 2 | 1 |
| **Total** | **71** | **8** | **24** | **27** | **12** |

---

## 1. Billing / Stripe Integration

### FINDING B-01: No idempotency key on Stripe Checkout Session creation
- **File:** `apps/api/billing.py` lines 171–192
- **Severity:** CRITICAL
- **Issue:** `stripe.checkout.Session.create()` is called without an `idempotency_key`. If a network timeout occurs and the client retries, duplicate checkout sessions may be created, leading to double charges.
- **Fix:** Add `idempotency_key=f"{ctx.tenant_id}:{ctx.user_id}:{body.billing_period}:{int(time.time()//60)}"` to the `Session.create()` call.

### FINDING B-02: Webhook `stripe_signature` header defaults to `None`
- **File:** `apps/api/billing.py` line 257
- **Severity:** CRITICAL
- **Issue:** `stripe_signature: str = Header(None)` means if the header is absent, `None` is passed to `construct_event()`. While Stripe SDK will reject it, this should be a 400 immediately rather than relying on exception handling. An attacker could send unsigned payloads and the error path on line 270–273 uses broad `except Exception` with string matching `"signature" in str(e).lower()` which is fragile.
- **Fix:** Make `stripe_signature` required: `stripe_signature: str = Header(...)`. Return 400 if missing. Replace string-matching with `except stripe.error.SignatureVerificationError`.

### FINDING B-03: No webhook event deduplication
- **File:** `apps/api/billing.py` lines 276–289
- **Severity:** HIGH
- **Issue:** Stripe may deliver the same webhook event multiple times. The handler processes every event without checking if `event["id"]` was already processed. This could lead to duplicate plan changes or double seat allocations.
- **Fix:** Store processed `event["id"]` values in a `webhook_events_processed` table with a UNIQUE constraint and skip duplicates.

### FINDING B-04: Race condition in `ensure_stripe_customer`
- **File:** `backend/domain/billing.py` lines 31–66
- **Severity:** HIGH
- **Issue:** Between checking if a customer exists (line 37–41) and inserting (line 56–65), two concurrent requests for the same tenant could both pass the check and create two Stripe customers. The `ON CONFLICT` handles the DB upsert but leaves an orphaned Stripe customer object.
- **Fix:** Use a database advisory lock on tenant_id or SELECT ... FOR UPDATE before the check.

### FINDING B-05: No trial period handling in checkout
- **File:** `apps/api/billing.py` lines 149–192, `apps/web/src/pages/Pricing.tsx`
- **Severity:** HIGH
- **Issue:** The Pricing page CTA says "Start Free 7-Day Trial" but the checkout session creation on line 172 does not set `subscription_data.trial_period_days=7` or `trial_end`. Users clicking "Start Free 7-Day Trial" are immediately charged.
- **Fix:** Add `subscription_data={"trial_period_days": 7}` to the `Session.create()` call. Handle `customer.subscription.trial_will_end` webhook.

### FINDING B-06: Pricing page shows $29/mo but plan config is not anchored to price
- **File:** `apps/web/src/pages/Pricing.tsx` line 234, `backend/domain/plans.py`
- **Severity:** HIGH
- **Issue:** The pricing page hardcodes "$29" monthly and "$24" annual but these are not derived from Stripe or any shared config. If the Stripe price changes, the UI will be out of sync, misleading customers.
- **Fix:** Fetch prices from a `/billing/prices` endpoint or a shared config that syncs with Stripe price IDs.

### FINDING B-07: No invoice display or billing history
- **File:** `apps/web/src/hooks/useBilling.ts`
- **Severity:** MEDIUM
- **Issue:** The billing hook and UI only show plan status and usage. There is no endpoint or UI to view past invoices, receipts, or payment history. Users have no way to access tax invoices without going to Stripe portal.
- **Fix:** Either surface `manageBilling()` prominently (Stripe portal has invoices) or add a `/billing/invoices` endpoint that returns `stripe.Invoice.list(customer=...)`.

### FINDING B-08: Error detail leaks Stripe internals to client
- **File:** `apps/api/billing.py` lines 191–192, 228–229, 250–251
- **Severity:** MEDIUM
- **Issue:** `detail=f"Payment provider error: {str(e)}"` exposes internal Stripe error messages (including API keys in some error contexts) directly to the client.
- **Fix:** Log the full error server-side and return a generic message: `detail="Payment processing failed. Please try again."`.

### FINDING B-09: Team checkout hardcodes 3 seats
- **File:** `apps/api/billing.py` line 217
- **Severity:** MEDIUM
- **Issue:** `"quantity": 3` is hardcoded. There's no way for the user to choose how many seats they want during checkout.
- **Fix:** Accept `seats` in the request body and validate it's >= minimum.

### FINDING B-10: No cancellation/downgrade confirmation flow
- **File:** `apps/web/src/hooks/useBilling.ts`
- **Severity:** MEDIUM
- **Issue:** The billing hook has `manageBilling()` (Stripe portal) but no explicit cancellation flow with confirmation, data retention warnings, or "are you sure" UI. Users might accidentally cancel.
- **Fix:** Add a cancellation confirmation modal explaining what they'll lose, with a reason picker for churn analysis.

### FINDING B-11: `past_due` still maps to PRO plan access
- **File:** `backend/domain/billing.py` line 22
- **Severity:** LOW
- **Issue:** `SUBSCRIPTION_STATUS_MAP` maps `past_due` to `"PRO"`, meaning users with failed payments retain full access indefinitely until Stripe marks them `canceled`.
- **Fix:** Add grace period logic — after N days of `past_due`, downgrade to FREE or restrict features.

### FINDING B-12: Circuit breaker stats manipulation is not thread-safe
- **File:** `backend/domain/stripe_client.py` lines 86–105
- **Severity:** LOW
- **Issue:** `self._cb.stats.successes += 1` and failure counter increments are not atomic. Under concurrent requests this could lead to inaccurate circuit breaker state.
- **Fix:** Use `threading.Lock` or atomic operations for counter updates.

---

## 2. Email / Transactional Emails

### FINDING E-01: Magic link token sent as URL query parameter
- **File:** `apps/api/auth.py` line 202
- **Severity:** CRITICAL
- **Issue:** The JWT token is appended as a query parameter (`?token=...`). Query parameters are logged in web server access logs, browser history, referrer headers, and analytics platforms. This is a token leakage vector.
- **Fix:** Use a short-lived opaque code stored in the database that exchanges for a session, or use a POST-based token consumption flow.

### FINDING E-02: No SPF/DKIM setup documentation or verification
- **File:** Email configuration across codebase
- **Severity:** HIGH
- **Issue:** While Resend handles sending, there's no code or documentation verifying that SPF/DKIM/DMARC records are properly configured for the sending domain. The `email_from` setting in `shared/config.py` may use a domain without proper email authentication, causing emails to land in spam.
- **Fix:** Add a startup health check that verifies Resend domain status. Document required DNS records in `docs/email-setup.md`.

### FINDING E-03: Only one email template exists (magic link)
- **File:** `templates/emails/magic_link.html`
- **Severity:** HIGH
- **Issue:** The only email template is for magic links. There are no templates for: welcome email, application status updates, weekly digest, team invite, billing receipts, account deletion confirmation, or trial expiration warnings.
- **Fix:** Create a template system with base layout and templates for each transactional email type.

### FINDING E-04: No email unsubscribe mechanism
- **File:** `templates/emails/magic_link.html`, `apps/api/auth.py`
- **Severity:** HIGH
- **Issue:** Transactional emails don't include an unsubscribe link or `List-Unsubscribe` header. While magic links are transactional, future notification emails (digests, alerts) will need this. CAN-SPAM and GDPR require it for marketing communications.
- **Fix:** Add `List-Unsubscribe` header to all non-critical emails. Add unsubscribe preferences to user settings.

### FINDING E-05: Magic link email logs recipient email in plaintext
- **File:** `apps/api/auth.py` lines 332–360
- **Severity:** MEDIUM
- **Issue:** The email address is logged in multiple `logger.info` calls with `extra={"email": email}`. If logs are shipped to a third-party service, this leaks PII.
- **Fix:** Hash or truncate email in logs: `email_masked = email[:3] + "***@" + email.split("@")[1]`.

### FINDING E-06: Email validation only uses Pydantic `EmailStr`
- **File:** `apps/api/auth.py` line 49
- **Severity:** MEDIUM
- **Issue:** `EmailStr` does basic format validation but doesn't check for disposable email domains, typos (gmial.com), or MX record existence. Users can sign up with throwaway emails.
- **Fix:** Add disposable email domain blocklist and optional MX record verification.

### FINDING E-07: Magic link `X-Priority: 1` header is aggressive
- **File:** `apps/api/auth.py` lines 321–324
- **Severity:** MEDIUM
- **Issue:** Setting `X-Priority: 1` and `X-MSMail-Priority: High` on every magic link email may trigger spam filters and is not appropriate for routine sign-in emails.
- **Fix:** Remove priority headers from magic link emails. Reserve high priority for genuinely urgent communications only.

### FINDING E-08: Team invite email not implemented
- **File:** `backend/domain/teams.py` lines 33–84
- **Severity:** LOW
- **Issue:** `create_invite()` generates a token but doesn't send an email to the invitee. The invite token is returned in the API response but there's no automated notification.
- **Fix:** Send an invite email with a deep link containing the token after creating the invite.

---

## 3. Analytics / Tracking

### FINDING A-01: Google Analytics ID hardcoded as fallback
- **File:** `apps/web/src/hooks/useGoogleAnalytics.ts` line 14
- **Severity:** HIGH
- **Issue:** `const gaId = config.analytics.gaId || 'G-P1QLYH3M13';` hardcodes a GA measurement ID as fallback. If the env var is not set, this ID is used. If this is a development/test property, production data goes to the wrong stream. If it's production, the ID is exposed in source code.
- **Fix:** Remove the hardcoded fallback. Only initialize GA if the env var is explicitly set.

### FINDING A-02: No Sentry or structured error tracking
- **File:** `apps/web/src/components/ErrorBoundary.tsx` lines 51–57
- **Severity:** HIGH
- **Issue:** The `_reportError` method just does `console.error('Error reported:', errorDetails)`. The comment says "Here you could integrate with error reporting services like Sentry" but it's never been implemented. Client-side errors are silently lost in production.
- **Fix:** Integrate Sentry SDK (`@sentry/react`) with proper DSN, source maps upload, and user context.

### FINDING A-03: No server-side error tracking (Sentry/Datadog)
- **File:** `apps/api/main.py`, `packages/shared/monitoring_config.py`
- **Severity:** HIGH
- **Issue:** While there are references to Sentry DSN in config, actual Sentry initialization code sends errors to `console.error` only. Backend exceptions in production are only captured in application logs, not in a centralized error tracking system.
- **Fix:** Initialize `sentry_sdk` with FastAPI integration in `apps/api/main.py` startup.

### FINDING A-04: No event tracking on key conversion actions
- **File:** `apps/web/src/hooks/useBilling.ts`, `apps/web/src/pages/Pricing.tsx`
- **Severity:** MEDIUM
- **Issue:** Critical funnel events are not tracked: pricing page view, plan comparison toggle, checkout initiation, checkout completion, upgrade success. The `useGoogleAnalytics` hook only tracks page views, not custom events.
- **Fix:** Add `gtag('event', ...)` calls for: `view_pricing`, `toggle_annual`, `begin_checkout`, `purchase`, `upgrade_complete`.

### FINDING A-05: Analytics events endpoint has no authentication
- **File:** `apps/api/analytics.py` lines 75–114
- **Severity:** MEDIUM
- **Issue:** The `POST /analytics/events` endpoint accepts events from any caller without authentication. An attacker could flood the analytics database with fake events, corrupting metrics and potentially causing DB storage issues.
- **Fix:** Add rate limiting per IP and optional auth token validation. Consider a lightweight API key for the analytics endpoint.

### FINDING A-06: No Hotjar/GTM despite config slots
- **File:** `apps/web/src/config.ts` lines 25–27
- **Severity:** MEDIUM
- **Issue:** Config defines `hotjarId` and `gtmId` but there's no code that initializes Hotjar or Google Tag Manager. These are dead configuration keys.
- **Fix:** Either implement the Hotjar/GTM script injection or remove the config slots to avoid confusion.

### FINDING A-07: Mobile analytics buffer has no max size limit
- **File:** `mobile/src/lib/analytics.ts` lines 108–119
- **Severity:** LOW
- **Issue:** If the flush keeps failing (e.g., no network), events are pushed back to `_buffer` (line 151) with no maximum size. This could consume unbounded memory on the device.
- **Fix:** Add `const MAX_BUFFER_SIZE = 500` and drop oldest events when exceeded.

---

## 4. Mobile App

### FINDING M-01: Placeholder EAS project ID throughout
- **File:** `mobile/app.json` lines 59, 75, 79; `mobile/src/lib/pushNotifications.ts` line 75
- **Severity:** CRITICAL
- **Issue:** `"YOUR_EAS_PROJECT_ID"` appears in `app.json` (updates URL, extra.eas.projectId) and in `pushNotifications.ts` (getExpoPushTokenAsync). Push notifications and OTA updates will completely fail.
- **Fix:** Replace all instances of `YOUR_EAS_PROJECT_ID` with the actual EAS project ID from Expo dashboard.

### FINDING M-02: No offline data handling or caching
- **File:** `mobile/src/api/client.ts`, `mobile/src/screens/DashboardScreen.tsx`
- **Severity:** HIGH
- **Issue:** All screens fetch data directly from the API with no local caching or offline fallback. If the user has no network, every screen shows an error state. No `AsyncStorage` caching or optimistic UI.
- **Fix:** Implement a caching layer using `@tanstack/react-query` with `AsyncStorage` persister, or add manual `AsyncStorage.setItem` for last-fetched data.

### FINDING M-03: No navigation/routing setup visible
- **File:** `mobile/src/` directory
- **Severity:** HIGH
- **Issue:** There's no `App.tsx`, `navigation.tsx`, or React Navigation setup. Individual screens exist (`DashboardScreen.tsx`, `OnboardingScreen.tsx`, etc.) but there's no navigation stack connecting them. The app has no entry point wiring screens together.
- **Fix:** Add a root navigation setup using `@react-navigation/native` with proper stack/tab navigators.

### FINDING M-04: No biometric auth integration despite file existing
- **File:** `mobile/src/lib/biometricAuth.ts`
- **Severity:** HIGH
- **Issue:** The file exists but it's unclear if it's wired into the app flow. The mobile app doesn't appear to have a login screen — `DashboardScreen` directly calls the admin dashboard endpoint, suggesting auth flow is incomplete.
- **Fix:** Implement a proper login → biometric unlock flow using `expo-local-authentication`.

### FINDING M-05: Google Services file missing for Android
- **File:** `mobile/app.json` line 43
- **Severity:** MEDIUM
- **Issue:** `"googleServicesFile": "./google-services.json"` references a file that needs to exist for Firebase Cloud Messaging. If it's missing, Android builds will fail or push notifications won't work.
- **Fix:** Add `google-services.json` to the mobile directory (from Firebase Console) or make the config conditional.

### FINDING M-06: No app store assets or store-readiness checks
- **File:** `mobile/app.json`
- **Severity:** MEDIUM
- **Issue:** `app.json` references `./assets/icon.png`, `./assets/splash.png`, `./assets/adaptive-icon.png`, `./assets/notification-icon.png`, `./assets/favicon.png` but the assets directory doesn't contain verified production-quality assets. iOS requires specific sizes (1024x1024 icon, etc.).
- **Fix:** Verify all required asset sizes exist. Add a pre-build script that validates icon dimensions.

### FINDING M-07: No deep linking handler for notification taps
- **File:** `mobile/src/lib/pushNotifications.ts` lines 126–128
- **Severity:** MEDIUM
- **Issue:** `setNotificationTapHandler` accepts a handler but nothing calls it from the main app. When users tap push notifications, nothing happens because no navigation handler is registered.
- **Fix:** Register a tap handler in the root component that navigates to the relevant screen based on notification data.

### FINDING M-08: No app version update check
- **File:** `mobile/app.json`
- **Severity:** LOW
- **Issue:** OTA updates URL points to `YOUR_EAS_PROJECT_ID`. Even with correct ID, there's no forced update mechanism for breaking API changes.
- **Fix:** Add a `/app/version-check` API endpoint and show an update prompt when `minSupportedVersion > currentVersion`.

### FINDING M-09: No i18n fallback handling
- **File:** `mobile/src/features/v3/i18n.ts`
- **Severity:** LOW
- **Issue:** i18n file exists but without proper fallback configuration, missing translation keys will show raw keys to users.
- **Fix:** Configure a default language fallback and missing key handler.

---

## 5. Extension

### FINDING X-01: Auth token stored in plain `chrome.storage.local`
- **File:** `apps/extension/src/background/index.ts` line 21, `apps/extension/src/content/auth.ts` line 6
- **Severity:** CRITICAL
- **Issue:** The JWT auth token is stored in `chrome.storage.local` which is accessible to any content script running in the extension context. If the extension is compromised or has a XSS vulnerability, the token is exposed. Additionally, `auth.ts` reads directly from `localStorage` of the web app page.
- **Fix:** Use `chrome.storage.session` (MV3) for ephemeral storage, or encrypt the token before storing. Consider using `chrome.identity` API for proper OAuth flow.

### FINDING X-02: Extension manifest includes `http://localhost` in production
- **File:** `apps/extension/manifest.json` lines 14, 38–39
- **Severity:** HIGH
- **Issue:** `host_permissions` includes `"http://localhost:8000/*"` and `content_scripts.matches` includes `"http://localhost:5173/*"`. This is a development-only config shipped to production, unnecessarily broadening permissions and potentially triggering Chrome Web Store review warnings.
- **Fix:** Use a build step to strip localhost entries for production builds. Use separate manifest files or environment-based manifest generation.

### FINDING X-03: Content scripts source files referenced directly in manifest
- **File:** `apps/extension/manifest.json` lines 25, 33
- **Severity:** HIGH
- **Issue:** `"js": ["src/content/index.ts"]` and `"src/content/auth.ts"` reference TypeScript source files. Chrome cannot execute `.ts` files. The manifest must reference compiled `.js` files from the build output.
- **Fix:** Update manifest to reference build output paths (e.g., `dist/content/index.js`). Ensure build process generates correct manifest.

### FINDING X-04: No Content Security Policy in manifest
- **File:** `apps/extension/manifest.json`
- **Severity:** MEDIUM
- **Issue:** No `content_security_policy` is defined. MV3 has defaults, but explicitly defining CSP prevents future issues if inline scripts are accidentally added.
- **Fix:** Add `"content_security_policy": { "extension_pages": "script-src 'self'; object-src 'self'" }`.

### FINDING X-05: No offline sync queue
- **File:** `apps/extension/src/background/index.ts` lines 48–61
- **Severity:** MEDIUM
- **Issue:** Jobs are saved to `chrome.storage.local` as backup but there's no mechanism to sync locally-saved jobs to the API when connectivity is restored. The offline notification says "Will sync when online" but this is a lie — no sync mechanism exists.
- **Fix:** Implement a sync queue that retries unsent jobs when `navigator.onLine` changes to `true`.

### FINDING X-06: Overly broad `scripting` permission
- **File:** `apps/extension/manifest.json` line 9
- **Severity:** MEDIUM
- **Issue:** The `scripting` permission is declared but not used in the codebase. Content scripts are injected via `content_scripts` in the manifest, not programmatically. Unnecessary permissions hurt Chrome Web Store approval chances.
- **Fix:** Remove `"scripting"` from permissions if not actively used.

### FINDING X-07: No extension versioning strategy
- **File:** `apps/extension/manifest.json` line 4
- **Severity:** LOW
- **Issue:** Version is `"1.0.0"` with no automated versioning. Chrome Web Store requires version increments for every update submission.
- **Fix:** Automate version bumping in CI/CD pipeline.

---

## 6. Admin Dashboard

### FINDING AD-01: Admin access check relies solely on client-side profile flag
- **File:** `apps/web-admin/src/App.tsx` lines 49–63
- **Severity:** CRITICAL
- **Issue:** `checkAdminAccess()` fetches `/profile` and checks `data?.is_system_admin === true || data?.role === "admin"`. This is a client-side check only. If the API endpoints (like `/admin/*`) don't independently verify admin status server-side, any authenticated user could call admin APIs directly.
- **Fix:** Ensure every `/admin/*` endpoint on the backend verifies admin role via `_get_admin_user_id` dependency. Add backend middleware that rejects non-admin users for admin routes.

### FINDING AD-02: Audit log export has no access control validation
- **File:** `apps/web-admin/src/compliance/AuditLogPage.tsx` line 53
- **Severity:** HIGH
- **Issue:** The audit log export endpoint `/billing/audit-log/export?days=90` is called with just the auth token. There's no visible rate limiting or abuse prevention on bulk data export. An attacker with a valid admin token could export all audit data.
- **Fix:** Add rate limiting on export endpoint. Log export events in the audit log itself. Consider adding a TOTP/MFA challenge for data exports.

### FINDING AD-03: No CSRF protection on admin actions
- **File:** `apps/web-admin/src/App.tsx`, `apps/web-admin/src/lib/api.ts`
- **Severity:** HIGH
- **Issue:** Admin dashboard uses `localStorage` auth tokens in `Authorization` headers, which protects against CSRF. However, there's no `SameSite` cookie policy documented and no explicit CSRF token mechanism if cookies are ever used.
- **Fix:** Document the auth mechanism explicitly. If switching to cookie-based auth in the future, add CSRF tokens.

### FINDING AD-04: No data sanitization on audit log display
- **File:** `apps/web-admin/src/compliance/AuditLogPage.tsx` line 132
- **Severity:** MEDIUM
- **Issue:** `{JSON.stringify(entry.details).slice(0, 60)}` renders raw JSON from the database. If audit details contain user-controlled content (e.g., team names with `<script>` tags), React's JSX escaping should prevent XSS, but truncated JSON could still display confusingly.
- **Fix:** Add a proper detail viewer with expandable rows and formatted JSON display.

### FINDING AD-05: No session timeout or activity-based logout
- **File:** `apps/web-admin/src/App.tsx`
- **Severity:** MEDIUM
- **Issue:** The admin dashboard has no idle timeout. An admin who walks away from their computer remains logged in indefinitely with full admin access.
- **Fix:** Implement a 30-minute idle timeout that clears the auth token and redirects to login.

### FINDING AD-06: Hardcoded `http://localhost:8000` as API fallback in audit log
- **File:** `apps/web-admin/src/compliance/AuditLogPage.tsx` line 3
- **Severity:** LOW
- **Issue:** `const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";` falls back to localhost. If the env var is missing in production, admin dashboard silently calls localhost and fails.
- **Fix:** Remove localhost fallback or show a configuration error.

---

## 7. SEO

### FINDING S-01: Structured data schema errors on Pricing page
- **File:** `apps/web/src/pages/Pricing.tsx` lines 99–131
- **Severity:** HIGH
- **Issue:** The Pricing page uses `PriceSpecification` schema type which is not a valid standalone schema type — it must be nested inside a `Product` or `Offer`. Google will ignore this. Additionally, the FAQPage schema is nested inside an array with PriceSpecification, which is non-standard.
- **Fix:** Use `Product` with nested `Offer` containing `PriceSpecification`. Separate FAQPage into its own `<script type="application/ld+json">` block.

### FINDING S-02: `lastUpdated` on Privacy/Terms uses `new Date()` (client-side)
- **File:** `apps/web/src/pages/Privacy.tsx` line 7, `apps/web/src/pages/Terms.tsx` line 7
- **Severity:** MEDIUM
- **Issue:** `const lastUpdated = new Date().toLocaleDateString(...)` renders today's date as "Last Updated." This means every visitor sees today as the last-updated date, which is misleading and could raise trust concerns ("they update their privacy policy every day?").
- **Fix:** Hardcode the actual last-updated date: `const lastUpdated = "February 15, 2026";`.

### FINDING S-03: No `hreflang` tags for international audiences
- **File:** `apps/web/src/components/marketing/SEO.tsx`
- **Severity:** MEDIUM
- **Issue:** The SEO component doesn't include `hreflang` alternate links. The app targets global job seekers but has no language/region targeting signals for search engines.
- **Fix:** Add `<link rel="alternate" hreflang="en" href="...">` for each supported locale. Even if only English, add `hreflang="x-default"`.

### FINDING S-04: Sitemap dates are static, not auto-generated
- **File:** `apps/web/public/sitemap.xml`
- **Severity:** MEDIUM
- **Issue:** `<lastmod>2026-02-17</lastmod>` is a hardcoded date. Sitemaps should reflect actual content change dates. Static dates signal to crawlers that content never changes, reducing crawl frequency.
- **Fix:** Generate sitemaps dynamically or update dates in the build process with the actual build/deploy timestamp.

### FINDING S-05: SEO component emits multiple structured data objects in one script tag
- **File:** `apps/web/src/components/marketing/SEO.tsx` lines 134–136
- **Severity:** LOW
- **Issue:** All schema objects (WebSite, Organization, BreadcrumbList, page-specific) are emitted as a JSON array in a single `<script>` tag. While technically valid, Google recommends separate `<script>` tags for each schema entity for clearer parsing.
- **Fix:** Render each schema object in its own `<script type="application/ld+json">` tag.

---

## 8. Legal Compliance

### FINDING L-01: No cookie consent banner
- **File:** Entire `apps/web/src/` directory
- **Severity:** CRITICAL
- **Issue:** There is no cookie consent banner, dialog, or preference center anywhere in the codebase. Google Analytics sets cookies, and GDPR/ePrivacy Directive requires explicit consent before setting non-essential cookies. This is a legal compliance violation in the EU.
- **Fix:** Implement a cookie consent banner using a library like `react-cookie-consent` or build a custom one. Block GA initialization until consent is given.

### FINDING L-02: GDPR deletion doesn't delete the `users` table row
- **File:** `apps/api/gdpr.py` lines 101–110
- **Severity:** CRITICAL
- **Issue:** `TABLES_FOR_DELETION` deletes from profiles, applications, analytics_events, etc., but does NOT delete the row from `public.users`. The user's email, ID, and account record persist after "full deletion." This violates GDPR Article 17 Right to Erasure.
- **Fix:** Add `("public.users", "id")` as the last entry in `TABLES_FOR_DELETION`. Handle foreign key cascades. Also delete from `public.billing_customers` and `public.tenant_members`.

### FINDING L-03: GDPR export download URL is not implemented
- **File:** `apps/api/gdpr.py` line 199
- **Severity:** HIGH
- **Issue:** `download_url=f"/gdpr/download/{export_id}"` is returned but there's no corresponding `GET /gdpr/download/{export_id}` endpoint. The export data is computed but never stored for download. Users request an export and get a dead link.
- **Fix:** Store the export data (e.g., in S3 or temp storage) and implement the download endpoint with proper auth, expiration, and cleanup.

### FINDING L-04: CCPA process endpoint lacks admin authorization
- **File:** `apps/api/ccpa.py` lines 216–236
- **Severity:** HIGH
- **Issue:** The `POST /ccpa/requests/{request_id}/process` endpoint has a TODO comment: "This endpoint should be admin-only in production." Currently any authenticated user can process (execute) CCPA data deletion requests for any user if they know the request ID.
- **Fix:** Add admin role check. Implement the TODO.

### FINDING L-05: Privacy policy references code internals (table names)
- **File:** `apps/web/src/pages/Privacy.tsx` lines 49–50, 67–68
- **Severity:** MEDIUM
- **Issue:** The privacy policy exposes internal database table names like `public.profiles`, `public.answer_memory`, `public.applications`. This unnecessarily exposes implementation details and could help attackers understand the database schema.
- **Fix:** Replace technical references with user-friendly descriptions: "Profile Data", "Application Memory", "Application History".

### FINDING L-06: Terms of Service references internal API endpoints
- **File:** `apps/web/src/pages/Terms.tsx` lines 38–41
- **Severity:** MEDIUM
- **Issue:** The ToS references `/webhook/resume_parse`, `/match-job`, `/claim_next`, and other internal API endpoints. This exposes the API surface to potential attackers.
- **Fix:** Replace with functional descriptions: "resume parsing service", "job matching algorithm", "application submission engine".

### FINDING L-07: No "Do Not Sell My Info" link visible on website
- **File:** `apps/web/src/components/marketing/MarketingFooter.tsx`
- **Severity:** LOW
- **Issue:** CCPA requires a visible "Do Not Sell or Share My Personal Information" link. While the API endpoint exists (`/ccpa/opt-out`), there's no visible link in the website footer or settings.
- **Fix:** Add "Do Not Sell My Info" link in the website footer linking to a CCPA preferences page.

---

## 9. 404, Maintenance, Offline Experiences

### FINDING P-01: No maintenance mode page
- **File:** Entire codebase
- **Severity:** HIGH
- **Issue:** There is no maintenance mode page, feature flag, or mechanism to gracefully show a maintenance message during deployments or outages. If the API is down, users see raw error states.
- **Fix:** Create a `Maintenance.tsx` page. Add a feature flag or environment variable that shows the maintenance page when enabled. Consider a static HTML maintenance page served by the CDN/reverse proxy.

### FINDING P-02: No offline/network-error page for the web app
- **File:** `apps/web/src/` directory
- **Severity:** MEDIUM
- **Issue:** The web app has no service worker or offline fallback. When users lose connectivity, API calls fail silently or show generic error states. There's no "You're offline" banner or cached content fallback.
- **Fix:** Add a `navigator.onLine` listener that shows an offline banner. Consider adding a service worker for basic offline caching of the app shell.

### FINDING P-03: 404 page has a fake live counter
- **File:** `apps/web/src/pages/NotFound.tsx` lines 9–13
- **Severity:** MEDIUM
- **Issue:** The 404 page shows a "live" application counter starting at 12,847 that increments by 1–3 every 4 seconds. This is a fabricated number with no connection to real data. If a user notices the counter resets on page reload, it damages trust.
- **Fix:** Either connect to a real counter via API, use a static "10,000+" label, or remove the counter.

### FINDING P-04: 404 page internal links go to non-existent routes
- **File:** `apps/web/src/pages/NotFound.tsx` lines 19–23
- **Severity:** LOW
- **Issue:** Trending searches link to paths like `/jobs/software-engineer/new-york` but there's no route handler for `/jobs/:role/:city` in the marketing layout — the route exists as `/jobs/:role/:city` under `MarketingLayout` in App.tsx as `JobNiche`, so this is actually fine. However, if those pages don't have real content, users clicking from the 404 page may land on empty job niche pages.
- **Fix:** Verify that `JobNiche` component actually renders useful content for the linked paths.

---

## 10. Team / Invitation / Multi-user Flows

### FINDING T-01: No tenant isolation on application queries
- **File:** `apps/api/analytics.py` lines 143–153
- **Severity:** HIGH
- **Issue:** The feedback endpoint checks `user_id` but uses `($3::uuid IS NULL OR tenant_id = $3)` which means if `tenant_id` is NULL, the query matches ANY application by that user across all tenants. A user who belongs to multiple tenants could access applications from another tenant context.
- **Fix:** Always require `tenant_id` in multi-tenant queries. Never allow NULL tenant_id to bypass isolation.

### FINDING T-02: Seat count update race condition
- **File:** `backend/domain/teams.py` lines 138–141
- **Severity:** HIGH
- **Issue:** `UPDATE public.tenants SET seat_count = seat_count + 1 WHERE id = $1` is not wrapped in a transaction with the member insertion. If two invites are accepted simultaneously, both could pass the seat capacity check (lines 52–60) before either increments the count, exceeding `max_seats`.
- **Fix:** Use `SELECT ... FOR UPDATE` on the tenants row before checking capacity and incrementing seats.

### FINDING T-03: Stripe seat quantity update not called on invite acceptance
- **File:** `backend/domain/teams.py` lines 87–150
- **Severity:** HIGH
- **Issue:** `accept_invite()` increments `seat_count` in the database but never calls `update_stripe_seat_quantity()`. The tenant gets more seats without being billed for them. Only the initial checkout handles Stripe billing.
- **Fix:** After incrementing `seat_count`, call `update_stripe_seat_quantity(conn, tenant_id, new_seat_count)` to update Stripe billing.

### FINDING T-04: No email normalization on invite
- **File:** `backend/domain/teams.py` lines 33–84
- **Severity:** MEDIUM
- **Issue:** `create_invite()` stores the email as-is without normalization (lowercase, trim). A user invited as `User@Gmail.com` won't match `user@gmail.com` during acceptance, creating duplicate invites.
- **Fix:** Normalize email: `email = email.strip().lower()` before storing and querying.

### FINDING T-05: Member removal doesn't revoke Stripe seat
- **File:** `backend/domain/teams.py` lines 219–242
- **Severity:** MEDIUM
- **Issue:** `remove_member()` decrements `seat_count` but doesn't call `update_stripe_seat_quantity()`. The tenant continues paying for the removed member's seat.
- **Fix:** Call `update_stripe_seat_quantity()` after removing a member to reduce the Stripe subscription quantity.

### FINDING T-06: No role hierarchy enforcement across app
- **File:** `backend/domain/teams.py` line 253
- **Severity:** LOW
- **Issue:** `update_member_role()` only allows "MEMBER" or "ADMIN" roles but doesn't check if the caller has sufficient privileges. An ADMIN shouldn't be able to promote themselves to OWNER or demote other ADMINs without OWNER permission.
- **Fix:** Add caller role validation: only OWNER can change roles, and ADMIN cannot modify other ADMINs.

---

## Priority Remediation Roadmap

### Immediate (Before Launch)
1. **B-01, B-02**: Fix Stripe webhook security and idempotency
2. **L-01**: Add cookie consent banner
3. **L-02**: Fix GDPR deletion to include users table
4. **E-01**: Fix magic link token exposure in URL
5. **X-01**: Secure extension token storage
6. **M-01**: Replace placeholder EAS project IDs
7. **AD-01**: Verify server-side admin access control
8. **B-05**: Implement trial period or fix CTA text

### High Priority (First 2 Weeks)
1. **B-03, B-04**: Add webhook dedup and customer creation lock
2. **A-02, A-03**: Integrate Sentry for error tracking
3. **T-01, T-02, T-03**: Fix tenant isolation and seat billing
4. **E-02, E-03**: SPF/DKIM verification and email templates
5. **P-01**: Create maintenance mode page
6. **L-03, L-04**: Fix GDPR export download and CCPA admin auth
7. **X-02, X-03**: Fix extension manifest for production

### Medium Priority (First Month)
1. **B-06, B-07**: Price sync and invoice display
2. **A-04, A-05**: Conversion tracking and analytics auth
3. **S-01, S-02**: Fix structured data and date issues
4. **M-02, M-03**: Mobile offline handling and navigation
5. **AD-04, AD-05**: Admin dashboard security hardening

---

*End of audit. 71 findings across 10 categories.*
