# JobHuntin Architecture

## Overview

JobHuntin is a monorepo that powers AI-driven job application automation. The system consists of consumer-facing web apps, a FastAPI backend, Playwright automation workers, and an AI-powered SEO engine.

## Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   apps/web      │     │   apps/api      │     │  apps/worker    │
│   (Vite/React)  │────▶│   (FastAPI)     │◀────│  (Playwright)   │
│   Port 5173     │     │   Port 8000     │     │  FormAgent      │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │PostgreSQL│ │  Redis   │ │   LLM    │
              │  (Render)│ │ (Render) │ │(OpenRouter)│
              └──────────┘ └──────────┘ └──────────┘
```

## Key Directories

| Path | Purpose |
|------|---------|
| `apps/web` | Consumer web app (Vite/React), SEO scripts |
| `apps/web-admin` | Operator dashboard |
| `apps/api` | FastAPI v1 (tenants, applications, webhooks) |
| `apps/worker` | Playwright FormAgent, job application automation |
| `packages/backend` | Domain models, repositories, LLM orchestration |
| `packages/shared` | Config, logging, Redis, telemetry |
| `packages/blueprints` | Job board adapters (auto-loaded by worker) |
| `infra/` | Database schema, migrations, Render manifests |

## Data Flow

1. **User** → Web app: upload resume, set preferences
2. **API** → Stores tenant, parses resume, creates application queue
3. **Worker** → Polls queue, drives Playwright through job forms
4. **Worker** → Emits metrics, updates application status
5. **SEO Engine** → Generates content, submits to Google Indexing API

## Tech Stack

- **Frontend**: React, Vite, Tailwind CSS
- **Backend**: FastAPI, asyncpg, Redis
- **Automation**: Playwright
- **AI**: OpenRouter (LLM), embeddings for matching
- **Infra**: Render (PostgreSQL, Redis, Docker services)
