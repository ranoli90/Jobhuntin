#!/usr/bin/env python3
"""Unsuspend services using PATCH method"""
import os
import json
import urllib.request

API_KEY = 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF'
headers = {
    'Authorization': f'Bearer {API_KEY}', 
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Try to unsuspend each service using PATCH
service_ids = [
    ('srv-d63l79hr0fns73boblag', 'jobhuntin-api'),
    ('srv-d63spbogjchc739akan0', 'jobhuntin-web'),
    ('srv-d66aadsr85hc73dastfg', 'jobhuntin-seo-engine'),
]

for svc_id, name in service_ids:
    print(f"\nTrying to unsuspend {name} ({svc_id})...")
    
    # Use PATCH method to update suspended status
    data = json.dumps({"suspended": "not_suspended"}).encode()
    req = urllib.request.Request(
        f'https://api.render.com/v1/services/{svc_id}',
        data=data,
        headers=headers,
        method='PATCH'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            print(f"OK: {result['service']['name']} - suspended: {result['service']['suspended']}")
    except urllib.error.HTTPError as e:
        print(f"Error: {e.code}")
        body = e.read().decode()
        print(body[:300])
