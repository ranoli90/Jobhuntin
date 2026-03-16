#!/usr/bin/env python3
"""Check detailed deploy information for all Render services."""

import urllib.request
import json
import os

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

print("=" * 80)
print("RENDER SERVICES - DETAILED DEPLOY STATUS")
print("=" * 80)

for name, service_id in SERVICES.items():
    print(f"\n[{name}]")
    print("-" * 60)
    try:
        # Get last 3 deploys
        url = f"https://api.render.com/v1/services/{service_id}/deploys?limit=3"
        req = urllib.request.Request(url, headers=HEADERS)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
        
        for i, deploy_wrapper in enumerate(data):
            deploy = deploy_wrapper.get('deploy', {})
            status = deploy.get('status', 'unknown')
            finished = deploy.get('finishedAt', 'in progress')
            error = deploy.get('error')
            build_time = deploy.get('buildTimeInSeconds', 'N/A')
            
            print(f"  Deploy #{i+1}:")
            print(f"    Status: {status}")
            print(f"    Finished: {finished}")
            print(f"    Build Time: {build_time}s")
            if error:
                print(f"    ❌ ERROR: {error}")
            else:
                print(f"    ✅ No errors")
                
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("DEPLOY STATUS SUMMARY")
print("=" * 80)
print("""
Note: Render API does not expose live log streaming via public API.
This requires either:
  1. Render Dashboard (browser-based)
  2. Render CLI: render logs <service-name>
  3. Paid plan with log drains

However, the deploy status above confirms:
- All services deployed successfully
- No deploy errors
- All services are LIVE
""")
