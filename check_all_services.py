#!/usr/bin/env python3
"""Check status of all Render services."""

import json
import time
import urllib.error
import urllib.request

API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
BASE_URL = "https://api.render.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

# All service IDs
SERVICES = [
    ("srv-d6p4l03h46gs73ftvuj0", "jobhuntin-api", "web_service"),
    ("srv-d6p5m0fafjfc739ij050", "jobhuntin-web", "static_site"),
    ("srv-d6p5n5vkijhs73fikui0", "jobhuntin-seo-engine", "background_worker"),
    ("srv-d6pd9gh5pdvs73ara9og", "jobhuntin-job-sync", "background_worker"),
    ("srv-d6pd9k24d50c73a8gvp0", "jobhuntin-job-queue", "background_worker"),
    ("srv-d6pd9np4tr6s73aks17g", "jobhuntin-follow-up-reminders", "background_worker"),
    ("srv-d6pdaeh5pdvs73arak1g", "sorce-auto-apply-agent", "background_worker"),
]


def get(path: str):
    """Make GET request to Render API."""
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": str(e), "code": e.code}
    except Exception as e:
        return {"error": str(e)}


def check_service(svc_id: str, name: str, svc_type: str):
    """Check a single service."""
    print(f"\n{'='*60}")
    print(f"Service: {name} ({svc_type})")
    print(f"ID: {svc_id}")
    print(f"{'='*60}")

    # Get service details
    service = get(f"/services/{svc_id}")
    if "error" in service:
        print(f"ERROR: {service}")
        return

    # Get the actual service data - it might be nested
    svc_data = service.get("service", service)

    print(f"State: {service.get('state', 'unknown')}")
    print(f"Status: {svc_data.get('status', 'unknown')}")
    print(f"Dashboard: {svc_data.get('dashboardUrl', 'N/A')}")

    # Get environment variables count
    env_vars = get(f"/services/{svc_id}/env-vars")
    if isinstance(env_vars, list):
        print(f"Env Vars: {len(env_vars)}")
    else:
        print(f"Env Vars: Error fetching - {env_vars.get('error', 'unknown')}")

    # Get recent deploys
    deploys = get(f"/services/{svc_id}/deploys?limit=3")
    print("\nRecent Deploys:")
    if isinstance(deploys, list):
        for d in deploys[:3]:
            dep = d.get("deploy", d) if isinstance(d, dict) else d
            if isinstance(dep, dict):
                status = dep.get("status", "?")
                created = dep.get("createdAt", "")[:19] if dep.get("createdAt") else "?"
                print(f"  [{created}] {status}")
    else:
        print(f"  Error: {deploys.get('error', 'unknown')}")

    # Get recent events (often contain crash info)
    events = get(f"/services/{svc_id}/events?limit=5")
    print("\nRecent Events:")
    if isinstance(events, list):
        for item in events[:5]:
            ev = item.get("event", item) if isinstance(item, dict) else item
            if isinstance(ev, dict):
                ts = ev.get("timestamp", "")[:19] if ev.get("timestamp") else "?"
                typ = ev.get("type", "?")
                data = ev.get("data") or {}
                reason = data.get("reason") or data.get("message") or ""
                print(f"  [{ts}] {typ}: {reason}")
    else:
        print(f"  Error: {events.get('error', 'unknown')}")


def main():
    print("="*60)
    print("RENDER SERVICES STATUS CHECK")
    print("="*60)

    for svc_id, name, svc_type in SERVICES:
        check_service(svc_id, name, svc_type)
        time.sleep(0.5)  # Rate limit

    print("\n" + "="*60)
    print("CHECK COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
