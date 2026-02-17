# Contributing to JobHuntin

This repo powers live job application automation, AI-powered SEO generation, and customer-facing UI. Every change must uphold two guardrails:

1. **Zero-Defect Standard** – No regressions in automation accuracy, Supabase data integrity, or SEO throughput. Ship with exhaustive tests, telemetry, and roll-back plans.
2. **No-Scroll UI Standard** – Any user-facing surface (web, mobile, extension) must keep critical CTAs above the fold. Avoid shipping components that require manual scrolling to reach the primary action unless UX explicitly approves.

## Code of Conduct

- Default to respectful, asynchronous-friendly communication.
- Document decisions in PRs/Issues so on-call staff can reconstruct context.
- Escalate incidents immediately in the on-call channel.

## Workflow

1. **Branching**
   - `main` – deployment-ready.
   - `dev` – staging/integration.
   - Feature: `feat/<scope>`; Hotfix: `fix/<scope>` (branch from `main` if urgent).

2. **Commits**
   - Conventional format: `type(scope): detail`.
   - Squash merge PRs unless release notes require granular history.

3. **Pull Requests**
   - Target `dev` (or `main` for hotfixes).
   - Include: problem statement, before/after screenshots or logs, test evidence, rollout plan.
   - Tag reviewers for every affected area (API, worker, web, SEO, infra).

## Quality Gates

| Area | Required Checks |
| --- | --- |
| Python | `ruff check .`, `pytest`, `mypy` (where configured) |
| Frontend | `npm run lint`, component/unit tests (Vitest/Jest), Storybook updates if UI changes |
| Worker | Run `python -m apps.worker.agent --dry-run` or integration tests covering blueprints touched |
| SEO Scripts | `npm run seo:engine -- --dry-run`, confirm AI model configuration remains consistent |

Telemetry hooks (metrics, logs) must be updated when adding new workflows so the Zero-Defect dashboard reflects reality.

## UX Expectations (No-Scroll UI)

- Keep top-of-fold content actionable on common breakpoints (1280×800, 1440×900). Use the existing layout primitives (`HeroStack`, `CTADeck` in `apps/web`) to guarantee visual consistency.
- Document any exception in the PR description and capture follow-up tasks for responsive tweaks.

## Secrets & Config

- Never hardcode Supabase, Render, or Google keys. Use `.env` (never committed) + `shared.config`.
- Update `.gitignore` if new secret files are introduced.
- For LLM changes: update `shared/config.py`, document cost impact, and tag finance/SEO owners.

## Testing Matrix

- **Backend / Domain** – `pytest tests/test_domain.py tests/test_agent_integration.py`
- **Worker** – `pytest tests/test_agent_integration.py` + manual `python -m apps.worker.agent --dry-run`
- **Web/App** – `npm run test`, `npm run lint`, Percy/Playwright visual tests when components change.
- **Mobile** – `npm run test --workspaces -- mobile`

## Issue Reporting

- Use templates in the tracker.
- Provide reproduction steps, logs, and mention whether AI SEO, database, or Playwright worker fleets are impacted.

## Release Checklist

1. Verify `render.yaml` + Supabase migrations are up to date.
2. Confirm SEO scripts run successfully via `npm run seo:monitor`.
3. Ensure worker scaling scripts (`python -m apps.worker.scaling`) start cleanly.
4. Tag release in Git and update `docs/reports` if this is a major feature.

Thank you for helping us keep JobHuntin operational-grade.
