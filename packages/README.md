# Packages

Shared Python libraries imported by the API, worker, CLI scripts, and tests. They keep database connections, Playwright agents, AI SEO calls, and blueprint orchestration consistent across runtimes.

## `backend/`
- **domain/** – CanonicalProfile models, repositories, and transaction helpers wrapping PostgreSQL (asyncpg). The worker and API both import these modules to fetch jobs, claim tasks, and emit application events.
- **llm/** – `LLMClient` + prompt registries for both the FormAgent DOM mapping flow and the AI-powered SEO content engine. Defaults to the OpenRouter `google/gemini-2.0-flash` model for optimal cost/performance unless `LLM_MODEL` overrides it.
- **blueprints/** – Registry helpers that load `packages/blueprints` definitions and expose them to APIs/workers. Includes default blueprint loading (job-app, grant, staffing-agency) driven by `shared.config` feature flags.
- **sso/** – Shared auth helpers for partner SSO integrations.

## `blueprints/`
- Houses the actual workflow definitions (community, staffing_agency, etc.). Each blueprint declares the form schema, hold-question policies, and UI/worker copy. The worker's `load_default_blueprints` call pulls from here on startup, so updates land without touching the FormAgent loop.

## `partners/`
- Tenant-specific adapters (currently `university/`) that override default prompts, rate limits, or blueprint selections. APIs consult these modules before dispatching to keep enterprise tenants isolated.

## `shared/`
- Cross-cutting infrastructure: `config.py` (database URLs, Browserless tokens, LLM defaults), `logging_config.py`, `metrics.py`, Redis clients, telemetry wiring, and middleware primitives. Every Python entry point imports `shared` before touching asyncpg/Playwright so we get uniform tracing + guardrails.
