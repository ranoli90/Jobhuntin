#!/usr/bin/env python3
"""Fetch logs from workers to diagnose crash"""
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
    print(f"\n{'='*60}")
    print(f"LOGS: {worker_name}")
    print(f"{'='*60}")

    # Get recent logs
    req = urllib.request.Request(
        f'https://api.render.com/v1/services/{worker_id}/logs?limit=50',
        headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            logs = json.loads(resp.read().decode())
            print(f"Log entries: {len(logs)}")
            # Print last 20 lines
            for entry in logs[-20:]:
                msg = entry.get('message', '')
                print(msg[:200])
    except Exception as e:
        print(f"Error: {e}")
