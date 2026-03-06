import json

import requests


def list_deploys(service_id, api_token):
    print(f"Listing deploys for {service_id}...")
    url = f"https://api.render.com/v1/services/{service_id}/deploys"
    headers = {"Authorization": f"Bearer {api_token}", "Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    api_token = "rnd_V3u4rM4GNZcTQXSWUzNjv375AVdY"
    service_id = "srv-d66aadsr85hc73dastfg"
    deploys = list_deploys(service_id, api_token)
    if isinstance(deploys, list):
        print(f"Found {len(deploys)} deploys.")
        for d in deploys[:5]:
            dep = d["deploy"]
            print(
                f"ID: {dep['id']}, Status: {dep['status']}, Created: {dep['createdAt']}"
            )
    else:
        print(json.dumps(deploys, indent=2))
