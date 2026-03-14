#!/usr/bin/env python3
"""Check service details and available endpoints."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

def main():
    print("🔍 Checking service details...")

    # Get services
    response = requests.get('https://api.render.com/v1/services', headers=headers)
    if response.status_code != 200:
        print(f"Error getting services: {response.status_code}")
        return

    services = response.json()

    # Find the web service
    for service in services:
        if isinstance(service, dict):
            service_info = service.get('service', {})
            name = service_info.get('name', '')
            service_type = service_info.get('type', '')

            if service_type == 'web_service' and 'jobhuntin' in name.lower():
                service_id = service_info.get('id')
                print(f"\n✅ Found web service: {name}")
                print(f"Service ID: {service_id}")

                # Try different log endpoints
                endpoints_to_try = [
                    f'https://api.render.com/v1/services/{service_id}/logs',
                    f'https://api.render.com/v1/services/{service_id}/instances',
                    f'https://api.render.com/v1/services/{service_id}/events',
                ]

                for endpoint in endpoints_to_try:
                    print(f"\n🔍 Trying: {endpoint}")
                    try:
                        logs_response = requests.get(endpoint, headers=headers)
                        print(f"Status: {logs_response.status_code}")

                        if logs_response.status_code == 200:
                            data = logs_response.json()
                            print(f"Response type: {type(data)}")
                            if isinstance(data, list) and data:
                                print(f"Sample data: {data[0]}")
                        elif logs_response.status_code == 404:
                            print("Endpoint not found")
                        else:
                            print(f"Response: {logs_response.text[:200]}...")
                    except Exception as e:
                        print(f"Error: {e}")

                break

if __name__ == "__main__":
    main()
