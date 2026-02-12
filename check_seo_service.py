import requests

RENDER_API_KEY = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}
SERVICE_ID = "srv-d66aadsr85hc73dastfg" # jobhuntin-seo-engine

def check_seo_env():
    print(f"Checking Env Vars for Service: {SERVICE_ID}")
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars?limit=50"
    
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print(f"Error fetching env vars: {resp.status_code} {resp.text}")
        return

    vars_list = resp.json()
    keys = [v['envVar']['key'] for v in vars_list]
    
    print("--- Environment Variables ---")
    for k in keys:
        print(f"- {k}")
        
    required = ["GOOGLE_SERVICE_ACCOUNT_KEY", "GOOGLE_SEARCH_CONSOLE_SITE", "NODE_ENV"]
    missing = [r for r in required if r not in keys]
    
    if missing:
        print(f"\n❌ Missing required vars: {missing}")
    else:
        print("\n✅ All required SEO env vars are present.")

if __name__ == "__main__":
    check_seo_env()
