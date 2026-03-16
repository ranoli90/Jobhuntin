# SEO Engine Setup Guide

**Document Version:** 1.0  
**Date:** March 16, 2026  
**Status:** Active  

---

## 1. Prerequisites

Before running SEO scripts, ensure you have:

### 1.1 Google Service Account (Required for Indexing API)

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project (e.g., "jobhuntin-seo")

2. **Enable Required APIs**
   - Web Search Indexing API
   - Search Console API (optional, for analytics)

3. **Create Service Account**
   - Go to IAM & Admin > Service Accounts
   - Create a service account with "Owner" role (or Editor with Indexing permissions)
   - Download the JSON key file

4. **Add to Google Search Console**
   - Go to [Google Search Console](https://search.google.com/search-console)
   - Add your site (e.g., https://jobhuntin.com)
   - Go to Settings > Users and permissions
   - Add the service account email as an **Owner**

### 1.2 OpenRouter API Key (Required for Content Generation)

1. **Create OpenRouter Account**
   - Go to [OpenRouter.ai](https://openrouter.ai/)
   - Sign up and get an API key

2. **Add Credits**
   - Add funds to your account (minimum $5 recommended)

### 1.3 Database Requirements

- PostgreSQL database (see migrations/041_seo_engine_tables.sql)
- Database user with permission to create tables

---

## 2. Environment Variable Setup

### 2.1 Create .env File

Create a `.env` file in the project root:

```bash
# Required
GOOGLE_SERVICE_ACCOUNT_KEY=/path/to/your/service-account-key.json
DATABASE_URL=postgresql://username:password@host:5432/database
LLM_API_KEY=your-openrouter-api-key

# Optional - URLs (defaults provided)
BASE_URL=https://jobhuntin.com
OPENROUTER_API_URL=https://openrouter.ai/api/v1

# Optional - Generation Settings
SEO_PARALLEL_WORKERS=2
SEO_DAILY_LIMIT=50
SEO_BATCH_SIZE=5
SEO_BATCH_DELAY_MS=30000
SEO_CONTENT_FRESHNESS_HOURS=2

# Optional - Submission Settings
SEO_SUBMISSION_BATCH_SIZE=10
SEO_SUBMISSION_DELAY_MS=2000
SEO_SUBMISSION_MAX_RETRIES=5

# Optional - Other
REDIS_URL=redis://localhost:6379/0
LLM_MODEL=openai/gpt-4o-mini
NODE_ENV=development
LOG_LEVEL=info

# Optional - IndexNow (for Bing/Yandex instant indexing)
INDEXNOW_API_KEY=your-indexnow-key
```

### 2.2 Environment-Specific Configuration

#### Development
```bash
NODE_ENV=development
LOG_LEVEL=debug
SEO_DAILY_LIMIT=10
```

#### Production
```bash
NODE_ENV=production
LOG_LEVEL=warn
SEO_DAILY_LIMIT=100
SEO_PARALLEL_WORKERS=5
```

---

## 3. Database Migration

### 3.1 Run Migration

The SEO engine requires database tables defined in migration 041:

```bash
# Run the migration
psql $DATABASE_URL -f migrations/041_seo_engine_tables.sql
```

Or if using the project's migration system:
```bash
alembic upgrade head
```

### 3.2 Verify Tables Created

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'seo_%';
```

Expected tables:
- `seo_engine_progress`
- `seo_generated_content`
- `seo_submission_log`
- `seo_metrics`
- `seo_logs`
- `seo_competitor_intelligence`

---

## 4. Running SEO Scripts

### 4.1 Submit URLs to Google Indexing API

```bash
cd apps/web

# Full submission
npx tsx scripts/seo/submit-to-google.ts

# Dry run (preview only)
npx tsx scripts/seo/submit-to-google.ts --dry-run

# Submit specific competitor only
npx tsx scripts/seo/submit-to-google.ts --slug teal
```

### 4.2 Fast Index (Multi-Method)

```bash
# Full run
npx tsx scripts/seo/fast-index.ts

# Dry run
npx tsx scripts/seo/fast-index.ts --dry-run

# Ping sitemaps only
npx tsx scripts/seo/fast-index.ts --ping-only

# IndexNow only
npx tsx scripts/seo/fast-index.ts --indexnow-only

# Reset progress tracker
npx tsx scripts/seo/fast-index.ts --reset
```

### 4.3 Generate Competitor Content

```bash
# Basic competitor
npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName"

# With URL
npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName" --url "https://competitor.com"

# Specific model
npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName" --model "openai/gpt-4o"
```

### 4.4 Generate Aggressive Competitor Content

```bash
# Standard
npx tsx scripts/seo/generate-aggressive-competitor-content.ts "CompetitorName"

# Aggressive mode (premium models)
npx tsx scripts/seo/generate-aggressive-competitor-content.ts "CompetitorName" --aggressive

# With URL
npx tsx scripts/seo/generate-aggressive-competitor-content.ts "CompetitorName" --url "https://competitor.com"
```

### 4.5 Modern SEO Engine

```bash
# Run the modern SEO engine
npx tsx scripts/seo/modern-seo-engine.ts

# With custom model
LLM_MODEL=openai/gpt-4o npx tsx scripts/seo/modern-seo-engine.ts
```

---

## 5. Verification

### 5.1 Test Google Credentials

```bash
npx tsx scripts/seo/test-google-creds.ts
```

Expected output:
```
🔑 Testing Google Service Account credentials...
✅ Credentials valid
   Email: your-service-account@project.iam.gserviceaccount.com
```

### 5.2 Verify Indexing API Access

```bash
npx tsx scripts/seo/verify-google-indexing.ts https://jobhuntin.com
```

### 5.3 Check Database Connection

```bash
# Run health checks via Python backend
cd packages/backend
python -c "from packages.backend.domain.seo_health import run_all_checks; print(run_all_checks())"
```

---

## 6. Common Setup Issues

### Issue: "GOOGLE_SERVICE_ACCOUNT_KEY is neither valid JSON nor a file path"

**Solution**: Ensure the path is correct and the file exists:
```bash
ls -la /path/to/your/service-account-key.json
```

### Issue: "Missing required environment variable: DATABASE_URL"

**Solution**: Ensure `.env` file is in the correct location (project root) and variables are exported:
```bash
source .env  # or use dotenv in your scripts
```

### Issue: "Permission denied" when creating files

**Solution**: Ensure the `logs/` directory exists and is writable:
```bash
mkdir -p apps/web/logs
```

---

## 7. Next Steps

After setup, see [SEO_TROUBLESHOOTING.md](SEO_TROUBLESHOOTING.md) for common issues and solutions.
