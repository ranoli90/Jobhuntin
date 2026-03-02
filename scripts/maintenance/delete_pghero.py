import os

import requests
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_TOKEN")
PGHERO_SERVICE_ID = "srv-d66k2k5um26s73fvgrlg"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
}

print(f"Attempting to delete PgHero service: {PGHERO_SERVICE_ID}...")

try:
    response = requests.delete(
        f"https://api.render.com/v1/services/{PGHERO_SERVICE_ID}",
        headers=headers,
        timeout=10
    )

    if response.status_code == 204:
        print("✅ Successfully sent delete request for PgHero service.")
    elif response.status_code == 404:
        print("⚠️  Service not found. It may have been already deleted.")
    else:
        print(f"❌ Error deleting service: {response.status_code} - {response.text}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
