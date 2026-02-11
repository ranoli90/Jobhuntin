# packages/partners

Partner-specific overrides that sit between the core domain logic and tenant deployments. Each package can inject blueprint defaults, rate limits, and Nemotron prompt tweaks without forking the backend.

## Current modules

| Partner | Location | Notes |
| --- | --- | --- |
| University | `partners/university/` | Overrides blueprint selection + applicant profile transforms for campus programs. Includes SSO helpers and custom Nemotron SEO metadata (e.g., campus-specific landing copy). |

## Usage

- APIs load partner adapters before calling `backend.domain` services. This lets enterprise tenants change default blueprint keys or inject custom prompts.
- Workers read partner metadata via the same adapters to ensure Playwright submissions reflect tenant-specific form variants.
- SEO scripts (apps/web/scripts/seo) reference partner-provided Nemotron prompt fragments so university pages stay on the free `nvidia/nemotron-4-340b-instruct` tier. Do **not** switch models inside partner overrides unless finance signs off.

## Adding a partner

1. Create a subpackage (e.g., `partners/acme/`).
2. Define adapters for:
   - default blueprint slug(s)
   - CanonicalProfile transformations
   - Nemotron SEO metadata (title, description, tone)
3. Register the adapter in the API boot sequence and update tests in `tests/test_agent_integration.py` if worker behavior changes.
