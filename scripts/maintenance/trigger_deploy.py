"""Trigger deploy to sync env vars from render.yaml"""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
SERVICE_ID = "srv-d63l79hr0fns73boblag"  # sorce-api

def trigger_deploy():
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Trigger deploy from latest commit
    resp = httpx.post(
        f"https://api.render.com/v1/services/{SERVICE_ID}/deploys",
        headers=headers,
        json={"clearCache": True},
        timeout=10
    )

    print(f"Deploy trigger status: {resp.status_code}")
    if resp.status_code in (200, 201):
        data = resp.json()
        print(f"Deploy ID: {data.get('deploy', {}).get('id', 'N/A')}")
        return True
    else:
        print(f"Error: {resp.text[:500]}")
        return False

def get_service_details():
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
    }

    resp = httpx.get(
        f"https://api.render.com/v1/services/{SERVICE_ID}",
        headers=headers,
        timeout=10
    )

    if resp.status_code == 200:
        data = resp.json()
        svc = data.get('service', {})
        print(f"Service: {svc.get('name')}")
        print(f"Status: {svc.get('serviceDetails', {}).get('suspenders', 'unknown')}")
        print(f"AutoDeploy: {svc.get('autoDeploy')}")
        return svc
    return None

if __name__ == "__main__":
    print("Checking service details...")
    get_service_details()

    print("\n\nTriggering deploy to sync env vars from render.yaml...")
    if trigger_deploy():
        print("\nDeploy triggered successfully!")
        print("Render will sync env vars from render.yaml during deployment.")
        print("\nMonitor at: https://dashboard.render.com/web/sorce-api")
    else:
        print("\nFailed to trigger deploy via API.")
        print("\nAlternative: Go to https://dashboard.render.com/web/sorce-api")
        print("Click 'Manual Deploy' -> 'Deploy latest commit'")
