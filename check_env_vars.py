#!/usr/bin/env python3
"""Check environment variables for all services"""
import json
import urllib.request

API_KEY = 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF'
headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}

# Get services
req = urllib.request.Request('https://api.render.com/v1/services', headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    services = json.loads(response.read().decode())

# Get env vars for each service
for svc in services:
    s = svc['service']
    svc_id = s['id']
    svc_name = s['name']
    svc_type = s['type']

    print(f"\n{'='*60}")
    print(f"Service: {svc_name} ({svc_type})")
    print(f"ID: {svc_id}")
    print(f"{'='*60}")

    # Get env vars
    req = urllib.request.Request(
        f'https://api.render.com/v1/services/{svc_id}/env-vars',
        headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            env_vars = json.loads(resp.read().decode())
            print(f"Environment Variables ({len(env_vars)}):")
            for env in env_vars:
                # Hide values for secrets
                key = env.get('key', '')
                value = env.get('value', '')
                if any(secret in key.lower() for secret in ['secret', 'key', 'password', 'token']):
                    value = '***HIDDEN***'
                print(f"  - {key}: {value}")
    except Exception as e:
        print(f"Error getting env vars: {e}")
