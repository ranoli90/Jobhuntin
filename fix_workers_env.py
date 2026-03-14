#!/usr/bin/env python3
"""Add missing environment variables to worker services."""

import json
import time
import urllib.request

API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
BASE_URL = "https://api.render.com/v1"

# Services that need additional env vars
WORKER_SERVICES = [
    "srv-d6pd9gh5pdvs73ara9og",  # jobhuntin-job-sync
    "srv-d6pd9k24d50c73a8gvp0",  # jobhuntin-job-queue
    "srv-d6pd9np4tr6s73aks17g",  # jobhuntin-follow-up-reminders
    "srv-d6pdaeh5pdvs73arak1g",  # sorce-auto-apply-agent
    "srv-d6p5n5vkijhs73fikui0",  # jobhuntin-seo-engine
]

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", headers={
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())

def set_env_var(svc_id, key, value):
    """Set a single environment variable."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    data = json.dumps([{"key": key, "value": value}])

    req = urllib.request.Request(
        f"{BASE_URL}/services/{svc_id}/env-vars",
        headers=headers,
        data=data.encode(),
        method="PUT"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status in (200, 201, 204)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()}")
        return False

# Get env vars from API service (which has all needed vars)
print("Getting env vars from API service...")
api_env = get("/services/srv-d6p4l03h46gs73ftvuj0/env-vars")

redis_url = None
jwt_secret = None
csrf_secret = None

for item in api_env:
    ev = item.get("envVar", item) if isinstance(item, dict) else item
    key = ev.get("key", "")
    if key == "REDIS_URL":
        redis_url = ev.get("value", "")
    elif key == "JWT_SECRET":
        jwt_secret = ev.get("value", "")
    elif key == "CSRF_SECRET":
        csrf_secret = ev.get("value", "")

print(f"Found REDIS_URL: {redis_url[:30] if redis_url else 'None'}...")
print(f"Found JWT_SECRET: {jwt_secret[:8] if jwt_secret else 'None'}...")
print(f"Found CSRF_SECRET: {csrf_secret[:8] if csrf_secret else 'None'}...")

# Add env vars to each worker
for svc_id in WORKER_SERVICES:
    print(f"\n=== Processing {svc_id} ===")

    # Get current env vars
    current = get(f"/services/{svc_id}/env-vars")
    current_keys = set()
    for item in current:
        ev = item.get("envVar", item) if isinstance(item, dict) else item
        current_keys.add(ev.get("key", ""))

    print(f"Current env vars: {current_keys}")

    # Add REDIS_URL if missing
    if redis_url and "REDIS_URL" not in current_keys:
        print("  Adding REDIS_URL...")
        set_env_var(svc_id, "REDIS_URL", redis_url)

    # Add JWT_SECRET if missing
    if jwt_secret and "JWT_SECRET" not in current_keys:
        print("  Adding JWT_SECRET...")
        set_env_var(svc_id, "JWT_SECRET", jwt_secret)

    # Add CSRF_SECRET if missing
    if csrf_secret and "CSRF_SECRET" not in current_keys:
        print("  Adding CSRF_SECRET...")
        set_env_var(svc_id, "CSRF_SECRET", csrf_secret)

    time.sleep(1)  # Rate limit

print("\n=== Done! ===")
print("Workers should now have the necessary environment variables.")
print("They will need to be redeployed to pick up the changes.")
