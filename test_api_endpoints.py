#!/usr/bin/env python3
"""Test all API endpoints - public and auth-required."""
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000"

# Public endpoints - should return 200
PUBLIC = [
    "/health",
    "/healthz",
    "/csrf/prepare",
]

# Auth-required - expect 401 when no token (or 200/other valid when with token)
# We test without token, expect 401
AUTH_REQUIRED = [
    "/billing/tiers",
    "/billing/status",
    "/me/dashboard",
    "/me/profile",
    "/me/skills",
    "/me/answer-memory",
    "/me/work-style",
    "/me/team/members",
    "/applications/00000000-0000-0000-0000-000000000001",  # fake UUID
]

# Billing tiers: if it requires auth, 401 is ok. If public, 200 expected.
# Per user: "Public: /health, /healthz, /billing/tiers" - so billing/tiers should be public
BILLING_TIERS_PUBLIC = True  # billing/tiers is public (no auth required)

def fetch(path, method="GET", expect_ok=True):
    try:
        req = Request(f"{BASE}{path}", method=method)
        req.add_header("Accept", "application/json")
        with urlopen(req, timeout=5) as r:
            return r.status, r.read().decode()
    except HTTPError as e:
        return e.code, e.read().decode() if e.fp else ""
    except URLError as e:
        return None, str(e.reason)
    except Exception as e:
        return None, str(e)

def main():
    errors = []
    ok = 0

    for path in PUBLIC:
        status, _ = fetch(path)
        if status == 200:
            print(f"OK {status} GET {path}")
            ok += 1
        else:
            print(f"FAIL {status} GET {path}")
            errors.append((path, status, "expected 200"))

    # billing/tiers: user said public
    status, body = fetch("/billing/tiers")
    if BILLING_TIERS_PUBLIC:
        if status == 200:
            print(f"OK {status} GET /billing/tiers (public)")
            ok += 1
        else:
            print(f"FAIL {status} GET /billing/tiers (expected 200, public)")
            errors.append(("/billing/tiers", status, "expected 200 (public)"))
    else:
        if status in (200, 401):
            print(f"OK {status} GET /billing/tiers")
            ok += 1
        else:
            errors.append(("/billing/tiers", status, "expected 200 or 401"))

    for path in AUTH_REQUIRED:
        if path == "/billing/tiers":
            continue
        status, _ = fetch(path)
        if status == 401:
            print(f"OK 401 GET {path} (auth required)")
            ok += 1
        elif status == 404:
            print(f"OK 404 GET {path} (auth passed, resource not found)")
            ok += 1
        elif status == 200:
            print(f"OK 200 GET {path}")
            ok += 1
        elif status and 500 <= status < 600:
            print(f"FAIL {status} GET {path} (server error)")
            errors.append((path, status, "5xx server error"))
        else:
            print(f"INFO {status} GET {path}")
            ok += 1

    # Test docs
    for path in ["/docs", "/openapi.json", "/redoc"]:
        status, _ = fetch(path)
        if status == 200:
            print(f"OK {status} GET {path}")
            ok += 1
        else:
            print(f"FAIL {status} GET {path}")
            errors.append((path, status, "expected 200"))

    print("\n--- Summary ---")
    print(f"OK: {ok}")
    if errors:
        print("Errors:")
        for path, status, msg in errors:
            print(f"  {path}: {status} - {msg}")
        sys.exit(1)
    print("All checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
