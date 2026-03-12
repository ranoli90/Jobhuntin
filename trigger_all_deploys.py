#!/usr/bin/env python3
"""Trigger deploys for all workers"""
import os
import json
import urllib.request

API_KEY = 'rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF'
headers = {
    'Authorization': f'Bearer {API_KEY}', 
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Workers to deploy
workers = [
    ('srv-d6pd9gh5pdvs73ara9og', 'jobhuntin-job-sync'),
    ('srv-d6pd9k24d50c73a8gvp0', 'jobhuntin-job-queue'),
    ('srv-d6pd9np4tr6s73aks17g', 'jobhuntin-follow-up-reminders'),
    ('srv-d6pdaeh5pdvs73arak1g', 'sorce-auto-apply-agent'),
    ('srv-d6p5n5vkijhs73fikui0', 'jobhuntin-seo-engine'),
]

for worker_id, worker_name in workers:
    print(f"Triggering deploy for {worker_name}...")
    
    # Trigger deploy
    data = json.dumps({}).encode()
    req = urllib.request.Request(
        f'https://api.render.com/v1/services/{worker_id}/deploys',
        data=data,
        headers=headers,
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            deploy_id = result.get('id', 'unknown')
            print(f"  OK: deploy {deploy_id}")
    except urllib.error.HTTPError as e:
        print(f"  Error: {e.code}")
        print(f"  {e.read().decode()[:200]}")

print("\nDone!")
