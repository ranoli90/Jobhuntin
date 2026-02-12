"""
Part 1: Configuration and Environments

Typed Settings model that:
  - Loads from environment variables with sensible local defaults
  - Enforces critical vars in staging/prod (fails startup if missing)
  - Provides env-specific tuning (timeouts, polling, retries)
  - Integrates with FastAPI (dependency) and worker (direct import)
"""

from __future__ import annotations

import os
import sys
from enum import StrEnum
from functools import lru_cache
import logging

# Basic logging before shared.logging_config is ready
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sorce.config")

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Environment(StrEnum):
    LOCAL = "local"
    STAGING = "staging"
    PROD = "prod"


class Settings(BaseSettings):
    """Central configuration for API and worker processes."""

    # ── Core ─────────────────────────────────────────────────────
    env: Environment = Environment.LOCAL

    # ── Database ─────────────────────────────────────────────────
    database_url: str = "postgresql://dpg-d66ck524d50c73bas62g-a:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a.oregon-postgres.render.com/dpg-d66ck524d50c73bas62g"
    db_pool_min: int = 2
    db_pool_max: int = 10

    # ── Web App ──────────────────────────────────────────────────
    app_base_url: str = "http://localhost:5173"

    # ── Redis ────────────────────────────────────────────────────
    redis_url: str | None = None

    # ── LLM ──────────────────────────────────────────────────────
    llm_api_base: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = ""
    llm_model: str = "openrouter/free"  # User requested free router
    llm_max_tokens: int = 4096
    llm_rate_limit_per_minute: int = 60  # in-process approximate cap
    llm_retry_count: int = 2
    llm_timeout_seconds: int = 60  # Increased for free model latency

    # ── Playwright / Agent ───────────────────────────────────────
    playwright_browser_type: str = "chromium"
    playwright_headless: bool = True
    max_concurrent_browser_contexts: int = 1

    # ── Agent tuning ─────────────────────────────────────────────
    poll_interval_seconds: int = 5
    max_attempts: int = 3
    max_form_steps: int = 5
    page_timeout_ms: int = 60_000
    submit_timeout_ms: int = 30_000

    # ── Rate limiting / guardrails ───────────────────────────────
    max_applications_per_minute: int = 30
    magic_link_requests_per_hour: int = 20
    magic_link_rate_limit_window_seconds: int = 300
    magic_link_token_ttl_seconds: int = 3600

    # ── Blueprints ────────────────────────────────────────────────
    default_blueprint_key: str = "job-app"
    enabled_blueprints: str = "job-app,grant,staffing-agency"  # comma-separated list

    # ── Security ─────────────────────────────────────────────────
    csrf_secret: str = ""  # Required in prod - generate with: secrets.token_hex(32)
    request_id_header: str = "X-Request-ID"
    db_ssl_ca_cert_path: str = (
        ""  # Path to CA cert for DB SSL verification (overrides CERT_NONE)
    )

    # ── Upload limits ─────────────────────────────────────────────
    max_upload_size_bytes: int = 15_728_640  # 10 MB for PDF resumes
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

    # ── Stripe / Billing ─────────────────────────────────────────
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = "dev-placeholder-webhook-secret"
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

    # Webhook signing (set real secrets in prod/staging)
    webhook_signing_secret: str = "dev-placeholder-webhook-signing"

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
    slack_webhook_url: str = ""
    slack_enterprise_channel: str = "#enterprise-alerts"
    slack_ops_channel: str = "#ops-alerts"

    # ── SSO ────────────────────────────────────────────────────────
    sso_sp_entity_id: str = "https://api.jobhuntin.com/sso/saml/metadata"
    sso_sp_acs_url: str = "https://api.jobhuntin.com/sso/saml/acs"
    sso_session_secret: str = ""  # HMAC secret for SSO session tokens

    # ── Sentry / Observability ─────────────────────────────────────
    sentry_dsn: str = ""
    sentry_environment: str = "production"
    sentry_traces_sample_rate: float = 0.1

    # ── Worker scaling ─────────────────────────────────────────────
    worker_instance_count: int = 1
    enterprise_db_pool_min: int = 2
    enterprise_db_pool_max: int = 10
    read_replica_url: str = ""  # Supabase read replica connection string

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
    email_from: str = "JobHuntin <noreply@jobhuntin.com>"

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

    # ── Logging ──────────────────────────────────────────────────
    log_level: str = "INFO"
    log_json: bool = False  # local: human-readable; staging/prod: JSON

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

    def validate_critical(self) -> None:
        """Abort startup in staging/prod if critical secrets are missing."""
        if self.env in (Environment.STAGING, Environment.PROD):
            missing: list[str] = []
            if not self.database_url or "localhost" in self.database_url:
                missing.append("DATABASE_URL (must not be localhost)")
            if not self.llm_api_key:
                missing.append("LLM_API_KEY")

            if not self.app_base_url:
                missing.append("APP_BASE_URL")
            if not self.csrf_secret:
                missing.append("CSRF_SECRET")
            # SSO_SESSION_SECRET is optional - only required for ENTERPRISE plans with SSO enabled
            # if not self.sso_session_secret:
            #     missing.append("SSO_SESSION_SECRET")
            if self.stripe_secret_key and not self.stripe_webhook_secret:
                missing.append(
                    "STRIPE_WEBHOOK_SECRET (required when STRIPE_SECRET_KEY is set)"
                )
            if not self.webhook_signing_secret:
                missing.append("WEBHOOK_SIGNING_SECRET")
            # Warn (non-fatal) if using a free-tier LLM model in production
            if ":free" in self.llm_model:
                logger.warning(
                    "LLM model '%s' is a free-tier model with no SLA. "
                    "Set LLM_MODEL to a production-grade model for reliability.",
                    self.llm_model,
                )
            if missing:
                logger.critical(
                    "FATAL: Missing critical env vars for %s: %s",
                    self.env.value,
                    ", ".join(missing),
                )
                sys.exit(1)

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
