#!/usr/bin/env python3
"""Fetch recent deploy events for a Render service.

Usage:
  export RENDER_API_KEY=rnd_xxx
  SERVICE_ID=srv-xxx python scripts/maintenance/fetch_logs.py
  # Or set SERVICE_ID in .env
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
SERVICE_ID = os.environ.get("SERVICE_ID", "srv-d63sipvgi27c739ni59g")

if not RENDER_API_KEY:
    print("Error: RENDER_API_KEY not found in .env")
    sys.exit(1)

headers = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}


def get_latest_deploy_logs(service_id: str) -> bool:
    url = f"https://api.render.com/v1/services/{service_id}/events"
    try:
        response = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as e:
        print(f"Error fetching events: {e}")
        return False
    if response.status_code == 200:
        events = response.json()
        print(f"--- Recent Events for {service_id} ---")
        for item in events[:10]:
            event = item.get("event", item)
            print(
                f"[{event.get(
    'timestamp', '?')}] {event.get('type', '?')}: {event.get('data', {}).get('reason', 'No reason provided')}"
            )
        return True
    print(f"Failed to fetch events: {response.status_code}")
    return False


if __name__ == "__main__":
    if not get_latest_deploy_logs(SERVICE_ID):
        sys.exit(1)
