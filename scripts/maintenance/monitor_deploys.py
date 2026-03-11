import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")

if not RENDER_API_KEY:
    print("Error: RENDER_API_KEY not found in .env")
    sys.exit(1)

headers = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}


def get_services():
    url = "https://api.render.com/v1/services"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching services: {e}")
        sys.exit(1)


def get_latest_deploy(service_id):
    url = f"https://api.render.com/v1/services/{service_id}/deploys"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        deploys = response.json()
        if deploys:
            return deploys[0].get("deploy", deploys[0])
    except requests.RequestException:
        pass
    return None


def monitor_deploys():
    print("Monitoring Render deployments...")
    services_data = get_services()
    if isinstance(services_data, dict) and "services" in services_data:
        services_data = services_data["services"]
    if not isinstance(services_data, list):
        services_data = []

    target_services = {}
    for item in services_data:
        svc = item.get("service", item)
        if not isinstance(svc, dict):
            continue
        if svc["name"] == "sorce-api":
            target_services[svc["name"]] = svc["id"]
            print(f"Found {svc['name']}: {svc['id']}")
        elif svc["name"] == "sorce-web":
            # Check if it's the new one
            if svc["id"] == "srv-d63spbogjchc739akan0":
                target_services[svc["name"]] = svc["id"]
                print(f"Found {svc['name']} (NEW): {svc['id']}")

    if not target_services:
        print("Could not find target services (sorce-api, sorce-web)")
        return

    completed = {name: False for name in target_services}

    while not all(completed.values()):
        for name, sid in target_services.items():
            if completed[name]:
                continue

            deploy = get_latest_deploy(sid)
            if not deploy:
                print(f"No deploys found for {name}")
                continue

            status = deploy["status"]
            print(f"Service {name} (Deploy {deploy['id']}) status: {status}")

            if status == "live":
                print(f"✅ Service {name} is LIVE!")
                completed[name] = True
            elif status in {"build_failed", "update_failed", "canceled"}:
                print(f"❌ Service {name} deploy FAILED with status: {status}")
                # We don't exit here to see if the other one succeeds or fails too
                completed[name] = True
            else:
                # Still deploying (pre_deploy_in_progress, build_in_progress, etc.)
                pass

        if not all(completed.values()):
            print("Waiting 30 seconds...")
            time.sleep(30)


if __name__ == "__main__":
    monitor_deploys()
