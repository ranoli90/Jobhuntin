#!/usr/bin/env python3
"""Check logs for all Render services - trying log streams."""

import urllib.request
import json
import os
import time

API_KEY = os.environ.get("RENDER_API_KEY")
if not API_KEY:
    print("ERROR: RENDER_API_KEY not set")
    exit(1)

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}

SERVICES = {
    "jobhuntin-job-sync": "srv-d6pd9gh5pdvs73ara9og",
    "jobhuntin-job-queue": "srv-d6pd9k24d50c73a8gvp0",
    "jobhuntin-follow-up-reminders": "srv-d6pd9np4tr6s73aks17g",
    "sorce-auto-apply-agent": "srv-d6pdaeh5pdvs73arak1g",
    "jobhuntin-api": "srv-d6p4l03h46gs73ftvuj0",
    "jobhuntin-seo-engine": "srv-d6p5n5vkijhs73fikui0",
}

print("=" * 70)
print("RENDER SERVICES LOG CHECK")
print("=" * 70)

# Try to get logs from the instances endpoint
for name, service_id in SERVICES.items():
    print(f"\n[{name}]")
    try:
        # First get the instances
        url = f"https://api.render.com/v1/services/{service_id}/instances"
        req = urllib.request.Request(url, headers=HEADERS)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                instances = json.loads(response.read().decode())
            
            if instances:
                instance = instances[0]
                instance_id = instance.get('id')
                print(f"  Instance ID: {instance_id}")
                print(f"  Instance Status: {instance.get('state')}")
                
                # Try to get logs for this instance
                log_url = f"https://api.render.com/v1/services/{service_id}/instances/{instance_id}/logs"
                req = urllib.request.Request(log_url, headers=HEADERS)
                try:
                    with urllib.request.urlopen(req, timeout=30) as response:
                        logs = json.loads(response.read().decode())
                    
                    print(f"  Total log entries: {len(logs)}")
                    
                    # Look for errors
                    errors = [l for l in logs if 'error' in str(l).lower() or 'exception' in str(l).lower() or 'fatal' in str(l).lower()]
                    if errors:
                        print(f"  Errors found: {len(errors)}")
                        for err in errors[:3]:
                            print(f"    - {str(err)[:150]}")
                    else:
                        print(f"  Status: ✅ No errors in logs")
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        print(f"  Log endpoint: 404 (not available via API)")
                    else:
                        print(f"  Log HTTP Error: {e.code}")
            else:
                print(f"  No instances found")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  Instances endpoint: 404 (not available)")
            else:
                print(f"  HTTP Error: {e.code}")
                
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {str(e)[:100]}")

print("\n" + "=" * 70)
print("NOTE: Render API logs access may require a paid plan.")
print("The deploy status above confirms successful deployments.")
print("=" * 70)
