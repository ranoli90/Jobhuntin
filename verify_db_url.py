#!/usr/bin/env python3
"""Check DATABASE_URL for workers"""
import os
import json
import urllib.request

API_KEY = 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF'
headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}

# Workers to check
workers = [
    ('srv-d6pd9gh5pdvs73ara9og', 'jobhuntin-job-sync'),
    ('srv-d6pdaeh5pdvs73arak1g', 'sorce-auto-apply-agent'),
]

for worker_id, worker_name in workers:
    print(f"\n{worker_name}:")
    
    # Get env vars
    req = urllib.request.Request(
        f'https://api.render.com/v1/services/{worker_id}/env-vars', 
        headers=headers
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        env_vars = json.loads(resp.read().decode())
    
    for item in env_vars:
        key = item.get('envVar', {}).get('key', '')
        value = item.get('envVar', {}).get('value', '')
        if key == 'DATABASE_URL':
            print(f"  DATABASE_URL: {value}")
            if 'sslmode' in value:
                print(f"    sslmode present")
            else:
                print(f"    ERROR: sslmode MISSING!")
