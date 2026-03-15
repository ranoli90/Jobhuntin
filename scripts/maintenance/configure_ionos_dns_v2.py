"""Configure Ionos DNS with correct API endpoints."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

# Ionos API credentials
IONOS_PUBLIC_PREFIX = os.environ.get("IONOS_PUBLIC_PREFIX")
IONOS_SECRET = os.environ.get("IONOS_SECRET")

# Domain and DNS records from Resend
DOMAIN = "jobhuntin.com"
DNS_RECORDS = [
    {
        "type": "TXT",
        "name": "resend._domainkey",
        "value": "p =
    MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDTNt9gMWn7w5Rqg8AjipC4rSEzRKCB8TZBurKjmKBEsGUR8mXTDi5611NgVspfrdIQB6lPDjnnHBIi
    VZW+O+n/2FNIyrXxTRHlQXmCjpdr/tZ5NXnfEg65Xqwc5eGI9useCBgeZowiUACLY3nE/xXkBTvyUWvBQs7vbkXhlMSErwIDAQAB",
        "priority": None,
    },
    {
        "type": "MX",
        "name": "send",
        "value": "feedback-smtp.us-east-1.amazonses.com",
        "priority": 10,
    },
    {
        "type": "TXT",
        "name": "send",
        "value": "v=spf1 include:amazonses.com ~all",
        "priority": None,
    },
    {"type": "TXT", "name": "_dmarc", "value": "v=DMARC1; p=none;", "priority": None},
]


def get_ionos_token():
    """Get Ionos API token - try different endpoints."""
    headers = {
        "Content-Type": "application/json",
    }

    payload = {"publicPrefix": IONOS_PUBLIC_PREFIX, "secret": IONOS_SECRET}

    # Try different Ionos API endpoints
    endpoints = [
        "https://api.hosting.ionos.com/auth",
        "https://api.ionos.com/auth",
        "https://api.hosting.ionos.com/v1/auth",
        "https://cdns.api.ionos.com/auth",
    ]

    for endpoint in endpoints:
        try:
            print(f"Trying endpoint: {endpoint}")
            resp = httpx.post(
                f"{endpoint}/tokens", headers=headers, json=payload, timeout=10
            )

            print(f"Status: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                token = data.get("token")
                print(f"✅ Got Ionos token from {endpoint}")
                return token, endpoint
            else:
                print(f"Failed: {resp.text[:200]}")
        except Exception as e:
            print(f"Error with {endpoint}: {e}")

    return None, None


def test_api_access(token, base_url):
    """Test API access with token."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        # Try to list zones/domains
        resp = httpx.get(f"{base_url}/zones", headers=headers, timeout=10)
        print(f"Zones list status: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ API access working. Found {len(data)} zones")
            return True
        else:
            print(f"❌ API access failed: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False


def find_domain(token, base_url):
    """Find the domain zone."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        print(f"Searching for domain {DOMAIN}...")
        resp = httpx.get(f"{base_url}/zones", headers=headers, timeout=10)

        if resp.status_code == 200:
            data = resp.json()

            for zone in data:
                if zone.get("name") == DOMAIN:
                    print(f"✅ Found {DOMAIN} (ID: {zone.get('id')})")
                    return zone

            print(f"❌ Domain {DOMAIN} not found")
            return None
        else:
            print(f"❌ Failed to list zones: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error finding domain: {e}")
        return None


def create_dns_record_manual():
    """Generate manual DNS configuration instructions."""
    print("\n" + "=" * 70)
    print("MANUAL DNS CONFIGURATION INSTRUCTIONS")
    print("=" * 70)

    print(f"\nDomain: {DOMAIN}")
    print("Provider: Ionos")
    print("\nGo to: https://my.ionos.com")
    print("Navigate to: Domains → jobhuntin.com → DNS Settings")
    print("\nAdd these records:")

    for i, record in enumerate(DNS_RECORDS, 1):
        print(f"\n{i}. {record['type']} Record")
        print(f"   Host/Name: {record['name']}")
        print(f"   Value: {record['value']}")
        if record["priority"]:
            print(f"   Priority: {record['priority']}")
        print("-" * 40)

    print("\nAfter adding records:")
    print("1. Save changes")
    print("2. Wait 5-10 minutes for DNS propagation")
    print("3. Check Resend dashboard for verification")
    print("4. Once verified, you can send from hello@jobhuntin.com")


def main():
    print("=" * 70)
    print("Ionos DNS Configuration for Resend")
    print("=" * 70)

    # Try to get Ionos token
    token, endpoint = get_ionos_token()

    if not token:
        print("\n❌ Could not authenticate with Ionos API.")
        print("This might be due to:")
        print("- Incorrect API credentials")
        print("- API endpoint changes")
        print("- Service restrictions")

        # Provide manual instructions
        create_dns_record_manual()
        return

    # Test API access
    base_url = endpoint.replace("/auth", "/dns/v1")
    if not test_api_access(token, base_url):
        create_dns_record_manual()
        return

    # Find domain
    zone = find_domain(token, base_url)
    if not zone:
        create_dns_record_manual()
        return

    print(f"\n✅ Ready to configure DNS for {DOMAIN}")
    print("Note: Ionos API might have restrictions on programmatic DNS changes.")
    print("Manual configuration recommended for reliability.")

    create_dns_record_manual()


if __name__ == "__main__":
    main()
