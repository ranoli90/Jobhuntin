# nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
import os
import urllib.request

from dotenv import load_dotenv

load_dotenv()

PROJECT_REF = "zglovpfwyobbbaaocawz"
URL = f"https://{PROJECT_REF}.supabase.co/rest/v1/"
# Try both keys
KEYS = [
    os.environ.get("SUPABASE_ANON_KEY"),
    os.environ.get("SUPABASE_SERVICE_KEY")
]

for key in KEYS:
    print(f"Testing key: {key[:15]}...")
    req = urllib.request.Request(URL, headers={"apikey": key, "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Status: {resp.getcode()}")
            print("Headers:")
            for k, v in resp.getheaders():
                print(f"  {k}: {v}")
    except Exception as e:
        print(f"Failed: {e}")
