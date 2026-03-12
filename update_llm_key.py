#!/usr/bin/env python3
"""Update LLM_API_KEY on Render"""

import json
import urllib.request

RENDER_API_KEY = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
API_SERVICE_ID = "srv-d6p4l03h46gs73ftvuj0"

# The OpenRouter key the user provided
llm_api_key = "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"

# Update LLM_API_KEY via PUT
url = f"https://api.render.com/v1/services/{API_SERVICE_ID}/env-vars/LLM_API_KEY"
data = {"value": llm_api_key}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode(),
    headers={
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json"
    },
    method="PUT"
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"LLM_API_KEY updated: {resp.status}")
except urllib.error.HTTPError as e:
    print(f"Error: {e.code}")
    print(f"Body: {e.read().decode()[:200]}")

print("\nDone!")
