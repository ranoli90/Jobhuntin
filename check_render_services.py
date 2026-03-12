#!/usr/bin/env python3
"""Check Render services status"""
import os
import json
import urllib.request

API_KEY = os.environ.get('RENDER_API_KEY', 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF')
headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}

req = urllib.request.Request('https://api.render.com/v1/services', headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    services = json.loads(response.read().decode())
    print(f'Found {len(services)} services')
    print()
    for svc in services:
        s = svc['service']
        print(f"Name: {s['name']}")
        print(f"  Type: {s['type']}")
        print(f"  ID: {s['id']}")
        print(f"  Suspended: {s.get('suspended', 'N/A')}")
        if 'serviceDetails' in s:
            sd = s['serviceDetails']
            if 'url' in sd:
                print(f"  URL: {sd['url']}")
        print()
