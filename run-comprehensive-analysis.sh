#!/bin/bash

# 🛠️ Comprehensive Code Analysis & Organization Script
# This script runs multiple analysis tools to assess code quality, security, and organization

echo "🚀 Starting Comprehensive Code Analysis..."
echo "========================================"

# Create reports directory
mkdir -p reports

echo ""
echo "📊 1. Running Security Analysis..."
echo "--------------------------------"

# Bandit Security Analysis
echo "🔒 Running Bandit security scan..."
bandit -r apps packages shared backend api worker -f json > reports/bandit-security.json 2>/dev/null
echo "✅ Bandit security scan completed"

# Safety Dependency Check
echo "📦 Running Safety dependency check..."
safety check --json > reports/safety-dependencies.json 2>/dev/null
echo "✅ Safety dependency check completed"

# pip-audit
echo "🔍 Running pip-audit..."
pip-audit --format=json > reports/pip-audit.json 2>/dev/null
echo "✅ pip-audit completed"

echo ""
echo "📊 2. Running Code Quality Analysis..."
echo "------------------------------------"

# Flake8 Code Quality
echo "🔧 Running Flake8 code quality check..."
flake8 apps packages shared backend api worker --format=json > reports/flake8-quality.json 2>/dev/null
echo "✅ Flake8 code quality check completed"

# Pylint Analysis
echo "🎯 Running Pylint analysis..."
pylint apps packages shared backend api worker --reports=no --json > reports/pylint-analysis.json 2>/dev/null
echo "✅ Pylint analysis completed"

echo ""
echo "📊 3. Running Complexity Analysis..."
echo "-----------------------------------"

# Radon Complexity
echo "📈 Running Radon complexity analysis..."
radon cc apps packages shared backend api worker --json > reports/radon-complexity.json 2>/dev/null
echo "✅ Radon complexity analysis completed"

# Radon Maintainability
echo "🔧 Running Radon maintainability analysis..."
radon mi apps packages shared backend api worker --json > reports/radon-maintainability.json 2>/dev/null
echo "✅ Radon maintainability analysis completed"

echo ""
echo "📊 4. Running Dead Code Analysis..."
echo "----------------------------------"

# Vulture Dead Code Detection
echo "🦅 Running Vulture dead code detection..."
vulture apps packages shared backend api worker --min-confidence 80 --sort-by size > reports/vulture-dead-code.txt 2>/dev/null
echo "✅ Vulture dead code detection completed"

echo ""
echo "📊 5. Running Import Organization Check..."
echo "-----------------------------------------"

# isort Check
echo "📚 Running isort import organization check..."
isort apps packages shared backend api worker --profile black --diff --check-only > reports/isort-imports.txt 2>/dev/null
echo "✅ isort import organization check completed"

echo ""
echo "📊 6. Running Type Checking..."
echo "-----------------------------"

# MyPy Type Checking
echo "🔤 Running MyPy type checking..."
PYTHONPATH=apps:packages:. mypy apps packages shared backend api worker --json > reports/mypy-types.json 2>/dev/null
echo "✅ MyPy type checking completed"

echo ""
echo "📊 7. Generating Summary Report..."
echo "--------------------------------"

# Generate summary
cat > reports/analysis-summary.md << EOF
# 📊 Comprehensive Code Analysis Summary

## 🔍 Analysis Overview
Generated on: $(date)
Tools run: Bandit, Safety, pip-audit, Flake8, Pylint, Radon, Vulture, isort, MyPy

## 📈 Key Metrics

### Security Issues
- High Severity: $(grep -c '"issue_severity":"HIGH"' reports/bandit-security.json 2>/dev/null || echo "0")
- Medium Severity: $(grep -c '"issue_severity":"MEDIUM"' reports/bandit-security.json 2>/dev/null || echo "0")
- Low Severity: $(grep -c '"issue_severity":"LOW"' reports/bandit-security.json 2>/dev/null || echo "0")

### Code Quality
- Flake8 Issues: $(wc -l < reports/flake8-quality.json 2>/dev/null || echo "0")
- Pylint Score: $(grep '"score"' reports/pylint-analysis.json 2>/dev/null | cut -d'"' -f4 || echo "N/A")

### Complexity
- Average Complexity: $(radon cc apps packages shared backend api worker --average 2>/dev/null | grep -o '[0-9.]*' | head -1 || echo "N/A")
- Complex Functions (>10): $(radon cc apps packages shared backend api worker --min B 2>/dev/null | grep -c '[A-F]' || echo "0")

### Dead Code
- Unused Items: $(grep -c 'unused' reports/vulture-dead-code.txt 2>/dev/null || echo "0")

### Type Safety
- MyPy Errors: $(grep -c 'error' reports/mypy-types.json 2>/dev/null || echo "0")

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
EOF

echo "✅ Summary report generated"

echo ""
echo "🎉 Comprehensive Analysis Complete!"
echo "=================================="
echo "📁 Reports generated in: reports/"
echo "📊 Summary: reports/analysis-summary.md"
echo ""
echo "🔧 Quick fixes you can run:"
echo "  isort . --profile black           # Fix imports"
echo "  black .                           # Format code"
echo "  autoflake --remove-all-unused-imports --remove-unused-variables --in-place .  # Remove unused imports/variables"
echo ""
echo "📖 View detailed reports:"
echo "  cat reports/analysis-summary.md"
echo "  open reports/  # Open in file browser"
