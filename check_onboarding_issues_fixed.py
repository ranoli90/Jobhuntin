import json

data = json.load(open('sonar-issues.json'))
onboarding_issues = [i for i in data['issues'] if 'Onboarding.tsx' in i['component']]
print(f'Onboarding.tsx issues: {len(onboarding_issues)}')
for issue in onboarding_issues[:10]:
    line = issue.get('line', 'N/A')
    message = issue.get('message', 'No message')
    rule = issue.get('rule', 'No rule')
    print(f'  Line {line}: {message} ({rule})')
