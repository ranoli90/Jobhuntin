#!/usr/bin/env python3
"""Fetch Render service logs and environment variables, fix issues, and trigger redeploy."""

import json
import time
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


def post(path: str, data: dict = None):
    """Make POST request to Render API."""
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers=HEADERS,
        data=json.dumps(data).encode() if data else None,
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


def put(path: str, data: dict):
    """Make PUT request to Render API."""
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={**HEADERS, "Content-Type": "application/json"},
        data=json.dumps(data).encode(),
        method="PUT"
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


def main():
    print(f"=== Fetching information for service: {SERVICE_ID} ===\n")

    # Get service details
    print("--- Service Details ---")
    try:
        service = get(f"/services/{SERVICE_ID}")
        print(f"Service Name: {service.get('name')}")
        print(f"Service Type: {service.get('type')}")
        print(
    f"Service Status: {service.get('service', {}).get('status') if isinstance(service.get('service'),
    dict) else 'N/A'}")
    except Exception as e:
        print(f"Error getting service: {e}")

    # Get environment variables
    print("\n--- Current Environment Variables ---")
    try:
        env_vars = get(f"/services/{SERVICE_ID}/env-vars")
        current_vars = {}
        for item in env_vars:
            ev = item.get("envVar", item) if isinstance(item, dict) else item
            key = ev.get("key")
            value = ev.get("value", "")
            # Mask sensitive values
            if key and any(s in key.lower() for s in ["secret", "key", "password", "token"]):
                value = value[:8] + "..." if len(value) > 8 else "***"
            current_vars[key] = value
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error getting env vars: {e}")
        current_vars = {}

    # Get recent deploys
    print("\n--- Recent Deploys ---")
    try:
        deploys = get(f"/services/{SERVICE_ID}/deploys?limit=5")
        items = deploys if isinstance(deploys, list) else deploys.get("deploys", [])
        for d in items[:5]:
            dep = d.get("deploy", d) if isinstance(d, dict) else d
            if not isinstance(dep, dict):
                continue
            status = dep.get("status", "?")
            created = dep.get("createdAt", "")[:19] if dep.get("createdAt") else "?"
            print(f"  [{created}] status={status}")
    except Exception as e:
        print(f"Error getting deploys: {e}")

    # Get recent events (often contain failure reasons)
    print("\n--- Recent Events ---")
    try:
        events = get(f"/services/{SERVICE_ID}/events?limit=10")
        for item in (events or [])[:10]:
            ev = item.get("event", item) if isinstance(item, dict) else item
            if not isinstance(ev, dict):
                continue
            ts = ev.get("timestamp", "")[:19] if ev.get("timestamp") else "?"
            typ = ev.get("type", "?")
            data = ev.get("data") or {}
            reason = data.get("reason") or data.get("message") or ""
            print(f"  [{ts}] {typ}: {reason}")
    except Exception as e:
        print(f"Error getting events: {e}")

    # Get logs
    print("\n--- Recent Logs (last 50) ---")
    try:
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - (3600 * 1000)  # last hour
        logs = get(
            f"/logs?resourceIds={SERVICE_ID}&startTime={start_ms}&endTime={end_ms}&limit=50"
        )
        entries = logs.get("logs", []) if isinstance(logs, dict) else (logs or [])
        for entry in entries[:50]:
            msg = entry.get("message", entry) if isinstance(entry, dict) else str(entry)
            ts = (
                entry.get("timestamp", "")[:19]
                if isinstance(entry, dict) and entry.get("timestamp")
                else ""
            )
            print(f"  [{ts}] {msg}")
        if not entries:
            print("  (No log entries returned)")
    except Exception as e:
        print(f"  Logs API error: {e}")

    # Check critical env vars
    print("\n--- Critical Environment Variables Check ---")
    required_critical = [
        "DATABASE_URL",
        "ENV",
        "LLM_API_KEY",
        "JWT_SECRET",
    ]

    for key in required_critical:
        if key in current_vars:
            print(f"  ✓ {key} is set")
        else:
            print(f"  ✗ {key} is MISSING")

    # Check DATABASE_URL format
    db_url = current_vars.get("DATABASE_URL", "")
    if db_url:
        print("\n--- DATABASE_URL Analysis ---")
        print(f"Current: {db_url[:50]}...")
        expected_host = "dpg-d6p53ghr0fns73e4da20-a"
        if expected_host in db_url:
            print(f"  ✓ DATABASE_URL contains correct host: {expected_host}")
        else:
            print(f"  ✗ DATABASE_URL does NOT contain expected host: {expected_host}")
            print(f"  Expected format: postgresql://username:password@{expected_host}:5432/jobhuntin_db_ghef")


if __name__ == "__main__":
    main()
