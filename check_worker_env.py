#!/usr/bin/env python3
"""Check env vars for workers"""
import json
import urllib.request

API_KEY = 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF'
headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}

# Check env vars for a worker - jobhuntin-job-sync
svc_id = 'srv-d6pd9gh5pdvs73ara9og'

req = urllib.request.Request(
    f'https://api.render.com/v1/services/{svc_id}/env-vars',
    headers=headers
)
with urllib.request.urlopen(req, timeout=30) as resp:
    env_vars = json.loads(resp.read().decode())
    print(f"jobhuntin-job-sync env vars ({len(env_vars)}):")
    for item in env_vars:
        key = item.get('envVar', {}).get('key', '')
        value = item.get('envVar', {}).get('value', '')
        if key and key not in ['DATABASE_URL', 'REDIS_URL', 'JWT_SECRET', 'CSRF_SECRET', 'LLM_API_KEY']:
            print(f"  - {key}: {value[:50]}...")
        else:
            print(f"  - {key}: [present]")
