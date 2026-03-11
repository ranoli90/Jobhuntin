#!/bin/bash
# Update Render environment variables for all services
# Requires RENDER_API_KEY in .env or environment (never commit the key)
# Service IDs: override via API_SERVICE_ID, WEB_SERVICE_ID, SEO_SERVICE_ID env vars

set -euo pipefail

if [ -z "${RENDER_API_KEY:-}" ]; then
  source .env 2>/dev/null || true
fi
if [ -z "${RENDER_API_KEY:-}" ]; then
  echo "ERROR: Set RENDER_API_KEY in .env or export it"
  exit 1
fi

API_SERVICE="${API_SERVICE_ID:-srv-d63l79hr0fns73boblag}"
WEB_SERVICE="${WEB_SERVICE_ID:-srv-d63spbogjchc739akan0}"
SEO_SERVICE="${SEO_SERVICE_ID:-srv-d66aadsr85hc73dastfg}"

# Stripe Configuration - load from .env (never hardcode)
STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY:-}"
STRIPE_PUBLISHABLE_KEY="${STRIPE_PUBLISHABLE_KEY:-}"
if [ -z "$STRIPE_SECRET_KEY" ] || [ -z "$STRIPE_PUBLISHABLE_KEY" ]; then
  echo "WARN: STRIPE_SECRET_KEY or STRIPE_PUBLISHABLE_KEY not set. Load from .env"
fi

# Create env var using Python for safe JSON encoding (avoids shell injection)
create_env_var() {
  local service_id=$1
  local key=$2
  local value=$3
  local json
  json=$(python3 -c "import json,sys; json.dump({'key':sys.argv[1],'value':sys.argv[2]}, sys.stdout)" "$key" "$value")
  if ! curl -sf -X POST \
    -H "Authorization: Bearer $RENDER_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$json" \
    "https://api.render.com/v1/services/${service_id}/env-vars"; then
    echo "WARN: curl failed for $key"
    return 1
  fi
  return 0
}

echo "Updating API service env vars..."

# Update Stripe keys for API service (skip if not set)
if [ -n "${STRIPE_SECRET_KEY:-}" ]; then
  create_env_var "$API_SERVICE" "STRIPE_SECRET_KEY" "$STRIPE_SECRET_KEY"
fi
if [ -n "${STRIPE_PUBLISHABLE_KEY:-}" ]; then
  create_env_var "$API_SERVICE" "STRIPE_PUBLISHABLE_KEY" "$STRIPE_PUBLISHABLE_KEY"
fi

# Add trial configuration - $10 first month, then $29/month
create_env_var "$API_SERVICE" "STRIPE_FREE_TRIAL_DAYS" "0"
create_env_var "$API_SERVICE" "PRO_PROMO_PRICE_CENTS" "1000"
create_env_var "$API_SERVICE" "PRO_REGULAR_PRICE_CENTS" "2900"

# Add CAPTCHA env vars
create_env_var "$API_SERVICE" "CAPTCHA_PROVIDER" "recaptcha"
create_env_var "$API_SERVICE" "CAPTCHA_MIN_SCORE" "0.5"

echo "Updating Web service env vars..."

if [ -n "${STRIPE_PUBLISHABLE_KEY:-}" ]; then
  create_env_var "$WEB_SERVICE" "VITE_STRIPE_PUBLISHABLE_KEY" "$STRIPE_PUBLISHABLE_KEY"
fi

echo "Triggering deploys..."

curl -sf -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/${API_SERVICE}/deploys" || echo "WARN: API deploy trigger failed"
curl -sf -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/${WEB_SERVICE}/deploys" || echo "WARN: Web deploy trigger failed"
curl -sf -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/${SEO_SERVICE}/deploys" || echo "WARN: SEO deploy trigger failed"

echo "Done! Check Render dashboard for deploy status."
