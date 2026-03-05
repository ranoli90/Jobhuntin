import json

data = json.load(open("sonar-issues.json"))
production_issues = [i for i in data["issues"] if "production.py" in i["component"]]
print(f"production.py issues: {len(production_issues)}")
for issue in production_issues[:10]:
    line = issue.get("line", "N/A")
    message = issue.get("message", "No message")
    rule = issue.get("rule", "No rule")
    print(f"  Line {line}: {message} ({rule})")
