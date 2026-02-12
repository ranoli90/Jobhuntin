import requests
import sys

RENDER_API_KEY = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json", "Content-Type": "application/json"}

SERVICE_ID = "srv-d66aadsr85hc73dastfg" # jobhuntin-seo-engine
NEW_DB_URL = "postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a/jobhuntin"

def update_render_service():
    print(f"Updating Render Service: {SERVICE_ID}")
    
    # Update DATABASE_URL
    target_key = "DATABASE_URL"
    url_update = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/{target_key}"
    payload = {"value": NEW_DB_URL}
    
    print(f"Updating {target_key}...")
    resp_update = requests.put(url_update, headers=HEADERS, json=payload, timeout=30)
    
    if resp_update.status_code == 200:
        print(f"✅ Successfully updated {target_key}")
    else:
        print(f"❌ Failed to update {target_key}: {resp_update.status_code} {resp_update.text}")
        return False

    # Check for Supabase vars and warn/try to delete (if API supported DELETE easily, but let's just Log them for now or set to empty)
    # Render API DELETE /services/{serviceId}/env-vars/{envVarKey}
    
    # Let's list and delete Supabase vars
    url_vars = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars?limit=50"
    resp = requests.get(url_vars, headers=HEADERS, timeout=10)
    if resp.status_code == 200:
        current_vars = resp.json()
        for item in current_vars:
            key = item['envVar']['key']
            if "SUPABASE" in key:
                print(f"Found legacy var: {key}. Deleting...")
                url_del = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/{key}"
                requests.delete(url_del, headers=HEADERS, timeout=10)
                print(f"Deleted {key}")

    return True

if __name__ == "__main__":
    success = update_render_service()

