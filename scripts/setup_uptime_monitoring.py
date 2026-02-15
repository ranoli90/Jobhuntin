#!/usr/bin/env python
"""
Setup external uptime monitoring for production services.

Creates monitors via UptimeRobot API for:
- API health checks
- Web frontend
- Database connectivity (via API healthz)
"""

import json
import os
import urllib.error
import urllib.request

UPTIMEROBOT_API_URL = "https://api.uptimerobot.com/v2/"

SERVICES = [
    {
        "name": "JobHuntin API - Health",
        "url": "https://sorce-api.onrender.com/health",
        "type": 1,  # HTTP(s)
        "interval": 300,  # 5 minutes
    },
    {
        "name": "JobHuntin API - Healthz (Deep)",
        "url": "https://sorce-api.onrender.com/healthz",
        "type": 1,
        "interval": 300,
    },
    {
        "name": "JobHuntin Web",
        "url": "https://sorce-web.onrender.com",
        "type": 1,
        "interval": 300,
    },
    {
        "name": "JobHuntin Production",
        "url": "https://jobhuntin.com",
        "type": 1,
        "interval": 300,
    },
]


def create_monitor(api_key: str, monitor: dict) -> dict:
    """Create a single monitor via UptimeRobot API."""
    data = {
        "api_key": api_key,
        "friendly_name": monitor["name"],
        "url": monitor["url"],
        "type": monitor["type"],
        "interval": monitor["interval"],
        "alert_contacts": "1",  # Default alert contact
    }

    req = urllib.request.Request(
        f"{UPTIMEROBOT_API_URL}newMonitor",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return {"error": str(e), "body": error_body}


def get_monitors(api_key: str) -> dict:
    """List all existing monitors."""
    data = {"api_key": api_key}

    req = urllib.request.Request(
        f"{UPTIMEROBOT_API_URL}getMonitors",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": str(e)}


def print_setup_instructions():
    print("=" * 60)
    print("UPTIME MONITORING SETUP")
    print("=" * 60)
    print()
    print("1. Create UptimeRobot account at https://uptimerobot.com")
    print("2. Get your API key from Account Settings → API Settings")
    print("3. Create Main API key (not Monitor-specific)")
    print("4. Set environment variable:")
    print("   export UPTIMEROBOT_API_KEY=your_api_key")
    print("5. Run this script:")
    print("   python scripts/setup_uptime_monitoring.py")
    print()
    print("Alternatively, manually create monitors for:")
    for svc in SERVICES:
        print(f"   - {svc['name']}: {svc['url']}")
    print()
    print("=" * 60)


def main():
    api_key = os.environ.get("UPTIMEROBOT_API_KEY")

    if not api_key:
        print_setup_instructions()
        return

    print("Creating uptime monitors...")
    print()

    for monitor in SERVICES:
        print(f"Creating: {monitor['name']}...")
        result = create_monitor(api_key, monitor)

        if "error" in result:
            print(f"  Error: {result['error']}")
            if "body" in result:
                print(f"  Details: {result['body']}")
        else:
            print(f"  Success: {result.get('monitor', {}).get('id', 'created')}")

    print()
    print("Done! Check https://dashboard.uptimerobot.com for status.")


if __name__ == "__main__":
    main()
