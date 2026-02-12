#!/usr/bin/env python3
"""
Try to create a paid database or check the existing one
"""

import requests
import json

def try_paid_database():
    """Try creating a paid database since free tier is used"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    
    # Database configuration with paid plan
    db_config = {
        "ownerID": "tea-d63jqusr85hc73b9bun0",
        "name": "jobhuntin-postgres-pro",
        "type": "postgres", 
        "region": "oregon",
        "plan": "standard",  # Paid plan
        "version": "16",
        "databaseName": "jobhuntin",
        "user": "jobhuntin_user"
    }
    
    print("=== Trying Paid Database Plan ===")
    print(f"Database name: {db_config['name']}")
    print(f"Plan: {db_config['plan']}")
    print()
    
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post("https://api.render.com/v1/postgres", headers=headers, json=db_config, timeout=30)
        
        if response.status_code == 201:
            db_info = response.json()
            print("✅ Paid database creation initiated!")
            print(f"Database ID: {db_info.get('id')}")
            
            # Wait for it to be live and get connection URL
            import time
            db_id = db_info.get('id')
            
            for i in range(20):  # Wait up to 10 minutes
                time.sleep(30)
                print(f"Checking status... (attempt {i+1}/20)")
                
                status_response = requests.get(f"https://api.render.com/v1/postgres/{db_id}", headers=headers, timeout=10)
                if status_response.status_code == 200:
                    status_info = status_response.json()
                    service_status = status_info.get('status')
                    
                    if service_status == 'live':
                        conn_url = status_info.get('connectionUrl')
                        if conn_url:
                            print(f"✅ Database is live!")
                            print(f"Connection URL: {conn_url}")
                            print()
                            print("=== MIGRATION READY ===")
                            print(f"Run this command:")
                            print(f"python run_migration.py \"{conn_url}\"")
                            return conn_url
                    elif service_status in ['failed', 'suspended']:
                        print(f"❌ Database failed: {service_status}")
                        break
                else:
                    print(f"Status check failed: {status_response.status_code}")
            
            print("⏰ Database still provisioning...")
            
        else:
            print(f"❌ Failed to create paid database: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def manual_instructions():
    """Provide manual creation instructions"""
    print("\n" + "="*60)
    print("MANUAL DATABASE CREATION INSTRUCTIONS")
    print("="*60)
    print()
    print("Since the free tier is already used, you have two options:")
    print()
    print("OPTION 1: Use Existing Database")
    print("1. Go to Render Dashboard: https://dashboard.render.com")
    print("2. Look for any existing PostgreSQL database")
    print("3. Get its connection URL")
    print("4. Run: python run_migration.py <CONNECTION_URL>")
    print()
    print("OPTION 2: Create New Paid Database")
    print("1. Go to Render Dashboard: https://dashboard.render.com")
    print("2. Click 'New' → 'PostgreSQL'")
    print("3. Use these settings:")
    print("   - Name: jobhuntin-postgres")
    print("   - Region: Oregon")
    print("   - Plan: Standard ($7/month)")
    print("   - Database Name: jobhuntin")
    print("   - User: jobhuntin_user")
    print("4. Click 'Create Database'")
    print("5. Wait for live status")
    print("6. Copy connection URL")
    print("7. Run: python run_migration.py <CONNECTION_URL>")
    print()
    print("OPTION 3: Delete and Recreate Free Database")
    print("1. Find existing free database in dashboard")
    print("2. Delete it")
    print("3. Create new free database with name 'jobhuntin-db'")
    print("4. Follow migration steps")

if __name__ == "__main__":
    result = try_paid_database()
    if not result:
        manual_instructions()
