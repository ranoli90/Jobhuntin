#!/usr/bin/env bash
# =============================================================================
# Debug Tools Installer
# Installs all debugging, analysis, and monitoring tools for the Sorce codebase.
# Run from repo root: bash debug-setup/install-tools.sh
# =============================================================================

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=== Debug Tools Installer ==="
echo "Root: $ROOT"
echo ""

# --- Python tools ---
echo "--- Installing Python tools ---"
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi
pip install -r requirements-dev.txt -q
pip install ipdb python-docx -q  # Runtime debugger + missing test dep
echo "Python: ruff, mypy, bandit, semgrep, vulture, radon, deptry, detect-secrets, pip-audit, pytest-cov installed"

# --- Node/Web tools ---
echo "--- Installing Node tools ---"
npm install
cd apps/web && npm install && cd "$ROOT"
echo "Node: ESLint, depcheck, knip, type-coverage, hadolint installed"

# --- Verify installations ---
echo ""
echo "--- Verification ---"
python -m ruff --version 2>/dev/null || echo "ruff: not found"
python -m mypy --version 2>/dev/null || echo "mypy: not found"
python -m bandit --version 2>/dev/null || echo "bandit: not found"
semgrep --version 2>/dev/null || python -m semgrep --version 2>/dev/null || echo "semgrep: not found"
python -m vulture --version 2>/dev/null || echo "vulture: not found"
python -m radon --version 2>/dev/null || echo "radon: not found"
python -m pip_audit --version 2>/dev/null || echo "pip-audit: not found"
python -m pytest --version 2>/dev/null || echo "pytest: not found"
npx depcheck --version 2>/dev/null || echo "depcheck: not found"
npx knip --version 2>/dev/null || echo "knip: not found"
npx type-coverage --version 2>/dev/null || echo "type-coverage: not found"

echo ""
echo "=== Install complete ==="
