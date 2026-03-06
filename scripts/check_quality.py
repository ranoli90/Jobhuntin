#!/usr/bin/env python3
"""Quality check script - consolidates all code quality checks.

Usage:
    python scripts/check_quality.py           # Run all checks
    python scripts/check_quality.py --major   # Major issues only
    python scripts/check_quality.py --minor   # Minor issues only
    python scripts/check_quality.py --ts      # TypeScript only
    python scripts/check_quality.py --py       # Python only
    python scripts/check_quality.py --all      # Run all including linters
"""

import argparse
import json
import os
import subprocess


def load_sonar_issues():
    """Load sonar issues from file."""
    sonar_file = "sonar-issues.json"
    if not os.path.exists(sonar_file):
        print("[WARN] sonar-issues.json not found. Run SonarQube scan first.")
        return None
    with open(sonar_file) as f:
        return json.load(f)


def check_python_major():
    """Check major Python issues from SonarQube scan."""
    data = load_sonar_issues()
    if not data:
        return

    # SonarQube rules for major Python issues
    python_major_rules = ["python:S8415", "python:S930", "python:S5876", "python:S1128"]
    python_issues = [
        i
        for i in data["issues"]
        if i["rule"] in python_major_rules and i.get("severity") == "MAJOR"
    ]

    print("\n=== Major Python Issues ===")
    print(f"Total: {len(python_issues)}")
    for rule in python_major_rules:
        rule_issues = [i for i in python_issues if i["rule"] == rule]
        rule_name = {
            "python:S8415": "HTTPException docs",
            "python:S930": "Missing arguments",
            "python:S5876": "SQL injection risk",
            "python:S1128": "Unused imports",
        }.get(rule, rule)
        print(f"  {rule_name}: {len(rule_issues)} issues")

    # Show first 5 examples
    if python_issues:
        print("\nSample issues:")
        for issue in python_issues[:5]:
            component = issue["component"].split(":")[-1]
            line = issue.get("line", "N/A")
            message = issue.get("message", "No message")[:60]
            print(f"  - {component}:{line} - {message}")


def check_python_minor():
    """Check minor Python issues from SonarQube scan."""
    data = load_sonar_issues()
    if not data:
        return

    python_minor_rules = ["python:S1874", "python:S1854", "python:S1130"]
    python_issues = [i for i in data["issues"] if i["rule"] in python_minor_rules]

    print("\n=== Minor Python Issues ===")
    print(f"Total: {len(python_issues)}")


def check_typescript():
    """Check TypeScript issues from SonarQube scan."""
    data = load_sonar_issues()
    if not data:
        return

    # SonarQube rules for TypeScript issues
    ts_rules = [
        "typescript:S7764",
        "typescript:S7781",
        "typescript:S7773",
        "typescript:S6479",
    ]
    ts_issues = [i for i in data["issues"] if i["rule"] in ts_rules]

    # Group by rule
    rule_counts = {}
    for issue in ts_issues:
        rule = issue["rule"]
        rule_counts[rule] = rule_counts.get(rule, 0) + 1

    print("\n=== TypeScript Issues ===")
    print(f"Total: {len(ts_issues)}")
    for rule, count in sorted(rule_counts.items(), key=lambda x: -x[1]):
        rule_name = {
            "typescript:S7764": "globalThis",
            "typescript:S7781": "naming-convention",
            "typescript:S7773": "parseInt",
            "typescript:S6479": "array-index-key",
        }.get(rule, rule)
        print(f"  {rule_name}: {count} issues")


def check_info():
    """Check info-level issues from SonarQube scan."""
    data = load_sonar_issues()
    if not data:
        return

    info_issues = [i for i in data["issues"] if i.get("severity") == "INFO"]
    print("\n=== Info Issues (TODOs, etc) ===")
    print(f"Total: {len(info_issues)}")


def run_ruff():
    """Run ruff linter LIVE on the codebase."""
    print("\n=== Running Ruff Linter ===")
    try:
        result = subprocess.run(
            ["ruff", "check", "."], capture_output=True, text=True, timeout=120
        )
        # Ruff returns 0 for no issues, 1 for some issues, 2 for invalid config
        if result.returncode == 1:
            line_list = [
                line
                for line in result.stdout.split("\n")
                if line and not line.startswith("===")
            ]
            print(f"Found {len(line_list)} lint issues")
            for single_line in line_list[:10]:
                print(f"  {single_line[:80]}")
        elif result.returncode == 0:
            print("No issues found - code is clean!")
        else:
            print(f"Error (code {result.returncode}): {result.stdout[:200]}")
    except FileNotFoundError:
        print("[WARN] ruff not installed. Install with: pip install ruff")
    except subprocess.TimeoutExpired:
        print("[WARN] Ruff timed out after 120 seconds")
    except Exception as e:
        print(f"[ERROR] {e}")


def run_mypy():
    """Run mypy type checker LIVE on the codebase."""
    print("\n=== Running MyPy Type Checker ===")
    try:
        result = subprocess.run(
            ["mypy", ".", "--ignore-missing-imports", "--no-error-summary"],
            capture_output=True,
            text=True,
            timeout=180,
        )
        # mypy returns 0 if no errors, 1 if errors found
        if result.returncode == 1:
            line_list = [
                line
                for line in result.stdout.split("\n")
                if line and not line.startswith("===")
            ]
            print(f"Found {len(line_list)} lint issues")
            for line in line_list[:10]:
                print(f"  {line[:80]}")
        elif result.returncode == 0:
            print("No type errors found!")
        else:
            print(f"Note: Exit code {result.returncode}")
            if result.stdout:
                print(result.stdout[:200])
    except FileNotFoundError:
        print("[WARN] mypy not installed. Install with: pip install mypy")
    except subprocess.TimeoutExpired:
        print("[WARN] MyPy timed out after 180 seconds")
    except Exception as e:
        print(f"[ERROR] {e}")


def run_tests():
    """Run the test suite."""
    print("\n=== Running Test Suite ===")
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        # Parse output for pass/fail counts
        output = result.stdout + result.stderr
        if "passed" in output:
            # Extract pass/skip/fail counts
            import re

            match = re.search(r"(\d+) passed", output)
            passed = match.group(1) if match else "?"
            match = re.search(r"(\d+) failed", output)
            failed = match.group(1) if match else "0"
            match = re.search(r"(\d+) skipped", output)
            skipped = match.group(1) if match else "0"
            print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
        else:
            print(f"Exit code: {result.returncode}")
    except FileNotFoundError:
        print("[WARN] pytest not installed")
    except subprocess.TimeoutExpired:
        print("[WARN] Tests timed out after 300 seconds")
    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Code quality checks - run static analysis and linters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/check_quality.py           # Show all static analysis
  python scripts/check_quality.py --major  # Major Python issues only
  python scripts/check_quality.py --ts      # TypeScript issues only
  python scripts/check_quality.py --live   # Run live linters (ruff, mypy)
  python scripts/check_quality.py --all     # Run everything
        """,
    )
    parser.add_argument("--major", action="store_true", help="Major Python issues")
    parser.add_argument("--minor", action="store_true", help="Minor Python issues")
    parser.add_argument("--ts", action="store_true", help="TypeScript issues")
    parser.add_argument("--py", action="store_true", help="All Python issues")
    parser.add_argument(
        "--live", action="store_true", help="Run live linters (ruff, mypy)"
    )
    parser.add_argument("--all", action="store_true", help="Run everything")
    parser.add_argument("--tests", action="store_true", help="Run test suite")
    args = parser.parse_args()

    # Default: show all static analysis from sonar-issues.json
    show_static = not any(
        [args.major, args.minor, args.ts, args.py, args.live, args.all, args.tests]
    )

    print("=" * 60)
    print("CODE QUALITY CHECKS")
    print("=" * 60)

    if show_static or args.all:
        check_python_major()
        check_python_minor()
        check_info()
        check_typescript()

    if args.major:
        check_python_major()

    if args.minor:
        check_python_minor()
        check_info()

    if args.ts or args.py:
        check_typescript()
        check_python_major()

    if args.live or args.all:
        run_ruff()
        run_mypy()

    if args.tests or args.all:
        run_tests()

    print("\n" + "=" * 60)
    if not args.live and not args.all and not args.tests:
        print("Tip: Use --live to run actual linters (ruff, mypy)")
        print("     Use --tests to run test suite")
        print("     Use --all for everything")
    print("=" * 60)


if __name__ == "__main__":
    main()
