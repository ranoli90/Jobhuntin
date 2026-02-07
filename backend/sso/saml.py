"""
SAML 2.0 Service Provider — handles ACS (Assertion Consumer Service),
metadata endpoint, and IdP-initiated login for enterprise tenants.

Uses python3-saml (onelogin) for SAML processing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any
from xml.etree import ElementTree as ET

import asyncpg

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.sso.saml")


# ---------------------------------------------------------------------------
# SAML metadata generation
# ---------------------------------------------------------------------------

def generate_sp_metadata() -> str:
    """Generate SAML Service Provider metadata XML."""
    s = get_settings()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="{s.sso_sp_entity_id}">
  <md:SPSSODescriptor
      AuthnRequestsSigned="false"
      WantAssertionsSigned="true"
      protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
    <md:AssertionConsumerService
        Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        Location="{s.sso_sp_acs_url}"
        index="0"
        isDefault="true"/>
  </md:SPSSODescriptor>
</md:EntityDescriptor>"""


# ---------------------------------------------------------------------------
# SAML response parsing (simplified — production should use python3-saml)
# ---------------------------------------------------------------------------

def parse_saml_response(saml_response_b64: str, idp_cert_pem: str) -> dict[str, Any] | None:
    """
    Parse a SAML Response and extract user attributes.

    Returns dict with: email, name_id, attributes, session_index
    Returns None if parsing fails.

    NOTE: In production, use python3-saml or pysaml2 for full
    signature verification. This implementation extracts claims
    for the MVP and logs warnings for unverified signatures.
    """
    try:
        xml_bytes = base64.b64decode(saml_response_b64)
        root = ET.fromstring(xml_bytes)

        ns = {
            "saml2p": "urn:oasis:names:tc:SAML:2.0:protocol",
            "saml2": "urn:oasis:names:tc:SAML:2.0:assertion",
        }

        # Extract NameID (email)
        name_id_el = root.find(".//saml2:NameID", ns)
        email = name_id_el.text.strip() if name_id_el is not None and name_id_el.text else None

        if not email:
            logger.warning("SAML response missing NameID")
            return None

        # Extract attributes
        attributes: dict[str, str] = {}
        for attr in root.findall(".//saml2:Attribute", ns):
            attr_name = attr.get("Name", "")
            value_el = attr.find("saml2:AttributeValue", ns)
            if value_el is not None and value_el.text:
                attributes[attr_name] = value_el.text.strip()

        # Extract session index
        authn_stmt = root.find(".//saml2:AuthnStatement", ns)
        session_index = authn_stmt.get("SessionIndex", "") if authn_stmt is not None else ""

        logger.warning("SAML signature verification skipped — use python3-saml in production")

        return {
            "email": email,
            "name_id": email,
            "attributes": attributes,
            "session_index": session_index,
            "first_name": attributes.get("firstName", attributes.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname", "")),
            "last_name": attributes.get("lastName", attributes.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname", "")),
        }
    except Exception as exc:
        logger.error("SAML parse error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# SSO session token
# ---------------------------------------------------------------------------

def create_sso_session_token(tenant_id: str, email: str, user_id: str) -> str:
    """Create a signed SSO session token for post-ACS redirect."""
    s = get_settings()
    payload = json.dumps({
        "tenant_id": tenant_id,
        "email": email,
        "user_id": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,  # 5 min validity
    })
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(s.sso_session_secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_sso_session_token(token: str) -> dict[str, Any] | None:
    """Verify and decode an SSO session token."""
    s = get_settings()
    try:
        payload_b64, sig = token.rsplit(".", 1)
        expected = hmac.new(s.sso_session_secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# ---------------------------------------------------------------------------
# SSO config management
# ---------------------------------------------------------------------------

async def get_sso_config(conn: asyncpg.Connection, tenant_id: str) -> dict[str, Any] | None:
    """Get SSO configuration for a tenant."""
    row = await conn.fetchrow(
        "SELECT * FROM public.sso_configs WHERE tenant_id = $1 AND is_active = true",
        tenant_id,
    )
    return dict(row) if row else None


async def upsert_sso_config(
    conn: asyncpg.Connection,
    tenant_id: str,
    provider: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create or update SSO configuration."""
    fields = {k: v for k, v in kwargs.items() if v is not None}
    row = await conn.fetchrow(
        """
        INSERT INTO public.sso_configs (tenant_id, provider, entity_id, sso_url, certificate,
            oidc_client_id, oidc_client_secret, oidc_issuer, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true)
        ON CONFLICT (tenant_id) DO UPDATE SET
            provider = $2, entity_id = COALESCE($3, sso_configs.entity_id),
            sso_url = COALESCE($4, sso_configs.sso_url),
            certificate = COALESCE($5, sso_configs.certificate),
            oidc_client_id = COALESCE($6, sso_configs.oidc_client_id),
            oidc_client_secret = COALESCE($7, sso_configs.oidc_client_secret),
            oidc_issuer = COALESCE($8, sso_configs.oidc_issuer),
            is_active = true, updated_at = now()
        RETURNING *
        """,
        tenant_id, provider,
        fields.get("entity_id", ""), fields.get("sso_url", ""),
        fields.get("certificate", ""), fields.get("oidc_client_id", ""),
        fields.get("oidc_client_secret", ""), fields.get("oidc_issuer", ""),
    )
    return dict(row)


async def find_tenant_by_sso_domain(conn: asyncpg.Connection, email_domain: str) -> str | None:
    """Find tenant ID by SSO email domain (from enterprise_settings.custom_domain)."""
    row = await conn.fetchrow(
        """
        SELECT es.tenant_id FROM public.enterprise_settings es
        WHERE es.custom_domain = $1
        """,
        email_domain,
    )
    return str(row["tenant_id"]) if row else None
