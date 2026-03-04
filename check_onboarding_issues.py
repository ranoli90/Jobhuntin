import json

data = json.load(open('sonar-issues.json'))
onboarding_issues = [i for i in data['issues'] if 'Onboarding.tsx' in i['component']]
print(f'Onboarding.tsx issues: {len(onboarding_issues)}')
for issue in onboarding_issues[:10]:
    print(f'  Line {issue["line"]}: {issue["message"]} ({issue["rule"]})')
