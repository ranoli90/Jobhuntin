import json

data = json.load(open("sonar-issues.json"))
python_major_rules = ["python:S8415", "python:S930", "python:S5876", "python:S1128"]
python_issues = [
    i
    for i in data["issues"]
    if i["rule"] in python_major_rules and i["severity"] == "MAJOR"
]

print(f"Major Python issues: {len(python_issues)}")
for rule in python_major_rules:
    rule_issues = [i for i in python_issues if i["rule"] == rule]
    print(f"  {rule}: {len(rule_issues)} issues")

print("\nTop 10 Major Python issues:")
for issue in python_issues[:10]:
    component = issue["component"].split(":")[-1]
    line = issue.get("line", "N/A")
    message = issue.get("message", "No message")
    rule = issue.get("rule", "No rule")
    print(f"  {component}:{line} - {message} ({rule})")
