# 🚨 CRITICAL ISSUE IDENTIFIED: API Keys Missing

## Root Cause
The deployment is failing because **required API keys are not configured** in render.yaml:
- ❌ LLM_API_KEY (missing)
- ❌ JWT_SECRET (missing) 
- ❌ CSRF_SECRET (missing)

## Why This Causes HTTP 503
1. **Service starts** but crashes when trying to initialize LLM client
2. **Authentication fails** because JWT_SECRET is not set
3. **CSRF protection fails** because CSRF_SECRET is not set
4. **Service becomes unavailable** (HTTP 503)

## Immediate Fix Required

### Step 1: Get API Keys

#### 1. OpenRouter API Key (LLM_API_KEY)
```
Go to: https://openrouter.ai/keys
1. Sign up or log in
2. Click "Create new key"
3. Copy the API key (starts with "sk-or-v1-")
```

#### 2. Generate JWT Secret
```bash
# Method 1: Using OpenSSL
openssl rand -hex 32

# Method 2: Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

#### 3. Generate CSRF Secret
```bash
# Use same command as JWT secret
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 2: Configure in Render Dashboard

1. **Go to**: https://dashboard.render.com
2. **Select**: jobhuntin-api service
3. **Click**: "Environment" tab
4. **Add these environment variables**:

```
LLM_API_KEY=sk-or-v1-your-openrouter-key-here
JWT_SECRET=your-generated-jwt-secret-here
CSRF_SECRET=your-generated-csrf-secret-here
```

5. **IMPORTANT**: Set all three to `sync: false`
6. **Click**: "Save Changes"

### Step 3: Verify Configuration

After saving, the dashboard should show:
- ✅ LLM_API_KEY: configured (sync: false)
- ✅ JWT_SECRET: configured (sync: false)
- ✅ CSRF_SECRET: configured (sync: false)

### Step 4: Monitor Deployment

The service should automatically redeploy and start working. Monitor:
- Render dashboard logs
- API health: https://sorce-api.onrender.com/health

## Quick Test Commands

### Generate Secrets Now
```bash
# Generate JWT Secret
JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
echo "JWT_SECRET: $JWT_SECRET"

# Generate CSRF Secret  
CSRF_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
echo "CSRF_SECRET: $CSRF_SECRET"

# Generate OpenRouter Key (get from https://openrouter.ai/keys)
echo "Get LLM_API_KEY from: https://openrouter.ai/keys"
```

### Test Configuration Locally
```bash
# Test with your keys
export LLM_API_KEY="your-openrouter-key"
export JWT_SECRET="your-jwt-secret"
export CSRF_SECRET="your-csrf-secret"
PYTHONPATH=apps:packages:. python -c "
from api.main import app
print('✅ API starts successfully!')
"
```

## Services That Need Keys

These services in render.yaml need the API keys:
- jobhuntin-api (main API service)
- sorce-auto-apply-agent (worker service)

## Security Notes

- ✅ All keys set to `sync: false` (prevents Render from storing in git)
- ✅ Use strong random secrets (32-character hex strings)
- ✅ Never commit keys to repository
- ✅ Rotate keys regularly

## Expected Result

After configuration:
- ✅ API service starts successfully
- ✅ HTTP 200 instead of 503
- ✅ All services operational
- ✅ No more syntax errors

## Emergency Rollback

If deployment completely fails:
```bash
git checkout 3fc9cd9  # Working commit before API key changes
git push origin main --force
```

## Support

- Render Dashboard: https://dashboard.render.com
- Service Logs: https://dashboard.render.com/services/jobhuntin-api
- API Documentation: https://sorce-api.onrender.com/docs
