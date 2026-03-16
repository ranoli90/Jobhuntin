"""Part 1: Configuration and Environments.

Typed Settings model that:
  - Loads from environment variables with sensible local defaults
  - Enforces critical vars in staging/prod (fails startup if missing)
  - Provides env-specific tuning (timeouts, polling, retries)
  - Integrates with FastAPI (dependency) and worker (direct import)
"""

from __future__ import annotations

import logging
import os
from enum import StrEnum
from functools import lru_cache
from urllib.parse import urlparse

# Basic logging before shared.logging_config is ready
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sorce.config")

from pydantic import field_validator
from pydantic_settings import BaseSettings


KNOWN_WEAK_SECRETS = {
    "secret",
    "password",
    "123456",
    "12345678",
    "123456789",
    "qwerty",
    "abc123",
    "monkey",
    "1234567",
    "letmein",
    "trustno1",
    "dragon",
    "baseball",
    "iloveyou",
    "master",
    "sunshine",
    "ashley",
    "bailey",
    "passw0rd",
    "shadow",
    "123123",
    "654321",
    "superman",
    "qazwsx",
    "michael",
    "football",
    "password1",
    "password123",
    "welcome",
    "welcome1",
    "admin",
    "root",
    "toor",
    "test",
    "test123",
    "guest",
    "changeme",
    "default",
}


class Environment(StrEnum):
    LOCAL = "local"
    STAGING = "staging"
    PROD = "prod"


class Settings(BaseSettings):
    """Central configuration for API and worker processes."""

    # ── Core ─────────────────────────────────────────────────────
    env: Environment = Environment.LOCAL

    @property
    def is_local_dev(self) -> bool:
        return self.env == Environment.LOCAL

    @property
    def is_prod(self) -> bool:
        return self.env == Environment.PROD

    @property
    def parsed_local_redirect_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.local_redirect_origins.split(",")
            if origin.strip()
        ]

    @property
    def resend_emails_api_url(self) -> str:
        return f"{self.resend_api_base.rstrip('/')}/emails"

    # ── Database ─────────────────────────────────────────────────
    # SECURITY: Database URL must be provided via DATABASE_URL environment variable
    # Hardcoded credentials are a critical security vulnerability
    database_url: str = ""  # Required - must be set via DATABASE_URL env var
    db_pool_min: int = 5
    db_pool_max: int = 25  # Per-process limit; use PgBouncer for higher concurrency

    # ── Web App ──────────────────────────────────────────────────
    app_base_url: str = "https://sorce-web.onrender.com"
    # Admin dashboard base URL (e.g. http://localhost:5174 or https://admin.jobhuntin.com).
# Used for admin magic link redirects.
    app_admin_base_url: str = ""
    # Public URL of the API (for magic link verify redirect). Set API_PUBLIC_URL in prod.
    api_public_url: str = "https://sorce-api.onrender.com"
    local_redirect_origins: str = (
        "http://localhost:5173,http://localhost:3000,"
        "http://127.0.0.1:5173,http://127.0.0.1:3000"
    )
    # App branding (used in emails, etc.)
    app_name: str = "JobHuntin"
    app_initials: str = "JH"
    app_tagline: str = "Find your next job, faster"
    support_email: str = "support@jobhuntin.com"

    # ── Redis ────────────────────────────────────────────────────
    redis_url: str | None = None
    local_redis_url: str = "redis://localhost:6379"

    # ── LLM ──────────────────────────────────────────────────────
    llm_api_base: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = ""
    llm_model: str = "openai/gpt-4o-mini"
    llm_fallback_models: str = "anthropic/claude-3-haiku"
    llm_max_tokens: int = 2048
    llm_rate_limit_per_minute: int = 60
    llm_retry_count: int = 2
    llm_timeout_seconds: int = 45

    # Production LLM configuration (recommendation #126)
    # Recommended production models (set LLM_MODEL to one of these in production):
    # - "openai/gpt-4o-mini" - Best value, fast, reliable ($0.15/1M input, $0.60/1M output)
    # - "openai/gpt-4o" - Best quality for complex tasks ($2.50/1M input, $10/1M output)
    # - "anthropic/claude-3.5-sonnet" - Excellent for structured outputs ($3/1M input, $15/1M output)
    # - "anthropic/claude-3-haiku" - Fast and cheap ($0.25/1M input, $1.25/1M output)
    # - "google/gemini-2.0-flash" - Very fast, good quality ($0.10/1M input, $0.40/1M output)
    llm_production_model: str = "openai/gpt-4o-mini"  # Recommended production model
    llm_production_fallbacks: str = "anthropic/claude-3-haiku"  # Production fallbacks
    llm_enable_auto_upgrade: bool = True  # Auto-upgrade from free tier in production

    # ── Playwright / Agent ───────────────────────────────────────
    playwright_browser_type: str = "chromium"
    playwright_headless: bool = True
    max_concurrent_browser_contexts: int = 5  # Each context uses ~500MB RAM; scale via worker replicas

    # ── Agent tuning ─────────────────────────────────────────────
    poll_interval_seconds: int = 5
    max_attempts: int = 3
    max_form_steps: int = 5
    page_timeout_ms: int = 60_000
    submit_timeout_ms: int = 30_000

    # ── Rate limiting / guardrails ───────────────────────────────
    max_applications_per_minute: int = 30
    # H1: Rate Limiting Hardening - Reduced from 20 to 10 per hour to prevent enumeration
    magic_link_requests_per_hour: int = 10
    magic_link_rate_limit_window_seconds: int = 3600  # 1 hour window
    magic_link_token_ttl_seconds: int = 3600
    # H2: IP Binding - Bind magic link tokens to requesting IP (security feature)
    # When enabled, magic links can only be used from the IP that requested them
    # This prevents token theft attacks. #9: Default True in prod (override with MAGIC_LINK_BIND_TO_IP=false to disable)
# .
    magic_link_bind_to_ip: bool = False

    # ── Tenant Rate Limits (per tier) ────────────────────────────────
    # Free tier: 10 req/min, 100 req/hour, 2 concurrent
    tenant_rate_limit_free_rpm: int = 10
    tenant_rate_limit_free_rph: int = 100
    tenant_rate_limit_free_concurrent: int = 2
    # Pro tier: 60 req/min, 1000 req/hour, 10 concurrent
    tenant_rate_limit_pro_rpm: int = 60
    tenant_rate_limit_pro_rph: int = 1000
    tenant_rate_limit_pro_concurrent: int = 10
    # Team tier: 100 req/min, 5000 req/hour, 25 concurrent
    tenant_rate_limit_team_rpm: int = 100
    tenant_rate_limit_team_rph: int = 5000
    tenant_rate_limit_team_concurrent: int = 25
    # Enterprise tier: 500 req/min, 25000 req/hour, 100 concurrent
    tenant_rate_limit_enterprise_rpm: int = 500
    tenant_rate_limit_enterprise_rph: int = 25000
    tenant_rate_limit_enterprise_concurrent: int = 100

    # ── AI Endpoint Rate Limits (per tier) ──────────────────────────
    # More restrictive limits due to LLM costs
    ai_rate_limit_free_rpm: int = 5
    ai_rate_limit_free_rph: int = 20
    ai_rate_limit_free_concurrent: int = 1
    ai_rate_limit_pro_rpm: int = 20
    ai_rate_limit_pro_rph: int = 200
    ai_rate_limit_pro_concurrent: int = 3
    ai_rate_limit_team_rpm: int = 50
    ai_rate_limit_team_rph: int = 500
    ai_rate_limit_team_concurrent: int = 10
    ai_rate_limit_enterprise_rpm: int = 200
    ai_rate_limit_enterprise_rph: int = 2000
    ai_rate_limit_enterprise_concurrent: int = 50

    # ── Upload Limits per tier ───────────────────────────────────────
    # Free tier upload limits
    upload_limit_free_resume_mb: int = 5
    upload_limit_free_cover_letter_mb: int = 2
    upload_limit_free_profile_image_mb: int = 2
    upload_limit_free_document_mb: int = 2
    upload_limit_free_resume_per_day: int = 3
    upload_limit_free_total_storage_mb: int = 50
    # Pro tier upload limits
    upload_limit_pro_resume_mb: int = 10
    upload_limit_pro_cover_letter_mb: int = 5
    upload_limit_pro_profile_image_mb: int = 5
    upload_limit_pro_document_mb: int = 10
    upload_limit_pro_resume_per_day: int = 20
    upload_limit_pro_total_storage_mb: int = 500
    # Enterprise tier upload limits
    upload_limit_enterprise_resume_mb: int = 25
    upload_limit_enterprise_cover_letter_mb: int = 10
    upload_limit_enterprise_profile_image_mb: int = 10
    upload_limit_enterprise_document_mb: int = 50
    upload_limit_enterprise_resume_per_day: int = -1  # Unlimited
    upload_limit_enterprise_total_storage_mb: int = 5000

    # ── Cache TTLs ──────────────────────────────────────────────────
    cache_ttl_short_seconds: int = 60  # 1 minute for frequently changing data
    cache_ttl_medium_seconds: int = 300  # 5 minutes for moderately static data
    cache_ttl_long_seconds: int = 3600  # 1 hour for static data
    cache_ttl_job_results_seconds: int = 1800  # 30 minutes for job search results
    api_cache_disk_path: str = "/tmp/api_cache"

    # ── Connection Pool Settings ─────────────────────────────────────
    connection_pool_timeout_seconds: int = 30
    connection_pool_max_overflow: int = 10
    connection_pool_recycle_seconds: int = 3600

    # ── Timeout configuration ─────────────────────────────────────
    email_timeout_seconds: int = 10
    api_client_timeout_seconds: int = 30
    voice_interview_timeout_seconds: int = 30

    # ── Blueprints ────────────────────────────────────────────────
    default_blueprint_key: str = "job-app"
    enabled_blueprints: str = "job-app,grant,staffing-agency"  # comma-separated list

    # ── Security ─────────────────────────────────────────────────
    csrf_secret: str = ""  # REQUIRED — generate with: python -c "import secrets; print(secrets.token_hex(32))"
    jwt_secret: str = ""  # REQUIRED — generate with: python -c "import secrets; print(secrets.token_hex(32))"
    request_id_header: str = "X-Request-ID"
    # Comma-separated CORS origins (overrides/augments built-in list). No wildcards.
    cors_allowed_origins: str = ""
    db_ssl_ca_cert_path: str = (
        ""  # Path to CA cert for DB SSL verification (overrides CERT_NONE)
    )

    # ── Upload limits ─────────────────────────────────────────────
    max_upload_size_bytes: int = 15_728_640  # 15 MB for PDF resumes
    max_avatar_size_bytes: int = 5_242_880  # 5 MB for avatar images
    resume_signed_url_ttl_seconds: int = 3600  # 1 hour

    # ── Storage (S3/R2/Render Disk) ───────────────────────────────
    storage_type: str = "local"  # local, s3, render_disk
    s3_endpoint_url: str = ""  # e.g., https://s3.amazonaws.com or R2 endpoint
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "auto"
    s3_bucket: str = "resumes"
    s3_public_url: str = ""  # Public URL base for serving files
    render_disk_path: str = "/opt/render/project/data/storage"
    local_storage_path: str = "./storage"

    # ── Adzuna Job Board API ─────────────────────────────────────
    adzuna_app_id: str = ""
    adzuna_api_key: str = ""
    adzuna_default_country: str = "us"
    adzuna_additional_countries: str = ""  # comma-separated ISO country codes
    adzuna_results_per_page: int = 50
    adzuna_max_pages: int = 3
    adzuna_job_ttl_days: int = 14
    adzuna_rate_limit_per_minute: int = 60

    @field_validator("adzuna_app_id", "adzuna_api_key")
    @classmethod
    def validate_adzuna_credentials(cls, v: str) -> str:
        """Adzuna is optional when JobSpy is primary. Empty/placeholder allowed."""
        if v and v not in (
            "your-adzuna-app-id",
            "your-adzuna-api-key",
            "your-app-id",
            "your-api-key",
        ):
            return v
        return ""  # Allow empty - JobSpy is primary; Adzuna is optional fallback

    # ── JobSpy Job Aggregation (Replaces Adzuna) ──────────────────
    jobspy_enabled: bool = True
    jobspy_sources: str = "indeed,linkedin,zip_recruiter,glassdoor"
    jobspy_results_per_source: int = 50
    jobspy_proxies: str = ""  # Comma-separated: "http://user:pass@host:port"
    jobspy_proxy_rotation: bool = True
    jobspy_use_free_proxies: bool = (
        False  # When no proxies configured, fetch from GimmeProxy/PubProxy
    )
    jobspy_validate_proxies: bool = (
        False  # Validate free proxies with httpbin before use (slower)
    )
    jobspy_linkedin_fetch_description: bool = True
    jobspy_hours_old: int = 168  # Only fetch jobs from last 7 days
    jobspy_job_ttl_days: int = 7
    jobspy_sync_interval_hours: int = 3
    jobspy_concurrent_sources: int = 2
    jobspy_timeout_seconds: int = 120
    jobspy_description_max_length: int = 50000
    jobspy_quality_min_desc_length: int = 50
    jobspy_retry_count: int = (
        2  # Retries with exponential backoff on transient failures
    )
    jobspy_rate_limit_per_minute: int = (
        12  # Proactive throttling between fetches (1 per ~5s)
    )

    # ── Stripe / Billing ─────────────────────────────────────────
    stripe_secret_key: str = ""
    # MUST be set via STRIPE_WEBHOOK_SECRET env in production (validation in validate_critical)
    stripe_webhook_secret: str = ""
    stripe_pro_price_id: str = ""  # Stripe Price ID for PRO plan ($29/month)
    stripe_team_base_price_id: str = ""  # Stripe Price ID for TEAM base ($199/month)
    stripe_team_seat_price_id: str = (
        ""  # Stripe Price ID for TEAM per-seat ($49/seat/month)
    )
    stripe_free_trial_days: int = 0  # 0 = no trial; set 7 for 7-day trial
    team_included_seats: int = 3  # seats included in TEAM base price
    stripe_enterprise_price_id: str = ""  # Stripe Price for ENTERPRISE ($999+/month)
    stripe_pro_annual_price_id: str = ""  # PRO annual ($278/yr = 20% off)
    stripe_team_annual_price_id: str = ""  # TEAM annual ($1,910/yr = 20% off)
    stripe_enterprise_annual_price_id: str = (
        ""  # ENTERPRISE annual ($9,590/yr = 20% off)
    )
    annual_discount_pct: int = 20  # percent discount for annual billing

    # Webhook signing. MUST be set via WEBHOOK_SIGNING_SECRET env in production (validation in validate_critical)
    webhook_signing_secret: str = ""

    # ── Stripe Connect (Marketplace) ──────────────────────────────
    stripe_connect_client_id: str = ""
    marketplace_platform_fee_pct: int = 30  # platform takes 30%

    # ── API v2 Platform ───────────────────────────────────────────
    api_v2_metered_price_id: str = ""  # Stripe metered price ($0.10/submission)
    api_v2_pro_price_id: str = ""  # API PRO tier ($99/mo)
    staffing_price_per_submit_cents: int = 200  # $2 per successful submission
    staffing_base_monthly_cents: int = 200000  # $2k/month base

    # ── Alerting v2 ──────────────────────────────────────────────
    pagerduty_api_key: str = ""
    pagerduty_service_id: str = ""
    opsgenie_api_key: str = ""  # M10: Opsgenie integration
    opsgenie_api_url: str = (
        "https://api.opsgenie.com/v2/alerts"  # M10: Opsgenie API endpoint
    )
    slack_webhook_url: str = ""
    slack_enterprise_channel: str = "#enterprise-alerts"
    slack_ops_channel: str = "#ops-alerts"
    alerting_footer_icon_url: str = "https://sorce.app/favicon.ico"

    # ── SSO ────────────────────────────────────────────────────────
    sso_sp_entity_id: str = "https://sorce-api.onrender.com/sso/saml/metadata"
    sso_sp_acs_url: str = "https://sorce-api.onrender.com/sso/saml/acs"
    sso_session_secret: str = ""  # HMAC secret for SSO session tokens

    # ── Sentry / Observability ─────────────────────────────────────
    sentry_dsn: str = ""
    sentry_environment: str = "production"
    sentry_traces_sample_rate: float = 0.1

    # ── Worker scaling ─────────────────────────────────────────────
    worker_instance_count: int = 1
    enterprise_db_pool_min: int = 5  # Increased from 2 for enterprise performance
    enterprise_db_pool_max: int = 25  # Increased from 10 for enterprise scaling
    read_replica_url: str = ""  # Read replica connection string (optional, for scaling)

    # ── Browser pool (distributed scaling) ────────────────────────
    browserless_url: str = (
        ""  # e.g. wss://chrome.browserless.io?token=XXX — empty = local Chromium
    )
    browserless_token: str = ""
    browser_pool_size: int = 1  # number of browser instances in the pool
    browser_context_max_uses: int = (
        50  # recycle context after N uses to prevent memory leaks
    )
    browser_context_memory_limit_mb: int = 512

    # ── Push Notifications ─────────────────────────────────────────
    expo_push_access_token: str = ""  # Expo push notification access token

    # ── Email (Resend) ────────────────────────────────────────────
    resend_api_key: str = ""
    resend_webhook_secret: str = ""  # #1: For Resend webhook signature verification
    resend_api_base: str = "https://api.resend.com"
    email_from: str = "JobHuntin <noreply@jobhuntin.com>"
    alert_email_from: str = "alerts@sorce.app"

    # ── CAPTCHA (Bot Protection) ───────────────────────────────────
    recaptcha_secret_key: str = ""  # reCAPTCHA v3 secret key
    hcaptcha_secret_key: str = ""  # hCaptcha secret key
    turnstile_secret_key: str = ""  # Cloudflare Turnstile secret key
    captcha_provider: str = "recaptcha"  # recaptcha, hcaptcha, turnstile
    captcha_min_score: float = 0.5  # Minimum score for reCAPTCHA v3

    # ── Promotions ───────────────────────────────────────────────────
    first_month_coupon: str = "FIRST_MONTH_10"  # Stripe coupon ID for $10 first month

    # ── Referral Program ──────────────────────────────────────────
    referral_reward_apps: int = 5  # bonus apps for both referrer and referee

    # ── App Store URLs ────────────────────────────────────────────
    app_store_url: str = "https://apps.apple.com/app/jobhuntin/idXXXXXXXXXX"
    play_store_url: str = (
        "https://play.google.com/store/apps/details?id=com.jobhuntin.mobile"
    )

    # ── Agent guardrails ──────────────────────────────────────────
    agent_enabled: bool = True  # set False to emergency-stop the worker
    prompt_version_override: str = ""  # e.g. "v2" to force a specific prompt version
    # apply_strategy: auto = try HTTP first for Greenhouse/Lever; browser_only = skip
    apply_strategy: str = "auto"

    # ── Logging ──────────────────────────────────────────────────
    log_level: str = "INFO"
    log_json: bool = False  # local: human-readable; staging/prod: JSON

    # ── Vector Database (Pinecone/Weaviate) ──────────────────────
    vector_db_provider: str = "memory"  # memory, pinecone, weaviate
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1-aws"
    pinecone_index_name: str = "jobhuntin"
    weaviate_url: str = ""
    weaviate_api_key: str = ""

    # ── Google Drive Integration ───────────────────────────────────
    google_drive_client_id: str = ""
    google_drive_client_secret: str = ""

    # ── Notion Integration ─────────────────────────────────────────
    notion_client_id: str = ""
    notion_client_secret: str = ""

    # ── Slack Integration ──────────────────────────────────────────
    slack_client_id: str = ""
    slack_client_secret: str = ""
    slack_signing_secret: str = ""

    # ── LinkedIn Job Board ─────────────────────────────────────────
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""

    # ── Indeed Job Board ───────────────────────────────────────────
    indeed_publisher_id: str = ""

    # ── Glassdoor Job Board ────────────────────────────────────────
    glassdoor_partner_id: str = ""
    glassdoor_api_key: str = ""

    # ── Google Calendar Integration ────────────────────────────────
    google_calendar_client_id: str = ""
    google_calendar_client_secret: str = ""

    # ── Microsoft/Outlook Calendar Integration ─────────────────────
    outlook_client_id: str = ""
    outlook_client_secret: str = ""

    # ── HaveIBeenPwned API (breach checking) ────────────────────────
    hibp_api_key: str = ""

    # ── Clearbit (company logos) ────────────────────────────────────
    clearbit_api_key: str = ""

    # ── CAPTCHA Solving Services ─────────────────────────────────────
    captcha_solvers: str = ""  # Comma-separated: 2captcha,anticaptcha
    twocaptcha_api_key: str = ""
    anticaptcha_api_key: str = ""
    captcha_solve_timeout: int = 120  # seconds
    captcha_max_attempts: int = 3

    # ── Feature Flags ───────────────────────────────────────────────
    enable_interview_simulator: bool = True
    enable_career_path: bool = True
    enable_calendar_integration: bool = True
    enable_mfa: bool = True
    enable_ccpa_portal: bool = True

    model_config = {
        "env_prefix": "",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    # ── Validators ───────────────────────────────────────────────
    @field_validator("env", mode="before")
    @classmethod
    def _normalize_env(cls, v: str) -> str:
        return v.strip().lower()

    @staticmethod
    def _is_localhost_host(host: str | None) -> bool:
        return host in {"localhost", "127.0.0.1", "0.0.0.0"}

    def _validate_runtime_secret(
        self,
        *,
        name: str,
        value: str,
        missing: list[str],
        reject_weak: bool = False,
    ) -> None:
        if not value:
            missing.append(f"{name} (required)")
            return
        if "dev-" in value or "change-in-production" in value:
            missing.append(f"{name} (dev default not allowed in prod)")
            return
        if len(value) < 32:
            missing.append(
                f"{name} (must be at least 32 characters for security; current length: {len(value)})"
            )
            return
        if reject_weak and value.lower().strip() in KNOWN_WEAK_SECRETS:
            missing.append(
                f"{name} (known weak secret not allowed - choose a strong, unique secret)"
            )

    def _validate_public_url(self, *, name: str, value: str, missing: list[str]) -> None:
        normalized = value.strip()
        if not normalized or normalized == "[REDACTED]":
            missing.append(f"{name} (must be set, not placeholder)")
            return

        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            missing.append(f"{name} (must be a valid absolute http(s) URL)")
            return

        if self.env in (Environment.STAGING, Environment.PROD) and self._is_localhost_host(parsed.hostname):
            missing.append(f"{name} (must not use localhost in {self.env.value})")
        elif self.env == Environment.PROD and parsed.scheme != "https":
            missing.append(f"{name} (must use https in prod)")

    def _validate_cors_origins(self, *, missing: list[str]) -> None:
        if not self.cors_allowed_origins:
            return

        invalid_origins: list[str] = []
        for origin in self.cors_allowed_origins.split(","):
            normalized = origin.strip()
            if not normalized:
                continue
            if normalized == "*":
                invalid_origins.append("* (wildcard not allowed)")
                continue
            if "[REDACTED]" in normalized:
                invalid_origins.append(f"{normalized} (placeholder not allowed)")
                continue

            parsed = urlparse(normalized)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                invalid_origins.append(
                    f"{normalized} (must be a valid absolute http(s) origin)"
                )
                continue

            if self.env in (Environment.STAGING, Environment.PROD) and self._is_localhost_host(parsed.hostname):
                invalid_origins.append(
                    f"{normalized} (localhost origins are not allowed in {self.env.value})"
                )

        if invalid_origins:
            missing.append(
                "CORS_ALLOWED_ORIGINS (invalid entries: " + "; ".join(invalid_origins) + ")"
            )

    def validate_critical(self) -> None:
        """Abort startup in staging/prod if critical secrets are missing."""
        if self.env in (Environment.STAGING, Environment.PROD):
            missing: list[str] = []
            if not self.database_url:
                missing.append("DATABASE_URL (required)")
            else:
                parsed_database_url = urlparse(self.database_url)
                if (
                    not parsed_database_url.scheme.startswith("postgres")
                    or not parsed_database_url.netloc
                ):
                    missing.append(
                        "DATABASE_URL (must be a valid PostgreSQL connection URL)"
                    )
                elif self._is_localhost_host(parsed_database_url.hostname):
                    missing.append("DATABASE_URL (must not be localhost)")
            if not self.llm_api_key:
                missing.append("LLM_API_KEY")

            self._validate_public_url(
                name="APP_BASE_URL", value=self.app_base_url, missing=missing
            )
            self._validate_public_url(
                name="API_PUBLIC_URL", value=self.api_public_url, missing=missing
            )
            self._validate_runtime_secret(
                name="CSRF_SECRET",
                value=self.csrf_secret,
                missing=missing,
                reject_weak=True,
            )
            self._validate_runtime_secret(
                name="JWT_SECRET",
                value=self.jwt_secret,
                missing=missing,
                reject_weak=True,
            )
            self._validate_cors_origins(missing=missing)
            # #8: Redis required for token replay protection and session revocation
            if not self.redis_url:
                missing.append(
                    "REDIS_URL (required for token replay protection and session revocation)"
                )
            else:
                parsed_redis_url = urlparse(self.redis_url)
                if (
                    parsed_redis_url.scheme not in {"redis", "rediss"}
                    or not parsed_redis_url.netloc
                ):
                    missing.append(
                        "REDIS_URL (must be a valid redis:// or rediss:// URL)"
                    )
                elif self.env == Environment.PROD and self._is_localhost_host(parsed_redis_url.hostname):
                    missing.append("REDIS_URL (must not use localhost in prod)")
            # SSO_SESSION_SECRET is optional - only required for ENTERPRISE plans with SSO enabled
            # if not self.sso_session_secret:
            #     missing.append("SSO_SESSION_SECRET")
            if self.stripe_secret_key and not self.stripe_webhook_secret:
                missing.append(
                    "STRIPE_WEBHOOK_SECRET (required when STRIPE_SECRET_KEY is set)"
                )
            if self.stripe_webhook_secret in ("", "dev-placeholder-webhook-secret"):
                if self.stripe_secret_key:
                    missing.append(
                        "STRIPE_WEBHOOK_SECRET (placeholder value not allowed in production)"
                    )
            if self.webhook_signing_secret in ("", "dev-placeholder-webhook-signing"):
                missing.append(
                    "WEBHOOK_SIGNING_SECRET (placeholder value not allowed in production)"
                )
            # Warn (non-fatal) if using a free-tier LLM model in production
            # Auto-upgrade to production model if enabled (recommendation #126)
            if ":free" in self.llm_model:
                if self.llm_enable_auto_upgrade:
                    logger.warning(
                        "LLM model '%s' is a free-tier model. "
                        "Auto-upgrading to production model '%s' for reliability.",
                        self.llm_model,
                        self.llm_production_model,
                    )
                    object.__setattr__(self, "llm_model", self.llm_production_model)
                    if not self.llm_fallback_models and self.llm_production_fallbacks:
                        object.__setattr__(
                            self, "llm_fallback_models", self.llm_production_fallbacks
                        )
                else:
                    logger.warning(
                        "LLM model '%s' is a free-tier model with no SLA. "
                        "Set LLM_MODEL to a production-grade model for reliability.",
                        self.llm_model,
                    )
            if missing:
                msg = f"Missing critical env vars for {self.env.value}: {', '.join(missing)}"
                logger.critical("FATAL: %s", msg)
                raise RuntimeError(msg)

    # ── Environment-specific overrides applied after load ────────
    def apply_env_defaults(self) -> Settings:
        """Return self with env-specific tuning applied where user didn't override."""
        if self.env == Environment.LOCAL:
            # Faster iteration locally
            if os.environ.get("POLL_INTERVAL_SECONDS") is None:
                object.__setattr__(self, "poll_interval_seconds", 2)
            if os.environ.get("PAGE_TIMEOUT_MS") is None:
                object.__setattr__(self, "page_timeout_ms", 30_000)
            if os.environ.get("LOG_JSON") is None:
                object.__setattr__(self, "log_json", False)
            if os.environ.get("LOG_LEVEL") is None:
                object.__setattr__(self, "log_level", "DEBUG")
        elif self.env == Environment.PROD:
            # More conservative in production
            if os.environ.get("POLL_INTERVAL_SECONDS") is None:
                object.__setattr__(self, "poll_interval_seconds", 5)
            if os.environ.get("MAX_ATTEMPTS") is None:
                object.__setattr__(self, "max_attempts", 3)
            if os.environ.get("LOG_JSON") is None:
                object.__setattr__(self, "log_json", True)
            if os.environ.get("LOG_LEVEL") is None:
                object.__setattr__(self, "log_level", "INFO")
            if os.environ.get("LLM_RATE_LIMIT_PER_MINUTE") is None:
                object.__setattr__(self, "llm_rate_limit_per_minute", 40)
            # #9: IP binding for magic links - default True in prod (security)
            if os.environ.get("MAGIC_LINK_BIND_TO_IP") is None:
                object.__setattr__(self, "magic_link_bind_to_ip", True)
        elif self.env == Environment.STAGING:
            if os.environ.get("LOG_JSON") is None:
                object.__setattr__(self, "log_json", True)
        return self


# ---------------------------------------------------------------------------
# Singleton access
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load, validate, and return the global Settings singleton."""
    settings = Settings()
    settings.validate_critical()
    settings = settings.apply_env_defaults()
    return settings


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


def settings_dependency() -> Settings:
    """FastAPI Depends() compatible function."""
    return get_settings()
