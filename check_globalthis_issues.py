import json

data = json.load(open('sonar-issues.json'))
globalthis_issues = [i for i in data['issues'] if i['rule'] == 'typescript:S7764']
print(f'globalThis issues: {len(globalthis_issues)}')

# Group by component
components = {}
for issue in globalthis_issues:
    component = issue['component'].split(':')[-1]
    if component not in components:
        components[component] = []
    components[component].append(issue)

print(f'\nTop components with globalThis issues:')
for component, issues in sorted(components.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
    print(f'  {component}: {len(issues)} issues')
