#!/bin/bash

# Render Environment Variables Setup Script
# This script configures your SEO engine environment variables using the Render API

set -e

RENDER_API_TOKEN="${RENDER_API_TOKEN:-}"
if [ -z "$RENDER_API_TOKEN" ]; then
  echo "❌ RENDER_API_TOKEN not set. Export it: export RENDER_API_TOKEN=your-key"
  exit 1
fi
WEB_SERVICE_ID="srv-d6p4l03h46gs73ftvuj0"
SEO_SERVICE_ID="srv-d6p5n5vkijhs73fikui0"

echo "🔧 Setting up Render environment variables for SEO Ranking Engine..."

# Function to set environment variables
set_env_vars() {
    local service_id=$1
    local service_name=$2
    
    echo ""
    echo "📝 Configuring $service_name (ID: $service_id)..."
    
    # Check if service account file exists
    if [ -f "service-account.json" ]; then
        echo "📄 Found service-account.json, reading content..."
        
        # Read and escape the service account JSON
        service_account_content=$(cat service-account.json | jq -c . | sed 's/"/\\"/g')
        
        # Set environment variables
        response=$(curl -s -X PATCH \
            "https://api.render.com/v1/services/$service_id/env-vars" \
            -H "Accept: application/json" \
            -H "Authorization: Bearer $RENDER_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"envVars\": [
                    {
                        \"key\": \"GOOGLE_SERVICE_ACCOUNT_KEY\",
                        \"value\": \"$service_account_content\"
                    },
                    {
                        \"key\": \"GOOGLE_SEARCH_CONSOLE_SITE\",
                        \"value\": \"https://jobhuntin.com\"
                    },
                    {
                        \"key\": \"NODE_ENV\",
                        \"value\": \"production\"
                    },
                    {
                        \"key\": \"PORT\",
                        \"value\": \"10000\"
                    }
                ]
            }")
        
        if echo "$response" | grep -q "envVars"; then
            echo "✅ Environment variables set successfully for $service_name"
        else
            echo "❌ Failed to set environment variables for $service_name"
            echo "Response: $response"
            return 1
        fi
    else
        echo "⚠️  service-account.json not found in current directory"
        echo "Please ensure you have your Google service account JSON file ready"
        
        # Set basic variables without service account
        response=$(curl -s -X PATCH \
            "https://api.render.com/v1/services/$service_id/env-vars" \
            -H "Accept: application/json" \
            -H "Authorization: Bearer $RENDER_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"envVars\": [
                    {
                        \"key\": \"GOOGLE_SEARCH_CONSOLE_SITE\",
                        \"value\": \"https://jobhuntin.com\"
                    },
                    {
                        \"key\": \"NODE_ENV\",
                        \"value\": \"production\"
                    },
                    {
                        \"key\": \"PORT\",
                        \"value\": \"10000\"
                    }
                ]
            }")
        
        echo "✅ Basic environment variables set (you'll need to add GOOGLE_SERVICE_ACCOUNT_KEY manually)"
    fi
}

# Function to get current environment variables
get_current_env_vars() {
    local service_id=$1
    local service_name=$2
    
    echo ""
    echo "📋 Current environment variables for $service_name:"
    
    response=$(curl -s -X GET \
        "https://api.render.com/v1/services/$service_id/env-vars" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer $RENDER_API_TOKEN")
    
    echo "$response" | jq -r '.envVars[] | "  - \(.key): \(.value[0:50])..."' 2>/dev/null || echo "  (No environment variables set)"
}

# Function to create service account template
create_service_account_template() {
    echo ""
    echo "📝 Creating service account template..."
    
    cat > service-account-template.json << 'EOF'
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
}
EOF
    
    echo "✅ Service account template created: service-account-template.json"
    echo "Please replace the placeholder values with your actual Google service account details"
}

# Main function
main() {
    echo "🎯 Render Environment Variables Configuration"
    echo "==========================================="
    echo ""
    echo "This script will configure your SEO Ranking Engine environment variables"
    echo "using your Render API token: $RENDER_API_TOKEN"
    echo ""
    
    # Check if service account file exists
    if [ ! -f "service-account.json" ]; then
        echo "⚠️  service-account.json not found!"
        create_service_account_template
        echo ""
        echo "Please:"
        echo "1. Copy service-account-template.json to service-account.json"
        echo "2. Fill in your actual Google service account details"
        echo "3. Run this script again"
        exit 1
    fi
    
    # Show current environment variables
    get_current_env_vars "$WEB_SERVICE_ID" "Web Service"
    get_current_env_vars "$SEO_SERVICE_ID" "SEO Worker Service"
    
    echo ""
    echo "🚀 Setting new environment variables..."
    
    # Set environment variables for both services
    set_env_vars "$WEB_SERVICE_ID" "Web Service"
    set_env_vars "$SEO_SERVICE_ID" "SEO Worker Service"
    
    echo ""
    echo "✅ Environment variables configuration complete!"
    echo ""
    echo "🔄 Next steps:"
    echo "1. Deploy your services using: ./deploy-to-render.sh"
    echo "2. Monitor deployment with: npm run seo:monitor"
    echo "3. Verify indexing with: npm run seo:verify"
    echo ""
    echo "🔗 Render Dashboard: https://dashboard.render.com"
}

# Handle script interruption
trap 'echo "❌ Configuration interrupted"; exit 1' INT TERM

# Run the configuration
main "$@"