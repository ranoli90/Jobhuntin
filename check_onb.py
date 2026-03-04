import json
with open('sonar-issues.json') as f:
    data = json.load(f)
issues = [i for i in data.get('issues', []) if 'Onboarding.tsx' in i.get('component', '')]
for iss in issues:
    print(f"L{iss.get('textRange', {}).get('startLine')}: {iss.get('message')} ({iss.get('rule')})")
