import json

data = json.load(open('sonar-issues.json'))
redis_issues = [i for i in data['issues'] if i['rule'] == 'python:S5655']
print(f'Redis issues: {len(redis_issues)}')
for issue in redis_issues[:10]:
    print(f'  {issue["component"]}:{issue["line"]} - {issue["message"]}')
