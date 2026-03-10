# Codebase Debug Plan — Sorce / JobHuntin.com

**Generated:** 2026-03-10  
**Codebase:** Full-stack SaaS (FastAPI backend, Vite/React frontend, PostgreSQL, Redis, Playwright worker)

---

## 1. Inventory Table

| Tool | Category | Install Cmd | Run Cmd | Status | Key Findings |
|------|----------|-------------|---------|--------|--------------|
| **ruff** | Static Analysis | `pip install ruff` | `ruff check apps packages shared scripts --select E,W,F,I` | ✅ Installed | 1189 errors: E501 (1131), E402 (58); F-codes 0 |
| **mypy** | Type Checking | `pip install mypy` | `mypy apps/api/ packages/backend/ --ignore-missing-imports` | ✅ Installed | 624 errors: attr-defined, assignment, union-attr, no-any-return |
| **bandit** | Security | `pip install bandit` | `bandit -c pyproject.toml -r apps packages shared` | ✅ Installed | 58 High, 11 Medium (B110 try_except_pass, B608 SQL, etc.) |
| **pip-audit** | Vulnerabilities | `pip install pip-audit` | `pip-audit -r requirements.txt -r requirements-dev.txt` | ✅ Installed | No known vulns (1 ignored: GHSA-7mpr-5m44-h73r) |
| **semgrep** | Security/Bugs | `pip install semgrep` | `semgrep scan --config p/python apps packages shared` | ✅ Installed | Use `p/python` or `p/default` (auto requires metrics) |
| **vulture** | Dead Code | `pip install vulture` | `vulture apps packages shared --min-confidence 80` | ✅ Installed | 16 unused variables across 8 files |
| **radon** | Complexity | `pip install radon` | `radon cc apps packages shared -a -s` | ✅ Installed | 5707 blocks, avg 3.45; CapacityPlanner._calculate_trend_confidence B(9) |
| **deptry** | Deps | `pip install deptry` | `deptry . --no-cache` | ✅ Installed | Dependency consistency |
| **detect-secrets** | Secrets | `pip install detect-secrets` | `detect_secrets scan apps packages shared --all-files` | ✅ Installed | Potential secrets detected (exit 120) |
| **pytest-cov** | Coverage | `pip install pytest-cov` | `pytest tests/ --cov=apps --cov=packages --cov-report=html` | ✅ Installed | 160 passed, 38 skipped, 0 failed; ~2% coverage |
| **TypeScript** | Type Check | `npm install` | `cd apps/web && npx tsc --noEmit` | ✅ Installed | 9+ errors: missing @sentry/react, react-i18next, implicit any |
| **ESLint** | Lint | `npm install` | `cd apps/web && npx eslint src --ext .ts,.tsx` | ⚠️ Partial | Plugin missing: eslint-plugin-react |
| **depcheck** | Unused deps | `npm install` | `npx depcheck` | ✅ Installed | Unused: @tanstack/react-virtual; Missing: playwright |
| **knip** | Dead Code | `npm install` | `npx knip` | ✅ Installed | 71 unused files, 7 unused deps |
| **hadolint** | Docker | `npm install` | `docker run hadolint/hadolint hadolint Dockerfile` | ✅ Installed | 0 issues (previously DL3008, DL3013, DL3025, DL3059 — fixed) |
| **SonarQube** | Multi-language | `npm install @sonar/scan` | `npm run sonar` | ✅ Installed | Requires SONAR_TOKEN, SONAR_ORGANIZATION |

---

## 2. Issues Summary

| Issue Type | File/Line | Severity | Fix Suggestion | Tool Source |
|------------|-----------|----------|----------------|-------------|
| **Undefined name** | apps/api/ai.py:703, 811 | Critical | `db` should be injected or passed; fix scope | ruff F821 |
| **Undefined name** | apps/api/analytics.py:82 | Critical | `TenantContext` undefined; add import or use correct type | ruff F821 |
| **Redefinition** | apps/api/main.py:286 | High | Remove duplicate `observe`, `incr` imports; fix F811 | ruff F811 |
| **Unused variable** | apps/api/dependencies.py:253 | Medium | Remove or use `session_id` | ruff F841 |
| **try_except_pass** | apps/api/sessions.py:88, 131 | Low | Replace with explicit logging or re-raise | bandit B110 |
| **Type: BaseException not iterable** | packages/backend/domain/batch_ops.py:105 | High | Fix exception handling; ensure iterable | mypy |
| **Type: attr-defined** | packages/backend/domain/query_optimizer.py:237 | High | Add `_analyze_query_pattern_for_indexes` or fix call | mypy |
| **Type: name-defined** | packages/backend/domain/match_weights.py:588, 593, 601 | Critical | Define `exact_matches`, `user_skill_set` | mypy |
| **Type: attr-defined** | packages/backend/domain/performance_monitor.py:862, 898 | High | Add `created_at` to PerformanceMetric/PerformanceAlert | mypy |
| **Type: attr-defined** | apps/api/match_weights.py:127+ | High | `backend.domain.repositories.get_pool` missing; fix API | mypy |
| ~~**Syntax: async with**~~ | ~~tests/~~ | Critical | ✅ Fixed — tests use async def | pytest |
| ~~**ImportError**~~ | ~~tests/~~ | Critical | ✅ Fixed — python-docx, import paths | pytest |
| **Missing module** | apps/web: @sentry/react, react-i18next | High | `npm install` in apps/web; ensure deps in package.json | tsc |
| **Implicit any** | apps/web/src/main.tsx:34 | Medium | Add types for event, hint | tsc |
| **Unused files** | 71 files in apps/web | Medium | Remove or wire up dead components; knip reports | knip |
| **Unused deps** | @tanstack/react-virtual, redis, zod, etc. | Low | Remove or use; depcheck/knip | depcheck |
| ~~**Dockerfile**~~ | ~~Dockerfile:22, 62, 83~~ | Low | ✅ Fixed — Hadolint 0 issues | hadolint |
| **Secrets** | detect-secrets | Medium | Review and fix/rotate any real secrets | detect-secrets |

---

## 3. Prioritized Roadmap

### Quick Wins (< 1 hour)

1. ~~**Fix test collection errors**~~ ✅ **DONE**
   - Tests: 160 passed, 38 skipped, 0 failed. Collection errors and async test syntax fixed.

2. **Fix critical undefined names**
   - `apps/api/ai.py`: Inject or pass `db` correctly
   - `apps/api/analytics.py`: Add `TenantContext` import or fix reference

3. **Fix web dependencies**
   - `cd apps/web && npm install` (ensure all deps installed)
   - `npm install eslint-plugin-react --save-dev` if ESLint fails

4. **Fix main.py redefinition**
   - Remove duplicate `observe`, `incr` imports; consolidate imports

### Medium (1–3 days)

5. **Reduce ruff errors**
   - Run `ruff format .` and `ruff check --fix` for auto-fixable (W291, W293, I001)
   - Address remaining F821, F841 manually

6. **Fix mypy critical errors**
   - `match_weights.py`: Define `exact_matches`, `user_skill_set`
   - `batch_ops.py`: Fix BaseException iteration
   - `query_optimizer.py`: Add missing method or fix call
   - `performance_monitor.py`: Add `created_at` to models

7. **Improve test coverage**
   - Fix failing tests (test_domain.py LLM mocks)
   - Add integration tests for critical paths
   - Target: > 50% coverage for apps/api, packages/backend

8. **Clean up dead code**
   - Remove or wire up 71 unused web files (knip)
   - Remove unused variables (vulture)

9. **Bandit fixes**
   - Replace `try_except_pass` in sessions.py with logging or minimal handling
   - Address 58 High + 11 Medium findings (B608 SQL whitelisted, B110, etc.)

### Long-term

10. **Mypy strict mode**
    - Enable `--check-untyped-defs`; add type annotations gradually
    - Fix 624 remaining errors (apps/api, packages/backend)

11. **SonarQube integration**
    - Add `sonar-project.properties` (see debug-setup/)
    - Set SONAR_TOKEN, SONAR_ORGANIZATION in CI
    - Use coverage.xml for Python coverage

12. **Dynamic analysis**
    - OWASP ZAP for web app security (if API is exposed)
    - Valgrind for native C extensions (if any)

13. **Performance profiling**
    - Add OpenTelemetry spans for critical paths (already in use)
    - Consider JMeter or k6 for load testing

---

## 4. Launch Checklist

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Ruff (E,W,F,I) | 0 | 1189 | ❌ |
| Ruff F (bugs) | 0 | 0 | ✅ |
| Mypy errors | 0 | 624 | ❌ |
| Bandit high/critical | 0 | 58 High, 11 Medium | ❌ |
| pip-audit vulns | 0 | 0 | ✅ |
| Test collection | 0 errors | 0 errors | ✅ |
| Test pass rate | 100% | 160 passed, 38 skipped | ✅ |
| Coverage | > 80% | ~2% | ❌ |
| TypeScript errors | 0 | 9+ | ❌ |
| ESLint | 0 | Plugin missing | ⚠️ |
| Hadolint | 0 | 0 | ✅ |

**Verification commands:**
```bash
# Run full audit
make audit
# or
npm run audit

# Run scans
bash debug-setup/run-scans.sh
```

**Metrics gathered:** 2026-03-10
- `ruff check apps packages shared scripts --select E,W,F,I` → 1189 errors (E501, E402)
- `mypy apps/api/ packages/backend/ --ignore-missing-imports` → 624 errors
- `pytest tests/ -v -q --tb=line` → 160 passed, 38 skipped, 2 warnings
- `bandit -c pyproject.toml -r apps packages shared` → 58 High, 11 Medium
- `hadolint Dockerfile` → 0 issues

---

## 4b. Post-cleanup (Applied by Other Agents)

| Item | Before | After | Notes |
|------|--------|-------|-------|
| **Test collection** | 5 errors | 0 | python-docx, async test syntax fixed |
| **Test failures** | 2 failed | 0 failed | All 160 pass, 38 skip |
| **Hadolint** | 3–4 warnings (DL3008, etc.) | 0 | Dockerfile fixes applied |
| **Ruff F-codes** | F821, F841, F811 | 0 | Critical undefined/redef bugs fixed |
| **Ruff total** | 403 | 1189 | E501/E402 now in scope (scripts added); style-only |

**Sprints 1–7 (from docs):** Test schema fixes ✅, Mypy fixes (partial) ✅, Bandit status documented ✅, Hadolint ✅, Production Readiness Sprint 0–1 ✅. See `docs/DEEP_AUDIT_SPRINT_PLAN.md`, `docs/reports/production_readiness_sprint_plan.md`.

---

## 5. Scripts Folder

| Script | Purpose |
|--------|---------|
| `debug-setup/install-tools.sh` | Batch-install Python + Node tools |
| `debug-setup/run-scans.sh` | Run all scans; output to logs/ |
| `debug-setup/sonar-project.properties` | SonarQube config template |
| `scripts/full-stack-audit.js` | Existing unified audit script |

**Usage:**
```bash
# Install
bash debug-setup/install-tools.sh

# Run scans
bash debug-setup/run-scans.sh

# View logs
ls debug-setup/logs/
```

---

## 6. CI Integration

Existing workflows:
- `.github/workflows/ci.yml` — lint, test, build, deploy
- `.github/workflows/sonar.yml` — SonarCloud scan

**Recommended additions:**
- Add `debug-setup/run-scans.sh` as a CI job (optional, non-blocking)
- Copy `debug-setup/sonar-project.properties` to repo root for SonarCloud
- Add `coverage.xml` upload step for SonarCloud (already in CI)

---

## 7. Cross-Verification

| Finding | Ruff | Mypy | Bandit | Semgrep |
|--------|------|------|--------|---------|
| `db` undefined in ai.py | ✅ (F-codes 0 now) | — | — | — |
| try_except_pass | — | — | ✅ | — |
| get_pool missing | — | ✅ | — | — |
| match_weights names | — | ✅ | — | — |

Recommendation: Run `make audit` and `ruff check` on every PR; address critical and high severity before merge.

---

## 8. Optional: Docker-Based Tools (2026)

For deeper analysis, consider adding:

| Tool | Purpose | Docker Run |
|------|---------|------------|
| **SonarQube CE** | Multi-language quality gate | `docker run -d -p 9000:9000 sonarqube:community` |
| **OWASP ZAP** | Web app security (dynamic) | `docker run -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:5173` |
| **ELK Stack** | Log aggregation | `docker compose -f elk-docker-compose.yml up` |
| **OpenObserve** | Observability | `docker run -p 5080:5080 openobserve/openobserve` |

These require additional setup and are not included in the default `run-scans.sh`.
