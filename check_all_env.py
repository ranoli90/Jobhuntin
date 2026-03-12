#!/usr/bin/env python3
"""Check all env vars"""

import json
import urllib.request

RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
API_SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"

url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {RENDER_API_KEY}"})

with urllib.request.urlopen(req, timeout=30) as r:
    env_vars = json.loads(r.read().decode())

print(f"Found {len(env_vars)} env vars:")
for item in env_vars:
    ev = item.get("envVar", {})
    key = ev.get("key")
    value = ev.get("value", "")
    # Mask sensitive values
    if "postgresql" in value or "redis" in value or "secret" in key.lower():
        print(f"  {key}: {value[:30]}...")
    else:
        print(f"  {key}: {value}")
