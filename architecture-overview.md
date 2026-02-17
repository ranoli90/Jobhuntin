# Architecture Overview - Sorce/JobHuntin Platform

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                    │
│  │   Web App    │   │  Admin App   │   │  Mobile App  │                    │
│  │  (React/Vite)│   │(React/Vite)  │   │  (Expo/RN)   │                    │
│  │ jobhuntin.com│   │admin.jobhuntin│  │iOS/Android   │                    │
│  └──────────────┘   └──────────────┘   └──────────────┘                    │
│         │                  │                  │                             │
│         └──────────────────┼──────────────────┘                             │
│                            │                                                 │
│                     ┌──────▼──────┐                                          │
│                     │  CDN/SSL    │                                          │
│                     │  (Render)   │                                          │
│                     └──────┬──────┘                                          │
└────────────────────────────┼────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────────┐
│                       API LAYER                                               │
├────────────────────────────┼────────────────────────────────────────────────┤
│                     ┌──────▼──────┐                                          │
│                     │  API Server │                                          │
│                     │  (FastAPI)  │                                          │
│                     │ api.jobhuntin│                                         │
│                     └──────┬──────┘                                          │
│                            │                                                 │
│  ┌─────────────────────────┼─────────────────────────────────┐              │
│  │                    MIDDLEWARE STACK                        │              │
│  │  • CORS (web + mobile origins)                            │              │
│  │  • Request ID (distributed tracing)                       │              │
│  │  • Security Headers (CSP, HSTS, X-Frame-Options)          │              │
│  │  • Rate Limiting (tenant-aware, Redis-backed)             │              │
│  │  • CSRF Protection                                        │              │
│  │  • JWT Authentication (Supabase Auth)                     │              │
│  └───────────────────────────────────────────────────────────┘              │
│                            │                                                 │
│  ┌─────────────────────────┼─────────────────────────────────┐              │
│  │                      API ROUTES                            │              │
│  ├───────────────────────────────────────────────────────────┤              │
│  │  /ai/*                    - AI Suggestions & Matching     │              │
│  │  /auth/*                  - Authentication (magic link)   │              │
│  │  /billing/*               - Stripe billing & teams        │              │
│  │  /admin/*                 - Admin dashboard & analytics   │              │
│  │  /marketplace/*           - Blueprint marketplace         │              │
│  │  /developer/*             - API keys & webhooks           │              │
│  │  /agent/*                 - Application workflow          │              │
│  │  /sso/*                   - SAML SSO                      │              │
│  └───────────────────────────────────────────────────────────┘              │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────────┐
│                      WORKER LAYER                                             │
├────────────────────────────┼────────────────────────────────────────────────┤
│                     ┌──────▼──────┐                                          │
│                     │   Worker    │                                          │
│                     │  (Playwright)│                                         │
│                     │  Background │                                          │
│                     └──────┬──────┘                                          │
│                            │                                                 │
│  ┌─────────────────────────┼─────────────────────────────────┐              │
│  │                   WORKER CAPABILITIES                      │              │
│  │  • Job application automation (Playwright)                │              │
│  │  • Form filling with AI-generated answers                 │              │
│  │  • Resume tailoring on-demand                             │              │
│  │  • Batch job matching                                     │              │
│  │  • Email notifications (Resend)                           │              │
│  └───────────────────────────────────────────────────────────┘              │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────────┐
│                     DATA LAYER                                                │
├────────────────────────────┼────────────────────────────────────────────────┤
│                            │                                                 │
│  ┌─────────────────────────▼──────────────────────────┐                     │
│  │              PostgreSQL (Render)                    │                     │
│  │  ┌─────────────────────────────────────────────────┐│                     │
│  │  │  Core Tables                                     ││                     │
│  │  │  • users, profiles, tenants                      ││                     │
│  │  │  • jobs, applications, application_inputs        ││                     │
│  │  │  • events, answer_memory                         ││                     │
│  │  └─────────────────────────────────────────────────┘│                     │
│  │  ┌─────────────────────────────────────────────────┐│                     │
│  │  │  AI/Matching Tables                              ││                     │
│  │  │  • job_embeddings, profile_embeddings            ││                     │
│  │  │  • user_preferences, job_match_cache             ││                     │
│  │  └─────────────────────────────────────────────────┘│                     │
│  │  ┌─────────────────────────────────────────────────┐│                     │
│  │  │  Billing Tables                                  ││                     │
│  │  │  • stripe_customers, subscriptions               ││                     │
│  │  │  • team_invites, team_members                    ││                     │
│  │  └─────────────────────────────────────────────────┘│                     │
│  │  ┌─────────────────────────────────────────────────┐│                     │
│  │  │  Analytics Tables                                ││                     │
│  │  │  • analytics_events, audit_log                   ││                     │
│  │  │  • gdpr_audit_log                                ││                     │
│  │  └─────────────────────────────────────────────────┘│                     │
│  └─────────────────────────────────────────────────────┘                     │
│                            │                                                 │
│  ┌─────────────────────────▼──────────────────────────┐                     │
│  │              Redis (Optional)                       │                     │
│  │  • Rate limiting (sliding window)                   │                     │
│  │  • Session caching                                  │                     │
│  │  • Circuit breaker state                            │                     │
│  └─────────────────────────────────────────────────────┘                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Database Schema Overview

### Core Entities

```
users ─────────┬──────── profiles ──────── tenants
    │              │                           │
    │              └── profile_embeddings     │
    │                           │             │
    └── applications ───────────┼─────────────┘
           │                    │
           ├── application_inputs
           └── events
```

### Multi-Tenant Isolation

All tenant-scoped tables include `tenant_id` with RLS policies:

- `profiles.tenant_id` → user's organization
- `applications.tenant_id` → application's organization
- `job_embeddings.tenant_id` → embedding's organization
- `profile_embeddings.tenant_id` → embedding's organization

### Embedding Schema

```sql
job_embeddings
├── id (uuid, PK)
├── job_id (uuid, FK → jobs)
├── tenant_id (uuid, FK → tenants)
├── embedding (jsonb) -- Vector stored as JSON
├── text_hash (text) -- Content hash for cache invalidation
└── timestamps

profile_embeddings
├── id (uuid, PK)
├── user_id (uuid, FK → users)
├── tenant_id (uuid, FK → tenants)
├── embedding (jsonb)
├── text_hash (text)
└── timestamps
```

## API Rate Limiting

### Tier-Based Limits

| Tier | Requests/min | Requests/hour | Concurrent |
|------|-------------|---------------|------------|
| FREE | 10 | 100 | 2 |
| PRO | 60 | 1,000 | 10 |
| TEAM | 100 | 5,000 | 25 |
| ENTERPRISE | 500 | 25,000 | 100 |

### AI-Specific Limits

| Tier | AI Requests/min | AI Concurrent |
|------|----------------|---------------|
| FREE | 5 | 1 |
| PRO | 20 | 3 |
| TEAM | 50 | 10 |
| ENTERPRISE | 200 | 50 |

## AI Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI FEATURE PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Semantic Matching                                            │
│     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│     │ Profile     │    │ Job         │    │ Match       │       │
│     │ Embedding   │───▶│ Embedding   │───▶│ Score       │       │
│     └─────────────┘    └─────────────┘    └─────────────┘       │
│            │                  │                  │               │
│            ▼                  ▼                  ▼               │
│     [PII Stripped]    [Dealbreakers]    [Explanation]           │
│                                                                  │
│  2. Resume Tailoring                                              │
│     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│     │ Resume      │    │ LLM         │    │ Tailored    │       │
│     │ Upload      │───▶│ Processing  │───▶│ Resume      │       │
│     └─────────────┘    └─────────────┘    └─────────────┘       │
│                                                                  │
│  3. ATS Scoring                                                   │
│     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│     │ Resume      │    │ 23 Metrics  │    │ ATS         │       │
│     │ Text        │───▶│ Analysis    │───▶│ Score       │       │
│     └─────────────┘    └─────────────┘    └─────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY LAYERS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Transport Layer                                                 │
│  ├── HTTPS enforced (Render SSL)                                │
│  ├── HSTS header (max-age=31536000)                             │
│  └── Secure cookies                                             │
│                                                                  │
│  Application Layer                                               │
│  ├── JWT Authentication (Supabase Auth)                         │
│  ├── CSRF Protection (double-submit cookie)                     │
│  ├── Rate Limiting (tenant-aware, Redis-backed)                 │
│  └── Input Validation (prompt injection, PII detection)         │
│                                                                  │
│  Data Layer                                                      │
│  ├── Row-Level Security (PostgreSQL RLS)                        │
│  ├── Tenant Isolation (tenant_id on all tables)                 │
│  └── PII Masking (before LLM calls)                             │
│                                                                  │
│  Headers                                                         │
│  ├── Content-Security-Policy                                    │
│  ├── X-Frame-Options: DENY                                      │
│  ├── X-Content-Type-Options: nosniff                            │
│  ├── X-XSS-Protection: 1; mode=block                            │
│  └── Referrer-Policy: strict-origin-when-cross-origin          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Observability Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Metrics (StructuredMetrics)                                     │
│  ├── Request counts (total, success, error)                     │
│  ├── Latency percentiles (p50, p95, p99)                        │
│  ├── Error rates by category                                    │
│  └── Prometheus export format                                   │
│                                                                  │
│  Logging                                                         │
│  ├── Structured JSON (production)                               │
│  ├── Human-readable (development)                               │
│  ├── Correlation IDs (request_id, tenant_id, user_id)           │
│  └── PII sanitization                                           │
│                                                                  │
│  Alerting (AlertManager)                                         │
│  ├── high_error_rate (> 5% in 5min)                             │
│  ├── high_latency_p99 (> 1000ms)                                │
│  ├── database_connection_failure                                │
│  ├── circuit_breaker_trip                                       │
│  └── rate_limit_threshold (> 80% usage)                         │
│                                                                  │
│  Health Checks                                                   │
│  ├── /health - Basic liveness                                   │
│  └── /healthz - Deep health (DB, Redis, circuit breakers)       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RENDER SERVICES                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐│
│  │   Web Service   │   │   API Service   │   │ Worker Service  ││
│  │   (Static)      │   │   (FastAPI)     │   │   (Playwright)  ││
│  │   jobhuntin.com │   │ api.jobhuntin.com│   │   Background    ││
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘│
│           │                     │                     │          │
│           └─────────────────────┼─────────────────────┘          │
│                                 │                                │
│                    ┌────────────▼────────────┐                   │
│                    │   PostgreSQL Database   │                   │
│                    │   (Render Managed)      │                   │
│                    │   dpg-d66ck524d50c73... │                   │
│                    └─────────────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                  GITHUB ACTIONS WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Push to main                                                    │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐                        │
│  │  Lint   │──▶│  Test   │──▶│  Build  │                        │
│  │(ruff+ts)│   │(pytest) │   │(Docker) │                        │
│  └─────────┘   └─────────┘   └─────────┘                        │
│                                   │                              │
│                                   ▼                              │
│                           ┌───────────────┐                      │
│                           │    Deploy     │                      │
│                           │   (Staging)   │                      │
│                           └───────┬───────┘                      │
│                                   │                              │
│                                   ▼                              │
│                           ┌───────────────┐                      │
│                           │  E2E Tests    │                      │
│                           │  (Playwright) │                      │
│                           └───────┬───────┘                      │
│                                   │                              │
│                                   ▼                              │
│                           ┌───────────────┐                      │
│                           │  Manual Gate  │                      │
│                           │  (Approval)   │                      │
│                           └───────┬───────┘                      │
│                                   │                              │
│                                   ▼                              │
│                           ┌───────────────┐                      │
│                           │    Deploy     │                      │
│                           │ (Production)  │                      │
│                           └───────────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

*Document Version: 1.1*
*Last Updated: February 2026*
