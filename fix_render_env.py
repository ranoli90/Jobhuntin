#!/usr/bin/env python3
"""
Fix Render environment variables
Specifically fixes DATABASE_URL to include sslmode=require
"""

import os
import sys
import json
import urllib.request
import urllib.error

# Render API Configuration
RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"

# Service IDs
API_SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"  # jobhuntin-api
SEO_SERVICE_ID = "srv-d6p5n5vkijhs73fikui0"  # jobhuntin-seo-engine

def api_get(path):
    """Make GET request to Render API"""
    url = f"https://api.render.com/v1{path}"
    req = urllib.request.Request(
        url, 
        headers={"Authorization": f"Bearer {RENDER_API_KEY}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        try:
            error_body = json.loads(e.read().decode())
            print(f"  Error: {json.dumps(error_body, indent=2)[:500]}")
        except:
            print(f"  Error body: {e.read().decode()[:500]}")
        return None

def api_put(path, data):
    """Make PUT request to Render API"""
    url = f"https://api.render.com/v1{path}"
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode(),
        headers={
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Content-Type": "application/json"
        },
        method="PUT"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        try:
            error_body = json.loads(e.read().decode())
            print(f"  Error: {json.dumps(error_body, indent=2)[:500]}")
        except:
            print(f"  Error body: {e.read().decode()[:500]}")
        return e.code, None

def get_env_vars(service_id):
    """Get environment variables for a service"""
    return api_get(f"/services/{service_id}/env-vars")

def main():
    print("=" * 70)
    print("RENDER ENVIRONMENT FIXER")
    print("=" * 70)
    
    # Get current environment variables
    print("\n[1] Fetching current environment variables...")
    env_vars = get_env_vars(API_SERVICE_ID)
    
    if not env_vars:
        print("Failed to fetch environment variables.")
        return 1
    
    # Find DATABASE_URL and its ID
    db_url_value = None
    db_url_id = None
    for item in env_vars:
        ev = item.get("envVar", {})
        key = ev.get("key")
        if key == "DATABASE_URL":
            db_url_value = ev.get("value", "")
            db_url_id = ev.get("id")
            break
    
    if not db_url_value:
        print("DATABASE_URL not found!")
        return 1
    
    print(f"\nCurrent DATABASE_URL:")
    print(f"  {db_url_value}")
    
    # Check if sslmode is already present
    if "sslmode" in db_url_value:
        print("\n[OK] DATABASE_URL already has sslmode parameter!")
        # Check if it's set to require
        if "sslmode=require" in db_url_value:
            print("[OK] sslmode=require is already set!")
            return 0
        else:
            print(f"[WARN] sslmode is present but not set to 'require'")
    
    # Add sslmode=require
    if "?" in db_url_value:
        # URL already has query params
        new_db_url = db_url_value + "&sslmode=require"
    else:
        # No query params yet
        new_db_url = db_url_value + "?sslmode=require"
    
    print(f"\nNew DATABASE_URL:")
    print(f"  {new_db_url}")
    
    # Update the DATABASE_URL
    print(f"\n[2] Updating DATABASE_URL on API service...")
    status, response = api_put(
        f"/services/{API_SERVICE_ID}/env-vars/{db_url_id}",
        {"value": new_db_url}
    )
    
    if status in (200, 201, 204):
        print("[OK] DATABASE_URL updated successfully!")
    else:
        print(f"[ERROR] Failed to update DATABASE_URL: HTTP {status}")
        return 1
    
    print("\n" + "=" * 70)
    print("ENVIRONMENT FIX COMPLETE")
    print("=" * 70)
    print("\nNOTE: You may need to redeploy the service for changes to take effect.")
    print("The API service should automatically pick up the new DATABASE_URL.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
