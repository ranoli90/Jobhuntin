#!/usr/bin/env python3
"""
Quick Render Log Puller
Uses API key to pull logs immediately
"""

import json
from datetime import datetime, timedelta

import requests


def pull_render_logs():
    """Pull logs from jobhuntin-api service"""

    # Use the correct Render API key
    api_key = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"

    if api_key == "YOUR_RENDER_API_KEY_HERE":
        print("❌ Please set your Render API key in the script")
        print("Get it from: https://dashboard.render.com/u/settings")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # First, get services to find jobhuntin-api
    print("🔍 Finding jobhuntin-api service...")
    services_response = requests.get("https://api.render.com/v1/services", headers=headers)

    if services_response.status_code != 200:
        print(f"❌ Failed to get services: {services_response.status_code}")
        print(f"Response: {services_response.text}")
        return

    services = services_response.json()
    print(f"🔍 Found {len(services)} services")

    jobhuntin_service = None

    for service_data in services:
        service = service_data.get("service", {})
        if service.get("name") == "jobhuntin-api":
            jobhuntin_service = service
            break

    if not jobhuntin_service:
        print("❌ jobhuntin-api service not found")
        print("Available services:")
        for service_data in services:
            service = service_data.get("service", {})
            print(f"   - {service.get('name')} ({service.get('type')})")
        return

    service_id = jobhuntin_service.get("id")
    print(f"✅ Found jobhuntin-api (ID: {service_id})")
    print(f"   Status: {jobhuntin_service.get('status')}")

    # Pull logs from last 24 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)

    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)

    print("\n📥 Pulling logs from last 24 hours...")

    # Try different log endpoints for Docker services
    log_endpoints = [
        f"https://api.render.com/v1/services/{service_id}/logs",
        f"https://api.render.com/v1/services/{service_id}/instances/logs",
        f"https://api.render.com/v1/services/{service_id}/builds/logs"
    ]

    logs = None
    for endpoint in log_endpoints:
        print(f"🔍 Trying endpoint: {endpoint}")

        params = {
            "startTime": start_timestamp,
            "endTime": end_timestamp,
            "limit": 1000
        }

        logs_response = requests.get(endpoint, headers=headers, params=params)

        print(f"   Status: {logs_response.status_code}")

        if logs_response.status_code == 200:
            logs_data = logs_response.json()
            logs = logs_data.get("logs", [])
            print(f"✅ Found {len(logs)} logs")
            break
        else:
            print(f"   Response: {logs_response.text[:200]}...")

    # Try getting service details and deployment logs
    print("\n🔍 Getting service details...")
    service_details_url = f"https://api.render.com/v1/services/{service_id}"
    details_response = requests.get(service_details_url, headers=headers)

    if details_response.status_code == 200:
        details = details_response.json()
        print("✅ Service details retrieved")
        print(f"   Type: {details.get('type')}")
        print(f"   Status: {details.get('status')}")
        print(f"   URL: {details.get('url')}")

        # Try to get recent builds
        builds_url = f"https://api.render.com/v1/services/{service_id}/builds"
        builds_response = requests.get(builds_url, headers=headers)

        if builds_response.status_code == 200:
            builds = builds_response.json()
            print(f"\n🏗️  Found {len(builds)} builds")

            if builds:
                latest_build = builds[0]  # Get most recent build
                build_id = latest_build.get("id")
                print(f"   Latest build ID: {build_id}")
                print(f"   Build status: {latest_build.get('status')}")

                # Get build logs
                build_logs_url = f"https://api.render.com/v1/services/{service_id}/builds/{build_id}/logs"
                logs_response = requests.get(build_logs_url, headers=headers)

                if logs_response.status_code == 200:
                    logs_data = logs_response.json()
                    logs = logs_data.get("logs", [])
                    print(f"✅ Found {len(logs)} build logs")
                else:
                    print(f"❌ Failed to get build logs: {logs_response.status_code}")
                    print(f"Response: {logs_response.text[:200]}...")
                    return
            else:
                print("❌ No builds found")
                return
        else:
            print(f"❌ Failed to get builds: {builds_response.status_code}")
            return
    else:
        print(f"❌ Failed to get service details: {details_response.status_code}")
        return

    print(f"✅ Retrieved {len(logs)} log entries")

    # Save logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"jobhuntin_api_logs_{timestamp}.json"

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, default=str)

    print(f"📁 Logs saved to: {log_file}")

    # Analyze logs for errors
    print("\n🔍 Analyzing logs for issues...")

    error_count = 0
    recent_errors = []

    for log in logs[-20:]:  # Check last 20 logs
        message = log.get("message", "")
        timestamp = log.get("timestamp", "")

        if any(error in message for error in ["error", "Error", "ERROR", "failed", "Failed", "FAILED"]):
            error_count += 1
            recent_errors.append(f"{timestamp}: {message}")

    print(f"📊 Found {error_count} recent errors")

    if recent_errors:
        print("\n🚨 Recent Errors:")
        for error in recent_errors[-10:]:
            print(f"   {error}")

    # Show last 5 logs
    print("\n📋 Last 5 log entries:")
    print("=" * 60)
    for log in logs[-5:]:
        timestamp = log.get("timestamp", "")
        message = log.get("message", "")
        print(f"{timestamp}: {message}")

if __name__ == "__main__":
    pull_render_logs()
