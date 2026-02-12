#!/usr/bin/env python3
"""
Setup proper DATABASE_URL for Render using API
"""

import requests
import json
import os

def setup_database_url():
    """Setup DATABASE_URL using Render API"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    api_service_id = "srv-d63l79hr0fns73boblag"
    
    # Construct the correct DATABASE_URL using Supabase details
    # From the error logs, we can see the app is trying to connect to:
    # aws-0-us-east-1.pooler.supabase.com:5432
    
    # Using the provided Supabase credentials
    supabase_project_id = "zglovpfwyobbbaaocawz"
    database_name = "postgres"
    
    # The connection string should use the pooler with proper credentials
    # Format: postgresql://postgres.[project_id]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
    database_url = f"postgresql://postgres.{supabase_project_id}:ravhuv-gitqec-nixvY4@aws-0-us-east-1.pooler.supabase.com:5432/{database_name}"
    
    print("=== DATABASE URL SETUP ===")
    print(f"Service ID: {api_service_id}")
    print(f"Database URL: {database_url}")
    print()
    
    # Prepare the API request
    url = f"https://api.render.com/v1/services/{api_service_id}/env-vars"
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "envVars": [
            {
                "key": "DATABASE_URL",
                "value": database_url
            }
        ]
    }
    
    print("Setting DATABASE_URL via Render API...")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print("✅ DATABASE_URL set successfully!")
            print("Response:", response.json())
        else:
            print(f"❌ Failed to set DATABASE_URL: {response.status_code}")
            print("Response:", response.text)
            
            # Provide manual instructions
            print("\n=== MANUAL SETUP INSTRUCTIONS ===")
            print("1. Go to Render Dashboard: https://dashboard.render.com")
            print("2. Navigate to 'jobhuntin-api' service")
            print("3. Click on 'Environment' tab")
            print("4. Click 'Add Environment Variable'")
            print("5. Enter:")
            print(f"   Name: DATABASE_URL")
            print(f"   Value: {database_url}")
            print("6. Click 'Save Changes'")
            print("7. Trigger a new deployment")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n=== MANUAL SETUP INSTRUCTIONS ===")
        print("1. Go to Render Dashboard: https://dashboard.render.com")
        print("2. Navigate to 'jobhuntin-api' service")
        print("3. Click on 'Environment' tab")
        print("4. Click 'Add Environment Variable'")
        print("5. Enter:")
        print(f"   Name: DATABASE_URL")
        print(f"   Value: {database_url}")
        print("6. Click 'Save Changes'")
        print("7. Trigger a new deployment")

if __name__ == "__main__":
    setup_database_url()
