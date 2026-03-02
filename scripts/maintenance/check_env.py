import json
import os
import urllib.request

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
if not RENDER_API_KEY:
    raise SystemExit("RENDER_API_KEY not set. Export it: export RENDER_API_KEY=your-key")
SERVICES = {
    "sorce-web": "srv-d63spbogjchc739akan0",
    "sorce-api": "srv-d63l79hr0fns73boblag"
}

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

def get_env_vars(service_id, service_name):
    print(f"\nChecking {service_name} ({service_id})...")
    try:
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected - service_id from SERVICES dict
        req = urllib.request.Request(f"https://api.render.com/v1/services/{service_id}/env-vars", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            env_vars = json.loads(response.read().decode())
            found = False
            for item in env_vars:
                ev = item['envVar']
                if service_name == "sorce-web" and ev['key'] == "VITE_API_URL":
                    print(f"  VITE_API_URL: {ev['value']}")
                    found = True
                if service_name == "sorce-api" and ev['key'] == "APP_BASE_URL":
                    print(f"  APP_BASE_URL: {ev['value']}")
                    found = True
            if not found:
                print("  Target variable not found.")
    except Exception as e:
        print(f"Error: {e}")

for name, sid in SERVICES.items():
    get_env_vars(sid, name)
