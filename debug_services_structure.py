#!/usr/bin/env python3
"""Debug the actual service structure from Render API."""

import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_KEY')
headers = {'Authorization': f'Bearer {token}'}

def main():
    print("🔍 Debugging service structure...")
    
    response = requests.get('https://api.render.com/v1/services', headers=headers)
    
    if response.status_code == 200:
        services = response.json()
        print(f"📊 Found {len(services)} services")
        
        for i, service in enumerate(services[:3]):  # Show first 3
            print(f"\n📋 Service {i+1}:")
            print(f"  Type: {type(service)}")
            print(f"  Keys: {list(service.keys()) if isinstance(service, dict) else 'Not a dict'}")
            
            if isinstance(service, dict):
                for key, value in service.items():
                    if isinstance(value, dict):
                        print(f"    {key}: dict with keys {list(value.keys())}")
                    elif isinstance(value, list):
                        print(f"    {key}: list with {len(value)} items")
                    else:
                        print(f"    {key}: {str(value)[:50]}...")
                        
    else:
        print(f"❌ Error: {response.status_code}")

if __name__ == "__main__":
    main()
