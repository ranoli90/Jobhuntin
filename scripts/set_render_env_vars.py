#!/usr/bin/env python3
"""Set environment variables on a Render service."""

import json
import urllib.error
import urllib.request

RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"

# Environment variables to set
env_vars = [
    (
    "DATABASE_URL",
    "postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a:5432/jobhuntin"),
    ("REDIS_URL", "redis://red-d6761bp5pdvs73e7b3mg:6379"),
    ("ENV", "prod"),
    ("NODE_ENV", "production"),
    ("PORT", "10000"),
    ("APP_BASE_URL", "https://jobhuntin.com"),
    ("API_PUBLIC_URL", "https://jobhuntin-api.onrender.com"),
    ("JWT_SECRET", "58433bcd5debda9951fbeba101e67d59f4042d07a46c83cdff242af7b13b1cee"),
    ("CSRF_SECRET", "e17772ebd77bf749e46928f60a7378b90ad6dec9acf6563016cf1c11969650b7"),
    ("WEBHOOK_SIGNING_SECRET", "36528db9daeaedd73a12a869a929d1a52e71ea44dabf4247eda103c2bb4d520d"),
]

BASE_URL = "https://api.render.com/v1"

def api_put_env(path: str, token: str, value: str) -> int:
    """PUT env var to Render API. Returns status_code."""
    url = f"https://api.render.com/v1{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps({"value": value}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.read().decode()}")
        return e.code


# Set each environment variable individually
for key, value in env_vars:
    # Render API: PUT /services/{id}/env-vars/{key}
    status = api_put_env(
        f"/services/{SERVICE_ID}/env-vars/{key}",
        RENDER_API_KEY,
        value,
    )
    print(f"Setting {key}: {status}")

print("\nDone setting environment variables!")
