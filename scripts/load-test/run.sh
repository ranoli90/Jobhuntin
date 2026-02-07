#!/usr/bin/env bash
# Load test runner for Sorce API
#
# Prerequisites:
#   npm install -g artillery@latest artillery-plugin-expect
#
# Usage:
#   API_URL=https://api.sorce.app TEST_TOKEN=xxx ./run.sh
#   API_URL=http://localhost:8000 TEST_TOKEN=xxx ./run.sh --quick

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

: "${API_URL:=http://localhost:8000}"
: "${TEST_TOKEN:=test-token}"

export API_URL TEST_TOKEN

echo "=== Sorce Load Test ==="
echo "Target: $API_URL"
echo ""

if [[ "${1:-}" == "--quick" ]]; then
    echo "Running quick smoke test (10s, 5 rps)..."
    artillery quick \
        --count 50 \
        --num 5 \
        "$API_URL/health"
else
    echo "Running full load test..."
    artillery run "$SCRIPT_DIR/artillery.yml" \
        --output "$SCRIPT_DIR/report.json"

    echo ""
    echo "Generating HTML report..."
    artillery report "$SCRIPT_DIR/report.json" \
        --output "$SCRIPT_DIR/report.html"

    echo ""
    echo "Report: $SCRIPT_DIR/report.html"
fi

echo ""
echo "=== Done ==="
