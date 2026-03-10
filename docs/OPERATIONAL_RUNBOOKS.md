# Operational Runbooks
**JobHuntin Production Operations Guide**

This document provides step-by-step procedures for common operational tasks, incident response, and deployment procedures.

---

## Table of Contents

1. [Incident Response](#incident-response)
2. [Deployment Procedures](#deployment-procedures)
3. [Database Operations](#database-operations)
4. [Monitoring & Alerts](#monitoring--alerts)
5. [Service Health Checks](#service-health-checks)
6. [Common Issues & Resolutions](#common-issues--resolutions)

---

## Incident Response

### Severity Levels

- **P0 (Critical)**: Service completely down, data loss, security breach
- **P1 (High)**: Major feature broken, significant user impact
- **P2 (Medium)**: Minor feature issues, workarounds available
- **P3 (Low)**: Cosmetic issues, minor bugs

### Incident Response Process

#### 1. Detection & Triage

**Sources:**
- Sentry error alerts
- Health check failures (`/healthz`)
- User reports
- Monitoring dashboards

**Initial Assessment:**
```bash
# Check service status
curl https://api.jobhuntin.com/healthz

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1"

# Check Redis connectivity
redis-cli -u $REDIS_URL ping

# Check recent errors
# (Access Sentry dashboard or logs)
```

#### 2. Immediate Actions

**For P0/P1 incidents:**

1. **Acknowledge the incident** (Slack/PagerDuty)
2. **Check service health:**
   ```bash
   # API health
   curl https://api.jobhuntin.com/healthz
   
   # Worker health (if endpoint exists)
   curl https://api.jobhuntin.com/worker/health
   ```

3. **Check logs:**
   ```bash
   # Render logs (if using Render)
   render logs --service api --tail 100
   
   # Or check application logs
   # (Location depends on deployment)
   ```

4. **Identify affected users:**
   - Check Sentry for error volume
   - Check analytics for drop in activity
   - Review recent deployments

#### 3. Containment

**Database Issues:**
- Check connection pool exhaustion
- Verify database is accessible
- Check for long-running queries

**API Issues:**
- Check rate limiting (may be blocking legitimate users)
- Verify Redis connectivity (affects auth, rate limiting)
- Check for memory/CPU spikes

**Worker Issues:**
- Check worker process status
- Verify Playwright/browser availability
- Check job queue depth
- See [Worker Horizontal Scaling](#worker-horizontal-scaling) for multi-instance setup

#### 4. Resolution

**Common Fixes:**

1. **Service Restart:**
   ```bash
   # Render
   render services:restart --service api
   
   # Or via Render dashboard
   ```

2. **Database Connection Reset:**
   ```sql
   -- Check active connections
   SELECT count(*) FROM pg_stat_activity;
   
   -- Kill long-running queries if needed
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
   WHERE state = 'active' AND query_start < now() - interval '5 minutes';
   ```

3. **Clear Rate Limits (Emergency Only):**
   ```bash
   # Connect to Redis
   redis-cli -u $REDIS_URL
   
   # Clear rate limit keys (use with caution)
   KEYS rate_limit:*
   # Review and delete specific keys if needed
   ```

4. **Rollback Deployment:**
   - See [Deployment Procedures](#deployment-procedures)

#### 5. Post-Incident

1. **Document the incident:**
   - Root cause
   - Timeline
   - Resolution steps
   - Prevention measures

2. **Update monitoring:**
   - Add alerts for detected issues
   - Improve health checks
   - Add dashboards

---

## Deployment Procedures

### Pre-Deployment Checklist

- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Linting passes (`ruff check .`)
- [ ] Type checking passes (`mypy`)
- [ ] Database migrations tested locally
- [ ] Environment variables updated
- [ ] Feature flags configured (if applicable)
- [ ] Rollback plan prepared

### Deployment Steps

#### 1. Staging Deployment

```bash
# 1. Merge to staging branch
git checkout staging
git merge main
git push origin staging

# 2. Monitor staging deployment
# (Automatic via Render or CI/CD)

# 3. Verify staging health
curl https://staging-api.jobhuntin.com/healthz

# 4. Run smoke tests
# (Manual or automated)
```

#### 2. Production Deployment

**Option A: Render Dashboard (Recommended)**
1. Navigate to Render dashboard
2. Select service (api, worker, web)
3. Click "Manual Deploy" → Select commit
4. Monitor deployment logs
5. Verify health check passes

**Option B: Git Push (Auto-deploy)**
```bash
# 1. Merge to main branch
git checkout main
git merge staging
git push origin main

# 2. Monitor deployment
# (Automatic via Render webhook)

# 3. Verify production health
curl https://api.jobhuntin.com/healthz
```

#### 3. Post-Deployment Verification

```bash
# 1. Health checks
curl https://api.jobhuntin.com/healthz
curl https://api.jobhuntin.com/health

# 2. Check error rates (Sentry)
# - Monitor for 5-10 minutes
# - Verify error rate is normal

# 3. Check key metrics
# - API latency (should be < 500ms p95)
# - Request success rate (should be > 99%)
# - Magic link delivery rate (should be > 95%)

# 4. Test critical flows
# - Magic link signup
# - Onboarding completion
# - Job application submission
```

### Rollback Procedure

**Immediate Rollback (< 5 minutes):**

1. **Render Dashboard:**
   - Navigate to service
   - Click "Rollback" → Select previous deployment
   - Confirm rollback

2. **Git-based Rollback:**
   ```bash
   # Revert commit
   git revert <commit-hash>
   git push origin main
   ```

**Post-Rollback:**
- Verify service health
- Check error rates return to normal
- Document rollback reason
- Schedule post-mortem

---

## Database Operations

### Migrations

**Running Migrations:**

```bash
# Local development
psql $DATABASE_URL -f infra/postgres/schema.sql
psql $DATABASE_URL -f infra/postgres/migrations.sql

# Production (Render PostgreSQL)
# 1. Backup database first
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 2. Run migrations
psql $DATABASE_URL -f infra/postgres/schema.sql
psql $DATABASE_URL -f infra/postgres/migrations.sql
# (Run migration files in order)
```

**Migration Best Practices:**
- Always backup before migrations
- Test migrations on staging first
- Run during low-traffic periods
- Monitor for long-running queries

### Database Maintenance

**Connection Pool Monitoring:**
```sql
-- Check active connections
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';

-- Check connection pool usage
SELECT 
  max_conn,
  used_conn,
  max_conn - used_conn as available_conn
FROM (
  SELECT 
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_conn,
    count(*) as used_conn
  FROM pg_stat_activity
) t;
```

**Index Maintenance:**
```sql
-- Reindex if needed (run during maintenance window)
REINDEX INDEX CONCURRENTLY idx_applications_claim;

-- Analyze tables for query planner
ANALYZE applications;
ANALYZE jobs;
```

**Vacuum (if needed):**
```sql
-- Vacuum analyze (non-blocking)
VACUUM ANALYZE applications;
```

### DB Pool Config for High Concurrency (#40)

**Environment Variables:**
- `DB_POOL_MIN` (default: 10) — Minimum connections per API instance
- `DB_POOL_MAX` (default: 100) — Maximum connections per API instance

**For 4000+ concurrent users:**
- API: Set `DB_POOL_MAX=100` per instance; scale API horizontally
- Worker: Uses separate pool (`db_pool_min`, `db_pool_max` from config)
- PostgreSQL `max_connections` must exceed sum of all pools (e.g. 3 API × 100 + 2 Worker × 20 = 340; set `max_connections` ≥ 500)

**Render PostgreSQL:** Default max_connections is 97; upgrade plan if needed.

---

## Worker Horizontal Scaling (#39)

**Current Design:** Single worker polls `applications` with `status = 'QUEUED'`, claims via `SELECT FOR UPDATE SKIP LOCKED` (safe for concurrent workers).

**Scaling Steps:**
1. **Deploy multiple worker instances** on Render (same image, same env)
2. Each worker polls independently; `SKIP LOCKED` ensures no duplicate claims
3. **Worker rate limits** are per-process (`max_applications_per_minute`, `llm_rate_limit_per_minute`); total throughput = N × limit
4. **Per-tenant fairness (#42):** Worker uses `claim_next_prioritized` (priority_score DESC); enterprise/team plans get higher priority. For stricter fairness, add per-tenant rate limiting in worker.

**Recommended:** 2–3 workers for production; 1 for staging.

---

## Monitoring & Alerts

### Key Metrics to Monitor

**API Metrics:**
- Request rate (requests/minute)
- Error rate (errors/requests)
- Latency (p50, p95, p99)
- Rate limit hits
- Slow requests (>1s)

**Database Metrics:**
- Connection pool usage
- Query performance
- Replication lag (if using read replicas)
- Disk usage

**Application Metrics:**
- Magic link delivery rate
- Onboarding completion rate
- Application success rate
- Worker task completion rate

**Infrastructure:**
- CPU usage
- Memory usage
- Disk I/O
- Network I/O

### Alert Thresholds

**Critical Alerts (P0):**
- API error rate > 5%
- Database connection pool > 90%
- Service health check failing
- Magic link delivery rate < 80%

**Warning Alerts (P1):**
- API latency p95 > 1s
- Error rate > 1%
- Worker queue depth > 1000
- Redis unavailable

### Setting Up Alerts

**Sentry:**
- Configure alert rules in Sentry dashboard
- Set up Slack/PagerDuty integration
- Alert on error rate spikes

**Custom Monitoring:**
- Use `/healthz` endpoint for uptime monitoring
- Monitor metrics via OpenTelemetry/Prometheus
- Set up dashboards (Grafana, Datadog, etc.)

---

## Service Health Checks

### Health Check Endpoints

**Basic Health:**
```bash
curl https://api.jobhuntin.com/health
# Returns: {"status": "ok"}
```

**Deep Health Check:**
```bash
curl https://api.jobhuntin.com/healthz
# Returns: {
#   "status": "ok",
#   "env": "prod",
#   "db": "ok"
# }
```

### Manual Health Verification

```bash
# 1. API Health
curl -f https://api.jobhuntin.com/healthz || echo "API unhealthy"

# 2. Database Connectivity
psql $DATABASE_URL -c "SELECT 1" || echo "DB unreachable"

# 3. Redis Connectivity
redis-cli -u $REDIS_URL ping || echo "Redis unreachable"

# 4. Worker Health (if endpoint exists)
curl -f https://api.jobhuntin.com/worker/health || echo "Worker unhealthy"
```

---

## Common Issues & Resolutions

### Issue: High Error Rate

**Symptoms:**
- Sentry showing spike in errors
- Users reporting failures

**Diagnosis:**
1. Check Sentry for error patterns
2. Review recent deployments
3. Check database/Redis connectivity
4. Check rate limiting (may be too aggressive)

**Resolution:**
- Rollback if recent deployment
- Check and fix root cause
- Temporarily increase rate limits if needed
- Restart service if needed

### Issue: Slow API Responses

**Symptoms:**
- High p95 latency
- User complaints about slowness

**Diagnosis:**
1. Check slow query logs
2. Review database connection pool
3. Check for N+1 queries
4. Review API latency metrics by endpoint

**Resolution:**
- Add missing database indexes
- Optimize slow queries
- Increase connection pool if needed
- Add caching for frequently accessed data

### Issue: Magic Links Not Delivered

**Symptoms:**
- Users not receiving emails
- Low delivery rate metrics

**Diagnosis:**
1. Check Resend webhook events
2. Verify RESEND_API_KEY is set
3. Check email bounce/complaint rates
4. Review rate limiting (may be blocking)

**Resolution:**
- Verify Resend API key
- Check email domain reputation
- Review rate limits
- Check Resend dashboard for issues

### Issue: Worker Not Processing Jobs

**Symptoms:**
- Applications stuck in QUEUED status
- Worker queue growing

**Diagnosis:**
1. Check worker process status
2. Verify database connectivity
3. Check for worker errors in logs
4. Verify Playwright/browser availability

**Resolution:**
- Restart worker process
- Check browser/Playwright installation
- Verify database connectivity
- Check for rate limiting on LLM API

### Issue: Session Token Issues

**Symptoms:**
- Users getting logged out unexpectedly
- "Session revoked" errors

**Diagnosis:**
1. Check Redis connectivity (required for revocation)
2. Verify JWT_SECRET is set correctly
3. Check session token TTL settings

**Resolution:**
- Verify Redis is available
- Check JWT_SECRET configuration
- Review session token rotation logic

---

## Emergency Contacts

- **On-Call Engineer**: [Configure in PagerDuty/Slack]
- **Database Admin**: [Contact info]
- **Infrastructure**: [Contact info]

---

## Appendix: Useful Commands

### Database

```bash
# Connect to database
psql $DATABASE_URL

# Backup database
pg_dump $DATABASE_URL > backup.sql

# Restore database
psql $DATABASE_URL < backup.sql

# Check table sizes
psql $DATABASE_URL -c "
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Redis

```bash
# Connect to Redis
redis-cli -u $REDIS_URL

# Check keys
redis-cli -u $REDIS_URL KEYS "auth:*"

# Clear rate limits (use with caution)
redis-cli -u $REDIS_URL DEL "rate_limit:magic_link_ip:1.2.3.4"

# Monitor commands
redis-cli -u $REDIS_URL MONITOR
```

### Application Logs

```bash
# Render logs
render logs --service api --tail 100

# Or check application log files
# (Location depends on deployment)
```

---

**Last Updated:** March 9, 2026  
**Maintainer:** DevOps Team
