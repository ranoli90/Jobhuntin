#!/usr/bin/env python3
"""Delete the old DATABASE_URL to use the linked one with sslmode"""

import json
import urllib.request
import urllib.error

RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
API_SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"

# Get all env vars
print("=" * 60)
print("Step 1: Get env vars and find DATABASE_URL entry")
print("=" * 60)

url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {RENDER_API_KEY}"})

with urllib.request.urlopen(req, timeout=30) as r:
    env_vars = json.loads(r.read().decode())

# Find DATABASE_URL entry ID
db_url_id = None
for item in env_vars:
    ev = item.get("envVar", {})
    key = ev.get("key")
    if key == "DATABASE_URL":
        # The cursor is the ID for delete
        db_url_id = item.get("cursor")
        print(f"Found DATABASE_URL entry:")
        print(f"  Key: {key}")
        print(f"  Value: {ev.get('value')}")
        print(f"  Cursor (ID): {db_url_id}")
        break

if not db_url_id:
    print("DATABASE_URL not found!")
    exit(1)

# Now delete it
print("\n" + "=" * 60)
print("Step 2: Delete the old DATABASE_URL env var")
print("=" * 60)

# The delete endpoint uses the cursor as the ID
delete_url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars/{db_url_id}"
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
print("\n" + "=" * 60)
print("Step 3: Verify DATABASE_URL")
print("=" * 60)

verify_req = urllib.request.Request(url, headers={"Authorization": f"Bearer {RENDER_API_KEY}"})
with urllib.request.urlopen(verify_req, timeout=30) as r:
    env_vars = json.loads(r.read().decode())

for item in env_vars:
    ev = item.get("envVar", {})
    key = ev.get("key")
    value = ev.get("value", "")
    if key is None or key == "DATABASE_URL":
        print(f"Entry:")
        print(f"  Key: {key}")
        print(f"  Value: {value}")
        if "sslmode" in value:
            print("  SSL mode: FOUND!")
        else:
            print("  SSL mode: MISSING!")
