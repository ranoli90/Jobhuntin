#!/usr/bin/env python3
"""Comprehensive check of environment variables and deploy issues."""

import json
import urllib.request

API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"
BASE_URL = "https://api.render.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}


def get(path: str):
    """Make GET request to Render API."""
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


def main():
    print(f"=== Comprehensive check for service: {SERVICE_ID} ===\n")

    # Get environment variables
    print("--- All Environment Variables ---")
    env_vars = get(f"/services/{SERVICE_ID}/env-vars")
    current_vars = {}
    for item in env_vars:
        ev = item.get("envVar", item) if isinstance(item, dict) else item
        key = ev.get("key")
        value = ev.get("value", "")
        current_vars[key] = value

    # Print all keys
    print("\nAll environment variable keys found:")
    for key in sorted(current_vars.keys()):
        print(f"  - {key}")

    # Check what's missing
    print("\n--- Checking Required Environment Variables ---")

    # Required for API to work
    required = [
        "ENV",
        "DATABASE_URL",
        "JWT_SECRET",
        "CSRF_SECRET",
        "WEBHOOK_SIGNING_SECRET",
        "APP_BASE_URL",
        "API_PUBLIC_URL",
        "PYTHONPATH",
        "PORT",
    ]

    # Recommended
    recommended = [
        "LLM_API_KEY",
        "LLM_API_BASE",
        "LLM_MODEL",
        "ADZUNA_APP_ID",
        "ADZUNA_API_KEY",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "RESEND_API_KEY",
        "LOG_LEVEL",
        "LOG_JSON",
    ]

    print("\nRequired (must be set):")
    all_good = True
    for key in required:
        if key in current_vars and current_vars[key]:
            print(f"  [OK] {key}")
        else:
            print(f"  [MISSING] {key}")
            all_good = False

    print("\nRecommended (for full functionality):")
    for key in recommended:
        if key in current_vars and current_vars[key]:
            print(f"  [OK] {key}")
        else:
            print(f"  [MISSING] {key}")

    # Check DATABASE_URL format
    print("\n--- DATABASE_URL Analysis ---")
    db_url = current_vars.get("DATABASE_URL", "")
    print(f"Current: {db_url}")
    expected_host = "dpg-d6p53ghr0fns73e4da20-a"
    if expected_host in db_url:
        print(f"  [OK] Contains correct host: {expected_host}")
    else:
        print(f"  [ERROR] Does NOT contain expected host: {expected_host}")

    # Get deploy details to find error messages
    print("\n--- Deploy Error Details ---")
    try:
        deploys = get(f"/services/{SERVICE_ID}/deploys?limit=3")
        items = deploys if isinstance(deploys, list) else deploys.get("deploys", [])
        for d in items[:3]:
            dep = d.get("deploy", d) if isinstance(d, dict) else d
            if not isinstance(dep, dict):
                continue
            status = dep.get("status", "?")
            created = dep.get("createdAt", "")[:19] if dep.get("createdAt") else "?"
            print(f"\nDeploy at {created}:")
            print(f"  Status: {status}")
            print(f"  ID: {dep.get('id')}")

            # Try to get build logs
            build_id = dep.get("buildId")
            if build_id:
                print(f"  Build ID: {build_id}")
    except Exception as e:
        print(f"Error getting deploy details: {e}")

    # Get the latest build to see errors
    print("\n--- Latest Build Details ---")
    try:
        # Get builds
        builds = get(f"/services/{SERVICE_ID}/builds?limit=3")
        for b in builds[:3]:
            build = b.get("build", b) if isinstance(b, dict) else b
            if not isinstance(build, dict):
                continue
            print(f"  Build ID: {build.get('id')}")
            print(f"  Status: {build.get('status')}")
            print(f"  Created: {build.get('createdAt')}")
            print(f"  Finished: {build.get('finishedAt')}")
            if build.get('error'):
                print(f"  ERROR: {build.get('error')}")
    except Exception as e:
        print(f"Error getting builds: {e}")


if __name__ == "__main__":
    main()
