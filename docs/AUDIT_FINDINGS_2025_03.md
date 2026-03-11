# Sorce/JobHuntin Codebase Audit — March 2025

Comprehensive audit covering JobSpy changes, Render env sync, Agent/Playwright, config gaps, and security.

---

## 1. JobSpy / Proxy / Job Sync

### F1. **CRITICAL: job_search.py schema mismatch — query will fail on current DB**
**File:** `packages/backend/domain/job_search.py:214-216`

**Issue:** The `_build_job_search_query` SELECT uses legacy column names:
- `url as application_url` — but `infra/postgres/schema.sql` has `application_url` (no `url`)
- `remote_policy` — schema has `is_remote` (boolean)
- `posted_date as date_posted` — schema has `date_posted`
- `experience_level as job_level` — schema has `job_level`

**Impact:** On a DB using `infra/postgres/schema.sql` (JobSpy schema), the query fails with "column does not exist".

**Fix:** Update the SELECT to match `schema.sql`:
```sql
SELECT id, title, company, description, location,
       salary_min, salary_max, application_url, source,
       is_remote, job_type, date_posted, job_level,
       company_industry, company_logo_url, raw_data, skills
FROM public.jobs
```
And update `is_remote` filter logic (lines 248–251) to use `is_remote` instead of `remote_policy`.

---

### F2. **CRITICAL: job_search.py _map_job_row expects wrong column names**
**File:** `packages/backend/domain/job_search.py:314-322`

**Issue:** `_map_job_row` uses `r["application_url"]` (from alias) and `r.get("posted_date")` / `r.get("date_posted")`. After fixing F1, the row will have `application_url` and `date_posted` directly. Also `r.get("remote_policy")` should be `r.get("is_remote")`.

**Fix:** Align with schema: use `application_url`, `date_posted`, `is_remote` (or `remote_policy` if that column exists in your DB).

---

### F3. **HIGH: JobRepo.get_by_id assumes companies table and company_id**
**File:** `packages/backend/domain/repositories.py:468-493`

**Issue:** `JobRepo.get_by_id` does `LEFT JOIN public.companies c ON j.company_id = c.id`, but `infra/postgres/schema.sql` jobs table has no `company_id`. It also expects `remote`, `requirements`, `responsibilities`, `is_active`, etc., which are not in the schema.

**Impact:** Agent fails when fetching job for application — `fetch_job` returns `JobRepo.get_by_id` result, which may have KeyError or wrong structure.

**Fix:** Either add a `companies` table and `company_id` to jobs, or simplify `JobRepo.get_by_id` to work with the current jobs schema (no `companies` join).

---

### F4. **HIGH: job_sync_service._sync_jobs_to_db new/updated count logic wrong**
**File:** `packages/backend/domain/job_sync_service.py:375-378`

**Issue:**
```python
n, u = await self._batch_upsert_jobs(conn, batch)
updated_count += min(existing_count, n + u)
new_count += max(0, n + u - existing_count)
```
`_batch_upsert_jobs` always returns `(len(jobs), 0)` — it never returns actual new vs updated. So `new_count` and `updated_count` are incorrect.

**Fix:** Either compute new/updated from the upsert result (e.g. `RETURNING` / `xmax`) or adjust `_batch_upsert_jobs` to return real counts.

---

### F5. **MEDIUM: jobspy_client passes single proxy per fetch; no per-job rotation**
**File:** `packages/backend/domain/jobspy_client.py:132-136`

**Issue:** One proxy is chosen per `fetch_jobs` call and used for all sources. `jobspy_proxy_rotation` exists in config but `_get_proxy` does round-robin; the real issue is one proxy per batch, not per-job rotation.

**Fix:** Document behavior or implement per-source proxy if JobSpy supports it.

---

### F6. **MEDIUM: proxy_fetcher free proxies have no validation**
**File:** `packages/backend/domain/proxy_fetcher.py:74-87`

**Issue:** GimmeProxy and PubProxy return proxies without validation. Free proxies can be slow, dead, or malicious.

**Fix:** Add optional health check (e.g. quick HEAD request) before use; consider timeout/retry limits.

---

### F7. **MEDIUM: jobspy_client _parse_salary missing interval handling**
**File:** `packages/backend/domain/jobspy_client.py:336-352`

**Issue:** Only `hourly`, `weekly`, `monthly` are converted to annual. `daily` or other intervals are left as-is.

**Fix:** Add `daily` handling (e.g. `* 260` or `* 365`) and log unknown intervals.

---

### F8. **MEDIUM: jobspy_client zip_recruiter source normalization**
**File:** `packages/backend/domain/jobspy_client.py:235-237`

**Issue:** `if source == "zip_recruiter": source = "zip_recruiter"` is a no-op.

**Fix:** Remove or replace with real normalization if needed.

---

### F9. **LOW: is_scam threshold may be too aggressive**
**File:** `packages/backend/domain/job_sync_service.py:403`  
**File:** `packages/backend/domain/job_search.py:350-367`

**Issue:** `is_scam = score < 40` and `"work from home"` in scam indicators. Many legitimate remote jobs are flagged.

**Fix:** Remove or soften “work from home”;
consider raising threshold or adding allowlist.

---

## 2. Render Env Sync

### F10. **HIGH: sync_render_env_from_dotenv.py get_env_vars may return wrong structure**
**File:** `scripts/maintenance/sync_render_env_from_dotenv.py:86-87`

**Issue:**
```python
return resp.json() if isinstance(resp.json(), list) else []
```
If Render returns `{"envVars": [...]}` or another object, the result is `[]`. Then `set_env_var` always adds new vars instead of updating, causing duplicates.

**Fix:** Inspect Render API response format; handle both list and object (e.g. `data.get("envVars", data) if isinstance(data, dict) else data`).

---

### F11. **MEDIUM: job-sync missing JobSpy env vars**
**File:** `scripts/maintenance/sync_render_env_from_dotenv.py:57`

**Issue:** `jobhuntin-job-sync` has `JOBSPY_USE_FREE_PROXIES` but not `JOBSPY_PROXIES`, `JOBSPY_SOURCES`, `JOBSPY_RESULTS_PER_SOURCE`, etc.

**Fix:** Add `JOBSPY_PROXIES`, `JOBSPY_SOURCES`, `JOBSPY_RESULTS_PER_SOURCE`, `JOBSPY_HOURS_OLD` if needed.

---

### F12. **MEDIUM: sorce-auto-apply-agent missing BROWSERLESS_TOKEN**
**File:** `scripts/maintenance/sync_render_env_from_dotenv.py:60-64`

**Issue:** `BROWSERLESS_URL` is synced but `BROWSERLESS_TOKEN` is not. config.py has `browserless_token`.

**Fix:** Add `BROWSERLESS_TOKEN` to the sync list for the agent service.

---

### F13. **LOW: Invalid key "env" in service lists**
**File:** `scripts/maintenance/sync_render_env_from_dotenv.py:41, 49, 57, 58, 59, 65, 66, 67`

**Issue:** `"env"` is used as an env var key. Render typically uses `ENV`. The script defaults `"env": "prod"` — ensure Render expects `env` or `ENV`.

**Fix:** Confirm which key Render uses and standardize.

---

## 3. Agent / Playwright

### F14. **HIGH: Agent uses application_url from job; JobRepo may not provide it**
**File:** `apps/worker/agent.py:1072, 1083`  
**File:** `packages/backend/domain/repositories.py:468-546`

**Issue:** Agent uses `job["application_url"]` for navigation. `JobRepo.get_by_id` returns `row.get("application_url")`, but the query joins `companies` and the jobs schema may not have `application_url` if the DB uses the legacy schema.

**Fix:** Ensure JobRepo returns `application_url` (or `url`) for the jobs table used in production.

---

### F15. **MEDIUM: OAuth/SSO flow uses profile oauth_credentials**
**File:** `apps/worker/agent.py:807-813`

**Issue:** `user_credentials = ctx.get("profile", {}).get("oauth_credentials")` — if OAuth is required but credentials are missing, the agent continues and may fail later.

**Fix:** Detect required OAuth and fail early with a clear message if credentials are missing.

---

### F16. **MEDIUM: submit_form fallback click can mask real failure**
**File:** `apps/worker/agent.py:524-533`

**Issue:** If `expect_navigation` times out, the code falls back to `btn.click()` and returns True. The form may not have submitted.

**Fix:** Differentiate “no navigation” vs “submit succeeded”; consider checking for success indicators (e.g. thank-you page) before returning True.

---

### F17. **MEDIUM: scaling.py WorkerScaler does not use wake_event**
**File:** `apps/worker/agent.py:569-576`  
**File:** `apps/worker/scaling.py:405-416`

**Issue:** `FormAgent.run_forever` uses `wake_event` for LISTEN/NOTIFY. `WorkerScaler._worker_loop` calls `agent.run_once()` in a loop with sleep. `FormAgent` is passed `context_factory` but the `run_forever` loop (with `wake_event`) is never used — each worker runs `run_once` in a tight loop.

**Fix:** Confirm whether scaling workers should use `run_forever` (with event-driven wake) or `run_once` polling. If using LISTEN/NOTIFY, workers need `run_forever` or equivalent.

---

### F18. **LOW: agent.py uses download_from_supabase_storage**
**File:** `apps/worker/agent.py:759`

**Issue:** `download_from_supabase_storage` is used but DB is Render PostgreSQL (no Supabase). Storage may be S3/R2/Render Disk.

**Fix:** Use a storage abstraction (e.g. `get_storage_service()`) that supports the configured backend.

---

### F19. **LOW: selectorFor nth-of-type fallback is fragile**
**File:** `apps/worker/agent.py:225-228`

**Issue:** `nth-of-type` selectors break when the DOM structure changes.

**Fix:** Prefer `data-testid`, `name`, `id`; document fallback as best-effort.

---

## 4. Config Gaps

### F20. **MEDIUM: No JOBSPY_PROXIES in .env.example**
**File:** `.env.example`

**Issue:** JobSpy proxy settings are not documented. Example has `BROWSERLESS_URL` but not `JOBSPY_PROXIES`, `JOBSPY_USE_FREE_PROXIES`.

**Fix:** Add `JOBSPY_PROXIES`, `JOBSPY_USE_FREE_PROXIES` to `.env.example`.

---

### F21. **MEDIUM: config.py has [REDACTED] literal**
**File:** `shared/config.py:137`

**Issue:** `[REDACTED]_path` appears to be a placeholder (e.g. `storage_path` or `render_disk_path`). Pydantic may treat it as a field name.

**Fix:** Replace with the real field name (e.g. `render_disk_path`).

---

### F22. **LOW: jobspy_proxy_rotation unused**
**File:** `shared/config.py:169`  
**File:** `packages/backend/domain/jobspy_client.py`

**Issue:** `jobspy_proxy_rotation` is defined but not used. `_get_proxy` already does round-robin.

**Fix:** Remove the setting or implement distinct behavior (e.g. random vs round-robin).

---

## 5. Security

### F23. **CRITICAL: update-render-env.sh hardcodes Stripe keys**
**File:** `scripts/maintenance/update-render-env.sh:19-20`

**Issue:**
```bash
STRIPE_SECRET_KEY="[REDACTED]"
STRIPE_PUBLISHABLE_KEY="pk1_46266a7da93f81522c85d9ce9521048e43ac4"
```
Even if secret is redacted, the publishable key is a real key. Keys should come from env or `.env`, not hardcoded.

**Fix:** Remove hardcoded values; source from `$STRIPE_SECRET_KEY` and `$STRIPE_PUBLISHABLE_KEY` from env or `.env`.

---

### F24. **HIGH: config.py default dev secrets**
**File:** `shared/config.py:118-119, 183, 199-200`

**Issue:** Defaults like `csrf_secret="dev-csrf-secret-change-in-production"`, `jwt_secret="dev-secret-key-change-in-production"`, `stripe_webhook_secret="dev-placeholder-webhook-secret"`. If `env` is misconfigured, prod could run with these.

**Fix:** `validate_critical` already checks some of these; ensure all critical secrets are validated in prod/staging.

---

### F25. **MEDIUM: RENDER_API_KEY from env**
**File:** `scripts/maintenance/sync_render_env_from_dotenv.py:30`

**Issue:** `RENDER_API_KEY = os.environ.get("RENDER_API_KEY") or os.environ.get("RENDER_API_TOKEN")` — key can come from env. If `.env` is loaded and contains the key, it is used. Ensure `.env` is never committed.

**Fix:** Already documented; add a pre-commit or CI check for secrets in `.env`.

---

### F26. **LOW: api_auth_middleware default jwt_secret**
**File:** `shared/api_auth_middleware.py:119`

**Issue:** `AuthConfig(jwt_secret_key="your-secret-key")` — weak default if not overridden.

**Fix:** Require explicit config; fail if default is used in prod.

---

## 6. Summary Table

| # | Severity | File | Line | Brief |
|---|----------|------|------|-------|
| F1 | Critical | job_search.py | 214-216 | Schema mismatch: url, remote_policy, posted_date, experience_level |
| F2 | Critical | job_search.py | 314-322 | _map_job_row wrong column names |
| F3 | High | repositories.py | 468-493 | JobRepo assumes companies table, company_id |
| F4 | High | job_sync_service.py | 375-378 | new/updated count logic wrong |
| F10 | High | sync_render_env_from_dotenv.py | 86-87 | get_env_vars may return [] for wrong API format |
| F14 | High | agent.py | 1072 | application_url from job may be missing |
| F23 | Critical | update-render-env.sh | 19-20 | Hardcoded Stripe keys |
| F5 | Medium | jobspy_client.py | 132-136 | Single proxy per fetch |
| F6 | Medium | proxy_fetcher.py | 74-87 | No proxy validation |
| F7 | Medium | jobspy_client.py | 336-352 | Missing daily salary interval |
| F8 | Medium | jobspy_client.py | 235-237 | No-op zip_recruiter check |
| F11 | Medium | sync_render_env_from_dotenv.py | 57 | job-sync missing JobSpy vars |
| F12 | Medium | sync_render_env_from_dotenv.py | 60-64 | Agent missing BROWSERLESS_TOKEN |
| F15 | Medium | agent.py | 807-813 | OAuth credentials missing handling |
| F16 | Medium | agent.py | 524-533 | submit_form fallback masks failure |
| F17 | Medium | scaling.py | 405-416 | Workers not using wake_event |
| F20 | Medium | .env.example | - | No JobSpy proxy vars |
| F21 | Medium | config.py | 137 | [REDACTED]_path placeholder |
| F24 | High | config.py | 118-119 | Dev default secrets |
| F9 | Low | job_sync_service.py | 403 | is_scam threshold aggressive |
| F13 | Low | sync_render_env_from_dotenv.py | 41 | "env" vs "ENV" key |
| F18 | Low | agent.py | 759 | Supabase storage import |
| F19 | Low | agent.py | 225-228 | Fragile nth-of-type selector |
| F22 | Low | config.py | 169 | jobspy_proxy_rotation unused |
| F25 | Medium | sync_render_env_from_dotenv.py | 30 | RENDER_API_KEY env |
| F26 | Low | api_auth_middleware.py | 119 | Default jwt secret |

---

**Total: 26 findings** (4 critical, 5 high, 13 medium, 4 low)
