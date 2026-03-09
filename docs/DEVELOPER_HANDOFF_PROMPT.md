# Developer Handoff Prompt — Sorce / JobHuntin

**Copy the content below and paste it to the next AI agent to continue the work.**

---

## Context

You are taking over development on the Sorce/JobHuntin monorepo (job-hunting platform with FastAPI backend, React/Vite frontend, Playwright agent, JobSpy integration). The previous agent completed Sprints 1–4 of a quality/audit backlog. Your job is to fix the remaining issues.

**Key paths:**
- Backend: `apps/api/`, `apps/worker/`, `packages/backend/`
- Frontend: `apps/web/`
- Shared: `shared/`
- Docs: `docs/` (especially `DEEP_AUDIT_SPRINT_PLAN.md`, `AGENTS.md`)

**How to run:**
- DB: `docker compose up db -d`
- API: `source .venv/bin/activate && PYTHONPATH=apps:packages:. uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`
- Web: `cd apps/web && npx vite --host 0.0.0.0 --port 5173`
- Tests: `PYTHONPATH=apps:packages:. DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sorce pytest tests/ -v`

---

## What Was Completed (March 2026)

1. **Sprint 1 — Test schema mismatches:** Added migration 015 (`tenants.slug`, `jobs.external_id`, `jobs.application_url`, `applications.attempt_count`), fixed `popular_searches` PRIMARY KEY, added `application_events` table. `test_agent_claim_navigate_fill_submit` and `test_application_input_meta_with_unknown_keys` now pass.

2. **Sprint 2 — Mypy:** Fixed masking, pagination, llm_monitoring, job_dedup, batch_processor, debug, experiments. Many Mypy errors remain in other modules.

3. **Sprint 3–4 — Bandit & npm audit:** Documented status. Bandit skips (B608, B108, B313, B314) are in `pyproject.toml`. npm high-severity fixes require breaking upgrades.

---

## What’s Left to Fix (Priority Order)

### 1. Python test failure (quick fix)

- **Test:** `tests/test_domain.py::TestLLMClient::test_validation_error_not_retried`
- **Issue:** Test expects `LLMValidationError` when LLM response fails schema validation, but the client raises `LLMError`.
- **Location:** `packages/backend/llm/client.py` (around line 141) and/or the test expectation.
- **Fix:** Either raise `LLMValidationError` (or a subclass) for validation failures, or update the test to expect `LLMError`.

### 2. Mypy errors (~50+ remaining)

Run: `PYTHONPATH=apps:packages:. mypy apps/api/ apps/worker/ packages/backend/ shared/ --ignore-missing-imports`

**Main problem areas:**
- `shared/cache_strategies.py` — `_cache_data`, `_strategies` attributes, `no-any-return`, `HybridStrategy` arg types
- `shared/api_request_validator.py` — `ValidationResult.value`, `errors` annotation, arg types
- `packages/backend/domain/ui_analytics_manager.py` — dataclass attribute order, `PageView.updated_at`
- `packages/backend/domain/work_style.py` — `WorkStyleProfile` `**dict[str, str]` vs Literal types
- `packages/backend/domain/job_signals.py` — variable type mix-up (WorkPace vs CompanyStage)
- `apps/api/mfa.py` — `MFAManager` interface mismatch (methods/args)
- `shared/batch_loader.py`, `shared/rate_limit_headers.py` — `no-any-return`
- Various `Need type annotation for "X"` — add explicit annotations

### 3. Ruff lint errors (~1044)

Run: `ruff check apps packages shared --select E,W,F,I`

- Mostly E501 (line length), import order, and style.
- Use `ruff check --fix` where safe.
- `pyproject.toml` already ignores E501 for some cases; may need broader config.

### 4. Bandit (optional)

- 52 medium, 63 low. No high.
- B608 already skipped (SQL false positives). Remaining medium findings are dynamic SQL with whitelisted column names — generally safe.
- Can add more skips or `# nosec` for specific lines if needed.

### 5. npm audit (breaking upgrades)

- 6 high, 9 moderate in `apps/web`.
- **esbuild/vite:** Needs vite@7.3.1 (breaking).
- **prismjs/react-syntax-highlighter:** Needs react-syntax-highlighter@16.1.1 (breaking).
- **robots-txt-guard, serialize-javascript:** Via broken-link-checker, vite-plugin-pwa — fixes require major upgrades.
- Recommend a dedicated upgrade sprint; test thoroughly after upgrades.

---

## Reference Files

- `docs/DEEP_AUDIT_SPRINT_PLAN.md` — Full audit and sprint plan
- `docs/AUDIT_ERRORS_REVIEW.md` — npm/audit error details
- `AGENTS.md` — Setup, gotchas, commands
- `pyproject.toml` — Ruff, Mypy, Bandit config

---

## Suggested Order of Work

1. Fix `test_validation_error_not_retried` (small, unblocks green tests).
2. Fix high-impact Mypy errors (cache_strategies, api_request_validator, work_style, job_signals).
3. Run `ruff check --fix` and resolve remaining Ruff issues.
4. Plan npm upgrade sprint if security is a priority.
