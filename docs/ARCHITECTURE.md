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
| `apps/web-admin` | Operator dashboard (Port 5174) |
| `apps/api` | FastAPI backend (tenants, applications, webhooks) |
| `apps/worker` | Playwright FormAgent, job application automation |
| `packages/backend` | Domain models, repositories, LLM orchestration |
| `shared` | Config, logging, Redis, telemetry, pagination, error handling |
| `packages/blueprints` | Job board adapters (auto-loaded by worker) |
| `infra/` | Database schema, migrations, Render manifests |

## Core Shared Modules

The `shared/` directory contains foundational modules used throughout the API:

| Module | Purpose |
|--------|---------|
| [`shared/error_responses.py`](shared/error_responses.py) | Standardized error response format with custom exceptions |
| [`shared/pagination.py`](shared/pagination.py) | Cursor-based pagination for API endpoints |
| [`shared/path_security.py`](shared/path_security.py) | Path traversal attack prevention |
| [`shared/query_cache.py`](shared/query_cache.py) | Redis-based query result caching |
| [`shared/config.py`](shared/config.py) | Application configuration management |
| [`shared/middleware.py`](shared/middleware.py) | Request/response middleware |

### Dependency Injection

The API uses centralized dependency injection via [`apps/api/deps.py`](apps/api/deps.py):

```python
from api.deps import (
    get_pool,           # Database pool (asyncpg.Pool)
    get_read_pool,      # Read replica pool or fallback to primary
    get_current_user_id, # Extract user ID from JWT
    get_tenant_context,  # Resolve TenantContext from JWT
    get_settings,        # Application settings
    get_redis,           # Redis client
)
```

## Data Flow

1. **User** → Web app: upload resume, set preferences
2. **API** → Stores tenant, parses resume, creates application queue
3. **Worker** → Polls queue, drives Playwright through job forms
4. **Worker** → Emits metrics, updates application status
5. **SEO Engine** → Generates content, submits to Google Indexing API

## Error Handling

The API uses standardized error responses via [`shared/error_responses.py`](shared/error_responses.py):

```python
from shared.error_responses import (
    ErrorCodes,
    APIError,
    ValidationError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)

# Example response format:
# {
#     "error": {
#         "code": "VALIDATION_ERROR",
#         "message": "Invalid input data",
#         "details": [{"field": "email", "message": "Invalid email format"}]
#     },
#     "request_id": "abc-123",
#     "timestamp": "2024-01-15T10:30:00Z"
# }
```

## Pagination

API endpoints use cursor-based pagination via [`shared/pagination.py`](shared/pagination.py):

```python
from shared.pagination import (
    PaginationParams,
    PaginatedResult,
    paginate_query,
    encode_cursor,
    decode_cursor,
)

# Default page size: 20, Max: 100
# Supports forward (first/after) and backward (last/before) pagination
```

## Query Caching

Frequently-accessed data is cached via [`shared/query_cache.py`](shared/query_cache.py):

```python
from shared.query_cache import (
    cached,              # Decorator for async functions
    get_cached,          # Manual cache get
    set_cached,          # Manual cache set
    invalidate_cache,    # Cache invalidation
    # Pre-configured TTLs
    DEFAULT_TTL,         # 5 minutes
    PROFILE_TTL,         # 15 minutes
    JOB_LISTINGS_TTL,    # 2 minutes
    TENANT_CONFIG_TTL,  # 1 hour
)
```

See [docs/QUERY_CACHING.md](docs/QUERY_CACHING.md) for detailed usage.

## Path Security

File operations use path traversal protection via [`shared/path_security.py`](shared/path_security.py):

```python
from shared.path_security import (
    validate_path,           # Validate path is within base directory
    validate_bucket_name,   # Validate storage bucket names
    validate_storage_path,  # Validate bucket + path combination
    is_path_safe,            # Boolean check without exception
    PathTraversalError,     # Exception for traversal attempts
)
```

## Tech Stack

- **Frontend**: React, Vite, Tailwind CSS
- **Backend**: FastAPI, asyncpg, Redis
- **Automation**: Playwright
- **AI**: OpenRouter (LLM), embeddings for matching
- **Infra**: Render (PostgreSQL, Redis, Docker services)
