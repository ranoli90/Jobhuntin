# ADR-001: Audit Remediation — March 2026

## Status: Accepted

## Context

A comprehensive codebase audit on 2026-03-14 identified 27 issues across security,
architecture, performance, code quality, and database layers. This ADR documents
the decisions made during remediation and deferred items.

## Decisions Made

### Security (Completed)

| ID | Decision | Rationale |
|----|----------|-----------|
| SEC-001 | `.env` confirmed not tracked; added audit/deploy artifacts to `.gitignore` | `.env` was in `.gitignore` already; real risk was history exposure |
| SEC-002 | Replaced `ssl.CERT_NONE` in worker with `"require"` / CA-cert pattern | MITM protection; mirrors API's SSL handling |
| SEC-003 | Moved 60+ loose scripts to `_scripts_archive/`, added to `.gitignore` | Reduces credential exposure risk, declutters repo root |
| SEC-004 | Changed CSRF/JWT secret defaults from known strings to empty `""` | Forces explicit configuration; prevents accidental use of dev secrets |
| SEC-005 | Created `docs/SECRET_ROTATION.md` runbook | Operational readiness for incident response |

### Architecture (Completed)

| ID | Decision | Rationale |
|----|----------|-----------|
| ARCH-001 | Extracted dead middleware code into proper `@app.middleware("http")` functions | Rate limiting and latency tracking were never executing |
| ARCH-002 | Fixed unreachable code in `submit_form()` | Warning was never logged; result was always returned before check |

### Performance / Config (Completed)

| ID | Decision | Rationale |
|----|----------|-----------|
| PERF-003 | Reduced `db_pool_max` from 100 → 25 | Prevents connection exhaustion on Render PostgreSQL |
| PERF-004 | Reduced `max_concurrent_browser_contexts` from 50 → 5 | Prevents OOM; each context uses ~500MB RAM |
| CODE-004 | Changed Dockerfile CMD to exec form | Enables proper SIGTERM forwarding for graceful shutdown |
| CODE-005 | Removed deprecated `version` field from docker-compose.yml | Compose V2 ignores it |

### Database (Completed)

| ID | Decision | Rationale |
|----|----------|-----------|
| DB-001 | Migration 040: Convert core TIMESTAMP → TIMESTAMPTZ | Timezone safety for multi-timezone users |
| DB-002 | Migration 040: Add `idx_applications_job_id` index | FK without index causes slow joins |

### Code Quality (Completed)

| ID | Decision | Rationale |
|----|----------|-----------|
| CODE-001 | Extracted `NEXT_BUTTON_SELECTORS` constant in agent.py | DRY: was duplicated in two functions |
| DEBT-003 | Added large output files to `.gitignore` | Repo cleanliness; 3.3MB+ files don't belong in VCS |

## Deferred Items

| ID | Reason | Recommended Approach |
|----|--------|---------------------|
| PERF-001 | Splitting `main.py` (2158 lines) risks breaking 60+ router imports | Dedicate a PR with full integration testing; extract models → `schemas.py`, inline endpoints → `routes/core.py`, middleware → `middleware/` |
| PERF-002 | Splitting `agent.py` (2570 lines) risks breaking worker task pipeline | Dedicate a PR; extract to `field_extraction.py`, `field_filling.py`, `form_submission.py`, `llm_mapping.py` |
| FE-002 | Reorganizing App.tsx routes needs frontend E2E testing | Extract into `routes/marketing.tsx`, `routes/app.tsx`, `routes/admin.tsx` |
| DEBT-002 | Scattered imports in main.py will resolve with PERF-001 | Address during main.py split |

## Consequences

- **Rate limiting is now active** — previously was dead code; may surface 429 errors for users hitting limits
- **JWT/CSRF secrets must be explicitly set** — local dev requires generating secrets before first run
- **DB pool is smaller** — may need tuning if connection pool errors appear under load
- **Worker SSL is stricter** — if Render changes SSL config, worker may need `db_ssl_ca_cert_path` set
