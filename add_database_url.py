#!/usr/bin/env python3
"""
Add DATABASE_URL to Render service using the correct format
"""

import requests
import json

def add_database_url():
    """Add DATABASE_URL to jobhuntin-api service"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    api_service_id = "srv-d63l79hr0fns73boblag"
    
    # From your .env file, the correct format is:
    # postgresql://postgres:ravhuv-gitqec-nixvY4@db.zglovpfwyobbbaaocawz.supabase.co:5432/postgres
    
    # But from the error logs, it's trying to connect to:
    # aws-0-us-east-1.pooler.supabase.com:5432
    
    # Let's use the pooler format which is recommended for production:
    database_url = "postgresql://postgres.zglovpfwyobbbaaocawz:ravhuv-gitqec-nixvY4@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    
    print("=== ADDING DATABASE_URL ===")
    print(f"Service ID: {api_service_id}")
    print(f"DATABASE_URL: {database_url}")
    print()
    
    # Use Render API to add the environment variable
    url = f"https://api.render.com/v1/services/{api_service_id}/env-vars"
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json"
    }
    
    # First, let's try to get current env vars to see the structure
    print("Checking current environment variables...")
    
    get_response = requests.get(url, headers=headers)
    print(f"GET response status: {get_response.status_code}")
    
    if get_response.status_code == 200:
        current_envs = get_response.json()
        print(f"Current env vars count: {len(current_envs)}")
        
        # Check if DATABASE_URL already exists
        existing_db_url = None
        for env_var in current_envs:
            if env_var.get('key') == 'DATABASE_URL':
                existing_db_url = env_var
                break
        
        if existing_db_url:
            print("DATABASE_URL already exists! Updating it...")
            # Update existing
            env_var_id = existing_db_url.get('id')
            update_url = f"https://api.render.com/v1/services/{api_service_id}/env-vars/{env_var_id}"
            update_data = {"value": database_url}
            
            update_response = requests.patch(update_url, headers=headers, json=update_data)
            print(f"UPDATE response status: {update_response.status_code}")
            
            if update_response.status_code == 200:
                print("✅ DATABASE_URL updated successfully!")
            else:
                print(f"❌ Failed to update: {update_response.text}")
        else:
            print("DATABASE_URL not found. Adding new...")
            # Add new
            add_data = {
                "key": "DATABASE_URL",
                "value": database_url
            }
            
            add_response = requests.post(url, headers=headers, json=add_data)
            print(f"ADD response status: {add_response.status_code}")
            
            if add_response.status_code == 200:
                print("✅ DATABASE_URL added successfully!")
            else:
                print(f"❌ Failed to add: {add_response.text}")
    else:
        print(f"❌ Failed to get current env vars: {get_response.text}")
    
    print("\n=== MANUAL INSTRUCTIONS ===")
    print("If the API approach doesn't work, manually add this in Render Dashboard:")
    print("1. Go to https://dashboard.render.com")
    print("2. Navigate to jobhuntin-api service")
    print("3. Click Environment tab")
    print("4. Add Environment Variable:")
    print(f"   Key: DATABASE_URL")
    print(f"   Value: {database_url}")
    print("5. Save and redeploy")

if __name__ == "__main__":
    add_database_url()
