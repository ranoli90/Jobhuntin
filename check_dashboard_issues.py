import json

data = json.load(open('sonar-issues.json'))
dashboard_issues = [i for i in data['issues'] if 'Dashboard.tsx' in i['component']]
print(f'Dashboard.tsx issues: {len(dashboard_issues)}')
for issue in dashboard_issues[:10]:
    line = issue.get('line', 'N/A')
    message = issue.get('message', 'No message')
    rule = issue.get('rule', 'No rule')
    print(f'  Line {line}: {message} ({rule})')
