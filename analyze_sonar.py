import json

# Load SonarCloud issues
with open('sonar-issues.json', 'r') as f:
    data = json.load(f)

print(f"📊 SonarCloud Analysis for sorce-monorepo")
print(f"=========================================")
print(f"Total Issues: {data['total']}")
print(f"Effort Total: {data['effortTotal']}")
print()

issues = data['issues']

# Analyze by severity
severity_counts = {}
for severity in ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO']:
    count = len([i for i in issues if i['severity'] == severity])
    severity_counts[severity] = count

print("🚨 Issues by Severity:")
for severity, count in severity_counts.items():
    print(f"  {severity}: {count}")

# Analyze by type
type_counts = {}
for issue_type in ['BUG', 'VULNERABILITY', 'CODE_SMELL']:
    count = len([i for i in issues if i['type'] == issue_type])
    type_counts[issue_type] = count

print()
print("📋 Issues by Type:")
for issue_type, count in type_counts.items():
    print(f"  {issue_type}: {count}")

# Top components with most issues
component_counts = {}
for issue in issues:
    component = issue['component'].split(':')[-1]  # Remove project prefix
    component_counts[component] = component_counts.get(component, 0) + 1

# Sort and get top 10
top_components = sorted(component_counts.items(), key=lambda x: x[1], reverse=True)[:10]

print()
print("🔥 Top 10 Components with Most Issues:")
for component, count in top_components:
    print(f"  {component}: {count}")

# Top rules
rule_counts = {}
for issue in issues:
    rule = issue['rule']
    rule_counts[rule] = rule_counts.get(rule, 0) + 1

# Sort and get top 10
top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]

print()
print("📏 Top 10 Rule Violations:")
for rule, count in top_rules:
    print(f"  {rule}: {count}")

# Blocker and Critical issues details
print()
print("🚨 BLOCKER and CRITICAL Issues:")
blocker_critical = [i for i in issues if i['severity'] in ['BLOCKER', 'CRITICAL']]
for issue in blocker_critical[:20]:  # Show first 20
    print(f"  {issue['severity']} - {issue['component'].split(':')[-1]}:{issue['line']} - {issue['message']}")

if len(blocker_critical) > 20:
    print(f"  ... and {len(blocker_critical) - 20} more")
