# Audit Tools (No Sign-Up Required)

This repo uses **free, no sign-up** tools for bugs, bottlenecks, anti-patterns, security, code quality, dead code, broken imports, and UI/UX (a11y).

## Installed Tools

### Frontend (apps/web)

| Tool | Purpose | Command |
|------|---------|---------|
| **TypeScript** | Broken imports, type errors | `npm run audit:tsc` |
| **ESLint** | Code quality, security, a11y, anti-patterns | `npm run lint` |
| **depcheck** | Unused dependencies | `npm run audit:deps` |
| **knip** | Dead code, unused exports | `npm run audit:dead` |
| **npm audit** | Dependency vulnerabilities | `npm run audit:npm` |
| **@axe-core/cli** | Accessibility (UI/UX) | `npm run dev` (then in another terminal) `npm run audit:a11y` |

### Backend (Python)

| Tool | Purpose | Command |
|------|---------|---------|
| **ruff** | Lint, style | `ruff check apps packages shared scripts --select E,W,F,I` |
| **mypy** | Type checking | `PYTHONPATH=apps:packages:. mypy apps/api/ apps/worker/ packages/backend/ shared/ --ignore-missing-imports` |
| **bandit** | Security issues | `bandit -r apps packages shared scripts -x .venv,node_modules,__pycache__` |
| **pip-audit** | Dependency vulnerabilities | `pip-audit -r requirements.txt -r requirements-dev.txt` |
| **vulture** | Dead code | `vulture apps packages shared scripts --min-confidence 80` |
| **radon** | Cyclomatic complexity | `radon cc apps packages shared -a -s` |

### Run Full-Stack Audit

From repo root:

```bash
# Install Python audit tools first (once)
pip install -r requirements-dev.txt

# Install web deps (once; use --legacy-peer-deps if needed)
cd apps/web && npm install --legacy-peer-deps && cd ../..

# Run all audits and write report
npm run audit:full
```

Report is written to `audit-report-<timestamp>.txt` in the repo root.

Skip npm install (use existing node_modules):

```bash
npm run audit:full:skip-install
```

## What Each Category Covers

- **Bugs / broken imports**: TypeScript (`tsc --noEmit`), ESLint `import/no-unresolved`, mypy
- **Bottlenecks / complexity**: radon (CC), ESLint sonarjs cognitive-complexity
- **Anti-patterns**: ESLint (sonarjs, security, promise, unicorn)
- **Security**: ESLint security plugin, bandit, npm audit, pip-audit
- **Code quality**: ESLint, ruff, black
- **Dead code**: knip, vulture
- **UI/UX / a11y**: ESLint jsx-a11y, @axe-core/cli

## Accessibility Audit (a11y)

1. Start the web app: `cd apps/web && npm run dev`
2. In another terminal: `cd apps/web && npm run audit:a11y`
3. Or pass a URL: `node scripts/audit-a11y.js http://localhost:5173`
