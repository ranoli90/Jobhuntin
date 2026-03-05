import json

data = json.load(open("sonar-issues.json"))
typescript_rules = [
    "typescript:S7764",
    "typescript:S7781",
    "typescript:S7773",
    "typescript:S6479",
]
ts_issues = [i for i in data["issues"] if i["rule"] in typescript_rules]

print(f"TypeScript rule violations: {len(ts_issues)}")
for rule in typescript_rules:
    rule_issues = [i for i in ts_issues if i["rule"] == rule]
    print(f"  {rule}: {len(rule_issues)} issues")

print("\nTop 10 TypeScript issues:")
for issue in ts_issues[:10]:
    component = issue["component"].split(":")[-1]
    line = issue.get("line", "N/A")
    message = issue.get("message", "No message")
    rule = issue.get("rule", "No rule")
    print(f"  {component}:{line} - {message} ({rule})")
