#!/usr/bin/env python3
"""Debug the API response"""
import os
import json
import urllib.request

API_KEY = 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF'
headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}

# Get services
req = urllib.request.Request('https://api.render.com/v1/services', headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    services = json.loads(response.read().decode())
    print(json.dumps(services, indent=2))
