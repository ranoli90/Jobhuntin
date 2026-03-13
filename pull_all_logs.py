#!/usr/bin/env python3
"""
Quick script to pull logs from all Render services
"""
import requests
import json
import os
import sys
from datetime import datetime, timedelta

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# API key from services.json
API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
BASE_URL = "https://api.render.com/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Service IDs from services.json
SERVICES = {
    "jobhuntin-api": "srv-d6p4l03h46gs73ftvuj0",
    "jobhuntin-seo-engine": "srv-d6p5n5vkijhs73fikui0",
    "jobhuntin-job-sync": "srv-d6pd9gh5pdvs73ara9og",
    "jobhuntin-job-queue": "srv-d6pd9k24d50c73a8gvp0",
    "jobhuntin-follow-up-reminders": "srv-d6pd9np4tr6s73aks17g",
    "sorce-auto-apply-agent": "srv-d6pdaeh5pdvs73arak1g"
}

def get_service_logs(service_id, limit=500):
    """Get logs for a specific service"""
    url = f"{BASE_URL}/services/{service_id}/logs"
    params = {"limit": limit}
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[ERROR] Failed to get logs for {service_id}: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return None

def analyze_logs(logs, service_name):
    """Analyze logs for errors"""
    if not logs:
        print(f"\n{'='*60}")
        print(f"SERVICE: {service_name}")
        print(f"   No logs found")
        return
    
    errors = []
    warnings = []
    
    for log in logs:
        message = log.get("message", "").lower()
        timestamp = log.get("timestamp", "")[:19]  # Just the date/time part
        
        if "error" in message or "exception" in message or "failed" in message or "traceback" in message:
            errors.append((timestamp, log.get("message", "")))
        elif "warning" in message or "warn" in message:
            warnings.append((timestamp, log.get("message", "")))
    
    print(f"\n{'='*60}")
    print(f"SERVICE: {service_name}")
    print(f"   Total logs: {len(logs)}")
    print(f"   Errors: {len(errors)}")
    print(f"   Warnings: {len(warnings)}")
    
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for i, (ts, msg) in enumerate(errors[:10]):  # Show first 10 errors
            print(f"   [{ts}] {msg[:200]}")
            if i >= 9:
                print(f"   ... and {len(errors) - 10} more errors")
                break
    
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for i, (ts, msg) in enumerate(warnings[:5]):  # Show first 5 warnings
            print(f"   [{ts}] {msg[:150]}")
            if i >= 4:
                print(f"   ... and {len(warnings) - 5} more warnings")
                break

def main():
    print("Pulling logs from all Render services...")
    print(f"   Time range: Last 24 hours")
    print()
    
    for service_name, service_id in SERVICES.items():
        print(f"Fetching logs for {service_name}...")
        logs_data = get_service_logs(service_id)
        
        if logs_data and "logs" in logs_data:
            logs = logs_data.get("logs", [])
            analyze_logs(logs, service_name)
        else:
            analyze_logs(None, service_name)
    
    print(f"\n{'='*60}")
    print("Done!")

if __name__ == "__main__":
    main()
