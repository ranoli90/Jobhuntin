# Deployment Emergency Fix

## Current Status
- API: HTTP 503 (Service Unavailable)
- Web: HTTP 503 (Service Unavailable) 
- Admin: HTTP 404 (Not found)
- Git: Clean (all fixes pushed)

## Issue Analysis
HTTP 503 typically means:
1. Service crashed during startup
2. Health check failed
3. Database connection issues
4. Environment variable problems

## Immediate Actions

### 1. Check Render Dashboard
Go to: https://dashboard.render.com/services/jobhuntin-api

Look for:
- Recent deployment logs
- Error messages
- Build failures
- Resource limits

### 2. Check Environment Variables
In Render dashboard, verify these are set correctly:

**Required for API:**
- `PYTHONPATH`: `apps:packages:.`
- `DATABASE_URL`: Your PostgreSQL connection string
- `JWT_SECRET`: Random secret string
- `LLM_API_KEY`: OpenRouter API key
- `env`: `prod`

### 3. Common 503 Fixes

#### Fix A: Database Connection
```bash
# Test database connection locally
DATABASE_URL="your-db-url" python -c "
import asyncpg
import asyncio

async def test():
    try:
        conn = await asyncpg.connect('your-db-url')
        await conn.execute('SELECT 1')
        await conn.close()
        print('Database OK')
    except Exception as e:
        print(f'Database Error: {e}')

asyncio.run(test())
"
```

#### Fix B: Memory/CPU Limits
- In Render dashboard, check service resources
- Try increasing memory allocation
- Check for CPU spikes

#### Fix C: Startup Timeout
- Increase startup timeout in render.yaml:
```yaml
startCommand: timeout 60 uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 2 --log-level info
```

#### Fix D: Health Check Issues
The health check might be failing. Temporarily disable it:
```yaml
# Comment out or remove this line:
healthCheckPath: /health
```

### 4. Emergency Rollback
If nothing works, rollback:

```bash
# Go to previous working commit
git log --oneline -5

# Rollback (choose a working commit)
git checkout 3fc9cd9  # Debug: Simplify CMD to use exec form without shell

# Force push rollback
git push origin main --force

# Monitor deployment
curl -s -o /dev/null -w "%{http_code}" https://sorce-api.onrender.com/health
```

### 5. Manual Health Test
Test if the underlying service is running:

```bash
# Test basic FastAPI app (bypass health check)
curl -s -X GET "https://sorce-api.onrender.com/docs" -w "%{http_code}"

# Test with different endpoints
curl -s -X GET "https://sorce-api.onrender.com/openapi.json" -w "%{http_code}"
```

## Debugging Steps

### 1. Enable Debug Logging
Add to render.yaml temporarily:
```yaml
envVars:
  - key: PYTHONPATH
    value: apps:packages:.
  - key: LOG_LEVEL
    value: DEBUG
```

### 2. Check Build Logs
In Render dashboard:
1. Go to jobhuntin-api service
2. Click "Events" tab
3. Look for red error messages
4. Check build logs for failures

### 3. Test Startup Sequence
```bash
# Test exact startup command locally
PYTHONPATH=apps:packages:. uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2 --log-level debug
```

## Quick Fix Checklist

- [ ] Check Render dashboard for error logs
- [ ] Verify all environment variables
- [ ] Test database connection
- [ ] Check resource limits (memory/CPU)
- [ ] Try rollback if needed
- [ ] Monitor deployment after changes

## Contact Support
If issues persist:
1. Check Render status page: https://status.render.com
2. Review Render documentation: https://render.com/docs
3. Check this troubleshooting guide for updates

## Next Steps
1. Check Render dashboard NOW
2. Look for specific error messages
3. Apply appropriate fix from above
4. Monitor deployment after changes
5. Report back with specific error details
