#!/usr/bin/env python3
"""Check worker services for auto-apply, job queue, and reminders."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

def main():
    print("🔍 Checking worker services...")

    response = requests.get('https://api.render.com/v1/services', headers=headers)

    if response.status_code == 200:
        services = response.json()
        print(f"\n📊 Found {len(services)} services:")

        worker_services = []
        for service in services:
            if isinstance(service, dict):
                service_info = service.get('service', {})
                name = service_info.get('name', '')
                service_type = service_info.get('type', '')
                status = service_info.get('status', '')

                if service_type == 'background_worker':
                    worker_services.append({
                        'name': name,
                        'type': service_type,
                        'status': status,
                        'id': service_info.get('id', ''),
                        'details': service_info
                    })
                    print(f"  📋 {name} ({service_type}) - {status}")
                    print(f"      ID: {service_info.get('id', 'N/A')}")
                    print(f"      Created: {service_info.get('createdAt', 'N/A')}")
                    print(f"      Service Type: {service_type}")

                    # Show key details
                    env_details = service_info.get('serviceDetails', {})
                    if env_details:
                        print(f"      Build Command: {env_details.get('startCommand', 'N/A')}")
                        print(f"      Environment: {env_details.get('env', 'N/A')}")
                        print(f"      Plan: {env_details.get('plan', 'N/A')}")
                        print(f"      Runtime: {env_details.get('runtime', 'N/A')}")
                    print()

        print("\n🔧 WORKER SERVICES SUMMARY:")
        print(f"Total worker services found: {len(worker_services)}")

        for service in worker_services:
            print(f"\n📋 {service['name']}")
            print(f"   Status: {service['status']}")
            print(f"   Type: {service['type']}")
            print("   Purpose: Background processing")

    else:
        print(f"❌ Error getting services: {response.status_code}")

if __name__ == "__main__":
    main()
