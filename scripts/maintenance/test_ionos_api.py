"""Try different Ionos API approaches."""
import base64

import httpx
from dotenv import load_dotenv

load_dotenv()

# Ionos credentials
IONOS_PUBLIC_PREFIX = "48e1b13910ac4a6aa4e18a32460a1812"
IONOS_SECRET = "Opgjoy-2ReOiIwd42BcbD1iLFGx1oMOXC9TLx_so1TPkuipLG-X8NvQQz-GSHlpm7RXTxqZ2HhPSTZZMhCRuaw"

def test_ionos_endpoints():
    """Test various Ionos API endpoints."""
    # Prepare basic auth
    credentials = f"{IONOS_PUBLIC_PREFIX}:{IONOS_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json",
    }

    # Different Ionos API endpoints to try
    endpoints = [
        {
            "name": "Ionos Cloud Auth",
            "url": "https://api.ionos.com/auth/tokens",
            "method": "POST"
        },
        {
            "name": "Ionos Hosting Auth",
            "url": "https://api.hosting.ionos.com/auth/tokens",
            "method": "POST"
        },
        {
            "name": "Ionos CDN Auth",
            "url": "https://cdns.api.ionos.com/auth/tokens",
            "method": "POST"
        },
        {
            "name": "Ionos Cloud API Root",
            "url": "https://api.ionos.com/",
            "method": "GET"
        },
        {
            "name": "Ionos Hosting API Root",
            "url": "https://api.hosting.ionos.com/",
            "method": "GET"
        },
        {
            "name": "Ionos DNS API",
            "url": "https://api.ionos.com/dns/v1/zones",
            "method": "GET"
        },
        {
            "name": "Ionos Hosting DNS",
            "url": "https://api.hosting.ionos.com/dns/v1/zones",
            "method": "GET"
        }
    ]

    print("=" * 70)
    print("Testing Ionos API Endpoints")
    print("=" * 70)

    working_endpoints = []

    for endpoint in endpoints:
        try:
            print(f"\nTesting: {endpoint['name']}")
            print(f"URL: {endpoint['url']}")

            if endpoint['method'] == 'POST':
                resp = httpx.post(endpoint['url'], headers=headers, json={}, timeout=10)
            else:
                resp = httpx.get(endpoint['url'], headers=headers, timeout=10)

            print(f"Status: {resp.status_code}")

            if resp.status_code in (200, 201):
                print(f"✅ SUCCESS - {endpoint['name']}")
                working_endpoints.append(endpoint)
                if resp.text:
                    print(f"Response preview: {resp.text[:200]}...")
            elif resp.status_code == 401:
                print("❌ Authentication failed")
            elif resp.status_code == 404:
                print("❌ Endpoint not found")
            elif resp.status_code == 403:
                print("❌ Access forbidden")
            else:
                print(f"❌ Error: {resp.text[:200]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if working_endpoints:
        print(f"✅ Found {len(working_endpoints)} working endpoints:")
        for endpoint in working_endpoints:
            print(f"  - {endpoint['name']}: {endpoint['url']}")
    else:
        print("❌ No working endpoints found")
        print("\nPossible issues:")
        print("- API credentials are for a different service")
        print("- Service not activated")
        print("- Network restrictions")
        print("- Incorrect endpoint URLs")

    return working_endpoints

def generate_manual_instructions():
    """Generate clear manual instructions."""
    print("\n" + "=" * 70)
    print("MANUAL DNS CONFIGURATION")
    print("=" * 70)

    print("\nSince API access is restricted, here's how to configure manually:")

    print("\n1. Go to Ionos Dashboard")
    print("   URL: https://my.ionos.com")

    print("\n2. Navigate to your domain")
    print("   Domains → jobhuntin.com → DNS Settings")

    print("\n3. Add these DNS records:")

    records = [
        {
            "type": "TXT",
            "name": "resend._domainkey",
            "value": "p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDTNt9gMWn7w5Rqg8AjipC4rSEzRKCB8TZBurKjmKBEsGUR8mXTDi5611NgVspfrdIQB6lPDjnnHBIiVZW+O+n/2FNIyrXxTRHlQXmCjpdr/tZ5NXnfEg65Xqwc5eGI9useCBgeZowiUACLY3nE/xXkBTvyUWvBQs7vbkXhlMSErwIDAQAB"
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
            "value": "v=spf1 include:amazonses.com ~all"
        },
        {
            "type": "TXT",
            "name": "_dmarc",
            "value": "v=DMARC1; p=none;"
        }
    ]

    for i, record in enumerate(records, 1):
        print(f"\n   Record {i}:")
        print(f"   Type: {record['type']}")
        print(f"   Name: {record['name']}")
        print(f"   Value: {record['value']}")
        if 'priority' in record:
            print(f"   Priority: {record['priority']}")

    print("\n4. Save and wait")
    print("   - Save all changes")
    print("   - Wait 5-10 minutes for DNS propagation")
    print("   - Check Resend dashboard for verification")

    print("\n5. Update application")
    print("   - Once verified, update EMAIL_FROM=hello@jobhuntin.com")
    print("   - Deploy changes to Render")

def main():
    # Test API endpoints
    working = test_ionos_endpoints()

    if not working:
        # Provide manual instructions
        generate_manual_instructions()

if __name__ == "__main__":
    main()
