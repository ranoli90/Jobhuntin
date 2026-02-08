import os
import httpx
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use the provided CLI token
RENDER_API_KEY = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"

# Render API base URL
RENDER_API_BASE = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json"
}

def get_services():
    """Fetch all Render services"""
    try:
        response = httpx.get(f"{RENDER_API_BASE}/services", headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error fetching services: {e.response.status_code}")
        print(f"Response: {e.response.text[:200]}")
        return []
    except Exception as e:
        print(f"Error fetching services: {str(e)}")
        return []

def get_service_env(service_id):
    """Get environment variables for a service"""
    try:
        response = httpx.get(f"{RENDER_API_BASE}/services/{service_id}/env-vars", 
                           headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting env for service {service_id}: {str(e)}")
        return []

def get_databases():
    """Fetch all databases - Render doesn't have a direct endpoint"""
    # Render doesn't have a /databases endpoint
    # Instead, we'll find databases by checking service configurations
    print("Render API doesn't have a direct databases endpoint. Checking service configurations...")
    
    services = get_services()
    databases = []
    
    for service in services:
        svc = service.get('service', {})
        if 'database' in svc.get('type', '').lower():
            databases.append(svc)
            
    return databases

def delete_database(service_id):
    """Delete a database service"""
    try:
        response = httpx.delete(f"{RENDER_API_BASE}/services/{service_id}", headers=headers)
        return response.status_code == 204
    except Exception as e:
        print(f"Error deleting database service {service_id}: {str(e)}")
        return False

def main():
    try:
        # 1. Get services
        services = get_services()
        
        if not services:
            print("No services found. Exiting.")
            return
            
        # 2. Verify sorce-api and sorce-web environment variables
        for service in services:
            svc = service.get('service', {})
            name = svc.get('name', '')
            service_id = svc.get('id', '')
            
            if not service_id:
                continue
                
            if name in ["sorce-api", "sorce-web"]:
                env_vars = get_service_env(service_id)
                print(f"\n--- Environment for {name} ({service_id}) ---")
                for var in env_vars:
                    env_var = var.get('envVar', {})
                    key = env_var.get('key', 'Unknown')
                    print(f"- {key}")
        
        # 3. Check and delete sorce-db if not needed
        databases = get_databases()
        sorce_db = None
        
        for db in databases:
            db_name = db.get('name', '')
            if "sorce-db" in db_name.lower():
                sorce_db = db
                break
        
        if sorce_db:
            db_id = sorce_db['id']
            db_name = sorce_db['name']
            print(f"\nFound database service: {db_name} (ID: {db_id})")
            
            # Check if any services reference this database
            db_in_use = False
            for service in services:
                svc = service.get('service', {})
                if svc.get('databaseId') == db_id:
                    db_in_use = True
                    print(f"Database is used by service: {svc.get('name')}")
                    break
            
            if not db_in_use:
                print("Database not in use. Deleting...")
                if delete_database(db_id):
                    print("Database service deleted successfully")
                else:
                    print("Failed to delete database service")
            else:
                print("Database is in use. Not deleting.")
        else:
            print("\nsorce-db database service not found")
        
    except Exception as e:
        print(f"Critical error: {e}")

if __name__ == "__main__":
    main()
