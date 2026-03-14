#!/usr/bin/env python3
"""List ALL Render services including databases and Redis"""
import json
import os
import urllib.request

API_KEY = os.environ.get('RENDER_API_KEY', 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF')
headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}

# Get all services (web, workers, etc)
req = urllib.request.Request('https://api.render.com/v1/services', headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    services = json.loads(response.read().decode())
    print(f"=== SERVICES: {len(services)} ===")
    for svc in services:
        s = svc['service']
        print(f"\nName: {s['name']}")
        print(f"  Type: {s['type']}")
        print(f"  ID: {s['id']}")
        print(f"  Suspended: {s.get('suspended', 'N/A')}")
        if 'serviceDetails' in s:
            sd = s['serviceDetails']
            if 'url' in sd:
                print(f"  URL: {sd['url']}")

# Get all databases
print("\n\n=== DATABASES ===")
req = urllib.request.Request('https://api.render.com/v1/databases', headers=headers)
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        dbs = json.loads(response.read().decode())
        print(f"Found {len(dbs)} databases")
        for db in dbs:
            d = db.get('database', {})
            print(f"\nName: {d.get('name')}")
            print(f"  ID: {d.get('id')}")
            print(f"  Status: {d.get('status')}")
except Exception as e:
    print(f"Error getting databases: {e}")

# Get all Redis instances
print("\n\n=== REDIS ===")
req = urllib.request.Request('https://api.render.com/v1/redis', headers=headers)
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        redis_instances = json.loads(response.read().decode())
        print(f"Found {len(redis_instances)} Redis instances")
        for r in redis_instances:
            r_obj = r.get('keyValue', {})
            print(f"\nName: {r_obj.get('name')}")
            print(f"  ID: {r_obj.get('id')}")
            print(f"  Status: {r_obj.get('status')}")
except Exception as e:
    print(f"Error getting Redis: {e}")
