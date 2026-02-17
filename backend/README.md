# packages/backend

Domain-heavy toolkit that every Python runtime imports. It owns database persistence, blueprint orchestration, and LLM contracts that power both the Playwright FormAgent and the AI-powered SEO writers.

## Layout

| Path | Purpose |
| --- | --- |
| `domain/` | CanonicalProfile models, repositories (`ApplicationRepo`, `JobRepo`, `ProfileRepo`, etc.), transactional helpers, notifications, and storage utilities. |
| `llm/` | `LLMClient`, prompt registry, and typed response contracts used by both DOM mapping (FormAgent) and the SEO engine. Defaults to `google/gemini-2.0-flash` through OpenRouter—do **not** swap models without procurement clearance. |
| `blueprints/` | Registry helpers that hydrate blueprint packages and expose `load_default_blueprints`, `get_blueprint`, and feature gating for job-app/grant/staffing-agency flows. |
| `sso/` | Shared helpers for partner SSO assertions and JWT validation. |

## How it is used

- `apps/api` and `apps/api_v2` import repositories + service functions straight from `domain/` to keep API handlers thin.
- `apps/worker/agent.py` imports `backend.blueprints.registry`, domain repos, and `LLMClient` to drive the Playwright loop.
- `apps/web/scripts/seo/*.ts` hit backend endpoints that ultimately run through `backend.llm` so AI prompts stay centralized.

## Guardrails

- **AI SEO**: Keep the default model identifier (`google/gemini-2.0-flash`). This model provides optimal cost/performance balance; changing it can incur different costs.
- **Transactions**: Always use `domain.repositories.db_transaction` when mixing reads/writes or emitting events.

## Testing

Run `pytest tests/test_domain.py tests/test_agent_integration.py` to cover domain invariants plus worker flows that rely on these modules.
