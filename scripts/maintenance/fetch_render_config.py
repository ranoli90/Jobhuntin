import os

import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")


def fetch_render_env():
    if not RENDER_API_KEY:
        print("Error: RENDER_API_KEY not found in .env")
        return

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
    }

    # 1. List services to find the API/Worker service ID
    try:
        print("\nChecking services...")
        response = httpx.get("https://api.render.com/v1/services", headers=headers)
        response.raise_for_status()
        services = response.json()

        for svc in services:
            service = svc["service"]
            service_id = service["id"]
            name = service["name"]
            if name != "sorce-api":
                continue  # Only focus on api

            print(f"Checking service: {name} ({service_id})")

            # Check secret groups
            sg_resp = httpx.get(
                f"https://api.render.com/v1/services/{service_id}/secret-groups",
                headers=headers,
            )
            if sg_resp.status_code == 200:
                sgs = sg_resp.json()
                for sg_item in sgs:
                    sg = sg_item["secretGroup"]
                    print(f"Linked Secret Group: {sg['name']} ({sg['id']})")
                    # Get env vars for this secret group
                    sg_env_resp = httpx.get(
                        f"https://api.render.com/v1/secret-groups/{sg['id']}/env-vars",
                        headers=headers,
                    )
                    if sg_env_resp.status_code == 200:
                        sg_envs = sg_env_resp.json()
                        for item in sg_envs:
                            ev = item["envVar"]
                            print(f"  [SG] {ev['key']}: {ev['value'][:10]}...")

            # 2. Get env vars for this service
            env_resp = httpx.get(
                f"https://api.render.com/v1/services/{service_id}/env-vars",
                headers=headers,
                timeout=10,
            )
            env_resp.raise_for_status()
            env_vars = env_resp.json()

            print(f"--- Environment Variables for {name} ---")
            for item in env_vars:
                env_var = item["envVar"]
                key = env_var["key"]
                print(f"KEY: {key}")
            print("\n")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    fetch_render_env()
