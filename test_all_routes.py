#!/usr/bin/env python3
"""Comprehensive API route testing - find 500/502 errors."""
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000"

def fetch(path, method="GET", body=None):
    try:
        req = Request(f"{BASE}{path}", method=method, data=body)
        req.add_header("Accept", "application/json")
        if body:
            req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=15) as r:
            return r.status, r.read().decode()
    except HTTPError as e:
        return e.code, e.read().decode() if e.fp else ""
    except URLError as e:
        return None, str(e.reason)
    except Exception as e:
        return None, str(e)

def main():
    # Get all routes from OpenAPI
    status, body = fetch("/openapi.json")
    if status != 200:
        print(f"Failed to get OpenAPI: {status}")
        sys.exit(1)

    spec = json.loads(body)
    paths = spec.get("paths", {})

    # Paths to skip (require specific IDs, webhooks, etc.)
    skip_patterns = [
        "/{", "/admin/", "/api/v2/", "/api/storage/",
        "/api/og", "/docs", "/redoc", "/openapi.json",
    ]
    # Skip auth/logout - returns 302 redirect to login which may be unreachable in test env
    skip_exact = {"/auth/logout"}

    errors = []
    tested = 0
    ok_200 = 0
    ok_401 = 0
    ok_404 = 0
    ok_4xx = 0
    ok_429 = 0
    ok_200_public = 0

    # Public endpoints that must return 200
    public = {"/health", "/healthz", "/csrf/prepare", "/billing/tiers"}

    for path in sorted(paths.keys()):
        if any(p in path for p in skip_patterns):
            continue
        if "{" in path and path.count("{") > 1:
            continue
        if path in skip_exact:
            continue

        # Replace path params with dummy values for testing
        test_path = path
        if "{application_id}" in test_path:
            test_path = test_path.replace("{application_id}", "00000000-0000-0000-0000-000000000001")
        if "{job_id}" in test_path:
            test_path = test_path.replace("{job_id}", "00000000-0000-0000-0000-000000000001")
        if "{session_id}" in test_path:
            test_path = test_path.replace("{session_id}", "00000000-0000-0000-0000-000000000001")
        if "{item_id}" in test_path:
            test_path = test_path.replace("{item_id}", "00000000-0000-0000-0000-000000000001")
        if "{alert_id}" in test_path:
            test_path = test_path.replace("{alert_id}", "00000000-0000-0000-0000-000000000001")
        if "{tenant_id}" in test_path:
            test_path = test_path.replace("{tenant_id}", "00000000-0000-0000-0000-000000000001")
        if "{bucket}" in test_path or "{path" in test_path:
            continue

        ops = paths[path]
        for method in ["get", "post", "put", "patch", "delete"]:
            if method not in ops:
                continue
            tested += 1
            status, _ = fetch(test_path, method.upper())
            if status is None:
                errors.append((method.upper(), test_path, "Connection/timeout error"))
            elif status == 429:
                ok_429 += 1  # Rate limit - acceptable
            elif status == 302:
                ok_4xx += 1  # Redirect (e.g. logout) - acceptable
            elif 500 <= (status or 0) < 600:
                errors.append((method.upper(), test_path, f"Server error {status}"))
            elif status == 200:
                ok_200 += 1
                if test_path in public:
                    ok_200_public += 1
            elif status == 401:
                ok_401 += 1
            elif status == 404:
                ok_404 += 1
            elif 400 <= (status or 0) < 500:
                ok_4xx += 1
            elif status == 405:
                pass  # Method not allowed
            else:
                if status and status not in (200, 201, 204, 301, 302):
                    errors.append((method.upper(), test_path, f"Unexpected {status}"))

    print("\n--- Results ---")
    print(f"Tested: {tested}")
    print(f"200 OK: {ok_200} (public: {ok_200_public})")
    print(f"401 (auth required): {ok_401}")
    print(f"404: {ok_404}")
    print(f"429 (rate limit): {ok_429}")
    print(f"4xx other: {ok_4xx}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for m, p, msg in errors[:50]:
            print(f"  {m} {p}: {msg}")
        if len(errors) > 50:
            print(f"  ... and {len(errors)-50} more")
        sys.exit(1)
    print("\nNo 500 errors found.")
    sys.exit(0)

if __name__ == "__main__":
    main()
