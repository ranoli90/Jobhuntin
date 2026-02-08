import urllib.request
import json
import os

RENDER_API_KEY = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

print("Fetching services...")
try:
    req = urllib.request.Request("https://api.render.com/v1/services", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        services = json.loads(response.read().decode())
        print(f"Found {len(services)} services")
        for svc in services:
             print(f"{svc['service']['name']} : {svc['service']['id']}")
except Exception as e:
    print(f"Error: {e}")
