#!/usr/bin/env python3
"""Delete DATABASE_URL using key name in URL"""

import json
import urllib.error
import urllib.request

RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
API_SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"

# Try DELETE with key name
print("Deleting DATABASE_URL using key name...")

delete_url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars/DATABASE_URL"
delete_req = urllib.request.Request(
    delete_url,
    headers={"Authorization": f"Bearer {RENDER_API_KEY}"},
    method="DELETE"
)

try:
    with urllib.request.urlopen(delete_req, timeout=30) as resp:
        print(f"Delete Status: {resp.status}")
        print(f"Response: {resp.read().decode()[:200]}")
except urllib.error.HTTPError as e:
    print(f"Delete HTTP Error: {e.code}")
    print(f"Error body: {e.read().decode()[:500]}")

# Verify
print("\nVerifying DATABASE_URL...")
url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars"
verify_req = urllib.request.Request(url, headers={"Authorization": f"Bearer {RENDER_API_KEY}"})

with urllib.request.urlopen(verify_req, timeout=30) as r:
    env_vars = json.loads(r.read().decode())

found = False
for item in env_vars:
    ev = item.get("envVar", {})
    key = ev.get("key")
    value = ev.get("value", "")
    if key == "DATABASE_URL":
        found = True
        print(f"DATABASE_URL: {value}")
        if "sslmode" in value:
            print("SSL mode: FOUND!")
        else:
            print("SSL mode: MISSING!")

if not found:
    print("DATABASE_URL not found - may have been deleted successfully!")
    # Check for the None key entry
    for item in env_vars:
        ev = item.get("envVar", {})
        key = ev.get("key")
        value = ev.get("value", "")
        if key is None and "postgresql" in value:
            print(f"Found linked DB entry (key=None): {value}")
            if "sslmode" in value:
                print("SSL mode: FOUND! This should now be used.")
