#!/usr/bin/env python3
"""Check database links and trigger deploy"""

import json
import urllib.request
import urllib.error

RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
API_SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"

# Get service details
url = f"https://api.render.com/v1/services/{API_SERVICE_ID}"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {RENDER_API_KEY}"})

with urllib.request.urlopen(req, timeout=30) as r:
    service = json.loads(r.read().decode())

print("Service details:")
print(f"  Name: {service.get('name')}")
print(f"  Type: {service.get('type')}")
print(f"  Status: {service.get('suspended')}")

# Check for linked databases
service_details = service.get("serviceDetails", {})
print(f"\n  Runtime: {service_details.get('runtime')}")
print(f"  Env: {service_details.get('env')}")

# Check for databases
if "database" in service:
    print(f"\n  Linked database: {service.get('database')}")

# Now trigger a deploy
print("\nTriggering deploy...")
deploy_url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/deploys"
deploy_req = urllib.request.Request(
    deploy_url,
    data=json.dumps({}).encode(),
    headers={
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(deploy_req, timeout=30) as resp:
        deploy = json.loads(resp.read().decode())
        print(f"Deploy triggered: {deploy.get('id')}")
        print(f"Status: {deploy.get('status')}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Error body: {e.read().decode()[:500]}")
