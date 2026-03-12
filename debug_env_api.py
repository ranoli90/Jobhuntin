#!/usr/bin/env python3
"""Debug env vars API response"""
import os
import json
import urllib.request

API_KEY = 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF'
headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}

# Check env vars for one service
svc_id = 'srv-d6p4l03h46gs73ftvuj0'  # jobhuntin-api

req = urllib.request.Request(
    f'https://api.render.com/v1/services/{svc_id}/env-vars', 
    headers=headers
)
with urllib.request.urlopen(req, timeout=30) as resp:
    env_vars = json.loads(resp.read().decode())
    print(f"Type: {type(env_vars)}")
    print(f"Length: {len(env_vars) if isinstance(env_vars, list) else 'N/A'}")
    print("\nFull response:")
    print(json.dumps(env_vars, indent=2)[:2000])
