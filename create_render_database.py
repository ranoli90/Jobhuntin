#!/usr/bin/env python3
"""
Create Render PostgreSQL database using API
"""

import requests
import json
import time

def create_render_database():
    """Create a new PostgreSQL database on Render"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    
    # Database configuration with correct owner ID
    db_config = {
        "ownerID": "tea-d63jqusr85hc73b9bun0",
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
    
    # Create the database
    url = "https://api.render.com/v1/services"
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json"
    }
    
    print("Creating database...")
    response = requests.post(url, headers=headers, json=db_config)
    
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
            status_response = requests.get(f"{url}/{service_id}", headers=headers)
            if status_response.status_code == 200:
                status_info = status_response.json()
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
                        print("2. Update your jobhuntin-api service environment")
                        print("3. Remove Supabase DATABASE_URLh entry")
                        print("4. Redeploy the service")
                        return conn_url
                    break
                elif service_status in ['failed', 'suspended']:
                    print(f"❌ Database creation failed: {service_status}")
                    break
                    
            time.sleep(10)
        else:
            print("⏰ Database is still provisioning. Check Render dashboard for connection details.")
            
    else:
        print(f"❌ Failed to create database: {response.status_code}")
        print(f"Response: {response.text}")
        
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
        print("6. Update DATABASE_URL in your jobhuntin-api service")

if __name__ == "__main__":
    create_render_database()
