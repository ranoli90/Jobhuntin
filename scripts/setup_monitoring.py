#!/usr/bin/env python
"""Setup monitoring and alerting for production.

This script helps configure:
- Slack webhooks for alert notifications
- Sentry for error tracking
- Alert rules for the AlertManager
"""



def setup_sentry(sentry_dsn: str, environment: str = "production"):
    """Initialize Sentry SDK for error tracking.

    Add this to your app startup (main.py):
    """
    code = f'''
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncpg import AsyncPGIntegration

sentry_sdk.init(
    dsn="{sentry_dsn}",
    environment="{environment}",
    traces_sample_rate=0.1,
    integrations=[
        FastApiIntegration(),
        AsyncPGIntegration(),
    ],
)
'''
    return code


def setup_slack_alerts():
    """Create Slack webhook configuration for alerts.

    In Slack:
    1. Go to https://api.slack.com/apps
    2. Create new app → Incoming Webhooks
    3. Add webhook to workspace
    4. Copy webhook URL

    Add to environment:
    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/TXXX/BXXX/XXXX
    """
    pass


def get_alert_rules():
    """Return built-in alert rules for production monitoring."""
    from packages.shared.alerting import AlertRule, AlertSeverity

    return [
        AlertRule(
            name="high_error_rate",
            description="Error rate exceeds 5% in 5 minutes",
            severity=AlertSeverity.ERROR,
            window_seconds=300,
            threshold=0.05,
            comparison="gt",
            cooldown_seconds=300,
        ),
        AlertRule(
            name="high_latency_p99",
            description="P99 latency exceeds 1 second",
            severity=AlertSeverity.WARNING,
            window_seconds=300,
            threshold=1000.0,
            comparison="gt",
            cooldown_seconds=300,
        ),
        AlertRule(
            name="database_connection_failure",
            description="Database connection failures detected",
            severity=AlertSeverity.CRITICAL,
            window_seconds=60,
            threshold=1.0,
            comparison="gte",
            cooldown_seconds=300,
        ),
        AlertRule(
            name="circuit_breaker_trip",
            description="Circuit breaker has opened",
            severity=AlertSeverity.ERROR,
            window_seconds=60,
            threshold=1.0,
            comparison="gte",
            cooldown_seconds=600,
        ),
        AlertRule(
            name="rate_limit_threshold",
            description="Rate limit usage exceeds 80%",
            severity=AlertSeverity.WARNING,
            window_seconds=300,
            threshold=0.80,
            comparison="gt",
            cooldown_seconds=300,
        ),
    ]


def print_setup_instructions():
    print("=" * 60)
    print("MONITORING SETUP INSTRUCTIONS")
    print("=" * 60)
    print()

    print("1. SLACK WEBHOOK SETUP")
    print("-" * 40)
    print("  a. Go to https://api.slack.com/apps")
    print("  b. Create new app → Incoming Webhooks")
    print("  c. Activate Incoming Webhooks")
    print("  d. Add new webhook to workspace")
    print("  e. Copy webhook URL")
    print("  f. Add to Render environment: SLACK_WEBHOOK_URL=<url>")
    print()

    print("2. SENTRY SETUP")
    print("-" * 40)
    print("  a. Go to https://sentry.io")
    print("  b. Create new project")
    print("  c. Copy DSN from project settings")
    print("  d. Add to Render environment: SENTRY_DSN=<dsn>")
    print()

    print("3. ENVIRONMENT VARIABLES")
    print("-" * 40)
    print("  Add these to Render dashboard:")
    print("  - SLACK_WEBHOOK_URL")
    print("  - SENTRY_DSN")
    print("  - SENTRY_ENVIRONMENT=production")
    print()

    print("4. VERIFY SETUP")
    print("-" * 40)
    print("  After deploying, verify:")
    print("  - Check /healthz endpoint")
    print("  - Trigger test alert")
    print("  - Verify Slack notification received")
    print()

    print("=" * 60)


if __name__ == "__main__":
    print_setup_instructions()
