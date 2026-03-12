#!/usr/bin/env python3
"""Add all missing env vars to all workers using PUT"""
import os
import json
import urllib.request

API_KEY = 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF'
headers = {
    'Authorization': f'Bearer {API_KEY}', 
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Get API service env vars to copy
req = urllib.request.Request(
    'https://api.render.com/v1/services/srv-d6p4l03h46gs73ftvuj0/env-vars', 
    headers=headers
)
with urllib.request.urlopen(req, timeout=30) as resp:
    api_env_vars = json.loads(resp.read().decode())

# Extract values from API service
env_values = {}
for item in api_env_vars:
    env_var = item.get('envVar', {})
    key = env_var.get('key', '')
    value = env_var.get('value', '')
    if key:
        env_values[key] = value

# Workers that need env vars
workers = [
    ('srv-d6pd9gh5pdvs73ara9og', 'jobhuntin-job-sync'),
    ('srv-d6pd9k24d50c73a8gvp0', 'jobhuntin-job-queue'),
    ('srv-d6pd9np4tr6s73aks17g', 'jobhuntin-follow-up-reminders'),
    ('srv-d6pdaeh5pdvs73arak1g', 'sorce-auto-apply-agent'),
    ('srv-d6p5n5vkijhs73fikui0', 'jobhuntin-seo-engine'),
]

# Required env vars for workers
required_env_vars = [
    'DATABASE_URL',
    'REDIS_URL', 
    'JWT_SECRET',
    'CSRF_SECRET',
    'LLM_API_KEY',
]

for worker_id, worker_name in workers:
    print(f"\n=== {worker_name} ===")
    
    # Check what env vars already exist
    req = urllib.request.Request(
        f'https://api.render.com/v1/services/{worker_id}/env-vars', 
        headers=headers
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        existing = json.loads(resp.read().decode())
    
    existing_keys = set()
    for item in existing:
        key = item.get('envVar', {}).get('key', '')
        if key:
            existing_keys.add(key)
    
    # Add/update missing env vars using PUT
    for env_key in required_env_vars:
        if env_key not in env_values:
            print(f"  ! {env_key}: NOT FOUND in API service!")
            continue
            
        value = env_values[env_key]
        
        # Use PUT to create/update env var
        data = json.dumps({"key": env_key, "value": value}).encode()
        req = urllib.request.Request(
            f'https://api.render.com/v1/services/{worker_id}/env-vars/{env_key}',
            data=data,
            headers=headers,
            method='PUT'
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                print(f"  + {env_key}: OK")
        except urllib.error.HTTPError as e:
            print(f"  ! {env_key}: ERROR {e.code}")

print("\n=== DONE ===")
