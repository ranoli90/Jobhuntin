import json
import os
import urllib.request

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
if not RENDER_API_KEY:
    raise SystemExit(
        "RENDER_API_KEY not set. Export it: export RENDER_API_KEY=your-key"
    )

headers = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}

print("Fetching services...")
try:
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected - static URL
    req = urllib.request.Request("https://api.render.com/v1/services", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        services = json.loads(response.read().decode())
        for svc in services:
            service = svc["service"]
            name = service["name"]
            sid = service["id"]
            url = service.get("serviceDetails", {}).get("url", "N/A")
            print(f"{name} : {sid} : {url}")
except Exception as e:
    print(f"Error: {e}")
