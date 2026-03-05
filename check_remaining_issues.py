import json

data = json.load(open("sonar-issues.json"))
info_issues = [i for i in data["issues"] if i["severity"] == "INFO"]
print(f"INFO issues: {len(info_issues)}")

# Group by component
components = {}
for issue in info_issues:
    component = issue["component"].split(":")[-1]
    if component not in components:
        components[component] = []
    components[component].append(issue)

print("\nTop components with INFO issues:")
for component, issues in sorted(
    components.items(), key=lambda x: len(x[1]), reverse=True
)[:5]:
    print(f"  {component}: {len(issues)} issues")

print("\nSample INFO issues:")
for issue in info_issues[:5]:
    component = issue["component"].split(":")[-1]
    line = issue.get("line", "N/A")
    message = issue.get("message", "No message")
    rule = issue.get("rule", "No rule")
    print(f"  {component}:{line} - {message} ({rule})")

# Check for any other uncategorized issues
other_issues = [
    i
    for i in data["issues"]
    if i["severity"] not in ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]
]
print(f"\nOther issues: {len(other_issues)}")
for issue in other_issues[:5]:
    component = issue["component"].split(":")[-1]
    severity = issue.get("severity", "N/A")
    message = issue.get("message", "No message")
    print(f"  {component} - {message} ({severity})")
