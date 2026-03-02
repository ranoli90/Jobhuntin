import json

data = None
try:
    with open("projects.json", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    pass

if isinstance(data, list) and len(data) > 0:
    proj = data[0]
    region = proj.get("region")
    ref = proj.get("id")
    print(f"Region: {region}")
    print(f"Ref: {ref}")
else:
    print("Error: No projects found or invalid JSON")
