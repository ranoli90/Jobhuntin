import json
import urllib.request

RENDER_API_KEY = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

print("Fetching services...")
try:
    req = urllib.request.Request("https://api.render.com/v1/services", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        services = json.loads(response.read().decode())
        for svc in services:
             service = svc['service']
             name = service['name']
             sid = service['id']
             url = service.get('serviceDetails', {}).get('url', 'N/A')
             print(f"{name} : {sid} : {url}")
except Exception as e:
    print(f"Error: {e}")
