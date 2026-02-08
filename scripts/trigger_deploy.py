import os

import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY", "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa")

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json"
}

def trigger_deploy():
    """Trigger a new deploy for the API service"""
    try:
        # Get services
        response = httpx.get("https://api.render.com/v1/services", headers=headers)
        response.raise_for_status()
        services = response.json()

        api_service = None
        for svc in services:
            service = svc.get('service', {})
            if service.get('name') == "sorce-api":
                api_service = service
                break

        if not api_service:
            print("API service not found")
            return

        # Trigger deploy
        deploy_url = f"https://api.render.com/v1/services/{api_service['id']}/deploys"
        response = httpx.post(deploy_url, headers=headers, json={})

        if response.status_code in [200, 201, 202]:
            print("Deploy triggered successfully")
        else:
            print(f"Failed to trigger deploy: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    trigger_deploy()
