# JobSpy Advanced Implementation Plan

**Goal:** 5000 concurrent users, perfect-match jobs, spam-free, fresh jobs first, near-perfect bot avoidance, free/low-cost proxies, per-user feeds.

---

## 1. Proxy Strategy (Free / Low-Cost)

| Tier | Source | Cost | Use |
|------|--------|------|-----|
| **Primary** | GimmeProxy API | Free | Per-request new proxy; no signup |
| **Secondary** | PubProxy, GetProxyList | Free | Fallback when GimmeProxy fails |
| **Self-hosted** | ProxyScraper + validation | VPS cost | Scrape free lists, validate, use once |
| **Kill-after-1-use** | GimmeProxy returns new proxy per request | — | Natural single-use |

**Implementation:** Proxy fetcher service that pulls from GimmeProxy/PubProxy; validate with httpbin; rotate per scrape call.

---

## 2. Bot Detection Avoidance

| Mitigation | Implementation |
|------------|----------------|
| User-Agent rotation | 10+ realistic UAs (Chrome, Firefox, Safari); rotate per request |
| Request throttling | 5–15s delay between (search_term, location) queries |
| Proxy per source | New proxy per source (Indeed, LinkedIn, etc.) |
| Human-like delays | Random 2–10s between requests |
| Residential preference | Use ProxyShare free tier or ScraperAPI free (1K/mo) for tough boards |

---

## 3. Job Boards (JobSpy)

- **Indeed, LinkedIn, ZipRecruiter, Glassdoor** — HTTP scraping
- **Adzuna** — REST API (fallback)
- **Indeed Publisher API** — Use when available (25 results/query, free)

---

## 4. Spam Filtering

- Persist `is_scam`, `quality_score` at sync
- Expand indicators: MLM, commission-only, crypto, SSN, Gmail contact
- Filter `is_scam=true` in queries

---

## 5. Fresh Jobs & Interview Likelihood

- `hours_old`: 72 for fresh mode, 168 default
- Sort: `interview_likelihood` = 0.5*match + 0.3*recency + 0.2*source_trust
- Source trust: LinkedIn 1.0, Glassdoor 0.9, ZipRecruiter 0.8, Indeed 0.7

---

## 6. Scale Architecture (5K Users)

- Sync by (role, location) — dedupe; ~50–100 unique pairs vs 5K users
- Batch upsert (ON CONFLICT)
- Redis cache for user feeds (60s TTL)
- Precompute match_scores for active users

---

## Implementation Phases

**Phase 1 (DONE):**
- [x] Proxy rotation (round-robin when configured; fetch from GimmeProxy/PubProxy when `jobspy_use_free_proxies=true`)
- [x] User-Agent rotation (8 realistic UAs, random per request)
- [x] Persist `is_scam`, `quality_score` at sync; filter `is_scam=true` in job search
- [x] Batch upsert (50 jobs per batch, unnest + ON CONFLICT)

**Phase 2:** Interview likelihood sort, source weighting
**Phase 3:** Redis feed cache, GimmeProxy integration
