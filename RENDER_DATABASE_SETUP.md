# Render Database Setup

**Database:** Render PostgreSQL (no Supabase)

## Current Database (from Render API)

| Property | Value |
|----------|-------|
| Name | jobhuntin-db |
| ID | dpg-d66ck524d50c73bas62g-a |
| Region | oregon |
| Database | jobhuntin |
| User | jobhuntin_user |
| Host (external) | dpg-d66ck524d50c73bas62g-a.oregon-postgres.render.com:5432 |

**Connection string** is set in `.env` (gitignored). Fetch via API:
```bash
curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/postgres/dpg-d66ck524d50c73bas62g-a/connection-info"
```

## Getting Database Connection Info (Manual)

1. **Render Dashboard**: https://dashboard.render.com
2. Navigate to your PostgreSQL database service (jobhuntin-db)
3. Copy the **Internal Database URL** (for services in same Render account) or **External Database URL** (for local/dev)
4. Set `DATABASE_URL` in your environment:
   ```bash
   export DATABASE_URL="postgresql://user:password@host:port/database?sslmode=require"
   ```

## Render CLI (Optional)

To use the Render CLI for deployments and service management:

```bash
# Install via official script
curl -sL https://render.com/docs/install.sh | sh

# Or download binary from: https://github.com/render-com/cli/releases
```

Then authenticate and list services:

```bash
render login
render services list
render shell <service-name>  # Get env vars including DATABASE_URL
```

## Schema & Migrations

- **Schema**: `infra/postgres/schema.sql`
- **Migrations**: `infra/postgres/migrations.sql`
- **Init script**: `scripts/init_render_db.py`

To initialize a fresh Render database:

```bash
python scripts/init_render_db.py "$DATABASE_URL"
```

## Environment Variables (Render Dashboard)

Set these for `jobhuntin-api` and workers:

| Variable | Required | Notes |
|----------|----------|-------|
| DATABASE_URL | Yes | From Render PostgreSQL service |
| REDIS_URL | Yes (prod) | For token replay protection, session revocation |
| JWT_SECRET | Yes | Generate with `secrets.token_hex(32)` |
| CSRF_SECRET | Yes | Generate with `secrets.token_hex(32)` |
| RESEND_API_KEY | Yes (prod) | For magic link emails |
| API_PUBLIC_URL | Yes | e.g. `https://api.sorce.app` |
