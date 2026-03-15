# 🛠️ Comprehensive Code Analysis & Organization Script (PowerShell)
# This script runs multiple analysis tools to assess code quality, security, and organization

Write-Host "🚀 Starting Comprehensive Code Analysis..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Create reports directory
New-Item -ItemType Directory -Force -Path "reports" | Out-Null

Write-Host ""
Write-Host "📊 1. Running Security Analysis..." -ForegroundColor Blue
Write-Host "--------------------------------" -ForegroundColor Blue

# Bandit Security Analysis
Write-Host "🔒 Running Bandit security scan..." -ForegroundColor Yellow
bandit -r apps packages shared backend api worker -f json | Out-File -FilePath "reports/bandit-security.json" -Encoding UTF8
Write-Host "✅ Bandit security scan completed" -ForegroundColor Green

# Safety Dependency Check
Write-Host "📦 Running Safety dependency check..." -ForegroundColor Yellow
try {
    safety check --json | Out-File -FilePath "reports/safety-dependencies.json" -Encoding UTF8
    Write-Host "✅ Safety dependency check completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Safety check had issues (may not be installed)" -ForegroundColor Yellow
}

# pip-audit
Write-Host "🔍 Running pip-audit..." -ForegroundColor Yellow
try {
    pip-audit --format=json | Out-File -FilePath "reports/pip-audit.json" -Encoding UTF8
    Write-Host "✅ pip-audit completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️ pip-audit had issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 2. Running Code Quality Analysis..." -ForegroundColor Blue
Write-Host "------------------------------------" -ForegroundColor Blue

# Flake8 Code Quality
Write-Host "🔧 Running Flake8 code quality check..." -ForegroundColor Yellow
flake8 apps packages shared backend api worker --format=json | Out-File -FilePath "reports/flake8-quality.json" -Encoding UTF8
Write-Host "✅ Flake8 code quality check completed" -ForegroundColor Green

# Pylint Analysis
Write-Host "🎯 Running Pylint analysis..." -ForegroundColor Yellow
try {
    pylint apps packages shared backend api worker --reports=no --json | Out-File -FilePath "reports/pylint-analysis.json" -Encoding UTF8
    Write-Host "✅ Pylint analysis completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Pylint had issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 3. Running Complexity Analysis..." -ForegroundColor Blue
Write-Host "-----------------------------------" -ForegroundColor Blue

# Radon Complexity
Write-Host "📈 Running Radon complexity analysis..." -ForegroundColor Yellow
radon cc apps packages shared backend api worker --json | Out-File -FilePath "reports/radon-complexity.json" -Encoding UTF8
Write-Host "✅ Radon complexity analysis completed" -ForegroundColor Green

# Radon Maintainability
Write-Host "🔧 Running Radon maintainability analysis..." -ForegroundColor Yellow
radon mi apps packages shared backend api worker --json | Out-File -FilePath "reports/radon-maintainability.json" -Encoding UTF8
Write-Host "✅ Radon maintainability analysis completed" -ForegroundColor Green

Write-Host ""
Write-Host "📊 4. Running Dead Code Analysis..." -ForegroundColor Blue
Write-Host "----------------------------------" -ForegroundColor Blue

# Vulture Dead Code Detection
Write-Host "🦅 Running Vulture dead code detection..." -ForegroundColor Yellow
vulture apps packages shared backend api worker --min-confidence 80 --sort-by size | Out-File -FilePath "reports/vulture-dead-code.txt" -Encoding UTF8
Write-Host "✅ Vulture dead code detection completed" -ForegroundColor Green

Write-Host ""
Write-Host "📊 5. Running Import Organization Check..." -ForegroundColor Blue
Write-Host "-----------------------------------------" -ForegroundColor Blue

# isort Check
Write-Host "📚 Running isort import organization check..." -ForegroundColor Yellow
isort apps packages shared backend api worker --profile black --diff --check-only | Out-File -FilePath "reports/isort-imports.txt" -Encoding UTF8
Write-Host "✅ isort import organization check completed" -ForegroundColor Green

Write-Host ""
Write-Host "📊 6. Running Type Checking..." -ForegroundColor Blue
Write-Host "-----------------------------" -ForegroundColor Blue

# MyPy Type Checking
$env:PYTHONPATH = "apps:packages:."
Write-Host "🔤 Running MyPy type checking..." -ForegroundColor Yellow
try {
    mypy apps packages shared backend api worker --json | Out-File -FilePath "reports/mypy-types.json" -Encoding UTF8
    Write-Host "✅ MyPy type checking completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️ MyPy had issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 7. Generating Summary Report..." -ForegroundColor Blue
Write-Host "--------------------------------" -ForegroundColor Blue

# Generate summary
$summary = @"
# 📊 Comprehensive Code Analysis Summary

## 🔍 Analysis Overview
Generated on: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Tools run: Bandit, Safety, pip-audit, Flake8, Pylint, Radon, Vulture, isort, MyPy

## 📈 Key Metrics

### Security Issues
- High Severity: $(if (Test-Path "reports/bandit-security.json") { (Get-Content "reports/bandit-security.json" | Measure-Object -Line).Lines } else { "0" })
- Medium Severity: $(if (Test-Path "reports/safety-dependencies.json") { (Get-Content "reports/safety-dependencies.json" | Measure-Object -Line).Lines } else { "0" })
- Low Severity: $(if (Test-Path "reports/pip-audit.json") { (Get-Content "reports/pip-audit.json" | Measure-Object -Line).Lines } else { "0" })

### Code Quality
- Flake8 Issues: $(if (Test-Path "reports/flake8-quality.json") { (Get-Content "reports/flake8-quality.json" | Measure-Object -Line).Lines } else { "0" })
- Pylint Score: $(if (Test-Path "reports/pylint-analysis.json") { "See detailed report" } else { "N/A" })

### Complexity
- Average Complexity: See radon-complexity.json
- Complex Functions (>10): See radon-complexity.json

### Dead Code
- Unused Items: $(if (Test-Path "reports/vulture-dead-code.txt") { (Get-Content "reports/vulture-dead-code.txt" | Measure-Object -Line).Lines } else { "0" })

### Type Safety
- MyPy Errors: $(if (Test-Path "reports/mypy-types.json") { (Get-Content "reports/mypy-types.json" | Measure-Object -Line).Lines } else { "0" })

## 📋 Detailed Reports
- [Security Analysis](bandit-security.json)
- [Dependency Check](safety-dependencies.json)
- [Code Quality](flake8-quality.json)
- [Complexity Analysis](radon-complexity.json)
- [Dead Code Detection](vulture-dead-code.txt)
- [Type Checking](mypy-types.json)

## 🎯 Recommendations
1. Fix high and medium severity security issues first
2. Address complex functions (complexity > 10)
3. Remove unused code identified by Vulture
4. Fix type checking issues
5. Organize imports with isort

## 🔧 Quick Fixes
```powershell
# Fix imports
isort . --profile black

# Format code
black .

# Remove unused imports/variables
autoflake --remove-all-unused-imports --remove-unused-variables --in-place .
```
"@

$summary | Out-File -FilePath "reports/analysis-summary.md" -Encoding UTF8
Write-Host "✅ Summary report generated" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Comprehensive Analysis Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host "📁 Reports generated in: reports/" -ForegroundColor Cyan
Write-Host "📊 Summary: reports/analysis-summary.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔧 Quick fixes you can run:" -ForegroundColor Yellow
Write-Host "  isort . --profile black           # Fix imports" -ForegroundColor White
Write-Host "  black .                           # Format code" -ForegroundColor White
Write-Host "  autoflake --remove-all-unused-imports --remove-unused-variables --in-place .  # Remove unused imports/variables" -ForegroundColor White
Write-Host ""
Write-Host "📖 View detailed reports:" -ForegroundColor Yellow
Write-Host "  Get-Content reports/analysis-summary.md" -ForegroundColor White
Write-Host "  Invoke-Item reports/  # Open in file browser" -ForegroundColor White
