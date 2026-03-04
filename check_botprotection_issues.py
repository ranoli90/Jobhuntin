import json

data = json.load(open('sonar-issues.json'))
botprotection_issues = [i for i in data['issues'] if 'botProtection.ts' in i['component']]
print(f'botProtection.ts issues: {len(botprotection_issues)}')
for issue in botprotection_issues[:10]:
    line = issue.get('line', 'N/A')
    message = issue.get('message', 'No message')
    rule = issue.get('rule', 'No rule')
    print(f'  Line {line}: {message} ({rule})')
