"""Ionos Cloud API DNS Configuration - Correct approach"""
import os
import httpx
import json
import base64
from dotenv import load_dotenv

load_dotenv()

# Ionos Cloud API credentials (different from hosting)
IONOS_PUBLIC_PREFIX = "48e1b13910ac4a6aa4e18a32460a1812"
IONOS_SECRET = "Opgjoy-2ReOiIwd42BcbD1iLFGx1oMOXC9TLx_so1TPkuipLG-X8NvQQz-GSHlpm7RXTxqZ2HhPSTZZMhCRuaw"

# Domain and DNS records from Resend
DOMAIN = "jobhuntin.com"
DNS_RECORDS = [
    {
        "type": "TXT",
        "name": "resend._domainkey",
        "value": "p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDTNt9gMWn7w5Rqg8AjipC4rSEzRKCB8TZBurKjmKBEsGUR8mXTDi5611NgVspfrdIQB6lPDjnnHBIiVZW+O+n/2FNIyrXxTRHlQXmCjpdr/tZ5NXnfEg65Xqwc5eGI9useCBgeZowiUACLY3nE/xXkBTvyUWvBQs7vbkXhlMSErwIDAQAB",
        "priority": None
    },
    {
        "type": "MX",
        "name": "send",
        "value": "feedback-smtp.us-east-1.amazonses.com",
        "priority": 10
    },
    {
        "type": "TXT",
        "name": "send",
        "value": "v=spf1 include:amazonses.com ~all",
        "priority": None
    },
    {
        "type": "TXT",
        "name": "_dmarc",
        "value": "v=DMARC1; p=none;",
        "priority": None
    }
]

def get_ionos_token():
    """Get Ionos Cloud API token"""
    # Ionos Cloud uses basic auth with prefix:secret
    credentials = f"{IONOS_PUBLIC_PREFIX}:{IONOS_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json",
    }
    
    try:
        print("Getting Ionos Cloud token...")
        resp = httpx.post(
            "https://api.ionos.com/auth/tokens",
            headers=headers,
            json={},
            timeout=10
        )
        
        print(f"Token response status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            token = data.get('token')
            print(f"✅ Got Ionos Cloud token")
            return token
        else:
            print(f"❌ Failed to get token: {resp.status_code}")
            print(f"Response: {resp.text[:300]}")
            return None
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None

def list_zones(token):
    """List DNS zones"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    
    try:
        print("Listing DNS zones...")
        resp = httpx.get(
            "https://api.ionos.com/dns/v1/zones",
            headers=headers,
            timeout=10
        )
        
        print(f"Zones list status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Found {len(data)} zones")
            
            for zone in data:
                print(f"  - {zone.get('name')} (ID: {zone.get('id')})")
                if zone.get('name') == DOMAIN:
                    print(f"✅ Found target domain")
                    return zone
            
            print(f"❌ Domain {DOMAIN} not found")
            return None
        else:
            print(f"❌ Failed to list zones: {resp.status_code}")
            print(f"Response: {resp.text[:300]}")
            return None
    except Exception as e:
        print(f"❌ Error listing zones: {e}")
        return None

def get_zone_records(token, zone_id):
    """Get existing records in zone"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    
    try:
        print(f"Getting records for zone {zone_id}...")
        resp = httpx.get(
            f"https://api.ionos.com/dns/v1/zones/{zone_id}/records",
            headers=headers,
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Found {len(data)} existing records")
            return data
        else:
            print(f"❌ Failed to get records: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting records: {e}")
        return None

def create_record(token, zone_id, record):
    """Create DNS record"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    # Ionos Cloud DNS API format
    payload = {
        "name": record['name'],
        "type": record['type'],
        "content": record['value'],
        "ttl": 3600,
        "disabled": False,
        "pinned": False
    }
    
    # Add priority for MX records
    if record['type'] == 'MX' and record['priority']:
        payload['priority'] = record['priority']
    
    try:
        print(f"\nCreating {record['type']} record: {record['name']}")
        print(f"Value: {record['value'][:50]}...")
        
        resp = httpx.post(
            f"https://api.ionos.com/dns/v1/zones/{zone_id}/records",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"Create status: {resp.status_code}")
        
        if resp.status_code in (200, 201):
            print(f"✅ Created {record['type']} record")
            return True
        else:
            print(f"❌ Failed to create: {resp.status_code}")
            print(f"Response: {resp.text[:300]}")
            return False
    except Exception as e:
        print(f"❌ Error creating record: {e}")
        return False

def update_record(token, zone_id, record_id, record):
    """Update existing DNS record"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    payload = {
        "name": record['name'],
        "type": record['type'],
        "content": record['value'],
        "ttl": 3600,
        "disabled": False,
        "pinned": False
    }
    
    if record['type'] == 'MX' and record['priority']:
        payload['priority'] = record['priority']
    
    try:
        print(f"Updating {record['type']} record: {record['name']}")
        resp = httpx.put(
            f"https://api.ionos.com/dns/v1/zones/{zone_id}/records/{record_id}",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if resp.status_code in (200, 204):
            print(f"✅ Updated {record['type']} record")
            return True
        else:
            print(f"❌ Failed to update: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error updating record: {e}")
        return False

def main():
    print("=" * 70)
    print("Ionos Cloud API DNS Configuration")
    print("=" * 70)
    
    # Get Ionos Cloud token
    token = get_ionos_token()
    if not token:
        print("\n❌ Could not authenticate with Ionos Cloud API.")
        print("This might be due to:")
        print("- Incorrect API credentials")
        print("- Service not activated")
        print("- API restrictions")
        return
    
    # List zones
    zone = list_zones(token)
    if not zone:
        print(f"\n❌ Domain {DOMAIN} not found in Ionos Cloud DNS.")
        print("Make sure the domain is added to your Ionos Cloud account first.")
        return
    
    zone_id = zone.get('id')
    
    # Get existing records
    existing = get_zone_records(token, zone_id) or []
    
    print(f"\n" + "=" * 70)
    print("Configuring DNS Records for Resend")
    print("=" * 70)
    
    success_count = 0
    
    for record in DNS_RECORDS:
        # Check if record already exists
        existing_record = None
        for existing_rec in existing:
            if (existing_rec.get('name') == record['name'] and 
                existing_rec.get('type') == record['type']):
                existing_record = existing_rec
                break
        
        if existing_record:
            # Update existing record
            if update_record(token, zone_id, existing_record.get('id'), record):
                success_count += 1
        else:
            # Create new record
            if create_record(token, zone_id, record):
                success_count += 1
    
    print(f"\n" + "=" * 70)
    print(f"Results: {success_count}/{len(DNS_RECORDS)} records configured")
    print("=" * 70)
    
    if success_count == len(DNS_RECORDS):
        print("✅ All DNS records configured successfully!")
        print("\nNext steps:")
        print("1. Wait 5-10 minutes for DNS propagation")
        print("2. Check Resend dashboard for domain verification")
        print("3. Once verified, update EMAIL_FROM=hello@jobhuntin.com")
        print("4. Test sending emails")
    else:
        print("⚠️  Some records failed. Manual configuration may be needed.")
        print("\nManual backup:")
        print("Go to https://my.ionos.com and add the DNS records manually")

if __name__ == "__main__":
    main()
