#!/usr/bin/env python3
"""
Render Service Debugger
Fetches logs and checks/fixes environment variables for all services
"""

import json
import sys
import urllib.error
import urllib.request

# Render API Configuration
RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"

# Service IDs from services.json
SERVICES = {
    "api": "srv-d6p4l03h46gs73ftvuj0",      # jobhuntin-api
    "web": "srv-d6p5m0fafjfc739ij050",       # jobhuntin-web
    "seo": "srv-d6p5n5vkijhs73fikui0",       # jobhuntin-seo-engine
}

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

def get_env_vars(service_id):
    """Get environment variables for a service"""
    return api_get(f"/services/{service_id}/env-vars")

def get_service_logs(service_id, limit=100):
    """Get recent logs for a service"""
    return api_get(f"/services/{service_id}/logs?limit={limit}")

def get_services():
    """Get all services"""
    return api_get("/services?limit=20")

def main():
    print("=" * 70)
    print("RENDER SERVICE DEBUGGER")
    print("=" * 70)

    # Get all services first
    print("\n[1] Fetching all services...")
    services = get_services()
    if not services:
        print("Failed to fetch services. Check API key.")
        return 1

    # Normalize services list
    svc_list = []
    for item in services:
        s = item.get("service", item) if isinstance(item, dict) else item
        if isinstance(s, dict) and s.get("id"):
            svc_list.append(s)

    print(f"\nFound {len(svc_list)} services:")
    for s in svc_list:
        status = s.get("suspended", "active")
        url = s.get("serviceDetails", {}).get("url", "N/A")
        print(f"  - {s.get('name')} ({s.get('type')}) [{status}]")
        if url and url != "N/A":
            print(f"    URL: {url}")

    # Check API service environment
    print("\n" + "=" * 70)
    print("[2] Checking API Service Environment Variables...")
    print("=" * 70)

    api_service_id = SERVICES["api"]
    env_vars = get_env_vars(api_service_id)

    if env_vars:
        # Extract keys
        keys_present = set()
        db_url_value = None
        for item in env_vars:
            ev = item.get("envVar", {})
            key = ev.get("key")
            if key:
                keys_present.add(key)
                if key == "DATABASE_URL":
                    db_url_value = ev.get("value", "")

        print(f"\nCurrent environment variables ({len(keys_present)}):")
        for key in sorted(keys_present):
            # Mask secrets
            secret_keys = ["DATABASE_URL", "REDIS_URL", "JWT_SECRET", "CSRF_SECRET",
                          "LLM_API_KEY", "RESEND_API_KEY", "WEBHOOK_SIGNING_SECRET",
                          "SUPABASE_SERVICE_KEY", "STRIPE_SECRET_KEY"]
            if key in secret_keys:
                print(f"  - {key}: [SECRET]")
            else:
                print(f"  - {key}")

        # Check DATABASE_URL for sslmode
        print("\n[DATABASE_URL Analysis]")
        if db_url_value:
            print(f"  Current value: {db_url_value}")
            if "sslmode" in db_url_value:
                print("  SSL mode: Found in URL")
            else:
                print("  SSL mode: MISSING! This is likely causing the SSL error!")
        else:
            print("  Could not retrieve DATABASE_URL value")

        # Check for required vars
        required = ["DATABASE_URL", "REDIS_URL", "APP_BASE_URL", "ENV"]
        print("\nRequired vars check:")
        for key in required:
            if key in keys_present:
                print(f"  [OK] {key}")
            else:
                print(f"  [MISSING] {key}!")
    else:
        print("Could not fetch environment variables")

    # Fetch API logs
    print("\n" + "=" * 70)
    print("[3] Fetching API Service Logs...")
    print("=" * 70)

    logs = get_service_logs(api_service_id, limit=50)
    if logs:
        # Handle response format
        logs_list = logs.get("logs", []) if isinstance(logs, dict) else logs
        print(f"\nRecent {len(logs_list)} log entries:")
        for log in logs_list[-20:]:
            timestamp = log.get("timestamp", "")
            message = log.get("message", "")
            # Show last part of message
            if len(message) > 100:
                message = "..." + message[-100:]
            print(f"  [{timestamp}] {message}")
    else:
        print("Could not fetch logs")

    # Fetch SEO logs
    print("\n" + "=" * 70)
    print("[4] Fetching SEO Worker Logs...")
    print("=" * 70)

    seo_service_id = SERVICES["seo"]
    seo_logs = get_service_logs(seo_service_id, limit=50)
    if seo_logs:
        logs_list = seo_logs.get("logs", []) if isinstance(seo_logs, dict) else seo_logs
        print(f"\nRecent {len(logs_list)} log entries:")
        for log in logs_list[-20:]:
            timestamp = log.get("timestamp", "")
            message = log.get("message", "")
            if len(message) > 100:
                message = "..." + message[-100:]
            print(f"  [{timestamp}] {message}")
    else:
        print("Could not fetch SEO logs")

    print("\n" + "=" * 70)
    print("LOG FETCH COMPLETE")
    print("=" * 70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
