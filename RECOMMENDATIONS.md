# Comprehensive Recommendations & Improvements List

## Overview
This document lists ALL recommendations for the Quickly/Sorce platform, categorized by priority and domain.

---

## 1. 🔴 CRITICAL - Must Fix Before Production Launch

### 1.1 Database & Infrastructure
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 1 | Supabase references in code | Remove/replace `upload_to_supabase_storage`, `download_from_supabase_storage` with Render-compatible storage (S3, Cloudflare R2, or Render disks) | ✅ FIXED |
| 2 | Supabase JWT validation | Verify JWT validation works with Render PostgreSQL (currently assumes Supabase Auth) | ✅ FIXED |
| 3 | Database migrations not applied | Run all 26 migrations on live Render PostgreSQL database | ✅ FIXED |
| 4 | Redis not configured | Set up Redis instance for distributed rate limiting (currently in-memory fallback) | ✅ FIXED |
| 5 | Environment variables on Render | Populate all secrets in Render dashboard (LLM_API_KEY, STRIPE keys, etc.) | ✅ FIXED |

### 1.2 Security
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 6 | CSRF secret placeholder | Generate real CSRF_SECRET with `secrets.token_hex(32)` | ✅ FIXED |
| 7 | Webhook signing secret | Replace `dev-placeholder-webhook-signing` with real secret | ✅ FIXED |
| 8 | JWT secret missing | Ensure SUPABASE_JWT_SECRET is set for token validation | ✅ FIXED |
| 9 | Hardcoded test credentials | Remove any test/demo credentials from codebase | ✅ FIXED |
| 10 | Rate limiting without Redis | In-memory rate limiting loses state on restart - set up Redis | ✅ FIXED |

### 1.3 Deployment
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 11 | Render API keys in workflow | Add RENDER_API_TOKEN, RENDER_STAGING_API_ID, RENDER_PROD_API_ID to GitHub secrets | ✅ FIXED |
| 12 | Health check endpoints | Verify /healthz returns 200 on live deployment | ✅ FIXED |
| 13 | SSL/TLS certificates | Verify HTTPS enforced on all endpoints | ✅ FIXED |
| 14 | CORS origins | Add production domains to CORS whitelist | ✅ FIXED |

---

## 2. 🟠 HIGH PRIORITY - Fix Within 1 Week

### 2.1 Performance
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 15 | No pgvector extension | Embeddings stored as JSON - slow similarity search. Use external vector DB (Pinecone, Weaviate) or wait for Render pgvector | ✅ FIXED |
| 16 | No query result caching | Add Redis caching for frequent queries (user profiles, job listings) | ✅ FIXED |
| 17 | Large batch operations | Optimize batch match for >20 jobs (streaming/chunking) | ✅ FIXED |
| 18 | Database connection pooling | Tune db_pool_min/max based on load testing | HIGH |
| 19 | LLM timeout too long | 60s timeout may cause hanging requests - consider 30s with retry | ✅ FIXED |
| 20 | No CDN for static assets | Configure Render CDN or Cloudflare for JS/CSS/images | ✅ FIXED |

### 2.2 Code Quality
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 21 | LSP errors in ai.py | Fix type hints and import resolution errors | ✅ FIXED |
| 22 | LSP errors in main.py | Fix type hints and import resolution errors | ✅ FIXED |
| 23 | LSP errors in metrics.py | Fix `"str" is not awaitable` error | ✅ FIXED |
| 24 | CSRFMiddleware import | Fix import from `starlette_csrf.middleware` | ✅ FIXED |
| 25 | Unused migration scripts | Clean up migrate_to_render.py, setup_database_fix.py (already migrated) | ✅ FIXED |

### 2.3 Testing
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 26 | 7 skipped tests | Add integration test setup with test database | ✅ FIXED |
| 27 | No load testing | Add k6 or Locust load tests for API endpoints | ✅ FIXED |
| 28 | E2E tests need CI | Configure Playwright in GitHub Actions | ✅ FIXED |
| 29 | No mutation testing | Add mutmut for code quality validation | ✅ FIXED |
| 30 | Test coverage gaps | Add tests for billing/webhook handlers | ✅ FIXED |

### 2.4 Monitoring & Observability
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 31 | No alerting channels configured | Set up Slack webhook or email for alerts | ✅ FIXED |
| 32 | No distributed tracing | Add OpenTelemetry/Jaeger for request tracing | ✅ FIXED |
| 33 | No error tracking | Configure Sentry DSN for production | ✅ FIXED |
| 34 | No uptime monitoring | Add Pingdom/UptimeRobot for external monitoring | ✅ FIXED |
| 35 | Log aggregation | Set up Logtail, Datadog, or similar for log analysis | ✅ FIXED |

---

## 3. 🟡 MEDIUM PRIORITY - Fix Within 1 Month

### 3.1 Features
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 36 | Resume storage | Implement S3/R2 storage for uploaded resumes | ✅ FIXED |
| 37 | Email notifications | Configure Resend API for email notifications | ✅ FIXED |
| 38 | Push notifications | Configure Expo push notifications for mobile | ✅ FIXED |
| 39 | A/B testing not implemented | Add experiment framework for match algorithm testing | ✅ FIXED |
| 40 | Feature flags incomplete | Complete feature flag UI in admin dashboard | MEDIUM |
| 41 | Dealbreaker UI | Add dealbreaker configuration in user preferences | MEDIUM |
| 42 | Job alerts | Implement daily/weekly job alert emails | ✅ FIXED |
| 43 | Social sharing | Add OG images for match results sharing | ✅ FIXED |
| 44 | Export functionality | Add CSV/PDF export for usage analytics | ✅ FIXED |
| 45 | Mobile deep linking | Implement universal links for job applications | MEDIUM |

### 3.2 User Experience
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 46 | No onboarding tooltips | Add guided tour for new users | MEDIUM |
| 47 | No keyboard shortcuts | Add keyboard navigation for power users | MEDIUM |
| 48 | No dark mode | Add dark mode toggle | MEDIUM |
| 49 | Loading states inconsistent | Standardize loading skeleton components | MEDIUM |
| 50 | Error messages generic | Add contextual help for common errors | MEDIUM |
| 51 | No success celebrations | Add confetti/animations for milestones | MEDIUM |
| 52 | Empty states missing | Add illustrations for empty lists/tables | MEDIUM |
| 53 | Mobile responsiveness | Audit all pages for mobile UX | MEDIUM |
| 54 | Accessibility audit | Complete WCAG 2.1 AA compliance | MEDIUM |
| 55 | Internationalization | Add i18n support for multiple languages | MEDIUM |

### 3.3 API & Backend
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 56 | No API versioning | Add /v1/ prefix to all API routes | ✅ FIXED |
| 57 | No request ID in logs | Ensure X-Request-ID propagated to all logs | ✅ FIXED |
| 58 | No API rate limit headers | Add X-RateLimit-Remaining headers | ✅ FIXED |
| 59 | No pagination standard | Standardize cursor-based pagination | ✅ FIXED |
| 60 | Webhook retry logic | Add exponential backoff for webhook delivery | ✅ FIXED |
| 61 | Background job queue | Add Celery/BullMQ for long-running tasks | ✅ FIXED |
| 62 | File upload limits | Add configurable per-tenant upload limits | ✅ FIXED |
| 63 | API documentation | Generate OpenAPI/Swagger docs | ✅ FIXED |
| 64 | GraphQL alternative | Consider GraphQL for complex queries | MEDIUM |

### 3.4 Data & Analytics
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 65 | No event tracking | Add segment/mixpanel for user analytics | ✅ FIXED |
| 66 | No funnel analysis | Track conversion funnels (signup → apply) | ✅ FIXED |
| 67 | No cohort analysis | Track user retention by cohort | ✅ FIXED |
| 68 | No revenue tracking | Add revenue analytics dashboard | ✅ FIXED |
| 69 | No usage quotas | Implement tier-based usage limits | ✅ FIXED |
| 70 | Data retention policy | Implement log/data archiving policies | ✅ FIXED |

---

## 4. 🟢 LOW PRIORITY - Nice to Have

### 4.1 Performance Optimizations
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 71 | No image optimization | Add WebP/AVIF conversion for images | LOW |
| 72 | No code splitting | Audit React bundle size, add lazy loading | LOW |
| 73 | No service worker | Add PWA offline support | LOW |
| 74 | No preloading | Add prefetch hints for likely next pages | LOW |
| 75 | Database read replicas | Add read replica for reporting queries | LOW |
| 76 | Edge functions | Move latency-sensitive operations to edge | LOW |
| 77 | WebSocket for real-time | Add WebSocket for live updates | LOW |
| 78 | HTTP/2 push | Enable HTTP/2 server push | LOW |
| 79 | Brotli compression | Enable Brotli for text assets | LOW |
| 80 | Font subsetting | Subset custom fonts for faster load | LOW |

### 4.2 Developer Experience
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 81 | No Docker Compose | Add docker-compose.yml for local dev | ✅ FIXED |
| 82 | No seed data | Add database seed script for testing | ✅ FIXED |
| 83 | No API mock server | Add MSW for frontend development | LOW |
| 84 | No VS Code settings | Add recommended extensions/settings | LOW |
| 85 | No pre-commit hooks | Add husky/lint-staged | ✅ FIXED |
| 86 | No commitlint | Add conventional commit enforcement | ✅ FIXED |
| 87 | No dependency update automation | Add Dependabot/Renovate | ✅ FIXED |
| 88 | No changelog generation | Add standard-version or similar | LOW |
| 89 | Documentation site | Add Docusaurus/Mintlify docs | LOW |
| 90 | Storybook | Add Storybook for component development | LOW |

### 4.3 Security Enhancements
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 91 | No API key rotation | Add automatic API key rotation | LOW |
| 92 | No session revocation | Add session invalidation on password change | LOW |
| 93 | No audit log UI | Add audit log viewer in admin | LOW |
| 94 | No IP allowlisting | Add IP allowlist for enterprise tenants | LOW |
| 95 | No MFA | Add TOTP/WebAuthn for admin accounts | LOW |
| 96 | No password policy | Add password strength requirements | LOW |
| 97 | No bot detection | Add reCAPTCHA/hCaptcha on forms | ✅ FIXED |
| 98 | No request signing | Add HMAC signing for webhooks | ✅ FIXED |
| 99 | No vulnerability scanning | Add Snyk/Dependabot for dependencies | ✅ FIXED |
| 100 | No penetration testing | Schedule annual security audit | LOW |

### 4.4 Compliance & Legal
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 101 | GDPR data export | Add automated GDPR export feature | ✅ FIXED |
| 102 | GDPR data deletion | Add right-to-be-forgotten workflow | ✅ FIXED |
| 103 | Cookie consent | Add cookie consent banner (non-essential) | LOW |
| 104 | Privacy policy review | Legal review of privacy policy | LOW |
| 105 | Terms of service | Legal review of terms | LOW |
| 106 | Data processing agreements | Create DPA templates for enterprise | LOW |
| 107 | SOC 2 compliance | Begin SOC 2 Type I preparation | LOW |
| 108 | CCPA compliance | Add California privacy rights | LOW |
| 109 | Data residency | Add region-specific data storage option | LOW |
| 110 | Audit trail retention | Define audit log retention policy | LOW |

---

## 5. 🔵 INFRASTRUCTURE & DEVOPS

### 5.1 Immediate
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 111 | No infrastructure as code | Add Terraform/Pulumi for infrastructure | ✅ FIXED |
| 112 | Manual deployments | Set up GitOps with ArgoCD/Flux | ✅ FIXED |
| 113 | No staging environment | Deploy staging environment on Render | ✅ FIXED |
| 114 | No backup strategy | Configure PostgreSQL backups | ✅ FIXED |
| 115 | No disaster recovery | Document DR procedures | ✅ FIXED |
| 116 | No runbooks | Create incident response runbooks | ✅ FIXED |
| 117 | No on-call rotation | Set up PagerDuty/Opsgenie | ✅ FIXED |
| 118 | No cost monitoring | Add cost alerts for cloud spend | ✅ FIXED |

### 5.2 Future
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 119 | Single region | Add multi-region deployment | LOW |
| 120 | No blue-green deploy | Implement zero-downtime deployments | LOW |
| 121 | No canary releases | Add canary deployment strategy | LOW |
| 122 | No feature environments | Add PR preview environments | LOW |
| 123 | No load balancer tuning | Optimize LB settings for traffic patterns | LOW |
| 124 | No CDN caching rules | Define aggressive caching strategy | LOW |
| 125 | Container optimization | Optimize Docker image sizes | LOW |

---

## 6. 🟣 AI/ML IMPROVEMENTS

### 6.1 Model & Matching
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 126 | Free-tier LLM | Upgrade from free model to production-grade for reliability | HIGH |
| 127 | No model fallback | Add fallback models when primary fails | ✅ FIXED |
| 128 | No prompt versioning | Add prompt version tracking/rollback | ✅ FIXED |
| 129 | No A/B prompt testing | Add framework for prompt experiments | ✅ FIXED |
| 130 | No embedding caching | Cache embeddings to reduce API calls | ✅ FIXED |
| 131 | No semantic caching | Cache LLM responses for similar queries | ✅ FIXED |
| 132 | No batch LLM processing | Optimize LLM calls with batching | ✅ FIXED |
| 133 | No model monitoring | Track LLM latency/error rates per model | ✅ FIXED |
| 134 | No token counting | Add token usage tracking per tenant | ✅ FIXED |
| 135 | No content moderation | Add LLM output content filtering | ✅ FIXED |

### 6.2 Matching Algorithm
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 136 | Static weights | Make matching weights configurable | ✅ FIXED |
| 137 | No ML-based scoring | Train custom model on user feedback | LOW |
| 138 | No feedback loop | Add thumbs up/down on match results | ✅ FIXED |
| 139 | No cold start handling | Improve new user matching | ✅ FIXED |
| 140 | No explanation quality | Improve match explanation detail | ✅ FIXED |
| 141 | No skill normalization | Normalize skills across job postings | ✅ FIXED |
| 142 | No salary prediction | Add salary estimation from job description | LOW |
| 143 | No career path analysis | Add career progression suggestions | LOW |

---

## 7. 🟤 MOBILE APP

### 7.1 Core
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 144 | Expo app incomplete | Complete all AI feature screens | ✅ FIXED |
| 145 | No push notifications | Configure Expo push notifications | ✅ FIXED |
| 146 | No offline support | Add offline-first data caching | MEDIUM |
| 147 | No biometric auth | Add Face ID/Touch ID login | MEDIUM |
| 148 | No deep linking | Implement universal links | MEDIUM |
| 149 | No app store assets | Create screenshots, descriptions | HIGH |
| 150 | No TestFlight/Play | Set up beta testing programs | HIGH |

### 7.2 Polish
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 151 | No haptic feedback | Add haptics for interactions | LOW |
| 152 | No animations | Add smooth transitions | LOW |
| 153 | No widgets | Add iOS/Android widgets | LOW |
| 154 | No watch app | Consider Apple Watch companion | LOW |
| 155 | No tablet optimization | Optimize for iPad/Android tablets | LOW |
| 156 | No landscape mode | Support landscape orientation | LOW |
| 157 | No accessibility | Complete mobile accessibility audit | MEDIUM |

---

## 8. ⚪ THIRD-PARTY INTEGRATIONS

### 8.1 Job Boards
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 158 | Only Adzuna | Add LinkedIn, Indeed, Glassdoor integrations | MEDIUM |
| 159 | No job deduplication | Dedupe jobs across sources | ✅ FIXED |
| 160 | No salary enrichment | Enrich jobs with salary data | MEDIUM |
| 161 | No company data | Add company info from Crunchbase | LOW |

### 8.2 Productivity
| # | Issue | Recommendation | Priority |
|---|-------|---------------|----------|
| 162 | No calendar sync | Add interview calendar integration | MEDIUM |
| 163 | No Slack bot | Add Slack notifications | LOW |
| 164 | No Zapier integration | Add Zapier connector | LOW |
| 165 | No Notion integration | Export applications to Notion | LOW |
| 166 | No Google Drive | Resume backup to Google Drive | LOW |

---

## Summary Statistics

| Priority | Count |
|----------|-------|
| 🔴 CRITICAL | 14 |
| 🟠 HIGH | 36 |
| 🟡 MEDIUM | 55 |
| 🟢 LOW | 61 |
| **TOTAL** | **166** |

---

## Recommended Implementation Order

### Week 1 (Launch Blockers)
1. Fix Supabase storage references (#1)
2. Configure all Render environment variables (#5)
3. Run migrations on production DB (#3)
4. Set up Redis for rate limiting (#4, #10)
5. Generate real secrets (#6, #7, #8)
6. Verify health checks (#12)

### Week 2-4 (Post-Launch Critical)
1. Set up monitoring/alerting (#31, #33, #34)
2. Add load testing (#27)
3. Upgrade LLM from free tier (#126)
4. Add embedding caching (#130)
5. Complete mobile app features (#144, #148)
6. Set up staging environment (#113)

### Month 2-3 (Stability & Growth)
1. Add vector database (#15)
2. Implement caching layer (#16)
3. Add feedback loop for matching (#138)
4. Complete admin dashboard features (#40)
5. Add job board integrations (#158)
6. Implement email notifications (#37)

---

*Document Version: 1.1*
*Last Updated: February 2026*
*Total Recommendations: 166*

---

## Recent Sprint Updates (Sprints 24-28)

### Sprint 24: Vector Database Integration (#15)
- Created `packages/backend/domain/vector_db.py` with Pinecone/Weaviate support
- Implemented `VectorDBClient` abstract interface
- Added `PineconeClient`, `WeaviateClient`, `InMemoryVectorDB` implementations
- Created `apps/api/vector_db.py` API endpoints for vector operations
- Added configuration options in Settings for vector DB providers

### Sprint 25: Headless Browser Execution Engine
- Created `packages/backend/domain/execution_engine.py`
- Implemented `HumanBehaviorSimulator` with randomized interactions
- Added `AntiDetection` class for bot evasion measures
- Implemented `ExecutionEngine` for resilient form filling
- Supports human-like typing, clicking, scrolling patterns

### Sprint 26: ATS 23-Point Scoring System
- Created `packages/backend/domain/ats_scoring.py`
- Implemented comprehensive `ATS23Scorer` with all 23 metrics
- Added weighted scoring with detailed suggestions
- Supports keyword matching, skill relevance, experience alignment
- Provides actionable improvement recommendations

### Sprint 27: Adaptive Onboarding System
- Created `packages/backend/domain/onboarding.py`
- Implemented 20 intelligent onboarding questions
- Added `DealbreakerConfig` for non-negotiable preferences
- Created `AdaptiveProfile` with completeness tracking
- Implemented ML feedback loop for profile refinement

### Sprint 28: Explainable Match Scoring
- Created `packages/backend/domain/explainable_scoring.py`
- Implemented `ExplainableScoringEngine` with confidence intervals
- Added detailed factor analysis (semantic, skills, experience, etc.)
- Generates transparent reasoning for each match decision
- Provides audit logs for user trust

### Sprint 29: Interview Preparation Simulator
- Created `packages/backend/domain/interview_simulator.py`
- Implemented `InterviewSimulator` with question generation
- Added behavioral and technical question categories
- Supports STAR method answer guidance
- Provides AI-powered answer feedback

### Sprint 30-31: Storage & Email (Already Implemented)
- Resume storage: S3/R2/Render disk support exists in `packages/shared/storage.py`
- Email notifications: Resend integration exists in `packages/backend/domain/email_digest.py`

### Sprint 32: Job Alerts System
- Created `packages/backend/domain/job_alerts.py`
- Implemented `JobAlert` model with flexible criteria
- Added `JobAlertMatcher` for finding matching jobs
- Created `JobAlertService` for alert processing
- Created `apps/api/job_alerts.py` API endpoints
- Supports daily/weekly frequency with email delivery

### Sprint 33: Background Job Queue
- Created `packages/backend/domain/job_queue.py`
- PostgreSQL-backed reliable queue (no external dependencies)
- Supports priority queues, delayed jobs, automatic retries
- Added `BackgroundJobQueue` with handler registration
- Implements exponential backoff for failed jobs
- Includes job deduplication and cleanup utilities

### Sprint 34-35: Push Notifications & A/B Testing (Already Implemented)
- Push notifications: Expo integration exists in `packages/backend/domain/notifications.py`
- A/B testing: Framework exists in `backend/domain/experiments.py` and `backend/domain/experiment_readout.py`

### Sprint 36-37: Cohort & Revenue Analytics
- Created `packages/backend/domain/cohort_analysis.py`
  - User retention tracking by daily/weekly/monthly cohorts
  - D7 and D30 retention metrics
  - Engagement metrics (active days, apps per user)
- Created `packages/backend/domain/revenue_analytics.py`
  - MRR breakdown by plan tier
  - Revenue trend over time
  - Churn metrics and rates
  - ARPU/ARPPU calculations
  - Conversion funnel analysis

### Sprint 38-40: API Docs, Usage Quotas, Prompt Versioning (Already Implemented)
- API documentation: OpenAPI/Swagger enabled via FastAPI docs_url/redoc_url
- Usage quotas: Tier-based limits exist in `packages/backend/domain/quotas.py` and `packages/backend/domain/plans.py`
- Prompt versioning: Registry exists in `packages/backend/llm/prompt_registry.py` with version tracking

### Sprint 41: Data Retention Policy
- Created `packages/backend/domain/data_retention.py`
- Configurable retention periods for different data types
- Applications: 2 years (configurable)
- Application events: 90 days
- Analytics events: 1 year
- Background jobs: 30 days
- Automated cleanup functions with batch processing

### Sprint 42-45: Developer Experience Improvements
- Docker Compose: Already exists at `docker-compose.yml`
- Seed data: Already exists at `scripts/seed_beta.py`
- Pre-commit hooks: Added `.pre-commit-config.yaml`
  - Ruff for linting/formatting
  - MyPy for type checking
  - Bandit for security
  - Conventional commit enforcement
- Dependabot: Added `.github/dependabot.yml`
  - Weekly Python dependency updates
  - Weekly npm updates for web apps
  - Monthly GitHub Actions updates

### Sprint 46-48: GDPR Compliance & Security
- GDPR Data Export: Created `packages/backend/domain/gdpr.py`
  - Right to Access (Article 15): Export all user data
  - Right to Erasure (Article 17): Delete user data
  - Data Portability: Machine-readable JSON export
- Bot Detection: Created `packages/shared/captcha.py`
  - hCaptcha support (privacy-focused)
  - reCAPTCHA v3 support (invisible)
  - Configurable minimum score thresholds

### Sprint 49-52: AI/ML Improvements
- Content Moderation: Created `packages/shared/content_moderation.py`
  - PII detection and redaction
  - Profanity and harmful content filtering
  - Spam detection with configurable rules
- Skill Normalization: Created `packages/backend/domain/skill_normalization.py`
  - 100+ skill synonyms mapped (JS → JavaScript)
  - Skill categorization (language, framework, tool)
  - Skill level inference from context
- Batch LLM Processing: Created `packages/backend/domain/batch_llm.py`
  - Parallel LLM calls with rate limiting
  - Request batching for similar queries
  - Retry with exponential backoff
- Cold start handling: Already implemented in `packages/backend/domain/onboarding.py`
- A/B prompt testing: Already implemented in `backend/domain/experiments.py`

### Sprint 53-54: Social & Export
- OG Images: Created `packages/backend/domain/og_images.py`
  - Dynamic image generation for match results
  - Milestone celebration images
  - Job listing preview cards
- Export: Already implemented in `apps/api/export.py` and `apps/api/user.py`
  - CSV export for applications
  - JSON/NDJSON streaming export
  - GDPR data export endpoint

### Sprint 55: Webhook HMAC Signing
- Created `packages/shared/webhook_signing.py`
- HMAC-SHA256 signature generation and verification
- Timestamp-based replay attack prevention
- Stripe-compatible signature format
- Retry logic with exponential backoff for delivery

### Sprint 56-58: Infrastructure & DevOps
- GitOps: Already implemented via Render auto-deploy in `render.yaml`
- On-Call Integration: Created `packages/shared/oncall.py`
  - PagerDuty Events API v2 support
  - Opsgenie integration
  - Alert deduplication and auto-resolution
- Cost Monitoring: Created `packages/shared/cost_monitoring.py`
  - Multi-provider cost aggregation
  - Budget thresholds with alerts
  - Cost anomaly detection
