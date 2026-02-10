import sys
import json
import subprocess

def get_render_services(token):
    cmd = ["curl.exe", "-s", "-H", f"Authorization: Bearer {token}", "https://api.render.com/v1/services"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        return [{"id": s["service"]["id"], "name": s["service"]["name"]} for s in data]
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return []

if __name__ == "__main__":
    token = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    cmd = ["curl.exe", "-s", "-H", f"Authorization: Bearer {token}", "https://api.render.com/v1/services"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    with open("render_full.json", "w") as f:
        f.write(result.stdout)
    
    data = json.loads(result.stdout)
    services = [{"id": s["service"]["id"], "name": s["service"]["name"]} for s in data]
    for s in services:
        print(f"{s['name']}: {s['id']}")
