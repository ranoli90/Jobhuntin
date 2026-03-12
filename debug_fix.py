#!/usr/bin/env python3
"""Debug the DATABASE_URL fix"""

import json
import urllib.request
import urllib.error

RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
API_SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"

# First, list all env vars to get the ID
url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {RENDER_API_KEY}"})

with urllib.request.urlopen(req, timeout=30) as r:
    env_vars = json.loads(r.read().decode())

print("All env vars:")
for item in env_vars:
    ev = item.get("envVar", {})
    key = ev.get("key")
    value = ev.get("value", "")
    ev_id = ev.get("id")
    print(f"  ID: {ev_id}, Key: {key}, Value: {value[:50] if value else 'None'}...")

# Find DATABASE_URL specifically
for item in env_vars:
    ev = item.get("envVar", {})
    key = ev.get("key")
    if key == "DATABASE_URL":
        ev_id = ev.get("id")
        current_value = ev.get("value", "")
        
        print(f"\n\nDATABASE_URL details:")
        print(f"  ID: {ev_id}")
        print(f"  Current value: {current_value}")
        
        # Add sslmode=require
        if "?" in current_value:
            new_value = current_value + "&sslmode=require"
        else:
            new_value = current_value + "?sslmode=require"
        
        print(f"  New value: {new_value}")
        
        # Try to update
        print(f"\n  Attempting PUT to update...")
        put_url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars/{ev_id}"
        put_req = urllib.request.Request(
            put_url,
            data=json.dumps({"value": new_value}).encode(),
            headers={
                "Authorization": f"Bearer {RENDER_API_KEY}",
                "Content-Type": "application/json"
            },
            method="PUT"
        )
        
        try:
            with urllib.request.urlopen(put_req, timeout=30) as resp:
                print(f"  Status: {resp.status}")
                print(f"  Response: {resp.read().decode()[:500]}")
        except urllib.error.HTTPError as e:
            print(f"  HTTP Error: {e.code}")
            print(f"  Error body: {e.read().decode()[:500]}")
