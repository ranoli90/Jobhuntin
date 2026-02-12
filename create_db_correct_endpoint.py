#!/usr/bin/env python3
"""
Create Render PostgreSQL database using correct database endpoint
"""

import requests
import json
import time

def create_render_database():
    """Create a new PostgreSQL database on Render using correct endpoint"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    
    # Database configuration with correct owner ID
    db_config = {
        "ownerID": "tea-d63jqusr85hc73b9bun0",
        "name": "jobhuntin-postgres",
        "type": "postgres", 
        "region": "oregon",
        "plan": "free",
        "version": "16",  # PostgreSQL version
        "databaseName": "jobhuntin",
        "user": "jobhuntin_user"
    }
    
    print("=== Creating Render PostgreSQL Database ===")
    print(f"Database name: {db_config['name']}")
    print(f"Region: {db_config['region']}")
    print(f"Plan: {db_config['plan']}")
    print()
    
    # Try different endpoints for databases
    endpoints = [
        "https://api.render.com/v1/databases",
        "https://api.render.com/v1/postgres", 
        "https://api.render.com/v1/services"  # fallback
    ]
    
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json"
    }
    
    for endpoint in endpoints:
        print(f"Trying endpoint: {endpoint}")
        
        try:
            response = requests.post(endpoint, headers=headers, json=db_config, timeout=30)
            
            if response.status_code == 201:
                db_info = response.json()
                print("✅ Database creation initiated!")
                print(f"Service ID: {db_info.get('id')}")
                print(f"Name: {db_info.get('name')}")
                print()
                
                # Wait for database to be ready
                service_id = db_info.get('id')
                print("Waiting for database to be ready...")
                
                for i in range(30):  # Wait up to 5 minutes
                    try:
                        status_response = requests.get(f"{endpoint}/{service_id}", headers=headers)
                        if status_response.status_code == 200:
                            status_info = status_response.json()
                            service_status = status_info.get('status', 'unknown')
                            print(f"Status: {service_status}")
                            
                            if service_status == 'live':
                                print("✅ Database is ready!")
                                
                                # Get connection details
                                conn_url = status_info.get('connectionUrl') or status_info.get('database', {}).get('connectionUrl')
                                if conn_url:
                                    print(f"Connection URL: {conn_url}")
                                    print()
                                    print("=== MIGRATION READY ===")
                                    print(f"Run this command:")
                                    print(f"python run_migration.py \"{conn_url}\"")
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
                    
                break
            else:
                print(f"❌ Failed with {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error with {endpoint}: {e}")
        
        print()
    
    print("=== MANUAL CREATION INSTRUCTIONS ===")
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
