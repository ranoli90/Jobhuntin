"""
SSO API — SAML 2.0 ACS, metadata, OIDC discovery, and SSO config management.

Mounted at /sso prefix by api/main.py.
"""

from __future__ import annotations

from typing import Any

import asyncpg
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

from backend.domain.audit import record_audit_event
from backend.domain.tenant import TenantContext, TenantScopeError, require_role
from backend.sso.saml import (
    create_sso_session_token,
    find_tenant_by_sso_domain,
    generate_sp_metadata,
    get_sso_config,
    parse_saml_response,
    upsert_sso_config,
)


async def _create_supabase_user(email: str, tenant_id: str) -> str:
    """Create a user in Supabase via Admin API."""
    s = get_settings()
    if not s.supabase_url or not s.supabase_service_key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured")

    payload = {
        "email": email,
        "email_confirm": True,  # Auto-confirm email for SSO users
        "user_metadata": {
            "tenant_id": tenant_id,
            "sso_provisioned": True,
        },
    }
    headers = {
        "apikey": s.supabase_service_key,
        "Authorization": f"Bearer {s.supabase_service_key}",
        "Content-Type": "application/json",
    }
    url = f"{s.supabase_url.rstrip('/')}/auth/v1/admin/users"
    
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, headers=headers, json=payload)
    
    if resp.status_code >= 400:
        logger.error("Supabase create user failed: %s - %s", resp.status_code, resp.text[:200])
        raise HTTPException(status_code=502, detail="Failed to create SSO user")
    
    data = resp.json()
    user_id = data.get("id")
    if not user_id:
        logger.error("Supabase create user response missing id: %s", data)
        raise HTTPException(status_code=502, detail="Failed to create SSO user")
    
    return str(user_id)

logger = get_logger("sorce.api.sso")

router = APIRouter(prefix="/sso", tags=["sso"])

# ---------------------------------------------------------------------------
# Dependency stubs (injected by api/main.py)
# ---------------------------------------------------------------------------

def _get_pool() -> asyncpg.Pool:
    return (_ for _ in ()).throw(
    NotImplementedError("Pool not injected")
)
def _get_tenant_ctx() -> TenantContext:
    return (_ for _ in ()).throw(
    NotImplementedError("Tenant ctx not injected")
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SSOConfigRequest(BaseModel):
    """Payload for configuring SSO."""
    provider: str = "saml"  # saml or oidc
    entity_id: str = ""
    sso_url: str = ""
    certificate: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_issuer: str = ""


class SSOConfigResponse(BaseModel):
    """SSO configuration details."""
    tenant_id: str
    provider: str
    is_active: bool
    entity_id: str
    sso_url: str


# ---------------------------------------------------------------------------
# SAML endpoints
# ---------------------------------------------------------------------------

@router.get("/saml/metadata", response_class=Response)
async def saml_metadata():  # type: ignore[return]
    """Return SAML Service Provider metadata XML."""
    xml = generate_sp_metadata()
    return Response(content=xml, media_type="application/xml")


@router.post("/saml/acs")
async def saml_acs(
    request: Request,
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """
    SAML Assertion Consumer Service — receives POST from IdP after authentication.

    Flow:
    1. Parse SAML response
    2. Find tenant by SSO config entity_id
    3. Create/find Supabase user
    4. Return SSO session token for client redirect
    """
    form = await request.form()
    saml_response = form.get("SAMLResponse", "")
    relay_state = form.get("RelayState", "")

    if not saml_response:
        raise HTTPException(status_code=400, detail="Missing SAMLResponse")

    # We need to find the tenant — try RelayState first (contains tenant_id)
    tenant_id = relay_state if relay_state else None

    async with db.acquire() as conn:
        # If no tenant from RelayState, do a soft parse to discover domain then re-parse with cert
        claims = None
        if not tenant_id:
            claims = parse_saml_response(str(saml_response), "")
            if claims and claims.get("email"):
                domain = claims["email"].split("@")[-1]
                tenant_id = await find_tenant_by_sso_domain(conn, domain)

        if not tenant_id:
            raise HTTPException(status_code=400, detail="Cannot determine tenant for SSO login")

        # Get SSO config for tenant
        sso_cfg = await get_sso_config(conn, tenant_id)
        if not sso_cfg:
            raise HTTPException(status_code=404, detail="SSO not configured for this tenant")

        # Parse with actual IdP certificate (enforce verification when provided)
        claims = parse_saml_response(str(saml_response), sso_cfg.get("certificate", ""))

        if not claims or not claims.get("email"):
            raise HTTPException(status_code=401, detail="Invalid SAML response")

        email = claims["email"]

        # Find or create user in Supabase auth
        user_row = await conn.fetchrow(
            "SELECT id FROM auth.users WHERE email = $1", email,
        )

        if user_row:
            user_id = str(user_row["id"])
        else:
            # Auto-provision user for SSO enterprise tenants
            user_id = await _create_supabase_user(email, tenant_id)
            logger.info("SSO: auto-provisioned user %s for tenant %s", email, tenant_id)

        # Ensure user is member of tenant
        await conn.execute(
            """
            INSERT INTO public.tenant_members (tenant_id, user_id, role)
            VALUES ($1, $2, 'MEMBER')
            ON CONFLICT (tenant_id, user_id) DO NOTHING
            """,
            tenant_id, user_id,
        )

        # Audit log
        await record_audit_event(
            conn, tenant_id, user_id,
            action="sso.login",
            resource="user",
            resource_id=user_id,
            details={"email": email, "provider": sso_cfg["provider"]},
            ip_address=request.client.host if request.client else None,
        )

    # Create session token
    token = create_sso_session_token(tenant_id, email, user_id)
    incr("sso.login.success")

    return {
        "status": "authenticated",
        "email": email,
        "tenant_id": tenant_id,
        "session_token": token,
        "redirect_url": f"sorce://sso/callback?token={token}",
    }


# ---------------------------------------------------------------------------
# OIDC discovery (for OIDC-based SSO)
# ---------------------------------------------------------------------------

@router.get("/.well-known/openid-configuration")
async def oidc_discovery() -> dict[str, Any]:
    """OpenID Connect discovery document."""
    s = get_settings()
    base = s.sso_sp_acs_url.rsplit("/", 2)[0]  # https://api.sorce.app/sso
    return {
        "issuer": s.sso_sp_entity_id,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "userinfo_endpoint": f"{base}/userinfo",
        "jwks_uri": f"{base}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "email", "profile"],
    }


# ---------------------------------------------------------------------------
# SSO config management (enterprise admins only)
# ---------------------------------------------------------------------------

@router.get("/config", response_model=SSOConfigResponse)
async def get_config(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> SSOConfigResponse:
    """Get SSO configuration for current tenant."""
    if ctx.plan != "ENTERPRISE":
        raise HTTPException(status_code=403, detail="SSO requires ENTERPRISE plan")

    async with db.acquire() as conn:
        cfg = await get_sso_config(conn, ctx.tenant_id)

    if not cfg:
        return SSOConfigResponse(
            tenant_id=ctx.tenant_id, provider="none",
            is_active=False, entity_id="", sso_url="",
        )

    return SSOConfigResponse(
        tenant_id=ctx.tenant_id,
        provider=cfg["provider"],
        is_active=cfg["is_active"],
        entity_id=cfg["entity_id"],
        sso_url=cfg["sso_url"],
    )


@router.post("/config", response_model=SSOConfigResponse)
async def update_config(
    body: SSOConfigRequest,
    request: Request,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> SSOConfigResponse:
    """Configure SSO for current tenant (ENTERPRISE only)."""
    if ctx.plan != "ENTERPRISE":
        raise HTTPException(status_code=403, detail="SSO requires ENTERPRISE plan")
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only admins can configure SSO")

    async with db.acquire() as conn:
        cfg = await upsert_sso_config(
            conn, ctx.tenant_id, body.provider,
            entity_id=body.entity_id, sso_url=body.sso_url,
            certificate=body.certificate,
            oidc_client_id=body.oidc_client_id,
            oidc_client_secret=body.oidc_client_secret,
            oidc_issuer=body.oidc_issuer,
        )
        await record_audit_event(
            conn, ctx.tenant_id, ctx.user_id,
            action="sso.configured",
            resource="sso",
            details={"provider": body.provider},
            ip_address=request.client.host if request.client else None,
        )

    incr("sso.config.updated")
    return SSOConfigResponse(
        tenant_id=ctx.tenant_id,
        provider=cfg["provider"],
        is_active=cfg["is_active"],
        entity_id=cfg["entity_id"],
        sso_url=cfg["sso_url"],
    )
