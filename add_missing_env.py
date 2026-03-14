#!/usr/bin/env python3
"""Add missing DATABASE_URL and LLM_API_KEY to Render service"""

import json
import urllib.error
import urllib.request

RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
API_SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"

# Read LLM_API_KEY from .env file
llm_api_key = None
try:
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("LLM_API_KEY="):
                llm_api_key = line.split("=", 1)[1].strip()
                break
except:
    pass

if not llm_api_key:
    print("WARNING: Could not find LLM_API_KEY in .env file")
    llm_api_key = input("Enter LLM_API_KEY: ").strip()

# DATABASE_URL with sslmode=require
db_url = "postgresql://jobhuntin_db_ghef_user:W0106M1RIEmzZTBI3A0vS0jq2NkCkP1x@dpg-d6p53ghr0fns73e4da20-a:5432/jobhuntin_db_ghef?sslmode=require"

def set_env_var(key, value):
    """Set an environment variable via POST"""
    url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars"
    data = {"key": key, "value": value}

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"[OK] {key}: {resp.status}")
            return True
    except urllib.error.HTTPError as e:
        print(f"[ERROR] {key}: {e.code} - {e.read().decode()[:200]}")
        return False

# Add DATABASE_URL
print("Adding DATABASE_URL...")
set_env_var("DATABASE_URL", db_url)

# Add LLM_API_KEY
print("Adding LLM_API_KEY...")
set_env_var("LLM_API_KEY", llm_api_key)

print("\nDone! Triggering deploy...")
