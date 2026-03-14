#!/usr/bin/env python3
"""List all Render services."""

import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

def main():
    print("🔍 Listing all Render services...")
    
    response = requests.get('https://api.render.com/v1/services', headers=headers)
    if response.status_code != 200:
        print(f"Error getting services: {response.status_code}")
        return
    
    services = response.json()
    print(f"\nFound {len(services)} services:\n")
    
    for i, service in enumerate(services):
        if isinstance(service, dict):
            name = service.get('name', f'Service_{i}')
            service_type = service.get('type', service.get('serviceType', 'unknown'))
            status = service.get('status', 'unknown')
            service_id = service.get('id', 'no-id')
            
            print(f"{i+1}. Name: {name}")
            print(f"   Type: {service_type}")
            print(f"   Status: {status}")
            print(f"   ID: {service_id}")
            
            # Check if it's a web service
            service_info = service.get('service', {})
            if service_info:
                url = service_info.get('url', 'N/A')
                print(f"   URL: {url}")
            print()

if __name__ == "__main__":
    main()
