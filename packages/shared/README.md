# packages/shared

Infrastructure glue consumed by every Python process (APIs, workers, scripts). These modules expose environment settings, logging, metrics, telemetry, cache helpers, and middleware so each runtime behaves consistently across Render, Supabase, and local dev.

## Modules

| Module | Purpose |
| --- | --- |
| `config.py` | Central Settings object (Pydantic) that reads env vars for Supabase, Render, Browserless, Redis, Playwright, and LLM defaults. Sets `LLM_MODEL` to `nvidia/nemotron-4-340b-instruct` via OpenRouter unless overridden, ensuring SEO scripts stay on the approved free tier. |
| `logging_config.py` | Structured logging setup with JSON support and request-scoped context helpers. |
| `metrics.py` | In-process counters, histograms, and rate limit helpers (`RateLimiter`) wired to StatsD/Prometheus exporters. |
| `telemetry.py` | OpenTelemetry exporters for traces/logs. |
| `cache.py`, `redis_client.py` | TTL caches plus Redis connection helpers (for rate limiting, blueprint caches, etc.). |
| `middleware.py` | FastAPI middleware for correlation IDs, auth, and error shaping. |
| `validators.py` | Shared validators for env and request payloads. |
| `repo_root.py` | Helper to resolve project root paths for scripts/tests. |

## Usage patterns

1. **Bootstrap** – Every Python entry point loads `shared.config.get_settings()` before touching asyncpg/Playwright so DB SSL flags, Supabase URLs, and Nemotron credentials are in memory.
2. **Workers** – `apps/worker/agent.py` imports `RateLimiter`, telemetry, and logging setup from here to enforce throughput caps and emit metrics.
3. **APIs** – FastAPI apps wire `middleware.py` components to enforce Zero-Defect policies (request IDs, auth, structured error responses).

## Guardrails

- **Nemotron enforcement** – `config.py` is the single source of truth for the LLM model string. Altering it without finance approval breaks the "no accidental paid LLM" rule.
- **Supabase SSL** – Settings expose CA paths and toggles; do not bypass them when adding new pools.
- **Rate limits** – Use `RateLimiter` + metrics when adding new bursty operations (magic links, Playwright claims, etc.).
