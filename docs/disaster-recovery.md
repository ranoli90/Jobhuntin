# Disaster Recovery Procedures

## Overview

This document outlines disaster recovery (DR) procedures for the JobHuntin platform.

---

## Recovery Time Objectives (RTO)

| Incident Type | RTO Target | RPO Target |
|--------------|------------|------------|
| Database failure | 15 min | 1 hour |
| API service failure | 5 min | 0 (stateless) |
| Redis failure | 5 min | 0 (cache only) |
| Region outage | 2 hours | 24 hours |
| Complete data loss | 4 hours | 24 hours |

---

## Recovery Scenarios

### Scenario 1: API Service Down

**Symptoms:**
- API returning 5xx errors
- Health check failing
- Users unable to access app

**Recovery Steps:**

1. **Check service status**
   ```bash
   curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/services/srv-d63l79hr0fns73boblag"
   ```

2. **Check recent logs**
   ```bash
   RENDER_API_KEY=rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa \
     render logs -r srv-d63l79hr0fns73boblag --limit 50
   ```

3. **Restart service**
   ```bash
   curl -X POST \
     -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/services/srv-d63l79hr0fns73boblag/restart"
   ```

4. **If restart fails, trigger new deploy**
   ```bash
   curl -X POST \
     -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/services/srv-d63l79hr0fns73boblag/deploys"
   ```

5. **Rollback to previous deploy if needed**
   - Go to Render Dashboard → Service → Deploys
   - Click "Rollback" on last successful deploy

**Estimated Recovery Time:** 5-10 minutes

---

### Scenario 2: Database Connection Failure

**Symptoms:**
- `/healthz` shows `db: "unreachable"`
- Queries timing out
- "Database pool not available" errors

**Recovery Steps:**

1. **Verify database status**
   ```bash
   curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/postgres/dpg-d66ck524d50c73bas62g-a"
   ```

2. **Check database is not suspended**
   - If `suspended: "suspended"`, contact Render support

3. **Verify connection string**
   - Check DATABASE_URL in Render environment variables
   - Ensure credentials are correct

4. **Check IP allowlist**
   ```bash
   curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/postgres/dpg-d66ck524d50c73bas62g-a" | \
     jq '.ipAllowList'
   ```

5. **Restart database (if available)**
   - Render databases auto-restart on failure

6. **Scale up if hitting limits**
   - Check connection count: `SELECT count(*) FROM pg_stat_activity;`
   - Upgrade plan if needed

**Estimated Recovery Time:** 10-15 minutes

---

### Scenario 3: Redis Failure

**Symptoms:**
- Rate limiting not working
- Caching errors in logs
- Sessions not persisting

**Recovery Steps:**

1. **Check Redis status**
   ```bash
   curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/redis/red-d6761bp5pdvs73e7b3mg"
   ```

2. **Verify Redis URL**
   - Check REDIS_URL in environment variables
   - Format: `rediss://red-ID:PASSWORD@oregon-keyvalue.render.com:6379`

3. **Test connection**
   ```bash
   redis-cli -u "$REDIS_URL" ping
   ```

4. **App continues without Redis**
   - Circuit breaker falls back to in-memory caching
   - Rate limiting uses in-memory fallback

5. **If Redis is deleted/recreated**
   - Update REDIS_URL in all services
   - Restart affected services

**Estimated Recovery Time:** 5 minutes (app continues with degraded caching)

---

### Scenario 4: Data Corruption / Accidental Deletion

**Symptoms:**
- Missing data in tables
- User reports missing records
- Suspicious queries in logs

**Recovery Steps:**

1. **Stop writes to prevent further damage**
   - Enable maintenance mode in Render

2. **Identify affected tables**
   ```sql
   SELECT table_name, n_live_tup 
   FROM pg_stat_user_tables 
   ORDER BY n_live_tup DESC;
   ```

3. **Create point-in-time recovery (if Standard plan)**
   - Render Dashboard → Database → Restore
   - Select timestamp before incident
   - Creates new database instance

4. **Restore from backup (if Basic plan)**
   ```bash
   # Download latest backup
   aws s3 cp s3://jobhuntin-backups/database/latest.dump .
   
   # Restore to new database or existing
   pg_restore --dbname="$DATABASE_URL" --clean latest.dump
   ```

5. **Verify data integrity**
   - Check row counts
   - Verify critical tables
   - Test user flows

6. **Resume operations**
   - Disable maintenance mode
   - Monitor for issues

**Estimated Recovery Time:** 1-4 hours depending on backup method

---

### Scenario 5: Region Outage

**Symptoms:**
- All Oregon services unreachable
- External monitoring shows downtime
- DNS resolution issues

**Recovery Steps:**

1. **Check Render status**
   - https://status.render.com

2. **If Render outage, wait for resolution**
   - No action needed, services auto-recover

3. **If prolonged outage (>1 hour)**
   - Consider deploying to backup region (Frankfurt)
   - Update DNS to point to backup

4. **Deploy to backup region**
   ```bash
   # Create services in Frankfurt
   curl -X POST \
     -H "Authorization: Bearer $RENDER_API_KEY" \
     -H "Content-Type: application/json" \
     "https://api.render.com/v1/services" \
     -d '{"name": "jobhuntin-api-backup", "region": "frankfurt", ...}'
   ```

5. **Update DNS**
   - Change A record to backup service
   - Wait for propagation

**Estimated Recovery Time:** 2-4 hours

---

### Scenario 6: Security Breach

**Symptoms:**
- Suspicious activity in logs
- Unauthorized access reported
- Data exfiltration detected

**Recovery Steps:**

1. **Immediately revoke compromised credentials**
   ```bash
   # Rotate API keys
   curl -X DELETE \
     -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/services/srv-d63l79hr0fns73boblag/env-vars/LLM_API_KEY"
   
   curl -X PUT \
     -H "Authorization: Bearer $RENDER_API_KEY" \
     -H "Content-Type: application/json" \
     "https://api.render.com/v1/services/srv-d63l79hr0fns73boblag/env-vars/LLM_API_KEY" \
     -d '{"key": "LLM_API_KEY", "value": "NEW_KEY"}'
   ```

2. **Force password reset for affected users**
   ```sql
   UPDATE users SET password_reset_required = true WHERE id IN (affected_ids);
   ```

3. **Audit access logs**
   - Check Render logs for unauthorized access
   - Review database query logs

4. **Notify affected users**
   - Send security notification email
   - Provide remediation steps

5. **Report incident**
   - Document timeline
   - File incident report
   - Update security measures

**Estimated Recovery Time:** Varies by severity

---

## Backup Region Setup

For DR, pre-configure services in a secondary region:

| Service | Primary Region | DR Region |
|---------|---------------|-----------|
| API | Oregon | Frankfurt |
| Web | Oregon | Frankfurt |
| Database | Oregon | (Replication not available on Basic) |
| Redis | Oregon | Frankfurt |

---

## Contact Information

| Role | Contact |
|------|---------|
| Render Support | support@render.com |
| On-call Engineer | (Configure in PagerDuty) |
| Team Lead | (Update with actual contact) |

---

## Post-Recovery Checklist

- [ ] All services healthy (`/healthz` returns 200)
- [ ] Database connections stable
- [ ] Redis cache working
- [ ] No errors in logs
- [ ] User-facing features working
- [ ] Monitoring dashboards normal
- [ ] Incident documented
- [ ] Postmortem scheduled (if P0/P1)

---

*Last Updated: February 2026*
