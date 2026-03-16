#!/usr/bin/env python3
"""Check deploy status for all Render services."""

import urllib.request
import json
import os
import sys

API_KEY = os.environ.get("RENDER_API_KEY")
if not API_KEY:
    print("ERROR: RENDER_API_KEY environment variable not set")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {API_KEY}"}

SERVICES = {
    "jobhuntin-job-sync": os.environ.get("RENDER_SERVICE_JOB_SYNC", "srv-d6pd9gh5pdvs73ara9og"),
    "jobhuntin-job-queue": os.environ.get("RENDER_SERVICE_JOB_QUEUE", "srv-d6pd9k24d50c73a8gvp0"),
    "jobhuntin-follow-up-reminders": os.environ.get("RENDER_SERVICE_FOLLOW_UP", "srv-d6pd9np4tr6s73aks17g"),
    "sorce-auto-apply-agent": os.environ.get("RENDER_SERVICE_AUTO_APPLY", "srv-d6pdaeh5pdvs73arak1g"),
    "jobhuntin-api": os.environ.get("RENDER_SERVICE_API", "srv-d6p4l03h46gs73ftvuj0"),
    "jobhuntin-seo-engine": os.environ.get("RENDER_SERVICE_SEO", "srv-d6p5n5vkijhs73fikui0"),
}

def check_deploy_status(name, service_id):
    url = f"https://api.render.com/v1/services/{service_id}/deploys?limit=1"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())
        if data:
            deploy = data[0]["deploy"]
            return deploy["status"], deploy.get("finishedAt")
    return "unknown", None

def main():
    print("=" * 60)
    print("Render Services Deploy Status")
    print("=" * 60)
    
    all_live = True
    for name, service_id in SERVICES.items():
        status, finished_at = check_deploy_status(name, service_id)
        icon = "[OK]" if status == "live" else "[..]" if status in ["build_in_progress", "update_in_progress"] else "[!!]"
        print(f"{icon} {name}: {status}")
        if status != "live":
            all_live = False
    
    print("=" * 60)
    if all_live:
        print("[OK] All services are live!")
    else:
        print("[..] Some services are still deploying...")
    
    return 0 if all_live else 1

if __name__ == "__main__":
    exit(main())
