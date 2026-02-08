"""Configure Ionos DNS for Resend domain verification"""
import httpx
from dotenv import load_dotenv

load_dotenv()

# Ionos API credentials
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
    """Get Ionos API token"""
    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "publicPrefix": IONOS_PUBLIC_PREFIX,
        "secret": IONOS_SECRET
    }

    try:
        print("Getting Ionos API token...")
        resp = httpx.post(
            "https://api.hosting.ionos.com/auth/tokens",
            headers=headers,
            json=payload,
            timeout=10
        )

        if resp.status_code == 200:
            data = resp.json()
            token = data.get('token')
            print("✅ Got Ionos token")
            return token
        else:
            print(f"❌ Failed to get token: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None

def list_domains(token):
    """List domains in Ionos"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        print("Listing domains...")
        resp = httpx.get(
            "https://api.hosting.ionos.com/dns/v1/zones",
            headers=headers,
            timeout=10
        )

        if resp.status_code == 200:
            data = resp.json()
            print(f"Found {len(data)} domains")

            for zone in data:
                if zone.get('name') == DOMAIN:
                    print(f"✅ Found {DOMAIN} (ID: {zone.get('id')})")
                    return zone

            print(f"❌ Domain {DOMAIN} not found")
            return None
        else:
            print(f"❌ Failed to list domains: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error listing domains: {e}")
        return None

def get_existing_records(token, zone_id):
    """Get existing DNS records"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        print("Getting existing DNS records...")
        resp = httpx.get(
            f"https://api.hosting.ionos.com/dns/v1/zones/{zone_id}/records",
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

def create_dns_record(token, zone_id, record):
    """Create a DNS record"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Ionos API format
    payload = {
        "name": record['name'],
        "type": record['type'],
        "content": record['value'],
        "ttl": 3600,
        "disabled": False
    }

    # Add priority for MX records
    if record['type'] == 'MX' and record['priority']:
        payload['priority'] = record['priority']

    try:
        print(f"\nCreating {record['type']} record: {record['name']}")
        print(f"Value: {record['value'][:50]}...")

        resp = httpx.post(
            f"https://api.hosting.ionos.com/dns/v1/zones/{zone_id}/records",
            headers=headers,
            json=payload,
            timeout=10
        )

        if resp.status_code in (200, 201):
            print(f"✅ Created {record['type']} record")
            return True
        else:
            print(f"❌ Failed to create {record['type']} record: {resp.status_code}")
            print(f"Response: {resp.text[:300]}")
            return False
    except Exception as e:
        print(f"❌ Error creating record: {e}")
        return False

def update_dns_record(token, zone_id, record_id, record):
    """Update an existing DNS record"""
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
        "disabled": False
    }

    if record['type'] == 'MX' and record['priority']:
        payload['priority'] = record['priority']

    try:
        print(f"Updating {record['type']} record: {record['name']}")
        resp = httpx.put(
            f"https://api.hosting.ionos.com/dns/v1/zones/{zone_id}/records/{record_id}",
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
    print("Ionos DNS Configuration for Resend")
    print("=" * 70)

    # Get Ionos token
    token = get_ionos_token()
    if not token:
        print("\n❌ Could not get Ionos token. Check API credentials.")
        return

    # Find domain
    zone = list_domains(token)
    if not zone:
        print(f"\n❌ Domain {DOMAIN} not found in Ionos.")
        print("Make sure the domain is added to your Ionos account first.")
        return

    zone_id = zone.get('id')

    # Get existing records
    existing = get_existing_records(token, zone_id) or []

    print("\n" + "=" * 70)
    print("Adding DNS Records for Resend")
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
            if update_dns_record(token, zone_id, existing_record.get('id'), record):
                success_count += 1
        else:
            # Create new record
            if create_dns_record(token, zone_id, record):
                success_count += 1

    print("\n" + "=" * 70)
    print(f"Results: {success_count}/{len(DNS_RECORDS)} records configured")
    print("=" * 70)

    if success_count == len(DNS_RECORDS):
        print("✅ All DNS records configured successfully!")
        print("\nNext steps:")
        print("1. Wait 5-10 minutes for DNS propagation")
        print("2. Check Resend dashboard for domain verification")
        print("3. Domain will be ready to send emails from hello@jobhuntin.com")
    else:
        print("⚠️  Some records failed. Check the errors above.")
        print("\nManual backup:")
        print("Go to https://my.ionos.com and add these DNS records:")
        for record in DNS_RECORDS:
            print(f"\n{record['type']} {record['name']}")
            print(f"Value: {record['value']}")
            if record['priority']:
                print(f"Priority: {record['priority']}")

if __name__ == "__main__":
    main()
