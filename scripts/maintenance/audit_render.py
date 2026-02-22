import json
import urllib.request

RENDER_API_KEY = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"

def audit_render():
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }

    try:
        print("Fetching services...")
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
        req = urllib.request.Request("https://api.render.com/v1/services", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            services = json.loads(response.read().decode())

        with open("render_audit.log", "w", encoding="utf-8") as f:
            for svc in services:
                service = svc['service']
                service_id = service['id']
                name = service['name']
                service_details = service.get('serviceDetails', {})
                url = service_details.get('url', 'N/A')

                msg = f"\nService: {name} ({service_id})\nURL: {url}\n"
                print(msg)
                f.write(msg)

                # Get env vars
                try:
                    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected - service_id from API
                    req_env = urllib.request.Request(f"https://api.render.com/v1/services/{service_id}/env-vars", headers=headers)
                    with urllib.request.urlopen(req_env, timeout=30) as env_resp:
                        env_vars = json.loads(env_resp.read().decode())
                        f.write("Environment Variables:\n")
                        for item in env_vars:
                            env_var = item['envVar']
                            key = env_var['key']
                            value = env_var['value']
                            if any(s in key.upper() for s in ['KEY', 'SECRET', 'PASSWORD', 'TOKEN']):
                                masked = f"{value[:3]}...{value[-3:]}" if len(value) > 6 else "***"
                                f.write(f"  {key}: {masked}\n")
                            else:
                                f.write(f"  {key}: {value}\n")
                except Exception as e:
                     f.write(f"  Could not fetch env vars: {e}\n")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    audit_render()
