# packages/backend

Domain-heavy toolkit that every Python runtime imports. It owns Supabase persistence, blueprint orchestration, and LLM contracts that power both the Playwright FormAgent and the Nemotron SEO writers.

## Layout

| Path | Purpose |
| --- | --- |
| `domain/` | CanonicalProfile models, repositories (`ApplicationRepo`, `JobRepo`, `ProfileRepo`, etc.), transactional helpers, notifications, and Supabase storage utilities. |
| `llm/` | `LLMClient`, prompt registry, and typed response contracts used by both DOM mapping (FormAgent) and the SEO engine. Defaults to `nvidia/nemotron-4-340b-instruct` through OpenRouter—do **not** swap models unless procurement clears the cost impact. |
| `blueprints/` | Registry helpers that hydrate blueprint packages and expose `load_default_blueprints`, `get_blueprint`, and feature gating for job-app/grant/staffing-agency flows. |
| `sso/` | Shared helpers for partner SSO assertions and JWT validation. |

## How it is used

- `apps/api` and `apps/api_v2` import repositories + service functions straight from `domain/` to keep API handlers thin.
- `apps/worker/agent.py` imports `backend.blueprints.registry`, domain repos, and `LLMClient` to drive the Playwright loop.
- `apps/web/scripts/seo/*.ts` hit backend endpoints that ultimately run through `backend.llm` so Nemotron prompts stay centralized.

## Guardrails

- **Nemotron SEO**: Keep the default model identifier (`nvidia/nemotron-4-340b-instruct`). The free tier plus cached prompts make the SEO generator economical; changing it can incur real costs.
- **Transactions**: Always use `domain.repositories.db_transaction` when mixing reads/writes or emitting events.

## Testing

Run `pytest tests/test_domain.py tests/test_agent_integration.py` to cover domain invariants plus worker flows that rely on these modules.
