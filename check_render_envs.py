import json
import subprocess


def get_env_vars(token, service_id):
    cmd = ["curl.exe", "-s", "-H", f"Authorization: Bearer {token}", f"https://api.render.com/v1/services/{service_id}/env-vars"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout)
    except:
        return []

if __name__ == "__main__":
    token = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    services = {
        "jobhuntin-web": "srv-d63spbogjchc739boblag",
        "jobhuntin-api": "srv-d63l79hr0fns73boblag"
    }

    results = {}
    for name, sid in services.items():
        results[name] = get_env_vars(token, sid)

    print(json.dumps(results, indent=2))
