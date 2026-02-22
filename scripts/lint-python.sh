#!/usr/bin/env bash
# Run Bandit and Flake8 on Python code. Install: pip install bandit flake8
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "Running Bandit..."
python3 -m bandit -r backend apps packages scripts -x .venv,node_modules,__pycache__ -q 2>/dev/null || true
echo "Running Flake8..."
python3 -m flake8 backend apps packages scripts --config .flake8 2>/dev/null || true
