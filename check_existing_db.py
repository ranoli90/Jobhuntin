#!/usr/bin/env python3
"""
Check existing jobhuntin-db database and get connection details
"""

import requests
import json

def check_existing_database():
    """Check if jobhuntin-db exists and get connection details"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    
    print("=== Checking Existing Database ===")
    
    # Get all services to find the database
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("https://api.render.com/v1/services", headers=headers, timeout=30)
        
        if response.status_code == 200:
            services = response.json()
            print(f"Found {len(services)} services")
            
            # Look for jobhuntin-db
            database_service = None
            for service in services:
                svc = service.get('service', {})
                if svc.get('name') == 'jobhuntin-db':
                    database_service = svc
                    break
            
            if database_service:
                print("✅ Found jobhuntin-db!")
                print(f"Service ID: {database_service.get('id')}")
                print(f"Status: {database_service.get('status')}")
                print(f"Type: {database_service.get('type')}")
                
                # Check if it's live
                if database_service.get('status') == 'live':
                    # Get connection details
                    conn_url = database_service.get('connectionUrl')
                    if conn_url:
                        print(f"Connection URL: {conn_url}")
                        print()
                        print("=== MIGRATION READY ===")
                        print(f"Run this command:")
                        print(f"python run_migration.py \"{conn_url}\"")
                        return conn_url
                    else:
                        print("❌ Connection URL not found in service info")
                else:
                    print(f"⏰ Database status: {database_service.get('status')}")
                    print("Waiting for database to be live...")
                    
                    # Wait and check again
                    import time
                    service_id = database_service.get('id')
                    
                    for i in range(10):  # Check for up to ~5 minutes
                        time.sleep(30)
                        print(f"Checking status... (attempt {i+1}/10)")
                        
                        status_response = requests.get(f"https://api.render.com/v1/services/{service_id}", headers=headers)
                        if status_response.status_code == 200:
                            status_info = status_response.json()
                            service_status = status_info.get('service', {}).get('status')
                            
                            if service_status == 'live':
                                conn_url = status_info.get('service', {}).get('connectionUrl')
                                if conn_url:
                                    print(f"✅ Database is now live!")
                                    print(f"Connection URL: {conn_url}")
                                    print()
                                    print("=== MIGRATION READY ===")
                                    print(f"Run this command:")
                                    print(f"python run_migration.py \"{conn_url}\"")
                                    return conn_url
                            elif service_status in ['failed', 'suspended']:
                                print(f"❌ Database failed with status: {service_status}")
                                break
                        else:
                            print(f"Failed to check status: {status_response.status_code}")
                    
                    print("⏰ Database still provisioning. Check Render dashboard manually.")
            else:
                print("❌ jobhuntin-db not found in services")
                print("Available services:")
                for service in services:
                    svc = service.get('service', {})
                    print(f"  - {svc.get('name')} ({svc.get('type')})")
        else:
            print(f"❌ Failed to get services: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    check_existing_database()
