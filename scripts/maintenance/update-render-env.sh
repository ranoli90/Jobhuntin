#!/bin/bash
# Update Render environment variables for all services
# Requires RENDER_API_KEY in .env or environment (never commit the key)

if [ -z "$RENDER_API_KEY" ]; then
  source .env 2>/dev/null || true
fi
if [ -z "$RENDER_API_KEY" ]; then
  echo "ERROR: Set RENDER_API_KEY in .env or export it"
  exit 1
fi

# API Service ID
API_SERVICE="srv-d63l79hr0fns73boblag"
WEB_SERVICE="srv-d63spbogjchc739akan0"
SEO_SERVICE="srv-d66aadsr85hc73dastfg"

# Stripe Configuration - load from .env (never hardcode)
STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY:-}"
STRIPE_PUBLISHABLE_KEY="${STRIPE_PUBLISHABLE_KEY:-}"
if [ -z "$STRIPE_SECRET_KEY" ] || [ -z "$STRIPE_PUBLISHABLE_KEY" ]; then
  echo "WARN: STRIPE_SECRET_KEY or STRIPE_PUBLISHABLE_KEY not set. Load from .env"
fi

# Function to update env var
update_env_var() {
  local service_id=$1
  local key=$2
  local value=$3
  
  curl -s -X PUT \
    -H "Authorization: Bearer $RENDER_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"key\":\"$key\",\"value\":\"$value\"}" \
    "https://api.render.com/v1/services/$service_id/env-vars/$key"
}

# Function to create env var  
create_env_var() {
  local service_id=$1
  local key=$2
  local value=$3
  
  curl -s -X POST \
    -H "Authorization: Bearer $RENDER_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"key\":\"$key\",\"value\":\"$value\"}" \
    "https://api.render.com/v1/services/$service_id/env-vars"
}

echo "Updating API service env vars..."

# Update Stripe keys for API service (skip if not set)
if [ -n "$STRIPE_SECRET_KEY" ]; then
  create_env_var $API_SERVICE "STRIPE_SECRET_KEY" "$STRIPE_SECRET_KEY"
fi
if [ -n "$STRIPE_PUBLISHABLE_KEY" ]; then
  create_env_var $API_SERVICE "STRIPE_PUBLISHABLE_KEY" "$STRIPE_PUBLISHABLE_KEY"
fi

# Add trial configuration - $10 first month, then $29/month
create_env_var $API_SERVICE "STRIPE_FREE_TRIAL_DAYS" "0"
create_env_var $API_SERVICE "PRO_PROMO_PRICE_CENTS" "1000"  # $10 first month
create_env_var $API_SERVICE "PRO_REGULAR_PRICE_CENTS" "2900"  # $29/month after

# Add CAPTCHA env vars
create_env_var $API_SERVICE "CAPTCHA_PROVIDER" "recaptcha"
create_env_var $API_SERVICE "CAPTCHA_MIN_SCORE" "0.5"

echo "Updating Web service env vars..."

# Add publishable key for web (VITE_ prefix for client-side)
create_env_var $WEB_SERVICE "VITE_STRIPE_PUBLISHABLE_KEY" "$STRIPE_PUBLISHABLE_KEY"

echo "Triggering deploys..."

# Trigger deploys
curl -s -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/$API_SERVICE/deploys"

curl -s -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/$WEB_SERVICE/deploys"

curl -s -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/$SEO_SERVICE/deploys"

echo "Done! Check Render dashboard for deploy status."
