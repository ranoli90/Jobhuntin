#!/usr/bin/env python3
"""Quick check for API service logs using render-dashboard logs."""

import urllib.request


def check_api_direct():
    """Try different API endpoints to diagnose the 502."""
    urls = [
        "https://jobhuntin-api.onrender.com/",
        "https://jobhuntin-api.onrender.com/health",
        "https://jobhuntin-api.onrender.com/docs",
    ]

    print("API ENDPOINT DIAGNOSTICS:")
    print("-" * 50)

    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Jobhuntin-Diag/1.0'})
            response = urllib.request.urlopen(req, timeout=10)
            print(f"URL: {url}")
            print(f"  Status: HTTP {response.getcode()}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            body = response.read().decode('utf-8', errors='ignore')[:200]
            print(f"  Body: {body}")
            print()
        except urllib.error.HTTPError as e:
            print(f"URL: {url}")
            print(f"  Status: HTTP {e.code} - {e.reason}")
            try:
                body = e.read().decode('utf-8', errors='ignore')[:500]
                print(f"  Body: {body}")
            except:
                pass
            print()
        except Exception as e:
            print(f"URL: {url}")
            print(f"  Error: {e}")
            print()

if __name__ == '__main__':
    check_api_direct()
