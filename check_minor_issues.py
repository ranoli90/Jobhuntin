import json

data = json.load(open("sonar-issues.json"))
minor_issues = [i for i in data["issues"] if i["severity"] == "MINOR"]
print(f"MINOR issues: {len(minor_issues)}")

# Group by component
components = {}
for issue in minor_issues:
    component = issue["component"].split(":")[-1]
    if component not in components:
        components[component] = []
    components[component].append(issue)

print("\nTop components with MINOR issues:")
for component, issues in sorted(
    components.items(), key=lambda x: len(x[1]), reverse=True
)[:5]:
    print(f"  {component}: {len(issues)} issues")

print("\nSample MINOR issues:")
for issue in minor_issues[:5]:
    component = issue["component"].split(":")[-1]
    line = issue.get("line", "N/A")
    message = issue.get("message", "No message")
    rule = issue.get("rule", "No rule")
    print(f"  {component}:{line} - {message} ({rule})")
