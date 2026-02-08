import os
import httpx
import json
import time
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")

def manage_render():
    if not RENDER_API_KEY:
        print("Error: RENDER_API_KEY not found in .env")
        return

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }

    try:
        # 1. Get all services
        print("Fetching services...")
        response = httpx.get("https://api.render.com/v1/services", headers=headers)
        response.raise_for_status()
        services = response.json()
        
        api_service = None
        web_service = None
        
        for svc in services:
            service = svc['service']
            if service['name'] == "sorce-api":
                api_service = service
            elif service['name'] == "sorce-web":
                web_service = service

        # 2. Check API service
        if api_service:
            print(f"Found backend service: {api_service['name']} ({api_service['id']})")
            # Trigger deploy for backend to apply latest main push
            print(f"Triggering deploy for {api_service['name']}...")
            deploy_resp = httpx.post(f"https://api.render.com/v1/services/{api_service['id']}/deploys", headers=headers, json={})
            if deploy_resp.status_code in {200, 201, 202}:
                print("Backend deploy triggered successfully (Status: 202 Accepted).")
            else:
                print(f"Failed to trigger backend deploy: {deploy_resp.status_code} - {deploy_resp.text}")
        else:
            print("Backend service 'sorce-api' not found.")

        # 3. Check Web service
        if web_service:
            print(f"Found frontend service: {web_service['name']} ({web_service['id']})")
            
            # Ensure VITE_API_URL is set in web_service env vars
            env_resp = httpx.get(f"https://api.render.com/v1/services/{web_service['id']}/env-vars", headers=headers)
            env_resp.raise_for_status()
            env_vars = env_resp.json()
            
            has_api_url = False
            for item in env_vars:
                if item['envVar']['key'] == "VITE_API_URL":
                    has_api_url = True
                    print(f"VITE_API_URL is already set to: {item['envVar']['value']}")
                    break
            
            if not has_api_url and api_service:
                api_url = "https://sorce-api.onrender.com"
                print(f"VITE_API_URL missing. Setting it to {api_url}...")
                patch_data = [{"key": "VITE_API_URL", "value": api_url}]
                patch_resp = httpx.put(f"https://api.render.com/v1/services/{web_service['id']}/env-vars", 
                                      headers=headers, json=patch_data)
                if patch_resp.status_code in {200, 201, 204}:
                    print("VITE_API_URL set successfully.")
                else:
                    print(f"Failed to set VITE_API_URL: {patch_resp.status_code} - {patch_resp.text}")
            
            # Trigger deploy for frontend
            print(f"Triggering deploy for {web_service['name']}...")
            deploy_resp = httpx.post(f"https://api.render.com/v1/services/{web_service['id']}/deploys", headers=headers, json={})
            if deploy_resp.status_code in {200, 201, 202}:
                print("Frontend deploy triggered successfully (Status: 202 Accepted).")
            else:
                print(f"Failed to trigger frontend deploy: {deploy_resp.status_code} - {deploy_resp.text}")
        else:
            print("Frontend service 'sorce-web' not found. You may need to create it manually via Render dashboard pointing to the web/ directory.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    manage_render()
