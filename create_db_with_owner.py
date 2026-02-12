#!/usr/bin/env python3
"""
Get owner ID from existing services and create database
"""

import json
import urllib.request
import time

def get_owner_from_existing_service():
    """Get owner ID from one of your existing services"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Accept": "application/json"
    }
    
    print("Checking existing services to find owner ID...")
    
    try:
        req = urllib.request.Request("https://api.render.com/v1/services", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            services = json.loads(response.read().decode())
            
            if services:
                # Get the first service to extract owner info
                first_service = services[0]['service']
                owner_id = first_service.get('owner', {}).get('id')
                
                if owner_id:
                    print(f"✅ Found owner ID: {owner_id}")
                    return owner_id
                else:
                    print("❌ No owner ID found in service")
                    return None
            else:
                print("❌ No services found")
                return None
                
    except Exception as e:
        print(f"❌ Error getting services: {e}")
        return None

def create_database_with_owner(owner_id):
    """Create database with the correct owner ID"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    
    # Database configuration with correct owner ID
    db_config = {
        "ownerID": owner_id,
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
    
    print(f"Creating database with owner ID: {owner_id}")
    
    url = "https://api.render.com/v1/services"
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    json_data = json.dumps(db_config).encode('utf-8')
    
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
                    
            else:
                print(f"❌ Failed to create database: {response.status}")
                print(f"Response: {response.read().decode()}")
                return None
                
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return None

def main():
    owner_id = get_owner_from_existing_service()
    
    if owner_id:
        conn_url = create_database_with_owner(owner_id)
        
        if conn_url:
            print(f"\n🎉 Database created successfully!")
            print(f"🔗 Connection URL: {conn_url}")
        else:
            print(f"\n❌ Database creation failed")
    else:
        print(f"\n❌ Could not get owner ID")
        print("Please create the database manually at: https://dashboard.render.com")

if __name__ == "__main__":
    main()
