#!/usr/bin/env python3
"""Add env vars using PUT method"""
import os
import json
import urllib.request

API_KEY = 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF'
headers = {
    'Authorization': f'Bearer {API_KEY}', 
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Try to add DATABASE_URL to jobhuntin-job-sync
worker_id = 'srv-d6pd9gh5pdvs73ara9og'
env_key = 'DATABASE_URL'
env_value = 'postgresql://jobhuntin_db_ghef_user:W0106M1RIEmzZTBI3A0vS0jq2NkCkP1x@dpg-d6p53ghr0fns73e4da20-a:5432/jobhuntin_db_ghef?sslmode=require'

# Try PUT to update/create
data = json.dumps({"key": env_key, "value": env_value}).encode()
req = urllib.request.Request(
    f'https://api.render.com/v1/services/{worker_id}/env-vars/{env_key}',
    data=data,
    headers=headers,
    method='PUT'
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        print(f"OK: {env_key}")
        print(json.dumps(result, indent=2)[:500])
except urllib.error.HTTPError as e:
    print(f"Error: {e.code}")
    print(e.read().decode()[:500])
