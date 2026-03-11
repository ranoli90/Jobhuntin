# Auth, Billing, and Worker Audit Findings

**Generated:** 2026-03-10  
**Scope:** auth, billing, worker modules

---

## AUTH

| ID | Severity | File:Line | Description | Trigger Scenario | Status |
|----|----------|-----------|-------------|------------------|--------|
| AUTH-001 | High | auth.py:1001-1010 | Session creation failure swallowed; minimal SessionInfo with random UUID. Session tracking lost. | Session creation fails (DB error). User logs in but session not stored; revocation ineffective. | fixed |
| AUTH-002 | Medium | auth.py:176-179 | `_is_session_token_revoked` fails open on Redis errors. | Redis down; revoked tokens remain valid. | fixed |
| AUTH-003 | Medium | middleware vs api_auth_middleware | Inconsistent X-Forwarded-For: rightmost vs leftmost IP. | Behind proxy; rate limiting and auth use different IPs. | fixed |
| AUTH-004 | Medium | auth.py:1001-1010 | `update_session_jti` failure only logged; JTI not stored. | DB error during update; logout cannot revoke JTI. | fixed |
| AUTH-005 | Low | auth.py:1318-1340 | Resend webhook signature handling may mismatch Svix format. | Valid webhooks rejected or unverified. | fixed |
| AUTH-006 | Low | auth.py:1001-1010 | Resend payload parsed before signature verification. | Body consumed; signature verification invalid. | fixed |
| AUTH-007 | Low | auth.py:629-631 | `_sanitize_return_to` fixed path whitelist. | New routes not allowed. | fixed |
| AUTH-008 | Low | auth.py:114-129 | In-memory consumed-token cache when Redis unavailable. | Magic link replay across instances. | fixed |

---

## BILLING

| ID | Severity | File:Line | Description | Trigger Scenario | Status |
|----|----------|-----------|-------------|------------------|--------|
| BILL-001 | **Critical** | billing.py:415-423, billing.py:43-58 | `tenants.plan` never set back to FREE on cancel/end. | User cancels; keeps PRO until next checkout. | fixed |
| BILL-002 | High | billing.py:381-390 | `protected_stripe_call` can return None; `session.url` accessed without check. | Circuit breaker open; AttributeError 500. | fixed |
| BILL-003 | Medium | billing.py:366-392 | team_checkout uses settings without redirect validation. | Misconfigured APP_BASE_URL. | fixed |
| BILL-004 | Medium | billing.py:381-392 | team_checkout does not pass success/cancel URLs in body. | UX inflexibility. | fixed |
| BILL-005 | Low | billing.py:499-508 | subscription.updated/deleted in separate transactions. | Order of arrival affects final state. | documented |
| BILL-006 | Low | billing.py:374-375 | HTTPException re-raised; others become generic 503. | 402 card declined shows "temporarily unavailable". | fixed |

---

## WORKER

| ID | Severity | File:Line | Description | Trigger Scenario | Status |
|----|----------|-----------|-------------|------------------|--------|
| WORK-001 | High | follow_up_reminders.py:216-264 | No claim/lock on get_pending_reminders; duplicate sends possible. | Two workers; both send same reminder; user gets duplicates. | fixed |
| WORK-002 | Medium | job_queue.py:364-375 | Retry indexing non-obvious. | Logic correct; maintainability risk. | fixed |
| WORK-003 | Medium | job_queue.py:270-271 | `json.loads` on payload/result without try/except. | Malformed JSON crashes worker loop. | fixed |
| WORK-004 | Medium | job_queue_worker.py:76-78 | No backoff on repeated handler failure. | External API down; worker polls every 5s. | fixed |
| WORK-005 | Low | job_queue.py:78 | CLAIM_TIMEOUT 5 min; long jobs can be reclaimed. | Job >5 min; runs twice. | documented |
| WORK-006 | Low | follow_up_reminders_worker.py:57-68 | Sequential processing; one slow send blocks rest. | One slow email delays others. | fixed |
| WORK-007 | Low | follow_up_reminders.py:242-243 | String concat for param_idx; fragile pattern. | SQL injection risk if extended carelessly. | documented |

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1 |
| High | 3 |
| Medium | 8 |
| Low | 9 |

**Top priorities:** BILL-001, BILL-002, WORK-001, AUTH-001
