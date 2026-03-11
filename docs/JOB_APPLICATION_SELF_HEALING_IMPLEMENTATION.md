# Job Application Self-Healing Implementation Plan

**Based on:** `docs/JOB_APPLICATION_FLOW_AUDIT_REPORT.md`

## Current State

- **Playwright** drives job applications (agent.py, scaling.py)
- **Pain points:** CAPTCHA, OAuth, rate limits, bot detection, fragile selectors
- **Unused:** `HumanBehaviorSimulator`, `AntiDetection`, `ats_handlers` (Greenhouse/Lever/Workday)

## Alternatives to Playwright (Open Source, Scalable)

| Tool | Use Case | Notes |
|------|----------|-------|
| **HTTP-first (Greenhouse/Lever APIs)** | Known ATS with apply API | Free, scalable, no browser |
| **Crawlee** | Anti-blocking + Playwright | Fingerprinting, request queues |
| **Pydoll** | CAPTCHA-heavy sites | CDP, Turnstile/reCAPTCHA bypass |
| **Browserless.io** | Scale without infra | Already supported; session pooling |

## Self-Healing Architecture

```
Strategy Router → HTTP (if ATS known) → Browser (Playwright) → CAPTCHA solver
       ↓                    ↓                    ↓                    ↓
  Failure Classifier → Retry with backoff → Switch strategy → REQUIRES_INPUT / DLQ
```

## Top 10 Implementation Priorities

1. **Wire ExecutionEngine** — Use `HumanBehaviorSimulator` and `AntiDetection` in agent
2. **HTTP-first for Greenhouse/Lever** — Try API apply before Playwright
3. **Integrate ATS handlers** — Use `ats_handlers` pre-fill and custom selectors
4. **CAPTCHA failure → REQUIRES_INPUT** — Don't silently continue; escalate to user
5. **Proxy rotation for agent** — Add `agent_proxies`; rotate on 429/403
6. **OAuth session persistence** — Store cookies per (user, domain)
7. **Browserless as prod default** — Remote browsers for scaling
8. **Evaluate Pydoll** — For Turnstile-heavy sites
9. **Structured error classification** — Add `error_type` to events/DLQ
10. **ApplicationOrchestrator** — Central strategy selection and retries

## Config Additions

| Key | Purpose |
|-----|---------|
| `agent_proxies` | Proxy list for agent (rotate on rate limit) |
| `browserless_token` | Browserless API token |
| `apply_strategy` | `http_first` \| `browser_only` \| `auto` |
