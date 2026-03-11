"""
OAuth/SSO Handler for Phase 12.1 Agent Improvements
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from shared.logging_config import get_logger

logger = get_logger("sorce.oauth_handler")


@dataclass
class OAuthCredentials:
    """OAuth credentials for external service integration."""

    provider: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str]
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    tenant_id: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class OAuthTokenResponse:
    """OAuth token response."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class OAuthUserInfo:
    """User information from OAuth provider."""

    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    provider: str


class OAuthHandler:
    """OAuth/SSO handler for external service integration."""

    def __init__(self):
        self._credentials: Dict[str, OAuthCredentials] = {}
        self._token_cache: Dict[str, OAuthTokenResponse] = {}
        self._user_info_cache: Dict[str, OAuthUserInfo] = {}

    async def get_credentials(
        self, provider: str, tenant_id: str
    ) -> Optional[OAuthCredentials]:
        """Get OAuth credentials for a provider and tenant."""
        key = f"{provider}:{tenant_id}"
        return self._credentials.get(key)

    async def store_credentials(
        self,
        provider: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: List[str],
    ) -> OAuthCredentials:
        """Store OAuth credentials securely."""
        key = f"{provider}:{tenant_id}"

        credentials = OAuthCredentials(
            provider=provider,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            tenant_id=tenant_id,
        )

        self._credentials[key] = credentials

        logger.info(f"Stored OAuth credentials for {provider} (tenant: {tenant_id})")
        return credentials

    async def initiate_flow(
        self,
        provider: str,
        client_id: str,
        redirect_uri: str,
        scopes: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Initiate OAuth flow and return authorization URL."""
        try:
            # Get OAuth provider configuration
            await self._get_oauth_config(provider)

            # Build authorization URL
            auth_params = {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": " ".join(scopes),
                "state": str(uuid.uuid4()),
            }

            if provider == "google":
                auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + "&".join(
                    [f"{k}={v}" for k, v in auth_params.items()]
                )
            elif provider == "linkedin":
                auth_url = (
                    "https://www.linkedin.com/oauth/v2/authorization?"
                    + "&".join([f"{k}={v}" for k, v in auth_params.items()])
                )
            elif provider == "microsoft":
                auth_url = (
                    "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
                    + "&".join([f"{k}={v}" for k, v in auth_params.items()])
                )
            elif provider == "github":
                auth_url = "https://github.com/login/oauth/authorize?" + "&".join(
                    [f"{k}={v}" for k, v in auth_params.items()]
                )
            else:
                # For custom providers, use a generic OAuth 2.0 flow
                auth_url = f"/oauth/authorize?provider={provider}&" + "&".join(
                    [f"{k}={v}" for k, v in auth_params.items()]
                )

            logger.info(f"Initiated OAuth flow for {provider}: {auth_url}")
            return auth_url

        except Exception as e:
            logger.error(f"Failed to initiate OAuth flow for {provider}: {e}")
            raise HTTPException(status_code=500, detail="Failed to initiate OAuth flow")

    async def exchange_code_for_tokens(
        self,
        provider: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        authorization_code: str,
        scopes: List[str],
    ) -> OAuthTokenResponse:
        """Exchange authorization code for access tokens."""
        try:
            # Get OAuth provider configuration
            await self._get_oauth_config(provider)

            # Exchange code for tokens
            token_data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            }

            if provider == "google":
                token_url = "https://oauth2.googleapis.com/token"
            elif provider == "linkedin":
                token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            elif provider == "microsoft":
                token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            elif provider == "github":
                token_url = "https://github.com/login/oauth/access_token"
            else:
                token_url = f"/oauth/token?provider={provider}"

            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.post(token_url, data=token_data)
                        response.raise_for_status()
                        token_data = response.json()
                    break
                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    if attempt < max_retries:
                        await asyncio.sleep(0.5 * (2**attempt))
                    else:
                        logger.error("OAuth token exchange failed after retries: %s", e)
                        raise HTTPException(
                            status_code=504,
                            detail="OAuth provider temporarily unavailable",
                        ) from e

            token_response = OAuthTokenResponse(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope"),
            )

            # Cache the token
            key = f"{provider}:default"
            self._token_cache[key] = token_response

            logger.info(f"Exchanged code for {provider} tokens")
            return token_response

        except Exception as e:
            logger.error(f"Failed to exchange code for {provider} tokens: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to exchange code for tokens"
            )

    async def get_user_info(
        self,
        provider: str,
        access_token: str,
    ) -> OAuthUserInfo:
        """Get user information from OAuth provider."""
        try:
            if provider == "google":
                user_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            elif provider == "linkedin":
                user_url = "https://api.linkedin.com/v2/people/me"
            elif provider == "microsoft":
                user_url = "https://graph.microsoft.com/v1.0/me"
            elif provider == "github":
                user_url = "https://api.github.com/user"
            else:
                raise HTTPException(
                    status_code=400, detail=f"Unsupported OAuth provider: {provider}"
                )

            headers = {"Authorization": f"Bearer {access_token}"}

            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.get(user_url, headers=headers)
                        response.raise_for_status()
                        user_data = response.json()
                    break
                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    if attempt < max_retries:
                        await asyncio.sleep(0.5 * (2**attempt))
                    else:
                        logger.error("OAuth user info failed after retries: %s", e)
                        raise HTTPException(
                            status_code=504,
                            detail=f"OAuth provider temporarily unavailable",
                        ) from e

            user_info = OAuthUserInfo(
                id=user_data.get("id"),
                email=user_data.get("email"),
                name=user_data.get("name"),
                avatar_url=user_data.get("picture"),
                provider=provider,
            )

            logger.info(f"Retrieved user info from {provider}")
            return user_info

        except Exception as e:
            logger.error(f"Failed to get user info from {provider}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get user info from {provider}"
            )

    async def refresh_token(
        self, provider: str, refresh_token: str
    ) -> OAuthTokenResponse:
        """Refresh access token using refresh token."""
        try:
            # Get OAuth provider configuration
            await self._get_oauth_config(provider)

            token_url = (
                f"/oauth/token?grant_type=refresh_token&refresh_token={refresh_token}"
            )

            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.post(token_url)
                        response.raise_for_status()
                        token_data = response.json()
                    break
                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    if attempt < max_retries:
                        await asyncio.sleep(0.5 * (2**attempt))
                    else:
                        logger.error("OAuth token refresh failed after retries: %s", e)
                        raise HTTPException(
                            status_code=504,
                            detail="OAuth provider temporarily unavailable",
                        ) from e

            token_response = OAuthTokenResponse(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope"),
            )

            # Update cache
            key = f"{provider}:default"
            self._token_cache[key] = token_response

            logger.info(f"Refreshed token for {provider}")
            return token_response

        except Exception as e:
            logger.error(f"Failed to refresh token for {provider}: {e}")
            raise HTTPException(status_code=500, detail="Failed to refresh token")

    async def _get_oauth_config(self, provider: str) -> Dict[str, Any]:
        """Get OAuth configuration for provider."""
        # In a real implementation, this would fetch from database or config
        oauth_configs = {
            "google": {
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scopes": ["openid", "email", "profile"],
            },
            "linkedin": {
                "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
                "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
                "user_info_url": "https://api.linkedin.com/v2/people/me",
                "scopes": ["r_liteprofile", "r_emailaddress", "r_basic_profile"],
            },
            "microsoft": {
                "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "user_info_url": "https://graph.microsoft.com/v1.0/me",
                "scopes": ["openid", "email", "profile", "User.Read"],
            },
            "github": {
                "auth_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "user_info_url": "https://api.github.com/user",
                "scopes": ["user:email"],
            },
        }

        return oauth_configs.get(provider, {})


# Factory function
def create_oauth_handler() -> OAuthHandler:
    """Create OAuth handler instance."""
    return OAuthHandler()
