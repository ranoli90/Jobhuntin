# JobHuntin

AI-powered job application automation. Upload your resume once — JobHuntin matches, tailors, and auto-applies to hundreds of jobs daily.

## For Developers

- **[Development Guide](docs/DEVELOPMENT.md)** — Local setup, environment, running services
- **[Architecture](docs/ARCHITECTURE.md)** — System design, components, data flow
- **[Documentation Index](docs/INDEX.md)** — Full doc map

### Quick Start

```bash
git clone <repo-url> && cd jobhuntin
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && npm install
cp .env.example .env   # Configure DATABASE_URL, JWT_SECRET, CSRF_SECRET, etc.
docker compose up db -d
PYTHONPATH=apps:packages:. uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
cd apps/web && npx vite --host 0.0.0.0 --port 5173
```

### Key Commands

| Command | Purpose |
|---------|---------|
| `make dev-backend` | Run FastAPI backend |
| `make dev-web` | Run web app |
| `make test-backend` | Run Python tests |
| `cd apps/web && npm run build` | Build web app |

## For Investors

- **[Investor Overview](docs/INVESTORS.md)** — Metrics API, data room endpoints
- **[investor-metrics/](investor-metrics/README.md)** — Core metrics export
- **[investor-data-room/](investor-data-room/README.md)** — Full diligence package

## Project Structure

```
├── apps/
│   ├── api/          FastAPI backend
│   ├── web/          Vite/React consumer app
│   ├── web-admin/    Operator dashboard
│   ├── extension/    Chrome extension
│   └── worker/       Playwright automation (FormAgent)
├── packages/
│   ├── backend/      Domain, repositories, LLM
│   └── blueprints/   Job board adapters
├── shared/           Config, logging, telemetry
├── infra/            Database schema, migrations
├── docs/             Documentation
└── scripts/          Maintenance, migrations, load tests
```

## Deployment

- **Render** — Production (PostgreSQL, Redis, API, worker, web)
- **Setup** — See [docs/RENDER_SETUP.md](docs/RENDER_SETUP.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow, quality gates, and standards.

## Security

See [SECURITY.md](SECURITY.md) for dependency advisories and remediation.

---

Proprietary. All rights reserved.
