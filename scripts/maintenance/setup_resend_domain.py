"""Setup Resend domain and configure DNS with Ionos"""
import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration
RESEND_API_KEY = "re_dXPn2f9H_3aqRCUsoQbzAGVz7Q2gejDBQ"
DOMAIN = "jobhuntin.com"
IONOS_PUBLIC_PREFIX = "48e1b13910ac4a6aa4e18a32460a1812"
IONOS_SECRET = "Opgjoy-2ReOiIwd42BcbD1iLFGx1oMOXC9TLx_so1TPkuipLG-X8NvQQz-GSHlpm7RXTxqZ2HhPSTZZMhCRuaw"

def add_domain_to_resend():
    """Add domain to Resend via API"""
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": DOMAIN,
        "region": "us-east-1"  # or eu-west-1 for EU
    }
    
    try:
        print(f"Adding domain {DOMAIN} to Resend...")
        resp = httpx.post(
            "https://api.resend.com/domains",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Response status: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code in (200, 201):
            data = resp.json()
            print(f"\n✅ Domain added successfully!")
            print(f"Domain ID: {data.get('id')}")
            print(f"Status: {data.get('status')}")
            
            # Get DNS records
            get_dns_records(data.get('id'))
            return data
        else:
            print(f"\n❌ Failed to add domain: {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

def get_dns_records(domain_id):
    """Get DNS records needed for domain verification"""
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"\nGetting DNS records for domain...")
        resp = httpx.get(
            f"https://api.resend.com/domains/{domain_id}",
            headers=headers,
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            records = data.get('records', [])
            
            print(f"\n📋 DNS Records to configure in Ionos:")
            print("=" * 60)
            
            for record in records:
                record_type = record.get('type')
                name = record.get('name', '')
                value = record.get('value', '')
                priority = record.get('priority', '')
                
                print(f"\nType: {record_type}")
                print(f"Name: {name}")
                print(f"Value: {value}")
                if priority:
                    print(f"Priority: {priority}")
                print("-" * 40)
            
            return records
        else:
            print(f"Failed to get DNS records: {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"Error getting DNS records: {e}")
        return None

def list_existing_domains():
    """List existing domains in Resend"""
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print("Listing existing domains...")
        resp = httpx.get(
            "https://api.resend.com/domains",
            headers=headers,
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            domains = data.get('data', [])
            
            print(f"\n📧 Existing domains:")
            for domain in domains:
                print(f"  - {domain.get('name')} (ID: {domain.get('id')}, Status: {domain.get('status')})")
            
            # Check if jobhuntin.com already exists
            for domain in domains:
                if domain.get('name') == DOMAIN:
                    print(f"\n⚠️  Domain {DOMAIN} already exists!")
                    print(f"Getting DNS records for existing domain...")
                    get_dns_records(domain.get('id'))
                    return domain
            
            return None
        else:
            print(f"Failed to list domains: {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"Error listing domains: {e}")
        return None

def main():
    print("=" * 60)
    print("Resend Domain Setup for JobHuntin")
    print("=" * 60)
    
    # First, check if domain already exists
    existing = list_existing_domains()
    
    if not existing:
        # Add new domain
        add_domain_to_resend()
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Copy the DNS records shown above")
    print("2. Log into your Ionos dashboard")
    print("3. Navigate to DNS settings for jobhuntin.com")
    print("4. Add the DNS records exactly as shown")
    print("5. Wait 5-10 minutes for DNS propagation")
    print("6. Domain will be automatically verified by Resend")
    print("\nYou can then send emails from: hello@jobhuntin.com")

if __name__ == "__main__":
    main()
