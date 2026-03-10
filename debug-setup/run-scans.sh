#!/usr/bin/env bash
# =============================================================================
# Run All Debug Scans
# Executes static analysis, security, coverage, and quality tools.
# Run from repo root: bash debug-setup/run-scans.sh
# Outputs: debug-setup/logs/
# =============================================================================

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="$ROOT/debug-setup/logs"
mkdir -p "$LOGS"
cd "$ROOT"

[ -d ".venv" ] && source .venv/bin/activate
export PYTHONPATH=apps:packages:.

TS=$(date +%Y%m%d_%H%M%S)
echo "=== Running Debug Scans ($TS) ==="

# --- Python: Ruff ---
echo "[1/12] Ruff..."
ruff check apps packages shared scripts --select E,W,F,I --ignore E501,E402 -o "$LOGS/ruff_$TS.txt" 2>&1 || true

# --- Python: Mypy ---
echo "[2/12] Mypy..."
mypy apps/api/ apps/worker/ packages/backend/ shared/ --ignore-missing-imports --no-error-summary > "$LOGS/mypy_$TS.txt" 2>&1 || true

# --- Python: Bandit ---
echo "[3/12] Bandit..."
bandit -c pyproject.toml -r apps packages shared scripts -x .venv,node_modules,__pycache__ -f txt -q > "$LOGS/bandit_$TS.txt" 2>&1 || true

# --- Python: pip-audit ---
echo "[4/12] pip-audit..."
pip-audit -r requirements.txt -r requirements-dev.txt --ignore-vuln GHSA-7mpr-5m44-h73r > "$LOGS/pip-audit_$TS.txt" 2>&1 || true

# --- Python: Semgrep (use p/python for Python-only; auto requires metrics) ---
echo "[5/12] Semgrep..."
semgrep scan --config p/python --metrics=off apps packages shared scripts -o "$LOGS/semgrep_$TS.json" 2>/dev/null || \
  echo '{"results":[],"note":"Semgrep skipped: use semgrep scan --config auto (with metrics) for full scan"}' > "$LOGS/semgrep_$TS.json"

# --- Python: Vulture ---
echo "[6/12] Vulture..."
vulture apps packages shared scripts --min-confidence 80 > "$LOGS/vulture_$TS.txt" 2>&1 || true

# --- Python: Radon ---
echo "[7/12] Radon..."
radon cc apps packages shared -a -s --total-average > "$LOGS/radon_$TS.txt" 2>&1 || true

# --- Python: pytest-cov ---
echo "[8/12] pytest-cov..."
pytest tests/ -v --tb=short --cov=apps --cov=packages --cov-report=html --cov-report=term-missing --cov-fail-under=0 -q > "$LOGS/pytest-cov_$TS.txt" 2>&1 || true

# --- Web: TypeScript ---
echo "[9/12] TypeScript..."
(cd apps/web && npx tsc --noEmit) > "$LOGS/tsc_$TS.txt" 2>&1 || true

# --- Web: ESLint ---
echo "[10/12] ESLint..."
(cd apps/web && npx eslint src --ext .ts,.tsx --max-warnings 99999) > "$LOGS/eslint_$TS.txt" 2>&1 || true

# --- Docker: Hadolint ---
echo "[11/12] Hadolint..."
docker run --rm -v "$ROOT:/app" -w /app hadolint/hadolint hadolint Dockerfile > "$LOGS/hadolint_$TS.txt" 2>&1 || true

# --- Full audit ---
echo "[12/12] Full-stack audit..."
npm run audit > "$LOGS/full-audit_$TS.txt" 2>&1 || true

echo ""
echo "=== Scans complete. Logs: $LOGS ==="
