import json

try:
    with open("projects.json", "r", encoding="utf-8") as f:
        data = json.load(f)
except:
    pass # Assume utf-8 worked or failed loudly, but json.load likely failed if file empty

if isinstance(data, list) and len(data) > 0:
    proj = data[0]
    region = proj.get("region")
    ref = proj.get("id")
    print(f"Region: {region}")
    print(f"Ref: {ref}")
else:
    print("Error: No projects found or invalid JSON")
