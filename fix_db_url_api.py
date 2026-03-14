#!/usr/bin/env python3
"""Fix DATABASE_URL using Render API - proper method"""

import json
import urllib.error
import urllib.request

RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
API_SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"

# First, let's get all env vars and their details
print("=" * 60)
print("Step 1: Get current environment variables")
print("=" * 60)

url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {RENDER_API_KEY}"})

with urllib.request.urlopen(req, timeout=30) as r:
    env_vars = json.loads(r.read().decode())

print(f"Found {len(env_vars)} env var entries:")
for item in env_vars:
    print(f"  Item: {json.dumps(item)[:200]}")

# Now try POST to create/update DATABASE_URL
print("\n" + "=" * 60)
print("Step 2: Try POST to create/update DATABASE_URL")
print("=" * 60)

new_db_url = "postgresql://jobhuntin_db_ghef_user:W0106M1RIEmzZTBI3A0vS0jq2NkCkP1x@dpg-d6p53ghr0fns73e4da20-a:5432/jobhuntin_db_ghef?sslmode=require"

post_url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars"
post_data = {
    "key": "DATABASE_URL",
    "value": new_db_url
}

post_req = urllib.request.Request(
    post_url,
    data=json.dumps(post_data).encode(),
    headers={
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(post_req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        print(f"POST Status: {resp.status}")
        print(f"Result: {json.dumps(result, indent=2)[:500]}")
except urllib.error.HTTPError as e:
    print(f"POST HTTP Error: {e.code}")
    print(f"Error body: {e.read().decode()[:500]}")

# Check if it worked
print("\n" + "=" * 60)
print("Step 3: Verify DATABASE_URL")
print("=" * 60)

verify_req = urllib.request.Request(url, headers={"Authorization": f"Bearer {RENDER_API_KEY}"})
with urllib.request.urlopen(verify_req, timeout=30) as r:
    env_vars = json.loads(r.read().decode())

for item in env_vars:
    ev = item.get("envVar", {})
    key = ev.get("key")
    if key == "DATABASE_URL":
        value = ev.get("value", "")
        print(f"DATABASE_URL: {value}")
        if "sslmode" in value:
            print("SSL mode: FOUND!")
        else:
            print("SSL mode: MISSING!")
