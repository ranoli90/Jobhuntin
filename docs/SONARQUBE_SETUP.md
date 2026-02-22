# SonarQube / SonarCloud Setup

SonarQube is configured for code quality analysis across the monorepo (TypeScript, JavaScript, Python).

## Quick Start (SonarCloud - Recommended)

1. **Create a SonarCloud account** at [sonarcloud.io](https://sonarcloud.io)

2. **Create or import your project** at [sonarcloud.io/projects/create](https://sonarcloud.io/projects/create)
   - Choose "Analyze new project"
   - Connect your GitHub/GitLab/Bitbucket
   - Select this repository
   - Note your **Organization Key** and **Project Key**

3. **Generate an authentication token** at [sonarcloud.io/account/security](https://sonarcloud.io/account/security)
   - Create a new token (e.g. "sorce-monorepo-scan")
   - Copy the token (you won't see it again)

4. **Configure your environment** — add to `.env`:
   ```bash
   SONAR_TOKEN=your-token-from-step-3
   SONAR_ORGANIZATION=your-org-key
   SONAR_PROJECT_KEY=your-project-key
   ```

5. **Update `sonar-project.properties`** — uncomment and set:
   ```properties
   sonar.organization=your-org-key
   sonar.projectKey=your-project-key
   ```
   Or pass via CLI: `npm run sonar -- -Dsonar.organization=... -Dsonar.token=...`

6. **Run the scan**:
   ```bash
   npm run sonar
   ```

## Running a Scan

```bash
# Full scan (requires SONAR_TOKEN in .env or -Dsonar.token=...)
npm run sonar

# Dry run (outputs config to sonar-report.json without uploading)
npm run sonar:dry
```

## Local SonarQube Server (Optional)

If you prefer a self-hosted SonarQube instance instead of SonarCloud:

1. **Start SonarQube with Docker**:
   ```bash
   docker compose -f docker/sonarqube.yml up -d
   ```
   Access at http://localhost:9000 (default login: admin/admin)

2. **Create a project** in the SonarQube UI and generate a token

3. **Configure** `sonar-project.properties` or `.env`:
   ```bash
   SONAR_HOST_URL=http://localhost:9000
   SONAR_TOKEN=your-local-sonarqube-token
   ```

## Configuration

- **Sources**: `apps/web`, `apps/web-admin`, `apps/extension`, `mobile`, `backend`, `packages/backend`, `packages/shared`
- **Excluded**: `node_modules`, `dist`, `build`, `__pycache__`, `.venv`, test files
- **Languages**: TypeScript, JavaScript, Python

## Troubleshooting

- **"sonar.organization" required**: You're using SonarCloud — set `sonar.organization` in `sonar-project.properties` or via `-Dsonar.organization=...`
- **"Invalid authentication"**: Regenerate your token at sonarcloud.io/account/security
- **Coverage not showing**: Run tests with coverage first (`npm run test -- --coverage`) and ensure `lcov.info` exists
