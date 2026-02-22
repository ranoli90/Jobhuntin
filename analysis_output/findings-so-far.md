# Static Analysis Findings (In-Progress)

Snapshot of results from tools run so far (no code changes applied). Pending tools noted at the end.

## Scope
- Python codebase (apps, backend, packages, scripts)
- JS/TS packages (apps/web, apps/extension, apps/web-admin, jobhuntin-e2e-tests, mobile) — NodeJsScan running
- Repo-wide Semgrep

## Tool Results

### Semgrep (auto rules)
- Status: Completed
- Findings: 68 (blocking) across 511 rules on 674 targets
- Output: `analysis_output/semgrep.json`
- Note: some files >1MB skipped; scan limited to git-tracked files

### Bandit (Python security)
- Status: Completed (exit 1: findings)
- Output: `analysis_output/bandit.json`
- Observations: includes venv noise; filter to project paths when triaging

### Pylint (Python quality/maintainability)
- Status: Completed (exit 1: findings)
- Output: console only (not captured)
- Highlights:
  - Numerous style issues (trailing whitespace, long lines)
  - Duplicate-code (R0801) across multiple scripts (migration/maintenance/test helpers)
  - Missing timeout on `requests.get`
  - Broad `except Exception` occurrences

### Flake8 (Python style)
- Status: Completed (exit 1: findings)
- Output: `analysis_output/flake8.txt`
- Highlights (high-volume):
  - Unused imports (e.g., json, sqlalchemy aliases)
  - Missing/extra blank lines, whitespace issues
  - Many E501 long lines across admin/AI modules and alembic migrations
  - f-strings missing placeholders in `add_database_url.py`

### NodeJsScan (JS/TS security)
- Status: Running on web/extension/web-admin/e2e/mobile
- Output (pending): `analysis_output/nodejsscan.html`

### Radon (Python complexity)
- Status: Running
- Output (pending): `analysis_output/radon_cc.json`

## Blocked/Skipped
- SonarQube CE: **Configured** — Use `npm run sonar` with SonarCloud token (see docs/SONARQUBE_SETUP.md) or `docker compose -f docker/sonarqube.yml up` for local server
- Trivy / Gitleaks / Grype / Syft: Not installed on PATH; not run
- Infer: Not installed; not run

## Next Steps Proposed
1) Let NodeJsScan and Radon finish; capture outputs.
2) Run ESLint with security plugins in JS/TS packages.
3) If binaries provided, run Trivy FS and Gitleaks; generate SBOM (Syft) then Grype.
4) Summarize dependency/hotspot/complexity signals and create normalized JSON + Markdown report.
