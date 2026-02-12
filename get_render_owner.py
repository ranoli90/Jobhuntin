#!/usr/bin/env python3
"""
Get Render owner ID for database creation
"""

import requests

def get_render_owner_id():
    """Get the correct owner ID from Render API"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json"
    }
    
    print("Getting Render owner information...")
    
    # Get owners
    response = requests.get("https://api.render.com/v1/owners", headers=headers)
    
    if response.status_code == 200:
        owners = response.json()
        print("Available owners:")
        for owner in owners:
            print(f"  ID: {owner.get('id')}")
            print(f"  Name: {owner.get('name', 'N/A')}")
            print(f"  Type: {owner.get('type', 'N/A')}")
            print()
        
        # Use the first owner for database creation
        if owners:
            owner_id = owners[0].get('id')
            print(f"Using owner ID: {owner_id}")
            return owner_id
    else:
        print(f"Failed to get owners: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def create_database_with_owner(owner_id):
    """Create database with correct owner ID"""
    
    render_api_key = "rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
    
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
    
    headers = {
        "Authorization": f"Bearer {render_api_key}",
        "Content-Type": "application/json"
    }
    
    response = requests.post("https://api.render.com/v1/services", headers=headers, json=db_config)
    
    if response.status_code == 201:
        db_info = response.json()
        print("✅ Database creation initiated!")
        print(f"Service ID: {db_info.get('id')}")
        print(f"Name: {db_info.get('name')}")
        return db_info.get('id')
    else:
        print(f"❌ Failed to create database: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def main():
    owner_id = get_render_owner_id()
    
    if owner_id:
        service_id = create_database_with_owner(owner_id)
        
        if service_id:
            print(f"\n✅ Database creation started!")
            print(f"Service ID: {service_id}")
            print("Check Render dashboard for connection details.")
        else:
            print("\n❌ Database creation failed")
    else:
        print("\n❌ Could not get owner ID")

if __name__ == "__main__":
    main()
