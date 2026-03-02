# Render & Stripe Setup Guide

Configure Render services and Stripe for production deployment.

## Security Notice

**Never commit API keys or secrets to the repository.** Use environment variables in Render's dashboard or `.env` (local only, gitignored).

If credentials have been exposed (e.g. shared in chat, committed by mistake), **rotate them immediately** in the respective dashboards.

---

## Render Setup

### 1. Environment Variables (Render Dashboard)

Add these to each Render service (API, Worker, Web):

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (SSL required) | `postgresql://user:pass@host:5432/db?sslmode=require` |
| `REDIS_URL` | Redis for rate limiting, token replay prevention | `redis://red-xxx:6379` |
| `ENV` | `local`, `staging`, or `prod` | `prod` |
| `JWT_SECRET` | JWT signing secret | Generate with `python scripts/generate_secrets.py` |
| `CSRF_SECRET` | CSRF protection | Generate with `python scripts/generate_secrets.py` |
| `APP_BASE_URL` | Public URL of the web app | `https://jobhuntin.com` |
| `API_PUBLIC_URL` | Public URL of the API (for magic-link httpOnly cookies) | `https://sorce-api.onrender.com` |

### 2. Render API Key (Optional)

For deployment automation or health checks, create an API key at [dashboard.render.com](https://dashboard.render.com) → Account Settings → API Keys.

**Store in GitHub Secrets** (not in code):
- `RENDER_API_TOKEN` – for CI/CD workflows

### 3. PostgreSQL SSL

The app requires `sslmode=require` on database connections. Render PostgreSQL provides SSL by default.

### 4. Redis

Required in production for:
- Magic-link token replay prevention
- Distributed rate limiting

Create a Redis instance in Render and set `REDIS_URL`. The API will fail startup if `REDIS_URL` is missing in prod.

---

## Stripe Setup

### 1. API Keys

Create keys at [dashboard.stripe.com](https://dashboard.stripe.com) → Developers → API keys.

| Variable | Description | Where to set |
|----------|-------------|--------------|
| `STRIPE_SECRET_KEY` | Server-side key (starts with `sk_live_` or `sk_test_`) | Render API service |
| `STRIPE_PUBLISHABLE_KEY` | Client-side key (starts with `pk_live_` or `pk_test_`) | Web app build / env |
| `STRIPE_WEBHOOK_SECRET` | Webhook signing secret (starts with `whsec_`) | Render API service |

### 2. Webhook Configuration

1. Stripe Dashboard → Developers → Webhooks → Add endpoint
2. URL: `https://your-api.onrender.com/webhooks/stripe` (or your API base)
3. Events: `checkout.session.completed`, `customer.subscription.*`, `invoice.*`, etc.
4. Copy the **Signing secret** → set as `STRIPE_WEBHOOK_SECRET`

### 3. Products & Prices

Ensure Stripe products and price IDs match `BILLING_TIERS` in `apps/web/src/pages/Dashboard.tsx` and `apps/api/billing.py`.

### 4. `.env.example` Reference

```bash
# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

---

## Verification Checklist

- [ ] `DATABASE_URL` connects (run migrations)
- [ ] `REDIS_URL` set in prod
- [ ] `API_PUBLIC_URL` matches your API's public URL
- [ ] Stripe webhook receives events (check Stripe Dashboard → Webhooks → Logs)
- [ ] Magic links work (email → verify-magic → cookie set → redirect)
- [ ] Billing/checkout flow completes successfully
