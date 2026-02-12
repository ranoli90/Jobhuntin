#!/usr/bin/env python3
"""
Find all databases in your Render account
"""

import requests
import json

def find_all_databases():
    """Find all databases in the account"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    
    print("=== Finding All Databases ===")
    
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get all services
        response = requests.get("https://api.render.com/v1/services", headers=headers, timeout=30)
        
        if response.status_code == 200:
            services = response.json()
            print(f"Checking {len(services)} services for databases...")
            
            databases = []
            for service in services:
                svc = service.get('service', {})
                service_type = svc.get('type', '').lower()
                
                # Check if it's a database service
                if 'postgres' in service_type or 'database' in service_type:
                    databases.append(svc)
                # Also check the service name for database indicators
                name = svc.get('name', '').lower()
                if 'db' in name or 'postgres' in name or 'database' in name:
                    databases.append(svc)
            
            if databases:
                print(f"Found {len(databases)} database services:")
                for db in databases:
                    print(f"\n📊 {db.get('name')}")
                    print(f"   ID: {db.get('id')}")
                    print(f"   Type: {db.get('type')}")
                    print(f"   Status: {db.get('status')}")
                    print(f"   Region: {db.get('region')}")
                    
                    # Get connection URL if available
                    conn_url = db.get('connectionUrl')
                    if conn_url:
                        print(f"   🔗 Connection: {conn_url[:50]}...")
                    else:
                        print("   🔗 Connection: Not available yet")
            else:
                print("❌ No database services found")
                
                # Let's also check if there are any databases by trying the postgres endpoint
                print("\nTrying to list databases via postgres endpoint...")
                try:
                    postgres_response = requests.get("https://api.render.com/v1/postgres", headers=headers, timeout=30)
                    if postgres_response.status_code == 200:
                        postgres_dbs = postgres_response.json()
                        print(f"Found {len(postgres_dbs)} PostgreSQL databases:")
                        for db in postgres_dbs:
                            print(f"\n📊 {db.get('name')}")
                            print(f"   ID: {db.get('id')}")
                            print(f"   Status: {db.get('status')}")
                            conn_url = db.get('connectionUrl')
                            if conn_url:
                                print(f"   🔗 Connection: {conn_url[:50]}...")
                    else:
                        print(f"Postgres endpoint failed: {postgres_response.status_code}")
                except Exception as e:
                    print(f"Error checking postgres endpoint: {e}")
        else:
            print(f"❌ Failed to get services: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_all_databases()
