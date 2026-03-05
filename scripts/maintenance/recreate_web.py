import os

import requests
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

WEB_SERVICE_ID = "srv-d63sipvgi27c739ni59g"


def delete_and_recreate():
    # 1. Get current details
    print(f"Fetching details for {WEB_SERVICE_ID}...")
    resp = requests.get(
        f"https://api.render.com/v1/services/{WEB_SERVICE_ID}",
        headers=headers,
        timeout=10,
    )

    if resp.status_code != 200:
        print(f"Error fetching service: {resp.text}")
        # Try to find by name if ID is wrong
        services_resp = requests.get(
            "https://api.render.com/v1/services", headers=headers, timeout=10
        )
        if services_resp.status_code == 200:
            for item in services_resp.json():
                svc = item["service"]
                if svc["name"] == "sorce-web":
                    print(f"Found sorce-web by name: {svc['id']}")
                    current_svc = svc
                    break
            else:
                print("Could not find sorce-web at all.")
                return
        else:
            return
    else:
        current_svc = resp.json()

    repo_url = current_svc["repo"]
    owner_id = current_svc["ownerId"]
    target_id = current_svc["id"]

    # 2. Delete the service
    print(f"Deleting service {target_id}...")
    del_resp = requests.delete(
        f"https://api.render.com/v1/services/{target_id}", headers=headers, timeout=10
    )
    if del_resp.status_code not in {200, 204}:
        print(f"Error deleting service: {del_resp.text}")
    else:
        print("Successfully deleted sorce-web.")

    # 3. Create new Static Site service with CORRECT nested structure
    new_svc_data = {
        "type": "static_site",
        "name": "sorce-web",
        "ownerId": owner_id,
        "repo": repo_url,
        "branch": "main",
        "rootDir": "web",
        "serviceDetails": {
            "buildCommand": "npm install && npm run build",
            "publishPath": "dist",
        },
        "envVars": [
            {"key": "VITE_API_URL", "value": "https://sorce-api.onrender.com"},
            {
                "key": "VITE_SUPABASE_URL",
                "value": "https://zntqsqyhqsqyhqsqyhqsqy.supabase.co",
            },
            {
                "key": "VITE_SUPABASE_ANON_KEY",
                "value": "sbp_d2258f6603d6bc4b5fb5fd4c081207d2b5f7734e",
            },
        ],
    }

    print("Creating new sorce-web static site with proper settings...")
    create_resp = requests.post(
        "https://api.render.com/v1/services",
        headers=headers,
        json=new_svc_data,
        timeout=10,
    )

    if create_resp.status_code in {200, 201}:
        new_svc = create_resp.json()
        # For static site creation response, it might be the svc object directly or wrapped
        svc_info = new_svc.get("service", new_svc)
        print(f"✅ Successfully recreated sorce-web! New ID: {svc_info['id']}")
        print(f"Dashboard URL: {svc_info['dashboardUrl']}")
    else:
        print(f"❌ Error creating service: {create_resp.text}")


if __name__ == "__main__":
    delete_and_recreate()
