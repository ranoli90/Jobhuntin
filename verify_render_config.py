import requests
import os
import sys
import json
import traceback

RENDER_API_KEY = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}

OLD_DB_STRINGS = [
    "zglovpfwyobbbaaocawz",
    "supabase.co",
    "postgres.zglovpfwyobbbaaocawz",
]

NEW_DB_INTERNAL = "postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a/jobhuntin"

def check_render_services():
    print("--- Checking Render Services ---")
    results = []
    url = "https://api.render.com/v1/services?limit=50"
    try:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"Error fetching services: {resp.status_code} {resp.text}")
            return results

        services = resp.json()
        print(f"Found {len(services)} services.")

        for svc in services:
            svc_id = svc['service']['id']
            name = svc['service']['name']
            
            # Fetch env vars
            env_url = f"https://api.render.com/v1/services/{svc_id}/env-vars?limit=50"
            env_resp = requests.get(env_url, headers=HEADERS)
            status = "unknown"
            current_val = None
            
            if env_resp.status_code == 200:
                env_vars = env_resp.json()
                db_url_var = next((item for item in env_vars if item['envVar']['key'] == 'DATABASE_URL'), None)
                
                if db_url_var:
                    val = db_url_var['envVar']['value']
                    current_val = val
                    if NEW_DB_INTERNAL in val:
                        status = "ok"
                    elif "dpg-d66ck524d50c73bas62g-a" in val:
                         status = "ok_partial"
                    else:
                        status = "mismatch"
                else:
                    status = "missing"
            
            results.append({
                "id": svc_id,
                "name": name,
                "status": status,
                "current_db_url": current_val
            })

    except Exception as e:
        traceback.print_exc()
        print(f"Exception checking render: {e}")
        
    return results

def scan_codebase():
    print("\n--- Scanning Codebase for Old DB Strings ---")
    root_dir = os.getcwd()
    found_issues = []

    for root, dirs, files in os.walk(root_dir):
        if ".git" in dirs: 
            dirs.remove(".git")
        if "node_modules" in dirs:
            dirs.remove("node_modules")
        if ".venv" in dirs:
            dirs.remove(".venv")
            
        for name in files:
            if name.endswith(('.pyc', '.exe', '.dll', '.so', '.dylib', '.png', '.jpg', '.json')):
                continue
            if name == "verify_render_config.py" or name == "render_audit.log" or name == "render_audit_results.json":
                continue
                
            path = os.path.join(root, name)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for s in OLD_DB_STRINGS:
                        if s in content:
                            rel_path = os.path.relpath(path, root_dir)
                            found_issues.append((rel_path, s))
            except Exception as e:
                pass
                
    return found_issues

if __name__ == "__main__":
    services = check_render_services()
    code_issues = scan_codebase()
    
    report = {
        "services": services,
        "code_issues": code_issues
    }
    
    with open("render_audit_results.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print("Report saved to render_audit_results.json")
