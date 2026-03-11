#!/usr/bin/env bash
# Run Bandit and Flake8 on Python code. Install: pip install -r requirements-dev.txt
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY_PATHS=(apps packages shared scripts)
echo "Running Bandit (security)..."
python3 -m bandit -r "${PY_PATHS[@]}" -x .venv,node_modules,__pycache__ -q 2>/dev/null || true
echo "Running Flake8 (style)..."
python3 -m flake8 "${PY_PATHS[@]}" --config .flake8 2>/dev/null || true
