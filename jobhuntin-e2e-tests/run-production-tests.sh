#!/bin/bash

# Production Readiness Validation Script
# This script runs the complete browser automation test suite for JobHuntin

set -e

echo "🚀 Starting JobHuntin Production Readiness Validation"
echo "=================================================="

# Check environment variables
if [ -z "$BASE_URL" ]; then
    echo "⚠️  BASE_URL not set, using default: https://jobhuntin.com"
    export BASE_URL="https://jobhuntin.com"
fi

if [ -z "$TEST_EMAIL" ]; then
    echo "⚠️  TEST_EMAIL not set, using default: test-e2e-production@jobhuntin.com"
    export TEST_EMAIL="test-e2e-production@jobhuntin.com"
fi

echo "📊 Configuration:"
echo "   - Base URL: $BASE_URL"
echo "   - Test Email: $TEST_EMAIL"
echo "   - Environment: ${NODE_ENV:-production}"
echo "   - CI Mode: ${CI:-false}"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm ci
fi

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
npx playwright install

# Create reports directory
echo "📁 Creating reports directory..."
mkdir -p reports/screenshots
mkdir -p reports/html
mkdir -p test-results

# Run the production readiness test suite
echo "🧪 Running Production Readiness Test Suite..."
echo "=================================================="

# Run tests with production configuration
npx playwright test --config=playwright.config.production.ts

# Generate test report
echo "📊 Generating test report..."
npx playwright show-report reports/html

# Check test results
echo "📈 Test Results Summary:"
if [ -f "reports/results.json" ]; then
    node -e "
    const results = JSON.parse(require('fs').readFileSync('reports/results.json', 'utf8'));
    const totalTests = results.suites?.reduce((acc, suite) => acc + (suite.specs?.length || 0), 0) || 0;
    console.log(\`   - Total tests: \${totalTests}\`);
    console.log(\`   - Passed: \${results.passed || 0}\`);
    console.log(\`   - Failed: \${results.failed || 0}\`);
    console.log(\`   - Flaky: \${results.flaky || 0}\`);
    console.log(\`   - Skipped: \${results.skipped || 0}\`);
    
    if (results.failed > 0) {
        console.log('❌ Some tests failed - check reports for details');
        process.exit(1);
    } else {
        console.log('✅ All tests passed!');
    }
    "
else {
    echo "⚠️  No test results found"
fi

echo ""
echo "📊 Reports generated:"
echo "   - HTML Report: reports/html/index.html"
echo "   - Screenshots: reports/screenshots/"
echo "   - Test Results: reports/results.json"
echo "   - Test Summary: reports/test-summary.json"

echo ""
echo "🎉 Production Readiness Validation Complete!"
echo "=================================================="

# Open HTML report if not in CI
if [ -z "$CI" ] && command -v open &> /dev/null; then
    echo "🌐 Opening HTML report..."
    open reports/html/index.html
fi
