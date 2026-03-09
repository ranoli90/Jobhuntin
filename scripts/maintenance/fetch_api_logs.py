#!/usr/bin/env python3
"""Fetch API service logs and deploy status from Render.

Usage:
  export RENDER_API_KEY=rnd_xxx   # or RENDER_API_TOKEN
  python scripts/maintenance/fetch_api_logs.py

Requires: RENDER_API_KEY or RENDER_API_TOKEN in env (or .env)
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

API_KEY = os.environ.get("RENDER_API_KEY") or os.environ.get("RENDER_API_TOKEN")
if not API_KEY:
    print("Error: Set RENDER_API_KEY or RENDER_API_TOKEN in .env or environment")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
BASE = "https://api.render.com/v1"


def get(path: str) -> dict | list:
    import urllib.request
    req = urllib.request.Request(f"{BASE}{path}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        import json
        return json.loads(r.read().decode())


def main():
    print("Fetching Render services...")
    try:
        services = get("/services?limit=50")
    except Exception as e:
        print(f"API error: {e}")
        sys.exit(1)

    # Normalize: API may return list of {service: {...}} or [{...}]
    svc_list = []
    for item in services:
        s = item.get("service", item) if isinstance(item, dict) else item
        if isinstance(s, dict) and s.get("id"):
            svc_list.append(s)

    api_svc = next(
        (s for s in svc_list if "api" in s.get("name", "").lower() and s.get("type") in ("web_service", "worker")),
        None,
    )
    if not api_svc:
        api_svc = next((s for s in svc_list if "jobhuntin-api" in s.get("name", "") or "sorce-api" in s.get("name", "")), None)
    if not api_svc:
        print("Services found:", [s.get("name") for s in svc_list])
        print("Could not find API service. Specify service ID manually.")
        sys.exit(1)

    sid = api_svc["id"]
    name = api_svc.get("name", "unknown")
    print(f"\n=== API Service: {name} ({sid}) ===\n")

    # Deploys
    print("--- Recent Deploys ---")
    try:
        deploys = get(f"/services/{sid}/deploys?limit=5")
        items = deploys if isinstance(deploys, list) else deploys.get("deploys", [])
        for d in items[:5]:
            dep = d.get("deploy", d) if isinstance(d, dict) else d
            if not isinstance(dep, dict):
                continue
            status = dep.get("status", "?")
            created = dep.get("createdAt", "")[:19] if dep.get("createdAt") else "?"
            reason = dep.get("reason", "") or dep.get("message", "") or ""
            print(f"  [{created}] status={status}  {reason}")
    except Exception as e:
        print(f"  Error: {e}")

    # Events (often contain failure reasons)
    print("\n--- Recent Events ---")
    try:
        events = get(f"/services/{sid}/events?limit=15")
        for item in (events or [])[:15]:
            ev = item.get("event", item) if isinstance(item, dict) else item
            if not isinstance(ev, dict):
                continue
            ts = ev.get("timestamp", "")[:19] if ev.get("timestamp") else "?"
            typ = ev.get("type", "?")
            data = ev.get("data") or {}
            reason = data.get("reason") or data.get("message") or ""
            print(f"  [{ts}] {typ}: {reason}")
    except Exception as e:
        print(f"  Error: {e}")

    # Logs API (if available)
    print("\n--- Logs (last 50) ---")
    try:
        import time
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - (3600 * 1000)  # last hour
        logs = get(f"/logs?resourceIds={sid}&startTime={start_ms}&endTime={end_ms}&limit=50")
        entries = logs.get("logs", []) if isinstance(logs, dict) else (logs or [])
        for entry in entries[:50]:
            msg = entry.get("message", entry) if isinstance(entry, dict) else str(entry)
            ts = entry.get("timestamp", "")[:19] if isinstance(entry, dict) and entry.get("timestamp") else ""
            print(f"  [{ts}] {msg}")
        if not entries:
            print("  (No log entries returned - try Render Dashboard for full logs)")
    except Exception as e:
        print(f"  Logs API error: {e}")


if __name__ == "__main__":
    main()
