import json

data = json.load(open('sonar-issues.json'))
parseint_issues = [i for i in data['issues'] if i['rule'] == 'typescript:S7773']
print(f'parseInt issues: {len(parseint_issues)}')

for issue in parseint_issues[:10]:
    component = issue['component'].split(':')[-1]
    line = issue.get('line', 'N/A')
    message = issue.get('message', 'No message')
    print(f'  {component}:{line} - {message}')
