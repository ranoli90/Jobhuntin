# Sorce / JobHuntin Monorepo

**Outcomes first:** This codebase runs the JobHuntin consumer surfaces, the FastAPI control plane, the Playwright worker fleet that completes "zero-scroll" job applications, and the Nvidia Nemotron–powered SEO engine that keeps the top of funnel fed. Supabase hosts the primary Postgres + storage, Render runs the long-lived services, and shared Python packages keep every surface typed, observable, and rate-limited.

## Architecture at a Glance

- **User & Admin Surfaces** – `apps/web` (Vite/React) and `apps/web-admin` push the "No-Scroll UI" ethos: every CTA lands above the fold and is backed by SSR-friendly SEO copy generated from Nemotron prompts.
- **APIs** – `apps/api` (FastAPI) and `apps/api_v2` expose tenant, application, and blueprint orchestration endpoints. They lean on `packages/backend` for domain models, Supabase storage helpers, and LLM prompt coordination.
- **Automation Workers** – `apps/worker` runs FormAgent + ScalingManager. Each worker polls Supabase queues via `backend.domain.repositories`, drives Playwright through multi-step forms, and emits metrics/telemetry via `packages/shared`.
- **SEO Engine** – `apps/web/scripts/seo/*.ts` orchestrate the Nemotron ranking engine. They hit `backend.llm` through OpenRouter with the `nvidia/nemotron-4-340b-instruct` preset so we stay on a free/high-capacity tier.
- **Shared Libraries** – `packages/shared` (config, logging, redis, telemetry) and `packages/backend` (domain, LLM, blueprint registry) are consumed by every Python runtime to guarantee consistent guardrails.
- **Infrastructure** – `supabase/` + `infra/` track database schema, migrations, Render service manifests, and the Supabase CLI workflow.

## Quick Start (10-Min Path to Value)

> Copy `.env.example` to `.env` and wire it to your Supabase project before running anything.

1. **Clone + bootstrap tooling**
   ```bash
   git clone <repo-url>
   cd sorce
   python -m venv .venv && .venv/Scripts/activate  # `source .venv/bin/activate` on macOS/Linux
   pip install -r requirements.txt
   npm install --prefix apps/web
   npm install --prefix apps/web-admin
   npm install --prefix apps/extension
   npm install --prefix mobile
   ```
2. **Run FastAPI + worker loop**
   ```bash
   export PYTHONPATH="apps;packages"  # Windows: set PYTHONPATH=apps;packages
   uvicorn api.main:app --reload
   python -m apps.worker.agent  # single FormAgent
   # or for horizontal tests
   python -m apps.worker.scaling --instances 4
   ```
3. **Run the consumer web app**
   ```bash
   cd apps/web
   npm run dev
   ```
4. **Kick the SEO engine (Nemotron)**
   ```bash
   cd apps/web
   npm run seo:engine        # automated-ranking-engine.ts (Nemotron prompts)
   npm run seo:monitor       # dashboard + verification via Google APIs
   ```
5. **Mobile sanity check**
   ```bash
   cd mobile
   npm run start
   ```

## Project Map

```
.
├─ apps/
│  ├─ api/            FastAPI v1 surface (tenants, applications, webhook ingestion).
│  ├─ api_v2/         Experimental routes + OpenAPI for new auth/magic-link flows.
│  ├─ web/            Vite/React JobHuntin UI + Nemotron SEO scripts.
│  ├─ web-admin/      Operator dashboard powering staffing agencies + experiments.
│  ├─ extension/      Chromium extension that piggybacks on API contracts.
│  └─ worker/         Playwright FormAgent + scaling harness (asyncpg + Supabase SSL).
├─ packages/
│  ├─ backend/        Domain models, repositories, LLM orchestration, blueprint registry.
│  ├─ blueprints/     Community + staffing-agency blueprints auto-loaded by the worker.
│  ├─ partners/       University + enterprise adapters that override defaults per tenant.
│  └─ shared/         Config, logging, metrics, redis, telemetry, middleware.
├─ scripts/           Render maintenance, load tests, remediation utilities.
├─ infra/             Render + Supabase infrastructure as code (see `infra/supabase`).
├─ supabase/          SQL migrations + CLI helpers.
├─ docs/, plans/      Launch playbooks, audits, and investor-ready reports.
├─ mobile/            Expo/React Native client.
├─ tests/             Pytest suite (agent integration, domain invariants, failure drills).
└─ templates/, templates/emails, etc. for quick blueprint scaffolding.

## Pending Verification

- Database connection to Render PostgreSQL needs verification when network restrictions are lifted
- All code has been updated to use Render database configuration
- Schema initialization will complete once connection is established

## Script & Tooling Inventory

- `apps/web/package.json` scripts prefixed with `seo:*` run the Nemotron SEO batch (generation, submission, monitoring, backend handoffs).
- `scripts/` contains Python utilities for Render remediation, Supabase schema checks, and load tests (Artillery in `scripts/load-test`).
- `deploy-to-render.sh` + `.github/workflows/deploy-render-seo.yml` wire CI/CD.
- `setup-render-env.sh` and `scripts/setup/` scaffolding (ignored via `.gitignore`) keep secrets out of Git.

## Testing & Quality Gates

- **Python** – `pytest` (entire repo) with contracts covering FormAgent, blueprint orchestration, and failure drills.
- **JavaScript** – `apps/web` uses Vitest/Jest-style `npm test`; `mobile` leverages Expo’s Jest preset.
- **Zero-Defect expectation** – see `CONTRIBUTING.md` for review/observability requirements and "No-Scroll UI" checks.

## Deployment & Operations

- **Render** – `render.yaml` + `render_full.json` describe production services (API, worker, SEO engine) plus environment variables.
- **Supabase** – `supabase/migrations.sql` + `infra/supabase/migrations` manage schema; Playwright workers and APIs connect with SSL + connection pooling (`shared.config`).
- **SEO Ops** – `SEO_DEPLOYMENT_COMPLETE.md` documents how the Nemotron engine ships via Render + Google Indexing APIs.

## Documentation Index

- `docs/INDEX.md` – entry point into strategy notes, playbooks, and audits.
- `docs/reports/root-docs/audit_report.md` – security + readiness audits.
- `plans/` – architecture/system plans used during remediation projects.

---

Proprietary. All rights reserved.
