#!/usr/bin/env python3
"""Quick check of DATABASE_URL on Render API"""

import json
import urllib.request

RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
API_SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"

url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {RENDER_API_KEY}"})

with urllib.request.urlopen(req, timeout=30) as r:
    env_vars = json.loads(r.read().decode())

print("DATABASE_URL check:")
for item in env_vars:
    ev = item.get("envVar", {})
    key = ev.get("key")
    if key == "DATABASE_URL":
        value = ev.get("value", "")
        print(f"  Key: {key}")
        print(f"  Value: {value}")
        if "sslmode" in value:
            print(f"  SSL mode: FOUND in URL")
        else:
            print(f"  SSL mode: MISSING!")
