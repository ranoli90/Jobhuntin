import requests
import os
import sys
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")

if not RENDER_API_KEY:
    print("Error: RENDER_API_KEY not found in .env")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

def get_latest_deploy_logs(service_id, deploy_id):
    # Note: Render API doesn't have a direct "get logs for deploy X" endpoint that returns a string easily
    # It usually requires a websocket or a streaming endpoint. 
    # However, we can try to fetch the service events which often contain the failure reason.
    url = f"https://api.render.com/v1/services/{service_id}/events"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        events = response.json()
        print(f"--- Recent Events for {service_id} ---")
        for item in events[:10]:
            event = item['event']
            print(f"[{event['timestamp']}] {event['type']}: {event.get('data', {}).get('reason', 'No reason provided')}")
    else:
        print(f"Failed to fetch events: {response.status_code}")

if __name__ == "__main__":
    WEB_SERVICE_ID = "srv-d63sipvgi27c739ni59g"
    DEPLOY_ID = "dep-d63siq7gi27c739ni5gg"
    get_latest_deploy_logs(WEB_SERVICE_ID, DEPLOY_ID)
