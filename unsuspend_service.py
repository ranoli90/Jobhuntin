#!/usr/bin/env python3
"""Unsuspend a Render service"""
import json
import os
import urllib.request

API_KEY = os.environ.get('RENDER_API_KEY', 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF')
SERVICE_ID = 'srv-d63l79hr0fns73boblag'  # jobhuntin-api

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Unsuspend the service
data = json.dumps({"suspended": "not_suspended"}).encode()
req = urllib.request.Request(
    f'https://api.render.com/v1/services/{SERVICE_ID}',
    data=data,
    headers=headers,
    method='PUT'
)

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        print(f"Status: {response.status}")
        result = json.loads(response.read().decode())
        print(f"Service unsuspended: {result['service']['name']}")
        print(f"Status: {result['service']['suspended']}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode())
