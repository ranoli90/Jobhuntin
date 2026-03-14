# Secret Rotation Runbook

This document describes how to rotate all application secrets. Secrets should be
rotated **immediately** if there is any indication of compromise, and on a
regular schedule (quarterly recommended).

---

## Quick Reference

| Secret | Where to Rotate | Env Var |
|--------|----------------|---------|
| Database password | Render Dashboard → PostgreSQL | `DATABASE_URL` |
| JWT signing key | Generate locally, set in Render | `JWT_SECRET` |
| CSRF secret | Generate locally, set in Render | `CSRF_SECRET` |
| Webhook signing | Generate locally, set in Render | `WEBHOOK_SIGNING_SECRET` |
| SSO session secret | Generate locally, set in Render | `SSO_SESSION_SECRET` |
| Render API token | Render Dashboard → Account → API Keys | `RENDER_API_TOKEN` |
| Stripe webhook | Stripe Dashboard → Webhooks | `STRIPE_WEBHOOK_SECRET` |
| Resend API key | Resend Dashboard → API Keys | `RESEND_API_KEY` |
| LLM API key | OpenRouter Dashboard → API Keys | `LLM_API_KEY` |

---

## Step-by-Step Rotation

### 1. Generate New Secrets Locally

```bash
# JWT_SECRET (64-char hex)
python -c "import secrets; print(secrets.token_hex(32))"

# CSRF_SECRET (64-char hex)
python -c "import secrets; print(secrets.token_hex(32))"

# WEBHOOK_SIGNING_SECRET (64-char hex)
python -c "import secrets; print(secrets.token_hex(32))"

# SSO_SESSION_SECRET (64-char hex)
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Rotate Database Password

1. Go to **Render Dashboard** → your PostgreSQL service
2. Click **Info** → find the connection details
3. Use Render's password rotation feature (or create a new database user)
4. Update `DATABASE_URL` in **all services** that reference it (API, Worker)
5. Redeploy all services

> **Warning:** Rotating the DB password causes a brief downtime. Plan for a
> maintenance window or use a blue-green approach with a new DB user.

### 3. Rotate Render API Token

1. Go to **dashboard.render.com** → **Account Settings** → **API Keys**
2. Revoke the old token
3. Create a new token
4. Update `RENDER_API_TOKEN` in any CI/CD pipelines or scripts
5. **Never commit this token to version control**

### 4. Update Render Environment Variables

For each service (API, Worker):

1. Go to **Render Dashboard** → select the service
2. Click **Environment** → **Edit**
3. Update each rotated secret
4. Click **Save** (this triggers a redeploy)

### 5. Verify After Rotation

```bash
# Test API health
curl https://sorce-api.onrender.com/health

# Test auth flow (request a magic link)
curl -X POST https://sorce-api.onrender.com/auth/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Verify JWT tokens still work (generate a test token with new secret)
python -c "
import jwt, uuid
token = jwt.encode(
    {'sub': str(uuid.uuid4()), 'aud': 'authenticated', 'jti': str(uuid.uuid4())},
    '<NEW_JWT_SECRET>',
    algorithm='HS256'
)
print(token)
"
```

### 6. Invalidate Old Sessions

After rotating `JWT_SECRET`, all existing JWTs become invalid. Users will need
to sign in again. If you need a graceful migration:

1. Keep the old secret as `JWT_SECRET_OLD` temporarily
2. Update token validation to try both secrets
3. After 24-48 hours, remove the old secret

---

## Automated Rotation (Future)

Consider implementing:
- AWS Secrets Manager or HashiCorp Vault for secret storage
- Automated rotation schedules with alerts
- Secret scanning in CI/CD (e.g., `detect-secrets`, `trufflehog`)

---

## Emergency Rotation Checklist

If secrets are compromised:

- [ ] Rotate all secrets listed above (assume all are compromised)
- [ ] Revoke Render API token immediately
- [ ] Check Render audit logs for unauthorized access
- [ ] Check database access logs for unauthorized queries
- [ ] Review git history for when secrets were exposed
- [ ] Run `git filter-branch` or BFG Repo Cleaner to purge secrets from history
- [ ] Notify affected users if PII may have been accessed
- [ ] Document the incident and timeline
