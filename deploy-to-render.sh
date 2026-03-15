#!/bin/bash

# Render Deployment Script for SEO Ranking Engine
# This script deploys your automated SEO system to Render using your API token

set -e

# Configuration - use env vars (never commit keys)
RENDER_API_TOKEN="${RENDER_API_TOKEN:-}"
if [ -z "$RENDER_API_TOKEN" ]; then
  echo "❌ RENDER_API_TOKEN not set. Export it: export RENDER_API_TOKEN=your-key"
  exit 1
fi

# Check dependencies
if ! command -v jq &> /dev/null; then
  echo "❌ jq is not installed. Install it:"
  echo "   macOS: brew install jq"
  echo "   Linux: sudo apt-get install jq"
  exit 1
fi

# Service IDs must be provided via environment variables (never commit to git)
SERVICE_ID_WEB="${SERVICE_ID_WEB:-}"
SERVICE_ID_API="${SERVICE_ID_API:-}"
SERVICE_ID_SEO="${SERVICE_ID_SEO:-}"

if [ -z "$SERVICE_ID_WEB" ] || [ -z "$SERVICE_ID_API" ] || [ -z "$SERVICE_ID_SEO" ]; then
  echo "❌ Service IDs not set. Export them:"
  echo "   export SERVICE_ID_WEB=srv-xxx"
  echo "   export SERVICE_ID_API=srv-xxx"
  echo "   export SERVICE_ID_SEO=srv-xxx"
  exit 1
fi

echo "🚀 Starting Render deployment for SEO Ranking Engine..."

# Function to trigger deployment
trigger_deployment() {
    local service_id=$1
    local service_name=$2
    
    echo "📦 Deploying $service_name..."
    
     response=$(curl -s -X POST \
         "https://api.render.com/v1/services/$service_id/deploys" \
         -H "Accept: application/json" \
         -H "Authorization: Bearer $RENDER_API_TOKEN" \
         -d '{"clearCache": "clear"}')
    
    if echo "$response" | grep -q "deploy"; then
        echo "✅ $service_name deployment triggered successfully"
        return 0
    else
        echo "❌ $service_name deployment failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to check deployment status
check_deployment_status() {
    local service_id=$1
    local service_name=$2
    
    echo "🔍 Checking $service_name deployment status..."
    
    response=$(curl -s -X GET \
        "https://api.render.com/v1/services/$service_id/deploys" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer $RENDER_API_TOKEN")
    
    status=$(echo "$response" | jq -r '.[0].status' 2>/dev/null || echo "unknown")
    
    echo "📊 $service_name deployment status: $status"
    
    case "$status" in
        "live")
            echo "🎉 $service_name is live and running!"
            return 0
            ;;
        "build_in_progress"|"update_in_progress")
            echo "⏳ $service_name is still building..."
            return 1
            ;;
        "build_failed"|"update_failed")
            echo "💥 $service_name deployment failed!"
            return 1
            ;;
        *)
            echo "❓ $service_name status: $status"
            return 1
            ;;
    esac
}

# Function to set environment variables
set_environment_variables() {
    local service_id=$1
    local service_name=$2

    echo "🔧 Setting environment variables for $service_name..."

    # SECURITY: Google service account key must be set manually in Render dashboard
    # Never read from local files to prevent secret exposure in git history
    echo "⚠️  GOOGLE_SERVICE_ACCOUNT_KEY must be set manually in Render dashboard"
    echo "   Do not use service-account.json files in this repo"
}

# Main deployment process
main() {
    echo "🎯 Render SEO Engine Deployment"
    echo "================================"
    
    # Check if we're in the right directory
    if [ ! -f "apps/web/package.json" ]; then
        echo "❌ Error: Not in the correct project directory"
        echo "Please run this script from the project root"
        exit 1
    fi
    
    # Set environment variables first
    echo ""
    set_environment_variables "$SERVICE_ID_WEB" "Web Service"
    echo ""
    set_environment_variables "$SERVICE_ID_SEO" "SEO Worker Service"
    
# Trigger deployments
echo ""
trigger_deployment "$SERVICE_ID_WEB" "Web Service"
echo ""
trigger_deployment "$SERVICE_ID_API" "API Service"
echo ""
trigger_deployment "$SERVICE_ID_SEO" "SEO Worker Service"
    
    # Wait and check status
    echo ""
    echo "⏳ Waiting 30 seconds for deployments to start..."
    sleep 30
    
    # Check deployment status
    max_attempts=10
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo ""
        echo "🔍 Deployment check attempt $attempt/$max_attempts"
        
        web_status=0
        seo_status=0
        
        check_deployment_status "$SERVICE_ID_WEB" "Web Service" || web_status=1
        check_deployment_status "$SERVICE_ID_SEO" "SEO Worker Service" || seo_status=1
        
        if [ $web_status -eq 0 ] && [ $seo_status -eq 0 ]; then
            echo ""
            echo "🎉 ALL DEPLOYMENTS SUCCESSFUL!"
            echo "🚀 Your SEO Ranking Engine is now live!"
            echo ""
            echo "📊 Next steps:"
            echo "   1. Check deployment logs in Render dashboard"
            echo "   2. Monitor with: npm run seo:monitor"
            echo "   3. Verify with: npm run seo:verify"
            echo "   4. Check Google Search Console for indexing"
            exit 0
        fi
        
        echo ""
        echo "⏳ Waiting 30 seconds before next check..."
        sleep 30
        attempt=$((attempt + 1))
    done
    
    echo ""
    echo "⚠️  Deployment verification timeout"
    echo "Please check Render dashboard manually for deployment status"
    exit 1
}

# Handle script interruption
trap 'echo "❌ Deployment interrupted"; exit 1' INT TERM

# Run the deployment
main "$@"