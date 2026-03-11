# JobSpy Integration Audit Findings

**Generated:** 2026-03-11  
**Sources:** 3 sub-agent audits (architecture, scraping implementation, user-specific design)

---

## Executive Summary

JobSpy scrapes jobs **globally** every 4 hours using aggregated search queries. Jobs are stored in a shared `public.jobs` table. User personalization happens at **read time** (match scoring, dealbreakers), not at scrape time. Several schema mismatches and missing pieces could cause sync failures.

---

## 1. Current Implementation

### 1.1 Entry Points

| Trigger | Location | When |
|---------|----------|------|
| **Background worker** | `apps/worker/job_sync_worker.py` | Startup + every 4h |
| **Admin (tenant)** | `POST /me/admin/jobs/sync/trigger` | Manual |
| **Admin (system)** | `POST /jobs/sync` | Manual |
| **Adzuna fallback** | `job_search.py` | First search when DB empty |

### 1.2 Data Flow

```
Triggers → JobSyncService.sync_all_sources()
         → _get_search_queries() (popular_searches, user_preferences, profiles, or DEFAULT)
         → For each (search_term, location): JobSpyClient.fetch_jobs()
         → jobspy.scrape_jobs() (HTTP, no browser)
         → _normalize_jobs() → UPSERT public.jobs (by external_id)
         → cleanup_expired_jobs(), _record_sync_complete()
```

### 1.3 Search Parameters (Current)

| Source | Used for scraping? |
|-------|--------------------|
| `popular_searches` (top 10) | Yes |
| `user_preferences` (role_type, location) | Yes, aggregated DISTINCT |
| `profiles.profile_data` (role_type, location, target_roles) | Yes, aggregated |
| `job_alerts` (keywords, locations, salary, remote) | **No** |
| `salary_min`, `salary_max`, `remote_only` | **No** |
| `DEFAULT_SEARCH_QUERIES` | Fallback (software engineer, product manager, etc.) |

### 1.4 Job Sources

- **JobSpy:** Indeed, LinkedIn, ZipRecruiter, Glassdoor
- **Adzuna:** REST API fallback when DB empty

---

## 2. Bugs & Missing Pieces

### Critical: Schema Mismatches (FIXED 2026-03-11)

| Issue | File | Schema | Code Expects |
|-------|------|--------|--------------|
| **job_sync_runs** | job_sync_service.py:519 | `source, status, jobs_fetched, jobs_new, jobs_updated, jobs_skipped, errors, duration_ms, started_at, completed_at` | Inserts `search_term`, `location` (columns don't exist) |
| **job_sync_runs** | job_sync_service.py:545 | `errors` (JSONB) | Updates `error_message` (column doesn't exist) |
| **job_sync_config** | job_sync_service.py:578 | `last_synced_at` only | Updates `last_sync_at`, `consecutive_failures`, `total_jobs_fetched`, `total_syncs`, `last_error_at`, `last_error_message` (none exist) |
| **cleanup_expired_jobs** | job_sync_service.py:606 | — | Calls `public.cleanup_expired_jobs($1)` — function not in migrations |
| **job_source_stats** | job_sync_service.py:634 | — | Fallback: derive from job_sync_runs when table missing |

### Medium

| Issue | Description |
|-------|-------------|
| **No JobSpy rate limiting** | Relies on circuit breaker only; no proactive throttling |
| **No retries** | Sync failures are logged; no retry with backoff |
| **Proxy rotation** | `_get_proxy()` always returns `proxies[0]`; rotation not implemented |
| **Salary interval** | Hourly/weekly conversion may fail if JobSpy returns numeric interval |
| **Concurrent sync** | `_running` flag not persisted; multiple workers could sync simultaneously |

### Low

| Issue | Description |
|-------|-------------|
| **Job schema gaps** | `emails`, `skills`, `benefits`, `is_scam`, `quality_score` not stored |
| **Exception scope** | `_normalize_job` exception handler may reference undefined `k` |

---

## 3. Per-User vs Global Design

### Current: Global

- One sync run for all users
- Same job pool for everyone
- Personalization at read time (match score, dealbreakers)

### Proposed: Per-User, On-Login, Every 3 Hours

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Trigger** | Worker every 4h | On login + every 3h per user |
| **Queries** | Aggregated from all users | User's profile, preferences, job_alerts |
| **Scope** | Global job pool | User-specific scrape (still writes to shared `jobs` table) |
| **Interval** | 4 hours | 3 hours |

### Pros of Per-User Scraping

1. **Relevance:** Jobs match the user's role, location, salary, remote preference
2. **Freshness:** New users get jobs immediately on login
3. **Efficiency:** Don't scrape irrelevant (role, location) combos for inactive users
4. **Job alerts alignment:** Use same queries as job_alerts for consistency

### Cons / Considerations

1. **Rate limits:** More scrape calls (one per user × sources); need throttling
2. **Cost:** JobSpy/proxy usage scales with active users
3. **Deduplication:** Same job can be scraped for multiple users; `external_id` handles this
4. **Cold start:** New user with no profile gets default queries

### Implementation Path

1. **Add `sync_for_user(user_id)`** to `JobSyncService`:
   - Load `user_preferences`, `profiles.profile_data`, `job_alerts` for that user
   - Build queries from those sources (role, location, salary, remote)
   - Call existing scrape pipeline with user-specific queries

2. **On-login hook** in `auth.py`:
   - After successful login, enqueue `sync_user_jobs` job with `user_id`
   - Job queue worker processes it (or dedicated sync worker)

3. **Per-user scheduler** (every 3h):
   - Option A: Cron/worker iterates active users, enqueues sync per user
   - Option B: Per-user "last_synced_at" in DB; worker picks users due for sync
   - Option C: Frontend triggers `POST /me/jobs/refresh` which enqueues sync (user-initiated)

4. **Config:** `jobspy_sync_interval_hours = 3` for global worker; per-user interval could be separate

5. **Include job_alerts** in `_get_search_queries()` for both global and per-user paths

---

## 4. Expanded Recommendations

### Immediate Fixes

1. **Verify schema:** Ensure `job_sync_runs`, `job_sync_config`, `cleanup_expired_jobs`, `job_source_stats` exist and match code
2. **Add retries:** Retry JobSpy fetch 2–3 times with exponential backoff on transient failures
3. **Use job_alerts:** Include `job_alerts` (keywords, locations) in query building

### Per-User Scraping (Phase 2)

1. **`sync_for_user(user_id)`** – user-specific query building and sync
2. **Login hook** – enqueue sync on first login / return visit
3. **3-hour interval** – config change + per-user last_synced tracking
4. **Throttling** – limit concurrent per-user syncs, respect JobSpy rate limits

### Implemented (2026-03-11)

- **Login hook:** `sync_for_user` triggered on magic-link verification (fire-and-forget)
- **3-hour interval:** `jobspy_sync_interval_hours` default changed from 4 to 3
- **Retries:** JobSpy fetch retries up to 2 times with exponential backoff (1s, 2s)

### Further Enhancements

- **Job alerts as primary driver:** When user has job_alerts, use those exclusively for their sync
- **Priority users:** Sync active users (recent login) more frequently
- **Geographic batching:** Group users by location to reduce duplicate (location, role) scrapes
- **Fallback to global:** If user has no profile/preferences, use popular_searches or defaults

---

## 5. File Reference

| File | Purpose |
|------|---------|
| `packages/backend/domain/jobspy_client.py` | JobSpy scrape wrapper, circuit breaker |
| `packages/backend/domain/job_sync_service.py` | Sync orchestration, query building, DB upsert |
| `packages/backend/domain/job_boards.py` | Adzuna API client |
| `apps/worker/job_sync_worker.py` | Background worker loop |
| `packages/backend/domain/job_search.py` | Search + Adzuna fallback |
| `shared/config.py` | JobSpy config (sources, interval, etc.) |
