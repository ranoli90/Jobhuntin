"""
Deep linking service for mobile universal links.

This addresses recommendation #45: Implement universal links for job applications.

Features:
- Generate universal links for iOS and Android
- Support for job details, application status, and onboarding flows
- Branch.io integration for attribution
- Firebase Dynamic Links alternative
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from urllib.parse import urlencode, urlparse, urljoin

import httpx

from shared.config import Settings, get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.deep_links")


class DeepLinkType(StrEnum):
    """Types of deep links."""
    JOB_DETAILS = "job"
    APPLICATION_STATUS = "application"
    ONBOARDING = "onboarding"
    MATCH_RESULTS = "matches"
    SETTINGS = "settings"
    SUBSCRIPTION = "subscription"
    REFERRAL = "referral"


@dataclass
class DeepLink:
    """A deep link with all its properties."""
    link_type: DeepLinkType
    resource_id: str | None = None
    params: dict[str, str] = field(default_factory=dict)
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    
    # Generated URLs
    universal_link: str | None = None
    android_link: str | None = None
    short_link: str | None = None


class DeepLinkService:
    """
    Service for generating and resolving deep links.
    
    Supports:
    - iOS Universal Links
    - Android App Links
    - Branch.io for attribution and short links
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._base_url = self._settings.app_base_url
        self._branch_key = getattr(self._settings, "branch_key", "") or ""
        self._branch_secret = getattr(self._settings, "branch_secret", "") or ""

    def generate_universal_link(
        self,
        link_type: DeepLinkType,
        resource_id: str | None = None,
        params: dict[str, str] | None = None,
        utm_params: dict[str, str] | None = None,
    ) -> DeepLink:
        """
        Generate a universal link that works on both iOS and Android.
        
        Universal links use the https:// format and are handled by the app
        when installed, or fall back to the web when not.
        """
        params = params or {}
        utm_params = utm_params or {}

        # Build path
        path = f"/app/{link_type.value}"
        if resource_id:
            path += f"/{resource_id}"

        # Build query params
        query_params = {}
        query_params.update(params)
        if utm_params:
            query_params.update({
                "utm_source": utm_params.get("source", ""),
                "utm_medium": utm_params.get("medium", ""),
                "utm_campaign": utm_params.get("campaign", ""),
            })

        # Remove empty params
        query_params = {k: v for k, v in query_params.items() if v}

        # Build full URL
        if query_params:
            url = f"{self._base_url}{path}?{urlencode(query_params)}"
        else:
            url = f"{self._base_url}{path}"

        return DeepLink(
            link_type=link_type,
            resource_id=resource_id,
            params=params,
            utm_source=utm_params.get("source"),
            utm_medium=utm_params.get("medium"),
            utm_campaign=utm_params.get("campaign"),
            universal_link=url,
            android_link=url,  # Same URL for Android App Links
        )

    async def generate_branch_link(
        self,
        link: DeepLink,
        channel: str = "mobile_app",
        feature: str = "deep_link",
        tags: list[str] | None = None,
    ) -> str:
        """
        Generate a Branch.io short link for attribution.
        
        Branch links provide:
        - Attribution tracking
        - Deferred deep linking
        - Short URLs for sharing
        """
        if not self._branch_key:
            logger.warning("Branch key not configured, returning universal link")
            return link.universal_link or ""

        # Build Branch link data
        branch_data = {
            "branch_key": self._branch_key,
            "campaign": link.utm_campaign or "",
            "channel": channel,
            "feature": feature,
            "tags": tags or [],
            "data": {
                "link_type": link.link_type.value,
                "resource_id": link.resource_id,
                **link.params,
                "$canonical_url": link.universal_link,
                "$og_title": self._get_og_title(link),
                "$og_description": self._get_og_description(link),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.branch.io/v1/url",
                    json=branch_data,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("url", link.universal_link or "")
                else:
                    logger.warning(
                        "Branch link creation failed: %s - %s",
                        resp.status_code,
                        resp.text,
                    )
                    return link.universal_link or ""
        except Exception as exc:
            logger.error("Error creating Branch link: %s", exc)
            return link.universal_link or ""

    def parse_universal_link(self, url: str) -> DeepLink | None:
        """
        Parse a universal link URL into a DeepLink object.
        
        Used by the mobile app to handle incoming links.
        """
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip("/").split("/")

            # Expected format: /app/{type}/{id}
            if len(path_parts) < 2 or path_parts[0] != "app":
                return None

            link_type_str = path_parts[1]
            try:
                link_type = DeepLinkType(link_type_str)
            except ValueError:
                return None

            resource_id = path_parts[2] if len(path_parts) > 2 else None

            # Parse query params
            params = {}
            utm_params = {}
            if parsed.query:
                for key, value in [
                    pair.split("=", 1) if "=" in pair else (pair, "")
                    for pair in parsed.query.split("&")
                ]:
                    if key.startswith("utm_"):
                        utm_params[key[4:]] = value
                    else:
                        params[key] = value

            return DeepLink(
                link_type=link_type,
                resource_id=resource_id,
                params=params,
                utm_source=utm_params.get("source"),
                utm_medium=utm_params.get("medium"),
                utm_campaign=utm_params.get("campaign"),
                universal_link=url,
            )

        except Exception as exc:
            logger.error("Error parsing universal link: %s", exc)
            return None

    def generate_referral_link(
        self,
        referrer_user_id: str,
        referral_code: str,
        channel: str = "share",
    ) -> DeepLink:
        """Generate a referral link for user sharing."""
        return self.generate_universal_link(
            link_type=DeepLinkType.REFERRAL,
            params={
                "ref": referral_code,
                "referrer_id": referrer_user_id,
            },
            utm_params={
                "source": "referral",
                "medium": channel,
                "campaign": "user_referral",
            },
        )

    def generate_job_share_link(
        self,
        job_id: str,
        job_title: str,
        company: str,
        share_channel: str = "share",
    ) -> DeepLink:
        """Generate a shareable link for a job posting."""
        return self.generate_universal_link(
            link_type=DeepLinkType.JOB_DETAILS,
            resource_id=job_id,
            params={
                "title": job_title,
                "company": company,
            },
            utm_params={
                "source": "job_share",
                "medium": share_channel,
                "campaign": "job_discovery",
            },
        )

    def _get_og_title(self, link: DeepLink) -> str:
        """Get Open Graph title for the link."""
        if link.link_type == DeepLinkType.JOB_DETAILS:
            return f"Job Opportunity on JobHuntin"
        elif link.link_type == DeepLinkType.REFERRAL:
            return "Join JobHuntin - Get 5 Free Applications"
        elif link.link_type == DeepLinkType.APPLICATION_STATUS:
            return "Your Application Status"
        return "JobHuntin - AI-Powered Job Search"

    def _get_og_description(self, link: DeepLink) -> str:
        """Get Open Graph description for the link."""
        if link.link_type == DeepLinkType.JOB_DETAILS:
            return "Check out this job opportunity matched just for you!"
        elif link.link_type == DeepLinkType.REFERRAL:
            return "Your friend invited you to JobHuntin. Sign up and get 5 free job applications!"
        elif link.link_type == DeepLinkType.APPLICATION_STATUS:
            return "Track your job application progress"
        return "Land your dream job with AI-powered job matching and auto-apply"


# iOS Universal Links configuration
# Add to apple-app-site-association file at /.well-known/apple-app-site-association:
APPLE_APP_SITE_ASSOCIATION = {
    "applinks": {
        "apps": [],
        "details": [
            {
                "appID": "TEAM_ID.com.jobhuntin.mobile",
                "paths": [
                    "/app/job/*",
                    "/app/application/*",
                    "/app/matches/*",
                    "/app/onboarding/*",
                    "/app/settings/*",
                    "/app/subscription/*",
                    "/app/referral/*",
                ],
            }
        ],
    }
}

# Android App Links configuration
# Add to assetlinks.json at /.well-known/assetlinks.json:
ANDROID_ASSET_LINKS = [
    {
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": "com.jobhuntin.mobile",
            "sha256_cert_fingerprints": [
                "CERTIFICATE_FINGERPRINT"  # Replace with actual fingerprint
            ],
        },
    }
]


# Singleton instance
_deep_link_service: DeepLinkService | None = None


def get_deep_link_service() -> DeepLinkService:
    """Get or create the singleton deep link service."""
    global _deep_link_service
    if _deep_link_service is None:
        _deep_link_service = DeepLinkService()
    return _deep_link_service
