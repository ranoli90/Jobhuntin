# Sorce/JobHuntin Job Application Flow — Audit Report

**Date:** March 11, 2025  
**Scope:** Full flow trace, Playwright pain points, alternatives research, self-healing design, recommendations

---

## 1. Flow Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           JOB APPLICATION FLOW — FULL TRACE                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  USER LAYER
  ──────────
  [User swipes Apply] ──► POST /me/applications (job_id) ──► INSERT applications (QUEUED)
                                                                      │
                                                                      ▼
                                                              NOTIFY job_queue
                                                                      │
  WORKER LAYER (apps/worker/agent.py, scaling.py)                     │
  ───────────────────────────────────────────────────────────────────┘
                                                                      │
  ┌──────────────────────────────────────────────────────────────────▼──────────────────┐
  │  FormAgent.run_forever()                                                              │
  │  ├─ _listen_loop() ──► LISTEN job_queue (Postgres NOTIFY)                             │
  │  └─ run_once() loop:                                                                  │
  │       ├─ [Guard] AGENT_ENABLED?                                                       │
  │       ├─ [Guard] Processing rate limit (max_applications_per_minute)?                 │
  │       ├─ [Guard] Concurrent limit (max_concurrent_applications, max_per_tenant)?      │
  │       ├─ claim_task() ──► SELECT * FROM claim_next_prioritized(MAX_ATTEMPTS)           │
  │       │                    (FOR UPDATE SKIP LOCKED, priority_score DESC)               │
  │       ├─ concurrent_tracker.start_task()                                              │
  │       └─ _process_task()                                                              │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                                                      │
  BROWSER LAYER (Playwright)                                          │
  ───────────────────────────────────────────────────────────────────▼──────────────────┐
  │  context = context_factory()  (local Chromium or Browserless CDP)                      │
  │  page = context.new_page()                                                            │
  │                                                                                       │
  │  _build_context() ──► fetch job, profile, resume, blueprint                          │
  │  _emit_started() ──► application_events (STARTED_PROCESSING)                         │
  │  _navigate_to_app() ──► page.goto(application_url, wait_until=networkidle)             │
  │       ├─ [OAuth] oauth_handler.detect_oauth_flow() → handle_oauth_flow()               │
  │       └─ Retry 3x on timeout/network errors (exponential backoff)                      │
  │  _extract_fields() ──► extract_all_form_fields() (walk multi-step, EXTRACT_FORM_*)   │
  │  _map_fields() ──► map_fields_via_llm() (DOM → profile mapping)                       │
  │  [Hold] unresolved_required_fields? ──► _enter_hold() → REQUIRES_INPUT                │
  │  _fill_form() ──► page.goto() again, fill_form_from_mapping() per step               │
  │  _submit_application() ──► CaptchaHandler.handle_captcha() → submit_form()           │
  │  _handle_success() ──► blueprint.on_task_completed() → APPLIED                        │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                                                      │
  FAILURE PATH                                                        │
  ────────────                                                         │
  _handle_failure() ──► attempt < MAX_ATTEMPTS? ──► QUEUED + available_at + backoff       │
                     └─ attempt >= MAX_ATTEMPTS? ──► FAILED + DLQ + notify                 │
```

### Key Files

| Step | File | Function/Class |
|------|------|----------------|
| Queue | `apps/api/user.py` | `POST /me/applications` → INSERT QUEUED, NOTIFY |
| Claim | `apps/worker/agent.py` | `claim_task()` → `claim_next_prioritized()` |
| Scale | `apps/worker/scaling.py` | `WorkerScaler`, `BrowserPoolManager` |
| Navigate | `apps/worker/agent.py` | `_navigate_to_app()` |
| OAuth | `apps/worker/oauth_handler.py` | `OAuthHandler.detect_oauth_flow()`, `handle_oauth_flow()` |
| Extract | `apps/worker/agent.py` | `extract_form_fields_single_step()`, `EXTRACT_FORM_FIELDS_JS` |
| Map | `apps/worker/agent.py` | `map_fields_via_llm()` |
| Fill | `apps/worker/agent.py` | `fill_form_from_mapping()` |
| CAPTCHA | `packages/backend/domain/captcha_handler.py` | `CaptchaHandler.handle_captcha()` |
| Submit | `apps/worker/agent.py` | `submit_form()` |
| ATS | `packages/backend/domain/ats_handlers.py` | `detect_ats_platform()`, `ATSSpecificHandler` (not wired into agent) |
| Execution | `packages/backend/domain/execution_engine.py` | `HumanBehaviorSimulator`, `AntiDetection` (not wired into agent) |

---

## 2. Failure Modes

### 2.1 CAPTCHA

| Failure | Description | Current Handling |
|---------|-------------|------------------|
| reCAPTCHA v2/v3 | Invisible or checkbox challenge | `CaptchaHandler` detects, calls 2Captcha/Anti-Captcha; injects solution. Continues on failure. |
| hCaptcha | Similar to reCAPTCHA | Supported via solver services. |
| Cloudflare Turnstile | Challenge page | Selectors in `ats_handlers.CAPTCHA_SELECTORS`; no dedicated solver. |
| Arkose Labs | Harder to solve | Detection only; no solver. |
| Image/Math CAPTCHA | Text-based | 2Captcha ImageToText; Anti-Captcha not fully implemented. |

**Pain points:** reCAPTCHA v3 invisible often needs site key; Turnstile/Arkose require specialized solvers; cost per solve ($2–3/1000); injection can fail if page structure changes.

### 2.2 OAuth / SSO

| Failure | Description | Current Handling |
|---------|-------------|------------------|
| OAuth redirect | Google/LinkedIn/Microsoft/Facebook/Apple | `OAuthHandler` detects, clicks button, fills email/password from `oauth_credentials`. |
| 2FA | TOTP/SMS code | Detects 2FA; requires `two_factor_code` in credentials. Fails if not provided. |
| SAML/Enterprise SSO | Company login | Detection only; no automated handling. |
| Session expiry | Cookies expire mid-flow | No session persistence; each task starts fresh. |

**Pain points:** User must store OAuth credentials; 2FA blocks automation; no session reuse across applications.

### 2.3 Dynamic Forms

| Failure | Description | Current Handling |
|---------|-------------|------------------|
| Multi-step forms | Next/Continue buttons | `click_next_button()` with 30+ selector variants; max 5 steps. |
| SPA / lazy load | Fields appear after JS | `wait_for_selector` 10s; `wait_for(state="visible")` 5s. |
| Custom components | Shadow DOM, non-standard inputs | `EXTRACT_FORM_FIELDS_JS` uses `form.querySelectorAll`; Shadow DOM not fully handled. |
| Selector fragility | nth-of-type, class-based | Last resort: `nth-of-type`; breaks on DOM changes. |

**Pain points:** Workday uses heavy SPAs; `data-automation-id` can change; some forms use infinite scroll or virtual lists.

### 2.4 Rate Limits & Bot Detection

| Failure | Description | Current Handling |
|---------|-------------|------------------|
| IP rate limiting | Too many requests from same IP | No proxy rotation in agent; config has `jobspy_proxies` for job search only. |
| Bot detection | Fingerprinting, WebDriver checks | `execution_engine.AntiDetection` exists but not used by agent; agent uses random UA/viewport. |
| Cloudflare challenge | Browser verification | No Turnstile solver; blocks submission. |

**Pain points:** `AntiDetection` and `HumanBehaviorSimulator` are not integrated; agent uses `page.fill()` instead of human-like typing.

### 2.5 Other Failures

| Failure | Description | Current Handling |
|---------|-------------|------------------|
| Navigation timeout | Slow page load | 3 retries, exponential backoff; `PAGE_TIMEOUT_MS` (60s default). |
| No form fields | Empty page, wrong URL | Raises `RuntimeError("No form fields detected")` → retry. |
| Submit button not found | Custom submit UX | 6 default selectors; blueprint can override. Fallback: click without navigation. |
| Form validation | Client-side errors | No validation feedback loop; may submit invalid data. |
| File upload | Resume/portfolio | `set_input_files()`; supports resume, cover letter, portfolio, documents. |
| LLM rate limit | Too many mapping calls | `_llm_limiter`; raises RuntimeError, task retried on next poll. |

---

## 3. Alternative Comparison Table

| Approach | Open Source | Scalable | Self-Healing | Cost | Best For |
|----------|-------------|----------|-------------|------|----------|
| **Current: Playwright** | ✅ Yes | Medium (local) / High (Browserless) | Partial (retry, backoff) | Low (local) / High (Browserless) | Full form automation |
| **Apify (HTTP)** | ❌ No (SaaS) | ✅ High | Managed | $1–150/1k jobs | Job scraping only; no apply |
| **Direct ATS APIs** | N/A | ✅ High | ✅ Yes | Free (if API exists) | Greenhouse, Lever (limited); Workday not public |
| **Crawlee** | ✅ Yes | Medium | Better anti-blocking | Free | Crawling + Playwright; adds fingerprinting |
| **Pydoll** | ✅ Yes | Medium | Built-in CAPTCHA bypass | Free | CDP; human-like; Turnstile/reCAPTCHA bypass |
| **Browserless.io** | ❌ No (SaaS) | ✅ High (1k+ sessions) | Managed | Pay-per-session | Scale Playwright without infra |
| **Puppeteer/Chrome CDP** | ✅ Yes | Same as Playwright | Same | Same | Same as Playwright; different API |

### Detailed Notes

- **Apify:** Job scraping APIs (LinkedIn, Greenhouse, etc.) — no apply/submit. Useful for job discovery only.
- **Direct ATS APIs:** Lever has `Apply to posting`; Greenhouse has webhooks; Workday has no public apply API. Coverage is limited.
- **Crawlee:** Uses Playwright under the hood; adds anti-blocking, fingerprinting, request queues. Python + Node.
- **Pydoll:** CDP-based; claims to bypass Turnstile/reCAPTCHA; human-like interactions. No WebDriver.
- **Browserless.io:** Already supported via `browserless_url`; CDP; session pooling; proxy rotation.

---

## 4. Self-Healing Design

### 4.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     SELF-HEALING JOB APPLICATION PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │   Strategy   │     │   Strategy   │     │   Strategy   │     │   Strategy   │
  │   Router     │────►│  HTTP/API    │────►│   Browser    │────►│   Browser    │
  │              │     │  (if ATS)    │     │  (Playwright)│     │  + CAPTCHA   │
  └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
         │                      │                     │                     │
         │                      │                     │                     │
         ▼                      ▼                     ▼                     ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │  Failure Detector → Classify Error → Retry with Backoff / Switch Strategy     │
  └──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Failure Detection

| Signal | Detection | Action |
|--------|-----------|--------|
| CAPTCHA block | `CaptchaHandler.detect` + solve failure | Retry with 2Captcha; if fail → escalate to human |
| OAuth block | `OAuthHandler` returns False | Require user credentials; retry with manual auth |
| Rate limit | HTTP 429, "Too Many Requests" | Exponential backoff; rotate proxy |
| Bot detection | Page shows "blocked" / challenge | Switch to Pydoll or Browserless; retry |
| Timeout | `TimeoutError`, `page load` | Retry 3x; increase timeout |
| No form fields | `extract_all_form_fields` empty | Check URL; retry; mark as manual |
| Submit failure | `submit_form` returns False | Try different selectors; retry |

### 4.3 Strategy Switching

1. **HTTP-first:** If ATS detected (Greenhouse, Lever) and API exists → try HTTP apply first.
2. **Browser fallback:** If HTTP fails or no API → use Playwright.
3. **CAPTCHA escalation:** If CAPTCHA unsolved → retry with solver; if still fail → `REQUIRES_INPUT` with "Complete CAPTCHA manually".
4. **Proxy rotation:** On rate limit → switch proxy (when configured).
5. **Browser pool:** On Browserless → use session pool; on local → recycle context after N uses.

### 4.4 Retry & Backoff

- **Current:** `backoff_seconds = 30 * (2 ** (attempt - 1))`; max 3 attempts.
- **Proposed:** Classify errors (transient vs permanent); retry only transient; cap backoff at 1 hour.
- **Proposed:** Per-ATS retry limits (e.g., Workday 2x, Greenhouse 3x).

### 4.5 Recovery from CAPTCHA/OAuth Blocks

| Block | Recovery |
|-------|----------|
| CAPTCHA unsolved | 1) Retry with 2Captcha; 2) If fail → `REQUIRES_INPUT` "Complete CAPTCHA"; 3) User completes in browser; re-queue. |
| OAuth required | 1) Store `oauth_credentials` in profile; 2) Retry with credentials; 3) If 2FA → `REQUIRES_INPUT` "Enter 2FA code". |
| Session expired | 1) Re-run OAuth flow; 2) Persist cookies for same domain (future). |

---

## 5. Top 10 Recommendations

### Priority 1 — Critical (Do First)

1. **Wire ExecutionEngine into Agent**  
   Use `HumanBehaviorSimulator` and `AntiDetection` in the agent flow. Replace `page.fill()` with `type_humanlike()` for text fields to reduce bot detection. Fix `HumanBehaviorConfig.minTyping_delay_ms` typo.

2. **Implement HTTP-First Strategy for Known ATS**  
   Add a strategy router: if `detect_ats_platform()` returns Greenhouse or Lever and API credentials exist, try HTTP apply first. Fall back to Playwright on failure.

3. **Integrate ATS Handlers**  
   `ats_handlers.py` defines `GreenhouseHandler`, `LeverHandler`, `WorkdayHandler` but they are not used. Call `get_handler(platform).pre_fill_hook`, `get_custom_selectors()` for submit/next, and `get_skip_selectors()` during form fill.

### Priority 2 — High Reliability

4. **CAPTCHA Failure Handling**  
   When CAPTCHA solve fails, do not silently continue. Set `REQUIRES_INPUT` with a clear message ("Complete the CAPTCHA to continue") and allow user to complete and re-queue.

5. **Proxy Rotation for Agent**  
   Add `agent_proxies` config (or reuse `jobspy_proxies`) and rotate on rate limit or 403. Use proxy per context in BrowserPoolManager.

6. **Session Persistence for OAuth**  
   Persist `OAuthHandler.auth_cookies` per (user, domain) in DB or Redis. Reuse when applying to same ATS domain within TTL (e.g., 24h).

### Priority 3 — Scalability

7. **Browserless as Default for Production**  
   Use `browserless_url` in prod; keep local Chromium for dev. Document session pooling and token usage.

8. **Evaluate Pydoll for CAPTCHA-Heavy Sites**  
   Proof-of-concept: use Pydoll for sites that block Playwright (e.g., Turnstile). Pydoll claims built-in bypass; compare success rate.

### Priority 4 — Observability & Maintenance

9. **Structured Error Classification**  
   Add `error_type` enum (CAPTCHA_BLOCK, OAUTH_BLOCK, RATE_LIMIT, BOT_DETECTION, TIMEOUT, NO_FIELDS, SUBMIT_FAILED) to `application_events` and `job_dead_letter_queue`. Use for retry logic and analytics.

10. **Self-Healing Orchestrator**  
    Introduce `ApplicationOrchestrator` that: (a) selects strategy (HTTP vs browser), (b) runs attempt, (c) on failure classifies error, (d) retries or switches strategy, (e) escalates to `REQUIRES_INPUT` or DLQ with clear reason.

---

## Appendix: Config Reference

| Config | Default | Purpose |
|--------|---------|---------|
| `agent_enabled` | true | Emergency stop |
| `max_attempts` | 3 | Max retries before DLQ |
| `max_form_steps` | 5 | Multi-step form limit |
| `page_timeout_ms` | 60_000 | Navigation timeout |
| `poll_interval_seconds` | 5 | Polling when no NOTIFY |
| `browserless_url` | "" | Remote Browser CDP |
| `browserless_token` | "" | Browserless API token |
| `max_applications_per_minute` | (config) | Rate limit |
| `max_concurrent_applications` | 10 | Global concurrency |
| `max_concurrent_per_tenant` | 3 | Per-tenant limit |
| `twocaptcha_api_key` | "" | CAPTCHA solver |
| `anticaptcha_api_key` | "" | CAPTCHA solver |
| `captcha_solvers` | "" | "2captcha,anticaptcha" |
