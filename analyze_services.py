#!/usr/bin/env python3
"""Analyze all services and check environment variables."""

import urllib.request
import json

API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
BASE_URL = "https://api.render.com/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

SERVICES = [
    ("srv-d6p4l03h46gs73ftvuj0", "jobhuntin-api", "web_service"),
    ("srv-d6p5m0fafjfc739ij050", "jobhuntin-web", "static_site"),
    ("srv-d6p5n5vkijhs73fikui0", "jobhuntin-seo-engine", "background_worker"),
    ("srv-d6pd9gh5pdvs73ara9og", "jobhuntin-job-sync", "background_worker"),
    ("srv-d6pd9k24d50c73a8gvp0", "jobhuntin-job-queue", "background_worker"),
    ("srv-d6pd9np4tr6s73aks17g", "jobhuntin-follow-up-reminders", "background_worker"),
    ("srv-d6pdaeh5pdvs73arak1g", "sorce-auto-apply-agent", "background_worker"),
]

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())

# Check each service
print("="*70)
print("SERVICE ENVIRONMENT VARIABLE ANALYSIS")
print("="*70)

for svc_id, name, svc_type in SERVICES:
    print(f"\n[{name}] ({svc_type})")
    print("-" * 50)
    
    # Get env vars
    env_vars = get(f"/services/{svc_id}/env-vars")
    if isinstance(env_vars, list):
        print(f"Total env vars: {len(env_vars)}")
        print("Env var keys:")
        for item in env_vars:
            ev = item.get("envVar", item) if isinstance(item, dict) else item
            key = ev.get("key", "unknown")
            print(f"  - {key}")
    else:
        print(f"Error getting env vars: {env_vars}")
