#!/usr/bin/env python3
"""Check API environment variables."""

import urllib.request
import json
import os
import sys

API_KEY = os.environ.get("RENDER_API_KEY")
SERVICE_ID = os.environ.get("RENDER_SERVICE_ID", "srv-d6p4l03h46gs73ftvuj0")  # default ok for fallback
if not API_KEY:
    print("ERROR: RENDER_API_KEY environment variable not set")
    sys.exit(1)

url = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})

with urllib.request.urlopen(req, timeout=30) as response:
    data = json.loads(response.read().decode())

# Required env vars for production
required = [
    "DATABASE_URL",
    "LLM_API_KEY", 
    "APP_BASE_URL",
    "API_PUBLIC_URL",
    "CSRF_SECRET",
    "JWT_SECRET",
    "REDIS_URL",
    "WEBHOOK_SIGNING_SECRET",
]

# Get all keys
keys = [e["envVar"]["key"] for e in data]

print("=== API Environment Variables ===")
print(f"Total: {len(keys)}")
print()

print("Required variables:")
for var in required:
    status = "[OK]" if var in keys else "[MISSING]"
    print(f"  {status} {var}")

print()
print("All variables:")
for e in data:
    key = e["envVar"]["key"]
    value = e["envVar"]["value"]
    if key in ["PORT", "NODE_ENV", "ENV", "PYTHONPATH"]:
        print(f"  {key}: {value}")
    else:
        print(f"  {key}: {'*' * 10}")
