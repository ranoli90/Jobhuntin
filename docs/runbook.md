# Incident Response Runbook

## Quick Reference

| Service | Dashboard | Logs |
|---------|-----------|------|
| API | https://dashboard.render.com/web/srv-d63l79hr0fns73boblag | `render logs -r srv-d63l79hr0fns73boblag` |
| Web | https://dashboard.render.com/static/srv-d63spbogjchc739akan0 | `render logs -r srv-d63spbogjchc739akan0` |
| Worker | https://dashboard.render.com/worker/srv-d66aadsr85hc73dastfg | `render logs -r srv-d66aadsr85hc73dastfg` |
| Database | https://dashboard.render.com/d/dpg-d66ck524d50c73bas62g-a | N/A |
| Redis | https://dashboard.render.com/redis/red-d6761bp5pdvs73e7b3mg | N/A |

---

## Incident Severity Levels

### P0 - Critical (Response: 5 min)
- Production API completely down
- Database connection failures
- Security breach detected
- Data loss confirmed

### P1 - High (Response: 15 min)
- API errors > 5% rate
- Database latency > 1s
- External integrations failing
- Payment processing issues

### P2 - Medium (Response: 1 hour)
- Elevated error rates (> 1%)
- Performance degradation
- Non-critical feature failures
- Staging environment issues

### P3 - Low (Response: Next business day)
- Minor bugs
- Documentation updates
- Feature requests

---

## Common Incidents & Fixes

### 1. API Returning 503 - Database Pool Not Available

**Symptoms:**
- `/healthz` returns `{"status": "degraded", "db": "unreachable"}`
- API requests fail with 503

**Diagnosis:**
```bash
# Check database status
curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/postgres/dpg-d66ck524d50c73bas62g-a"

# Check API logs
render logs -r srv-d63l79hr0fns73boblag --text "Database"
```

**Resolution:**
1. Check DATABASE_URL environment variable in Render dashboard
2. Verify database is not in maintenance mode
3. Check IP allowlist includes `0.0.0.0/0` or Render IPs
4. Restart API service if needed

**Prevention:**
- Use connection pooling
- Implement circuit breakers
- Add database health checks

---

### 2. API Returning 500 - ImportError

**Symptoms:**
- API crashes on startup
- Logs show `ImportError: cannot import name X from Y`

**Diagnosis:**
```bash
# Check recent deploy logs
render logs -r srv-d63l79hr0fns73boblag --text "ImportError"
```

**Resolution:**
1. Identify missing import or module
2. Add missing code or fix import path
3. Push fix to trigger new deploy
4. Monitor deploy status

---

### 3. High Latency / Slow Responses

**Symptoms:**
- API responses > 1 second
- Timeouts on client side

**Diagnosis:**
```bash
# Check health endpoint for metrics
curl -s https://sorce-api.onrender.com/healthz

# Check for slow queries
render logs -r srv-d63l79hr0fns73boblag --text "slow\|timeout\|latency"
```

**Resolution:**
1. Check database query performance (PgHero)
2. Verify Redis caching is working
3. Scale up database if needed
4. Check LLM API latency

---

### 4. Rate Limiting Errors (429)

**Symptoms:**
- Users getting 429 errors
- "Rate limit exceeded" messages

**Diagnosis:**
```bash
# Check rate limit logs
render logs -r srv-d63l79hr0fns73boblag --text "rate_limit\|429"
```

**Resolution:**
1. Check if Redis is connected: `/healthz` should show Redis available
2. Verify rate limit settings in config
3. Consider increasing limits for legitimate traffic
4. Check for DDoS patterns

---

### 5. Web Build Failures

**Symptoms:**
- Static site shows old version
- Deploy marked as "build_failed"

**Diagnosis:**
```bash
# Check build logs
render logs -r srv-d63spbogjchc739akan0 --text "error\|Error\|failed"
```

**Resolution:**
1. Fix TypeScript/build errors in code
2. Check for missing dependencies
3. Verify build command is correct
4. Push fix to trigger new build

---

## Rollback Procedure

### Via Render Dashboard
1. Go to service → Deploys
2. Find last successful deploy
3. Click "Rollback" button

### Via API
```bash
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/srv-d63l79hr0fns73boblag/deploys" \
  -H "Content-Type: application/json" \
  -d '{"commitId": "LAST_WORKING_COMMIT_SHA"}'
```

---

## Communication Templates

### P0 Initial Notification
```
🚨 P0 INCIDENT DETECTED
Service: [API/Web/Database]
Impact: [Brief description]
Status: Investigating
Lead: [Name]
Next Update: 15 min
```

### P0 Resolution
```
✅ P0 INCIDENT RESOLVED
Service: [API/Web/Database]
Duration: [X minutes]
Root Cause: [Brief description]
Action Items: [Link to postmortem]
```

---

## Escalation Path

1. **On-call Engineer** - First responder
2. **Team Lead** - If not resolved in 30 min
3. **Engineering Manager** - If P0 continues > 1 hour
4. **VP Engineering** - If customer impact is severe

---

## Post-Incident Actions

1. Create postmortem document
2. Schedule review meeting
3. Implement preventive fixes
4. Update runbook if needed
5. Close incident ticket

---

## Useful Commands

```bash
# Set Render API key (from dashboard.render.com → Account → API Keys)
export RENDER_API_KEY=your-key

# Set workspace
render workspace set tea-d63jqusr85hc73b9bun0

# Check all service statuses
render services list -o json

# Stream live logs
render logs -r srv-d63l79hr0fns73boblag --tail

# Restart service
render restart srv-d63l79hr0fns73boblag

# Trigger deploy
render deploys create srv-d63l79hr0fns73boblag
```

---

*Last Updated: February 2026*
