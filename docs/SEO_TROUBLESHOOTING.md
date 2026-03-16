# SEO Engine Troubleshooting Guide

**Document Version:** 1.0  
**Date:** March 16, 2026  
**Status:** Active  

---

## 1. Common Errors and Solutions

### 1.1 Google API Errors

#### Error: "PERMISSION_DENIED"
```
Error: Google Indexing API permission denied
Code: PERMISSION_DENIED
```

**Causes:**
- Service account not added to Google Search Console
- Service account lacks required permissions

**Solutions:**
1. Verify service account is added as **Owner** in Google Search Console
2. Check the service account email matches exactly
3. Re-download the JSON key file and ensure it's valid

#### Error: "QUOTA_EXCEEDED"
```
Error: Daily quota exceeded
Code: QUOTA_EXCEEDED
```

**Causes:**
- Exceeded 200 URL submissions per day
- Exceeded rate limits

**Solutions:**
1. Wait until midnight UTC for quota reset
2. Use IndexNow API (no daily limit)
3. Use sitemap ping for bulk re-crawl

#### Error: "INVALID_URL"
```
Error: URL not in Search Console
Code: INVALID_URL
```

**Causes:**
- URL not under verified domain
- Domain not added to Search Console

**Solutions:**
1. Verify domain in Google Search Console
2. Ensure URLs follow correct format (https://)
3. Check subdomain matches (www vs non-www)

### 1.2 Authentication Errors

#### Error: "AUTH_ERROR"
```
Error: Authentication failed
Code: AUTH_ERROR
```

**Solutions:**
1. Verify `GOOGLE_SERVICE_ACCOUNT_KEY` is set correctly
2. Check JSON key format is valid
3. Ensure private key has correct PEM headers:
   ```
   -----BEGIN PRIVATE KEY-----
   ...
   -----END PRIVATE KEY-----
   ```

#### Error: "Invalid key format"
```
Error: Invalid private key format (missing PEM headers)
```

**Solutions:**
The private key may have escaped newlines. The config.ts automatically fixes this, but ensure your key file has:
- Actual newlines (not `\n` literal)
- Proper PEM headers

### 1.3 Database Errors

#### Error: "DATABASE_ERROR"
```
Error: Database connection failed
Code: DATABASE_ERROR
```

**Solutions:**
1. Verify `DATABASE_URL` format:
   ```
   postgresql://user:password@host:5432/database
   ```
2. Check database server is running
3. Verify user has permissions
4. Test connection:
   ```bash
   psql $DATABASE_URL -c "SELECT 1"
   ```

### 1.4 LLM API Errors

#### Error: "Rate limited" from OpenRouter
```
Error: Model rate limited: {"error": {"message": "Rate limit exceeded"}}
```

**Solutions:**
1. Wait 5-10 seconds and retry
2. Use `--model` flag to try different model
3. Add credits to OpenRouter account
4. Reduce `SEO_PARALLEL_WORKERS`

#### Error: "Model not found"
```
Error: Model provider/model not found
```

**Solutions:**
1. Check model name format (e.g., `openai/gpt-4o-mini`)
2. Verify model is available on OpenRouter
3. Try backup model:
   ```bash
   npx tsx scripts/seo/generate-competitor-content.ts "Name" --model "meta-llama/llama-3.3-70b-instruct"
   ```

---

## 2. Rate Limiting Guidance

### 2.1 Google Indexing API Limits

| Limit Type | Value | Notes |
|------------|-------|-------|
| Daily submissions | 200 | Per owner |
| Minute rate | ~10 | Burst up to 50 |
| Batch size | 100 | Max per batch |

### 2.2 IndexNow API (No Daily Limit)

Use IndexNow for unlimited submissions to Bing and Yandex:

```bash
# Set environment variable
export INDEXNOW_API_KEY=your-key

# Run IndexNow only
npx tsx scripts/seo/fast-index.ts --indexnow-only
```

### 2.3 Configuration for Rate Limits

Adjust in `.env`:

```bash
# Reduce submissions to avoid rate limits
SEO_SUBMISSION_DELAY_MS=5000  # 5 seconds between submissions
SEO_SUBMISSION_BATCH_SIZE=5   # Smaller batches
```

### 2.4 Rate Limiter Presets

Available in [`rate-limiter.ts`](apps/web/scripts/seo/rate-limiter.ts):

| Preset | Requests | Per |
|--------|----------|-----|
| `googleIndexing` | 100 | 100 seconds |
| `searchConsole` | 60 | minute |
| `general` | 60 | minute |
| `aggressive` | 120 | minute |
| `conservative` | 30 | minute |

---

## 3. Debugging Tips

### 3.1 Enable Debug Logging

```bash
# Set log level
export LOG_LEVEL=debug

# Or in .env
LOG_LEVEL=debug

# Run script
npx tsx scripts/seo/submit-to-google.ts
```

### 3.2 Check Logs

```bash
# View recent logs
tail -f apps/web/logs/seo.log

# Or query database logs
psql $DATABASE_URL -c "SELECT * FROM seo_logs ORDER BY created_at DESC LIMIT 50;"
```

### 3.3 Dry Run Mode

Always test with dry run first:

```bash
npx tsx scripts/seo/submit-to-google.ts --dry-run
npx tsx scripts/seo/fast-index.ts --dry-run
```

### 3.4 Test Individual Components

```bash
# Test Google credentials
npx tsx scripts/seo/test-google-creds.ts

# Verify indexing API access
npx tsx scripts/seo/verify-google-indexing.ts https://jobhuntin.com/jobs/developer/new-york
```

### 3.5 Check Database State

```bash
# Check content status
psql $DATABASE_URL -c "SELECT url, google_indexed, created_at FROM seo_generated_content ORDER BY created_at DESC LIMIT 10;"

# Check quota usage
psql $DATABASE_URL -c "SELECT * FROM seo_engine_progress;"

# Check submission history
psql $DATABASE_URL -c "SELECT service_id, urls_submitted, success, created_at FROM seo_submission_log ORDER BY created_at DESC LIMIT 10;"
```

### 3.6 Progress File

For scripts using file-based progress tracking:

```bash
# View progress
cat apps/web/logs/indexing-progress.json

# Reset if stuck
npx tsx scripts/seo/fast-index.ts --reset
```

---

## 4. Health Check Interpretation

### 4.1 Run Health Checks

```bash
# Via Python backend
cd packages/backend
python -c "from packages.backend.domain.seo_health import run_all_checks; import json; print(json.dumps(run_all_checks(), indent=2))"
```

### 4.2 Health Check Results

#### ✅ All Checks Passing
```json
{
  "status": "healthy",
  "checks": {
    "database_connection": "pass",
    "progress_table": "pass",
    "content_table": "pass",
    "metrics_table": "pass"
  }
}
```

#### ⚠️ Warnings

| Warning | Meaning | Action |
|---------|---------|--------|
| `quota_low` | Daily quota < 20% remaining | Normal if running at end of day |
| `recent_errors` | Errors in last 24 hours | Review error logs |

#### ❌ Critical Issues

| Issue | Meaning | Action |
|-------|---------|--------|
| `database_connection: fail` | Cannot connect to DB | Check DATABASE_URL |
| `progress_table: fail` | Table missing | Run migration 041 |
| `content_table: fail` | Table missing | Run migration 041 |

### 4.3 Monitoring Metrics

Key metrics to track:

```sql
-- Success rate
SELECT success_rate FROM seo_metrics ORDER BY created_at DESC LIMIT 1;

-- Average generation time
SELECT average_generation_time_ms FROM seo_metrics ORDER BY created_at DESC LIMIT 1;

-- Today's API calls
SELECT api_calls_today FROM seo_metrics ORDER BY created_at DESC LIMIT 1;
```

---

## 5. Performance Optimization

### 5.1 Slow Generation

**Symptoms:** Content generation takes > 5 minutes

**Solutions:**
1. Reduce `SEO_BATCH_SIZE` (try 3)
2. Increase `SEO_BATCH_DELAY_MS` (try 60000)
3. Use faster model:
   ```bash
   LLM_MODEL=anthropic/claude-3-haiku npx tsx scripts/seo/modern-seo-engine.ts
   ```

### 5.2 High Failure Rate

**Symptoms:** > 10% submission failures

**Solutions:**
1. Check Google Search Console for URL errors
2. Verify URLs are valid and accessible
3. Enable retry logic (default: 5 retries)
4. Check rate limiting

### 5.3 Memory Issues

**Symptoms:** Script crashes with out-of-memory

**Solutions:**
1. Reduce `SEO_PARALLEL_WORKERS` (try 1)
2. Process smaller batches
3. Increase Node.js memory:
   ```bash
   node --max-old-space-size=4096 node_modules/.bin/ts-node ...
   ```

---

## 6. Emergency Procedures

### 6.1 Reset Daily Quota

If stuck or need to reset:

```bash
# Via database
psql $DATABASE_URL -c "UPDATE seo_engine_progress SET daily_quota_used = 0;"

# Or run fast-index with reset
npx tsx scripts/seo/fast-index.ts --reset
```

### 6.2 Clear All Progress

To start fresh:

```bash
# Database
psql $DATABASE_URL -c "TRUNCATE seo_generated_content, seo_submission_log, seo_metrics;"

# Or file-based
rm apps/web/logs/indexing-progress.json
```

### 6.3 Emergency Contact

For critical issues:
1. Check [SEO_IMPLEMENTATION_SUMMARY.md](SEO_IMPLEMENTATION_SUMMARY.md) for architecture
2. Review logs in database or `apps/web/logs/`
3. Contact the SEO team

---

## 7. FAQ

### Q: Why are my URLs not being indexed?
A: Check Google Search Console for URL inspection. Ensure URLs are valid JobPosting schema and not blocked by robots.txt.

### Q: How do I add more competitors?
A: Run the content generation script:
```bash
npx tsx scripts/seo/generate-competitor-content.ts "NewCompetitor"
```

### Q: Can I run multiple scripts at once?
A: Not recommended due to rate limits. Run sequentially or use different APIs (e.g., IndexNow + Google).

### Q: What's the difference between submission methods?
- **Google Indexing API**: 200/day, highest priority
- **Sitemap Ping**: Unlimited, triggers crawl
- **IndexNow**: Unlimited, instant for Bing/Yandex

### Q: How do I check my quota remaining?
A: Query the database:
```bash
psql $DATABASE_URL -c "SELECT daily_quota_used, daily_quota_reset FROM seo_engine_progress;"
```
