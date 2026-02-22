import urllib.error
import urllib.request

# nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected - PROJECT_REF constant
PROJECT_REF = "zglovpfwyobbbaaocawz"
URL = f"https://{PROJECT_REF}.supabase.co/rest/v1/"

try:
    print(f"Checking {URL}...")
    req = urllib.request.Request(URL, headers={"apikey": "sb_publishable_Mr5fIMoahb4_Jrkdp3D33Q_oA-5MXV2"})
    with urllib.request.urlopen(req) as resp:
        print(f"Status: {resp.getcode()}")
        print("Project exists and is reachable via REST API.")
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    print("Project exists (HTTP Error implies host resolution success).")
except urllib.error.URLError as e:
    print(f"Failed to resolve host: {e.reason}")
    print("Project Reference might be invalid.")
except Exception as e:
    print(f"Error: {e}")
