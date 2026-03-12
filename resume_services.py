#!/usr/bin/env python3
"""Unsuspend services using correct Render API"""
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

# Resume each suspended service
for svc in services:
    s = svc['service']
    if s.get('suspended') == 'suspended':
        svc_id = s['id']
        svc_name = s['name']
        print(f"Resuming {svc_name} ({svc_id})...")
        
        # Use POST to /services/:id/resume
        data = json.dumps({}).encode()
        req = urllib.request.Request(
            f'https://api.render.com/v1/services/{svc_id}/resume',
            data=data,
            headers=headers,
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                print(f"OK: {result['service']['name']} - {result['service']['suspended']}")
        except urllib.error.HTTPError as e:
            print(f"Error: {e.code}")
            body = e.read().decode()
            print(body[:500])
