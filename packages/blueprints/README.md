# packages/blueprints

Blueprint definitions that describe end-to-end workflows for each tenant vertical. Every blueprint exposes:
- canonical form schemas (fields, selectors, DOM hints)
- hold-question policies for the worker escalation path
- copy/UX overrides for JobHuntin surfaces

## Directory Map

| Path | Purpose |
| --- | --- |
| `community/scholarship/` | Blueprint for scholarship-style applications (multi-step forms, essay uploads). |
| `community/vendor_onboard/` | Vendor onboarding flows leveraging the Job App canonical profile. |
| `staffing_agency/` | Staffing/agency-specific flows including pay transparency steps and compliance attestations. |

## How they load

`backend.blueprints.registry.load_default_blueprints()` imports these packages at worker start-up. APIs also call `get_blueprint()` before kicking off a job so the same definition drives both UI hints and the Playwright agent DOM mapping prompts.

## SEO / LLM Coordination

Blueprint descriptors embed prompt fragments that the `backend.llm` module stitches into the AI-powered SEO generator as well as the FormAgent DOM mapping prompts. Model identifiers in blueprint metadata help maintain consistent LLM configuration across the platform.
