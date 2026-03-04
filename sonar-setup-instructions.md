# SonarCloud Setup Instructions

## Required Actions

### 1. Create SonarCloud Token
1. Go to https://sonarcloud.io
2. Sign in with your GitHub account
3. Click your account menu (top right)
4. Select "My Account" > "Security"
5. Click "Generate" to create a new token
6. Give it a name like "sorce-monorepo-scanner"
7. **Copy the token immediately** - you cannot retrieve it later

### 2. Update Environment Variables
Replace the placeholder in `.env`:
```bash
SONAR_TOKEN=paste-your-token-here
```

### 3. Verify Project Setup
The project should already exist in SonarCloud:
- Organization: ranoli90
- Project Key: ranoli90_sorce
- Project Name: sorce-monorepo

### 4. Run the Scan
```bash
npm run sonar
```

## Current Configuration
✅ SonarCloud scanner installed (@sonar/scan@4.3.4)
✅ Project configuration ready (sonar-project.properties)
✅ Coverage reports generated (Python tests completed)
✅ Environment variables configured (needs token)

## Next Steps
1. Get the SonarCloud token from the website
2. Update the .env file
3. Run the full scan
4. Organize all findings systematically
