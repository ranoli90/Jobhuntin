#!/usr/bin/env python
"""
Generate secure secrets for production deployment.
Run this script to generate values for:
  - CSRF_SECRET
  - WEBHOOK_SIGNING_SECRET
  - SSO_SESSION_SECRET
  - JWT_SECRET (if needed)
"""

import secrets


def generate_secrets():
    secrets_dict = {
        "CSRF_SECRET": secrets.token_hex(32),
        "WEBHOOK_SIGNING_SECRET": secrets.token_hex(32),
        "SSO_SESSION_SECRET": secrets.token_hex(32),
        "JWT_SECRET": secrets.token_hex(32),
    }

    print("=" * 60)
    print("GENERATED SECRETS - ADD THESE TO YOUR RENDER DASHBOARD")
    print("=" * 60)
    print()

    for key, value in secrets_dict.items():
        print(f"{key}={value}")

    print()
    print("=" * 60)
    print("IMPORTANT: Store these securely!")
    print("- Add to Render dashboard: Environment Variables")
    print("- Never commit these to git")
    print("- Rotate periodically (every 90 days recommended)")
    print("=" * 60)

    return secrets_dict


if __name__ == "__main__":
    generate_secrets()
