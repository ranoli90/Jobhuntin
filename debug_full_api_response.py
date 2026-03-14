#!/usr/bin/env python3
"""Debug full API response to see all services."""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

def main():
    print("🔍 Getting full API response...")
    
    response = requests.get('https://api.render.com/v1/services', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"📊 Response type: {type(data)}")
        print(f"📊 Total items in response: {len(data)}")
        
        services_found = []
        
        for i, item in enumerate(data):
            print(f"\n📋 Item {i+1}:")
            print(f"  Type: {type(item)}")
            
            if isinstance(item, dict):
                print(f"  Keys: {list(item.keys())}")
                
                if 'service' in item:
                    service = item['service']
                    services_found.append(service)
                    print(f"  ✅ Found service: {service.get('name', 'unknown')}")
                    print(f"      ID: {service.get('id', 'unknown')}")
                    print(f"      Type: {service.get('type', 'unknown')}")
                    print(f"      Status: {service.get('status', 'unknown')}")
                    print(f"      Owner: {service.get('ownerId', 'unknown')}")
                else:
                    print(f"  ❌ No 'service' key found")
            else:
                print(f"  ❌ Not a dict: {str(item)[:100]}...")
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total items in response: {len(data)}")
        print(f"  Services extracted: {len(services_found)}")
        print(f"  Expected services: 7 (api, web, job-sync, auto-apply, job-queue, follow-up-reminders, seo-engine)")
        
        # Check what's missing
        expected_services = [
            'jobhuntin-api', 'jobhuntin-web', 'jobhuntin-job-sync', 
            'sorce-auto-apply-agent', 'jobhuntin-job-queue', 
            'jobhuntin-follow-up-reminders', 'jobhuntin-seo-engine'
        ]
        
        found_names = [s.get('name', '') for s in services_found]
        missing_services = [name for name in expected_services if name not in found_names]
        
        print(f"  Missing services: {missing_services}")
        
        # Write full response to file for inspection
        with open('full_api_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  📁 Full response saved to: full_api_response.json")
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    main()
