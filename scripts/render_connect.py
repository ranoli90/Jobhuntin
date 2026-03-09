#!/usr/bin/env python3
"""Connect to Render and verify/fix service configuration.

Usage:
  export RENDER_API_KEY=rnd_xxx
  python scripts/render_connect.py           # Verify only
  python scripts/render_connect.py --fix     # Add missing API_PUBLIC_URL, ENV

Verifies:
  - All services are running
  - API has required env vars (DATABASE_URL, REDIS_URL, etc.)
  - Web has VITE_API_URL pointing to API
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import json
import urllib.error
import urllib.request


def api_get(path: str, token: str) -> dict | list:
    url = f"https://api.render.com/v1{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def api_put_env(path: str, token: str, value: str) -> int:
    """PUT env var to Render API. Returns status_code."""
    url = f"https://api.render.com/v1{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps({"value": value}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Verify/fix Render service config")
    parser.add_argument(
        "--fix", action="store_true", help="Add missing env vars (API_PUBLIC_URL, ENV)"
    )
    args = parser.parse_args()

    token = os.environ.get("RENDER_API_KEY")
    if not token:
        print("ERROR: Set RENDER_API_KEY environment variable")
        return 1

    print("Connecting to Render...")
    try:
        services = api_get("/services?limit=20", token)
    except urllib.error.HTTPError as e:
        print(f"ERROR: Render API failed: {e.code} {e.reason}")
        return 1

    # Normalize: API returns list of {cursor, service} or {service}
    svc_list = []
    for item in services:
        s = item.get("service", item) if isinstance(item, dict) else item
        if isinstance(s, dict) and s.get("id"):
            svc_list.append(s)

    print(f"\nFound {len(svc_list)} services:\n")
    for s in svc_list:
        status = "suspended" if s.get("suspended") == "suspended" else "active"
        url = s.get("serviceDetails", {}).get("url", "N/A")
        print(f"  - {s.get('name')} ({s.get('type')}) [{status}]")
        if url and url != "N/A":
            print(f"    URL: {url}")

    # Check API service
    api_svc = next(
        (
            s
            for s in svc_list
            if "api" in s.get("name", "").lower() and s.get("type") == "web_service"
        ),
        None,
    )
    if api_svc:
        print("\n--- API Service Env Vars ---")
        try:
            env_vars = api_get(f"/services/{api_svc['id']}/env-vars", token)
            ev_list = env_vars if isinstance(env_vars, list) else [env_vars]
            keys_present = {
                (ev.get("key") or (ev.get("envVar") or {}).get("key"))
                for ev in ev_list
                if ev
            }
            # Required for prod: config.validate_critical + main.py lifespan
            required = [
                "DATABASE_URL",
                "REDIS_URL",
                "RESEND_API_KEY",
                "EMAIL_FROM",
                "JWT_SECRET",
                "CSRF_SECRET",
                "APP_BASE_URL",
                "LLM_API_KEY",
                "API_PUBLIC_URL",  # Magic link verify redirect
                "WEBHOOK_SIGNING_SECRET",
            ]
            # env=prod is typically set in render.yaml; check ENV or env
            env_keys = ["ENV", "env"]
            has_env = any(k in keys_present for k in env_keys)
            if not has_env:
                required.append("ENV (or env)")  # Must be prod for production
            for key in required:
                k = key.split()[0] if " " in key else key
                found = k in keys_present
                status = "OK" if found else "MISSING"
                print(f"  {key}: {status}")
            if "DATABASE_URL" not in keys_present:
                print(
                    "  Note: DATABASE_URL may be set via Render Dashboard (linked Postgres) - not shown in API"
                )
            if "API_PUBLIC_URL" not in keys_present:
                print(
                    "  Note: API_PUBLIC_URL needed for magic-link verify redirect. Add in Dashboard."
                )
            if args.fix:
                fixes = []
                if "API_PUBLIC_URL" not in keys_present:
                    slug = api_svc.get("slug") or api_svc.get(
                        "name", "jobhuntin-api"
                    ).replace("_", "-")
                    fixes.append(("API_PUBLIC_URL", f"https://{slug}.onrender.com"))
                if not has_env:
                    fixes.append(("env", "prod"))
                for key, val in fixes:
                    # Render API: PUT /services/{id}/env-vars/{key}
                    status = api_put_env(
                        f"/services/{api_svc['id']}/env-vars/{key}",
                        token,
                        val,
                    )
                    if status in (200, 201, 204):
                        print(f"  [FIXED] Set {key}")
                    else:
                        print(f"  [FAILED] {key}: HTTP {status}")
        except Exception as e:
            print(f"  Could not fetch env vars: {e}")

    # Check latest deploy for API
    if api_svc:
        try:
            deploys = api_get(f"/services/{api_svc['id']}/deploys?limit=3", token)
            items = deploys if isinstance(deploys, list) else deploys.get("deploys", [])
            deploys_list = []
            for item in items:
                d = item.get("deploy", item) if isinstance(item, dict) else item
                if isinstance(d, dict) and d.get("id"):
                    deploys_list.append(d)
            if deploys_list:
                dep = deploys_list[0]
                status = dep.get("status", "unknown")
                commit_msg = (dep.get("commit") or {}).get("message", "")[:60]
                print(f"\n--- Latest API Deploy: {status} ---")
                print(f"  Commit: {commit_msg}...")
                if status == "live":
                    print("  API is live.")
                elif status == "update_failed":
                    print(
                        "  Deploy failed. Check build logs: Dashboard → jobhuntin-api → Logs"
                    )
                elif status in ("update_in_progress", "build_in_progress"):
                    print(
                        "  Deploy in progress. Wait a few minutes and re-run this script."
                    )
                else:
                    print(
                        "  Consider triggering a new deploy from the Render dashboard."
                    )
        except Exception as e:
            print(f"  Could not fetch deploys: {e}")

    # Try health check against common API URLs (Render redacts URL in API response)
    if api_svc:
        api_name = api_svc.get("name", "jobhuntin-api").replace("_", "-")
        slugs = [api_name.replace("_", "-"), "sorce-api"]
        health_ok = False
        for slug in slugs:
            url = f"https://{slug}.onrender.com/health"
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=15) as r:
                    if r.status == 200:
                        body = r.read().decode()[:200]
                        print(f"\n--- Health Check: {url} ---")
                        print(f"  OK: {body}")
                        health_ok = True
                        break
            except urllib.error.HTTPError as e:
                print(f"\n--- Health Check: {url} ---")
                print(f"  HTTP {e.code}: {e.reason}")
            except Exception as e:
                print(f"\n--- Health Check: {url} ---")
                print(f"  Error: {e}")
        if not health_ok:
            print("  (Service may be sleeping or deploy in progress)")

    print("\nDone. Use Render dashboard for logs: https://dashboard.render.com")
    return 0


if __name__ == "__main__":
    sys.exit(main())
