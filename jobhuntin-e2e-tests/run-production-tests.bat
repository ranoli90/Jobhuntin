@echo off
REM Production Readiness Validation Script for Windows
REM This script runs the complete browser automation test suite for JobHuntin

echo 🚀 Starting JobHuntin Production Readiness Validation
echo ==================================================

REM Check environment variables
if "%BASE_URL%"=="" (
    echo ⚠️  BASE_URL not set, using default: https://jobhuntin.com
    set BASE_URL=https://jobhuntin.com
)

if "%TEST_EMAIL%"=="" (
    echo ⚠️  TEST_EMAIL not set, using default: test-e2e-production@jobhuntin.com
    set TEST_EMAIL=test-e2e-production@jobhuntin.com
)

echo 📊 Configuration:
echo    - Base URL: %BASE_URL%
echo    - Test Email: %TEST_EMAIL%
echo    - Environment: %NODE_ENV%
echo    - CI Mode: %CI%

REM Install dependencies if needed
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm ci
)

REM Install Playwright browsers
echo 🌐 Installing Playwright browsers...
npx playwright install

REM Create reports directory
echo 📁 Creating reports directory...
if not exist "reports\screenshots" mkdir reports\screenshots
if not exist "reports\html" mkdir reports\html
if not exist "test-results" mkdir test-results

REM Run the production readiness test suite
echo 🧪 Running Production Readiness Test Suite...
echo ==================================================

REM Run tests with production configuration
npx playwright test --config=playwright.config.production.ts

REM Generate test report
echo 📊 Generating test report...
npx playwright show-report reports\html

REM Check test results
echo 📈 Test Results Summary:
if exist "reports\results.json" (
    node -e "const results = JSON.parse(require('fs').readFileSync('reports/results.json', 'utf8')); const totalTests = results.suites?.reduce((acc, suite) => acc + (suite.specs?.length || 0), 0) || 0; console.log(`   - Total tests: ${totalTests}`); console.log(`   - Passed: ${results.passed || 0}`); console.log(`   - Failed: ${results.failed || 0}`); console.log(`   - Flaky: ${results.flaky || 0}`); console.log(`   - Skipped: ${results.skipped || 0}`); if (results.failed > 0) { console.log('❌ Some tests failed - check reports for details'); process.exit(1); } else { console.log('✅ All tests passed!'); }"
) else (
    echo ⚠️  No test results found
)

echo.
echo 📊 Reports generated:
echo    - HTML Report: reports\html\index.html
echo    - Screenshots: reports\screenshots\
echo    - Test Results: reports\results.json
echo    - Test Summary: reports\test-summary.json

echo.
echo 🎉 Production Readiness Validation Complete!
echo ==================================================

REM Open HTML report if not in CI
if "%CI%"=="" if exist "reports\html\index.html" (
    echo 🌐 Opening HTML report...
    start reports\html\index.html
)
