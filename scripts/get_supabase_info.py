import json
import urllib.request

PROJECT_REF = "zglovpfwyobbbaaocawz"
# User provided sb_secret_... which might be a management token
TOKEN = "sb_secret_3RfgVxidbpUJ8xRpmIygtA_7SRKmbVk"

def get_project_info():
    url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
            print(json.dumps(data, indent=2))
            return data
    except Exception as e:
        print(f"Error fetching project info: {e}")
        return None

if __name__ == "__main__":
    get_project_info()
