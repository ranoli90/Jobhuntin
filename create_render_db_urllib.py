#!/usr/bin/env python3
"""
Create Render PostgreSQL database using urllib (like working scripts)
"""

import json
import urllib.request
import time

def create_render_database():
    """Create a new PostgreSQL database on Render using urllib"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    
    # Database configuration
    db_config = {
        "name": "jobhuntin-db",
        "type": "psql", 
        "region": "oregon",
        "plan": "free",
        "databaseName": "jobhuntin",
        "user": "jobhuntin_user",
        "ipAllowList": [
            {
                "source": "0.0.0.0/0",
                "description": "Allow all IPs for development"
            }
        ]
    }
    
    print("=== Creating Render PostgreSQL Database ===")
    print(f"Database name: {db_config['name']}")
    print(f"Region: {db_config['region']}")
    print(f"Plan: {db_config['plan']}")
    print()
    
    # Create the database using urllib (like working scripts)
    url = "https://api.render.com/v1/services"
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    json_data = json.dumps(db_config).encode('utf-8')
    
    print("Creating database...")
    try:
        req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 201:
                db_info = json.loads(response.read().decode())
                print("✅ Database creation initiated!")
                print(f"Service ID: {db_info.get('id')}")
                print(f"Name: {db_info.get('name')}")
                print()
                
                # Wait for database to be ready
                service_id = db_info.get('id')
                print("Waiting for database to be ready...")
                
                for i in range(30):  # Wait up to 5 minutes
                    try:
                        status_req = urllib.request.Request(f"{url}/{service_id}", headers=headers)
                        with urllib.request.urlopen(status_req, timeout=30) as status_response:
                            if status_response.status == 200:
                                status_info = json.loads(status_response.read().decode())
                                service_status = status_info.get('status', 'unknown')
                                print(f"Status: {service_status}")
                                
                                if service_status == 'live':
                                    print("✅ Database is ready!")
                                    
                                    # Get connection details
                                    conn_url = status_info.get('connectionUrl')
                                    if conn_url:
                                        print(f"Connection URL: {conn_url}")
                                        print()
                                        print("=== NEXT STEPS ===")
                                        print("1. Copy this DATABASE_URL:")
                                        print(f"   {conn_url}")
                                        print("2. Run migration: python run_migration.py <DATABASE_URL>")
                                        print("3. Update your jobhuntin-api service environment")
                                        return conn_url
                                    break
                                elif service_status in ['failed', 'suspended']:
                                    print(f"❌ Database creation failed: {service_status}")
                                    break
                                    
                        time.sleep(10)
                    except Exception as e:
                        print(f"Error checking status: {e}")
                        time.sleep(10)
                else:
                    print("⏰ Database is still provisioning. Check Render dashboard for connection details.")
                    
            else:
                print(f"❌ Failed to create database: {response.status}")
                print(f"Response: {response.read().decode()}")
                
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        
        print("\n=== MANUAL CREATION INSTRUCTIONS ===")
        print("1. Go to Render Dashboard: https://dashboard.render.com")
        print("2. Click 'New' → 'PostgreSQL'")
        print("3. Enter:")
        print("   - Name: jobhuntin-db")
        print("   - Region: Oregon (same as your app)")
        print("   - Plan: Free")
        print("   - Database Name: jobhuntin")
        print("   - User: jobhuntin_user")
        print("4. Click 'Create Database'")
        print("5. Wait for it to be live, then copy the connection URL")
        print("6. Run: python run_migration.py <DATABASE_URL>")

if __name__ == "__main__":
    create_render_database()
