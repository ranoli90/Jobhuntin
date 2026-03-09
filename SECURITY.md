# Security Advisory

## Dependency Vulnerability Report

Generated: 2026-03-05

### Summary

This document tracks known security vulnerabilities in project dependencies and their remediation status.

### Vulnerabilities Status

| Package | Version | Vulnerability | Fix Version | Status | Notes |
|---------|---------|---------------|-------------|--------|-------|
| Pillow | 10.4.0 | CVE-2026-25990 | 12.1.1 | **FIXED** | Updated in requirements.txt |
| markdownify | 0.13.1 | CVE-2025-46656 | 0.14.1 | **FIXED** | Added explicit constraint in requirements.txt |
| black | 24.1.1 | PYSEC-2024-48 | 24.3.0 | **FIXED** | Updated in requirements-dev.txt |
| pip | 25.0.1 | CVE-2025-8869, CVE-2026-1703 | 25.3+ | **ACCEPTED RISK** | System tool, not a project dependency |
| py | 1.11.0 | PYSEC-2022-42969 | No fix available | **ACCEPTED RISK** | Transitive dependency from pytest |

### Fixed Vulnerabilities

#### 1. Pillow (CVE-2026-25990)
- **Severity**: High
- **Description**: Buffer overflow vulnerability in image processing
- **Fix**: Updated Pillow from `>=10.3.0,<11` to `>=12.1.1` in [`requirements.txt`](requirements.txt:41)
- **Impact**: Major version upgrade (10.x → 12.x). Pillow 12.x drops support for Python 3.8 but maintains compatibility with Python 3.9+.

#### 2. markdownify (CVE-2025-46656)
- **Severity**: Medium
- **Description**: HTML injection vulnerability
- **Fix**: Added explicit constraint `markdownify>=0.14.1` in [`requirements.txt`](requirements.txt:63)
- **Impact**: Transitive dependency from `python-jobspy`. Explicit pinning ensures safe version.

#### 3. black (PYSEC-2024-48)
- **Severity**: Low
- **Description**: Code formatter vulnerability (not exploitable in production)
- **Fix**: Added constraint `black>=24.3.0` in [`requirements-dev.txt`](requirements-dev.txt:7)
- **Impact**: Development tool only, not used in production deployment.

### Accepted Risks

#### 1. pip (CVE-2025-8869, CVE-2026-1703)
- **Severity**: Medium
- **Description**: Python package installer vulnerabilities
- **Justification**: `pip` is a system tool managed by the Python installation, not a project dependency in requirements files.
- **Remediation**: Upgrade system Python installation to pip 25.3+ or 26.0+:
  ```bash
  python -m pip install --upgrade pip
  ```

#### 2. py (PYSEC-2022-42969)
- **Severity**: Medium
- **Description**: Local privilege escalation via temporary directory manipulation
- **Justification**: 
  - `py` is a transitive dependency from `pytest` (development tool)
  - No fixed version available yet
  - Vulnerability requires local system access and specific conditions
  - Impact limited to test environments, not production deployments
- **Remediation**: Monitor for pytest updates that replace or update the `py` dependency.

### Monitoring

To check for new vulnerabilities, run:

```bash
# Run pip-audit
python -m pip_audit

# Run Safety (if installed)
python -m safety check
```

### Security Scanning in CI/CD

The [`scripts/code_review.py`](scripts/code_review.py) script includes security scanning via pip-audit. These tools may report findings in large dependency trees, which is expected behavior. The script has been configured to:

1. Run pip-audit as an informational check
2. Continue execution even if vulnerabilities are found (since external dependencies may always have some issues)
3. Report findings for manual review

### Regular Maintenance

- Review this advisory monthly
- Update dependencies when security fixes are released
- Run `pip-audit` and `safety check` before each release
- Monitor GitHub Security Advisories for Python ecosystem
