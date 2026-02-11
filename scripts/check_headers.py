import urllib.request

PROJECT_REF = "zglovpfwyobbbaaocawz"
URL = f"https://{PROJECT_REF}.supabase.co/rest/v1/"
# Try both keys
KEYS = [
    "sb_publishable_Mr5fIMoahb4_Jrkdp3D33Q_oA-5MXV2",
    "sb_secret_3RfgVxidbpUJ8xRpmIygtA_7SRKmbVk"
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
