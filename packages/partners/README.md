# packages/partners

Partner-specific overrides that sit between the core domain logic and tenant deployments. Each package can inject blueprint defaults, rate limits, and AI prompt tweaks without forking the backend.

## Current modules

| Partner | Location | Notes |
| --- | --- | --- |
| University | `partners/university/` | Overrides blueprint selection + applicant profile transforms for campus programs. Includes SSO helpers and custom AI SEO metadata (e.g., campus-specific landing copy). |

## Usage

- APIs load partner adapters before calling `backend.domain` services. This lets enterprise tenants change default blueprint keys or inject custom prompts.
- Workers read partner metadata via the same adapters to ensure Playwright submissions reflect tenant-specific form variants.
- SEO scripts (apps/web/scripts/seo) reference partner-provided AI prompt fragments. Model configuration should remain consistent with the platform defaults unless finance signs off on changes.

## Adding a partner

1. Create a subpackage (e.g., `partners/acme/`).
2. Define adapters for:
   - default blueprint slug(s)
   - CanonicalProfile transformations
   - AI SEO metadata (title, description, tone)
3. Register the adapter in the API boot sequence and update tests in `tests/test_agent_integration.py` if worker behavior changes.
