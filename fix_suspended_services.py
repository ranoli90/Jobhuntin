#!/usr/bin/env python3
"""Unsuspend all suspended services and check their env vars"""
import os
import json
import urllib.request

API_KEY = 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF'
headers = {
    'Authorization': f'Bearer {API_KEY}', 
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Get services
req = urllib.request.Request('https://api.render.com/v1/services', headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    services = json.loads(response.read().decode())

# Services to unsuspend
service_ids = [
    'srv-d63l79hr0fns73boblag',  # jobhuntin-api
    'srv-d63spbogjchc739akan0',  # jobhuntin-web
    'srv-d66aadsr85hc73dastfg',  # jobhuntin-seo-engine
]

for svc_id in service_ids:
    print(f"\n=== Unsuspending {svc_id} ===")
    data = json.dumps({"suspended": "not_suspended"}).encode()
    req = urllib.request.Request(
        f'https://api.render.com/v1/services/{svc_id}',
        data=data,
        headers=headers,
        method='PUT'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            print(f"✓ Unsuspended: {result['service']['name']}")
    except urllib.error.HTTPError as e:
        print(f"✗ Error: {e.code}")
        print(e.read().decode()[:500])
