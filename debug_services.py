#!/usr/bin/env python3
"""Debug Render services response."""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

def main():
    print("🔍 Debugging Render services response...")

    response = requests.get('https://api.render.com/v1/services', headers=headers)
    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        services = response.json()
        print(f"Response type: {type(services)}")
        print(f"Number of services: {len(services)}")

        # Save raw response to file for inspection
        with open('services_response.json', 'w') as f:
            json.dump(services, f, indent=2)
        print("Raw response saved to services_response.json")

        # Try to parse first service
        if services:
            print(f"\nFirst service keys: {list(services[0].keys()) if isinstance(services[0], dict) else 'Not a dict'}")

            if isinstance(services[0], dict):
                print("First service details:")
                for key, value in services[0].items():
                    print(f"  {key}: {value}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    main()
