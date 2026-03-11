# JobHuntin Documentation

Documentation index for developers, operators, and investors.

## For Developers

| Document | Description |
|----------|-------------|
| [Development Guide](DEVELOPMENT.md) | Local setup, environment, running services, testing |
| [Architecture](ARCHITECTURE.md) | System design, components, data flow |
| [Render Setup](RENDER_SETUP.md) | Deployment, environment variables, verification |
| [Production Auth & CSRF](PRODUCTION_AUTH_CSRF.md) | Auth/CSRF architecture for Render, scaling, Bearer vs cookie |
| [API Versioning](API_VERSIONING.md) | Version negotiation, deprecation headers |
| [Migration Guides](MIGRATION_GUIDES.md) | Database migrations |
| [Job Application Flow](JOB_APPLICATION_FLOW_AND_LOGIN.md) | Application flow, login, magic links |
| [JobSpy Implementation](JOBSPY_ADVANCED_IMPLEMENTATION_PLAN.md) | JobSpy proxy strategy, bot avoidance, scaling |
| [Audit Tools](AUDIT_TOOLS.md) | Lint, security, quality tooling |

## For Operators

| Document | Description |
|----------|-------------|
| [Render Setup](RENDER_SETUP.md) | Production deployment on Render |
| [Operational Runbooks](OPERATIONAL_RUNBOOKS.md) | Runbooks for incidents |
| [SECURITY.md](../SECURITY.md) | Dependency vulnerabilities, remediation |

## For Investors

| Document | Description |
|----------|-------------|
| [Investor Overview](INVESTORS.md) | Metrics endpoints, data room, key metrics |
| [investor-metrics/](../investor-metrics/README.md) | Metrics API (JSON/CSV export) |
| [investor-data-room/](../investor-data-room/README.md) | Full diligence package |

## Reference

| Document | Description |
|----------|-------------|
| [Self-Heal Fixes](SELF_HEAL_FIXES.md) | Recent auth/CSRF fixes for local dev |

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for workflow, quality gates, and code standards.
