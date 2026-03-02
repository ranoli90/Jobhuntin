"""Check Render env vars. Requires RENDER_API_KEY. Use scripts/render_api_verify.py instead."""
import json
import os
import subprocess


def get_env_vars(token, service_id):
    cmd = [
        "curl",
        "-s",
        "-H",
        f"Authorization: Bearer {token}",
        f"https://api.render.com/v1/services/{service_id}/env-vars",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout)
    except Exception:
        return []


if __name__ == "__main__":
    token = os.environ.get("RENDER_API_KEY") or os.environ.get("RENDER_API_TOKEN")
    if not token:
        print("Set RENDER_API_KEY or RENDER_API_TOKEN")
        exit(1)
    services = {
        "jobhuntin-web": "srv-d63spbogjchc739akan0",
        "jobhuntin-api": "srv-d63l79hr0fns73boblag",
    }

    results = {}
    for name, sid in services.items():
        results[name] = get_env_vars(token, sid)

    print(json.dumps(results, indent=2))
