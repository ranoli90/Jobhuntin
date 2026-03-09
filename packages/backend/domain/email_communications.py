"""Enhanced email communication system for application status changes, magic links, and rate limits.

This module provides comprehensive email templates and sending functionality for:
- Application status change notifications
- Magic link expiry warnings
- Rate limit notifications
- Email template management
- Multi-language support
- Email delivery tracking
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from shared.logging_config import get_logger
import asyncpg

from shared.config import get_settings
from shared.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError

logger = get_logger("sorce.email_communications")


@dataclass
class EmailTemplate:
    """Email template configuration."""

    name: str
    subject: str
    html_template: str
    text_template: Optional[str] = None
    variables: List[str] = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = []


class EmailCommunicationManager:
    """Manages all email communications including status changes, magic links, and rate limits."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.settings = get_settings()
        self._templates: Dict[str, EmailTemplate] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all email templates."""
        self._templates = {
            "application_status_change": EmailTemplate(
                name="application_status_change",
                subject="Application Status Update: {new_status}",
                html_template=self._get_status_change_template(),
                variables=[
                    "user_name",
                    "company",
                    "job_title",
                    "old_status",
                    "new_status",
                    "application_id",
                    "reason",
                ],
            ),
            "magic_link_expiry": EmailTemplate(
                name="magic_link_expiry",
                subject="Your login link expires soon",
                html_template=self._get_magic_link_expiry_template(),
                variables=["user_name", "expires_in_hours", "magic_link", "login_url"],
            ),
            "magic_link_expired": EmailTemplate(
                name="magic_link_expired",
                subject="Your login link has expired",
                html_template=self._get_magic_link_expired_template(),
                variables=["user_name", "request_new_link_url"],
            ),
            "rate_limit_warning": EmailTemplate(
                name="rate_limit_warning",
                subject="Approaching usage limit",
                html_template=self._get_rate_limit_warning_template(),
                variables=[
                    "user_name",
                    "limit_type",
                    "current_usage",
                    "limit",
                    "reset_time",
                    "upgrade_url",
                ],
            ),
            "rate_limit_reached": EmailTemplate(
                name="rate_limit_reached",
                subject="Usage limit reached",
                html_template=self._get_rate_limit_reached_template(),
                variables=[
                    "user_name",
                    "limit_type",
                    "limit",
                    "reset_time",
                    "upgrade_url",
                ],
            ),
            "application_success": EmailTemplate(
                name="application_success",
                subject="Application Successfully Submitted!",
                html_template=self._get_application_success_template(),
                variables=[
                    "user_name",
                    "company",
                    "job_title",
                    "application_id",
                    "next_steps_url",
                ],
            ),
            "application_failed": EmailTemplate(
                name="application_failed",
                subject="Application Issue Detected",
                html_template=self._get_application_failed_template(),
                variables=[
                    "user_name",
                    "company",
                    "job_title",
                    "error_message",
                    "retry_url",
                ],
            ),
            "hold_questions_ready": EmailTemplate(
                name="hold_questions_ready",
                subject="Action Required: Complete Your Application",
                html_template=self._get_hold_questions_template(),
                variables=[
                    "user_name",
                    "company",
                    "job_title",
                    "question_count",
                    "application_id",
                    "answer_url",
                ],
            ),
        }

    async def send_status_change_email(
        self,
        user_id: str,
        application_id: str,
        old_status: str,
        new_status: str,
        reason: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Send email when application status changes."""
        try:
            # Get user and application details
            async with self.pool.acquire() as conn:
                user_data = await conn.fetchrow(
                    """
                    SELECT u.email, u.full_name, u.email_preferences
                    FROM public.users u
                    WHERE u.id = $1
                    """,
                    user_id,
                )

                if not user_data:
                    logger.warning("User %s not found for status change email", user_id)
                    return False

                email = user_data["email"]
                user_name = user_data["full_name"]
                email_prefs = user_data.get("email_preferences", {})

                # Check if user wants status change emails
                if not email_prefs.get("status_changes", True):
                    logger.info(
                        "User %s has opted out of status change emails", user_id
                    )
                    return False

                # Get application details
                app_data = await conn.fetchrow(
                    """
                    SELECT a.job_id, j.company, j.title
                    FROM public.applications a
                    JOIN public.jobs j ON j.id = a.job_id
                    WHERE a.id = $1
                    """,
                    application_id,
                )

                if not app_data:
                    logger.warning(
                        "Application %s not found for status change email",
                        application_id,
                    )
                    return False

                company = app_data["company"]
                job_title = app_data["title"]

            # Render email
            template = self._templates["application_status_change"]
            subject = template.subject.format(new_status=new_status.title())
            html = template.html_template.format(
                user_name=user_name or "there",
                company=company,
                job_title=job_title,
                old_status=old_status.title(),
                new_status=new_status.title(),
                application_id=application_id,
                reason=reason or "No additional information provided.",
            )

            # Send email
            success = await self._send_email(email, subject, html, "status_change")

            if success:
                # Log email sent
                await self._log_email_sent(
                    user_id=user_id,
                    email_type="status_change",
                    template_name="application_status_change",
                    recipient=email,
                    tenant_id=tenant_id,
                    metadata={
                        "application_id": application_id,
                        "old_status": old_status,
                        "new_status": new_status,
                        "reason": reason,
                    },
                )

            return success

        except Exception as e:
            logger.error("Failed to send status change email: %s", e)
            return False

    async def send_magic_link_expiry_warning(
        self,
        user_id: str,
        magic_link: str,
        expires_in_hours: int,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Send warning email when magic link is about to expire."""
        try:
            async with self.pool.acquire() as conn:
                user_data = await conn.fetchrow(
                    """
                    SELECT u.email, u.full_name, u.email_preferences
                    FROM public.users u
                    WHERE u.id = $1
                    """,
                    user_id,
                )

                if not user_data:
                    return False

                email = user_data["email"]
                user_name = user_data["full_name"]
                email_prefs = user_data.get("email_preferences", {})

                # Check if user wants security emails
                if not email_prefs.get("security", True):
                    return False

            template = self._templates["magic_link_expiry"]
            subject = template.subject
            html = template.html_template.format(
                user_name=user_name or "there",
                expires_in_hours=expires_in_hours,
                magic_link=magic_link,
                login_url=f"{self.settings.web_url}/login?token={magic_link}",
            )

            success = await self._send_email(email, subject, html, "magic_link_expiry")

            if success:
                await self._log_email_sent(
                    user_id=user_id,
                    email_type="magic_link_expiry",
                    template_name="magic_link_expiry",
                    recipient=email,
                    tenant_id=tenant_id,
                    metadata={"expires_in_hours": expires_in_hours},
                )

            return success

        except Exception as e:
            logger.error("Failed to send magic link expiry warning: %s", e)
            return False

    async def send_magic_link_expired_notification(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Send email when magic link has expired."""
        try:
            async with self.pool.acquire() as conn:
                user_data = await conn.fetchrow(
                    """
                    SELECT u.email, u.full_name, u.email_preferences
                    FROM public.users u
                    WHERE u.id = $1
                    """,
                    user_id,
                )

                if not user_data:
                    return False

                email = user_data["email"]
                user_name = user_data["full_name"]
                email_prefs = user_data.get("email_preferences", {})

                if not email_prefs.get("security", True):
                    return False

            template = self._templates["magic_link_expired"]
            subject = template.subject
            html = template.html_template.format(
                user_name=user_name or "there",
                request_new_link_url=f"{self.settings.web_url}/login",
            )

            success = await self._send_email(email, subject, html, "magic_link_expired")

            if success:
                await self._log_email_sent(
                    user_id=user_id,
                    email_type="magic_link_expired",
                    template_name="magic_link_expired",
                    recipient=email,
                    tenant_id=tenant_id,
                )

            return success

        except Exception as e:
            logger.error("Failed to send magic link expired notification: %s", e)
            return False

    async def send_rate_limit_warning(
        self,
        user_id: str,
        limit_type: str,
        current_usage: int,
        limit: int,
        reset_time: datetime,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Send warning email when approaching rate limits."""
        try:
            async with self.pool.acquire() as conn:
                user_data = await conn.fetchrow(
                    """
                    SELECT u.email, u.full_name, u.email_preferences
                    FROM public.users u
                    WHERE u.id = $1
                    """,
                    user_id,
                )

                if not user_data:
                    return False

                email = user_data["email"]
                user_name = user_data["full_name"]
                email_prefs = user_data.get("email_preferences", {})

                if not email_prefs.get("usage_alerts", True):
                    return False

            template = self._templates["rate_limit_warning"]
            subject = template.subject
            html = template.html_template.format(
                user_name=user_name or "there",
                limit_type=limit_type.replace("_", " ").title(),
                current_usage=current_usage,
                limit=limit,
                reset_time=reset_time.strftime("%Y-%m-%d %H:%M UTC"),
                upgrade_url=f"{self.settings.web_url}/pricing",
            )

            success = await self._send_email(email, subject, html, "rate_limit_warning")

            if success:
                await self._log_email_sent(
                    user_id=user_id,
                    email_type="rate_limit_warning",
                    template_name="rate_limit_warning",
                    recipient=email,
                    tenant_id=tenant_id,
                    metadata={
                        "limit_type": limit_type,
                        "current_usage": current_usage,
                        "limit": limit,
                        "reset_time": reset_time.isoformat(),
                    },
                )

            return success

        except Exception as e:
            logger.error("Failed to send rate limit warning: %s", e)
            return False

    async def send_rate_limit_reached(
        self,
        user_id: str,
        limit_type: str,
        limit: int,
        reset_time: datetime,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Send email when rate limit is reached."""
        try:
            async with self.pool.acquire() as conn:
                user_data = await conn.fetchrow(
                    """
                    SELECT u.email, u.full_name, u.email_preferences
                    FROM public.users u
                    WHERE u.id = $1
                    """,
                    user_id,
                )

                if not user_data:
                    return False

                email = user_data["email"]
                user_name = user_data["full_name"]
                email_prefs = user_data.get("email_preferences", {})

                if not email_prefs.get("usage_alerts", True):
                    return False

            template = self._templates["rate_limit_reached"]
            subject = template.subject
            html = template.html_template.format(
                user_name=user_name or "there",
                limit_type=limit_type.replace("_", " ").title(),
                limit=limit,
                reset_time=reset_time.strftime("%Y-%m-%d %H:%M UTC"),
                upgrade_url=f"{self.settings.web_url}/pricing",
            )

            success = await self._send_email(email, subject, html, "rate_limit_reached")

            if success:
                await self._log_email_sent(
                    user_id=user_id,
                    email_type="rate_limit_reached",
                    template_name="rate_limit_reached",
                    recipient=email,
                    tenant_id=tenant_id,
                    metadata={
                        "limit_type": limit_type,
                        "limit": limit,
                        "reset_time": reset_time.isoformat(),
                    },
                )

            return success

        except Exception as e:
            logger.error("Failed to send rate limit reached notification: %s", e)
            return False

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html: str,
        email_type: str,
    ) -> bool:
        """Send email via Resend API."""
        import httpx

        if not self.settings.resend_api_key:
            logger.warning("Resend API key not configured")
            return False

        circuit_breaker = get_circuit_breaker("resend")

        try:
            async with circuit_breaker:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        "https://api.resend.com/emails",
                        headers={
                            "Authorization": f"Bearer {self.settings.resend_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "from": self.settings.email_from,
                            "to": [to_email],
                            "subject": subject,
                            "html": html,
                        },
                    )

                    if response.status_code in (200, 202):
                        logger.info(
                            "Email sent successfully to %s: %s", to_email, email_type
                        )
                        return True
                    else:
                        logger.error(
                            "Email send failed: %d %s",
                            response.status_code,
                            response.text,
                        )
                        return False

        except CircuitBreakerOpenError:
            logger.warning("Resend circuit breaker is open")
            return False
        except Exception as e:
            logger.error("Email send failed: %s", e)
            return False

    async def _log_email_sent(
        self,
        user_id: str,
        email_type: str,
        template_name: str,
        recipient: str,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log email sent to database."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO public.email_communications_log
                    (user_id, tenant_id, email_type, template_name, recipient, metadata, sent_at)
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb, now())
                    """,
                    user_id,
                    tenant_id,
                    email_type,
                    template_name,
                    recipient,
                    json.dumps(metadata or {}),
                )
        except Exception as e:
            logger.error("Failed to log email sent: %s", e)

    def _get_status_change_template(self) -> str:
        """Get HTML template for status change emails."""
        return """
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1E293B;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #3B82F6; margin: 0; font-size: 24px;">Sorce</h1>
                <p style="color: #64748B; margin: 4px 0 0;">Application Status Update</p>
            </div>

            <p>Hi {user_name},</p>
            <p>Your application to <strong>{company}</strong> for the <strong>{job_title}</strong> position has been updated.</p>

            <div style="background: #F1F5F9; border-radius: 12px; padding: 20px; margin: 20px 0;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                    <span style="font-weight: 600; color: #64748B;">Status Change:</span>
                    <span style="background: #FEF3C7; color: #D97706; padding: 4px 12px; border-radius: 20px; font-size: 14px;">{old_status} → {new_status}</span>
                </div>
                {reason_block}
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{web_url}/applications/{application_id}" style="background: #3B82F6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">View Application</a>
            </div>

            <p style="color: #94A3B8; font-size: 12px; text-align: center; margin-top: 40px;">
                You're receiving this because you use Sorce. <a href="{web_url}/settings/notifications" style="color: #94A3B8;">Manage notifications</a>
            </p>
        </div>
        """.format(
            web_url=self.settings.web_url,
            reason_block=f'<div style="margin-top: 10px;"><strong>Additional Information:</strong><br>{reason}</div>'
            if "{reason}" != "{reason}"
            else "",
            user_name="{user_name}",
            company="{company}",
            job_title="{job_title}",
            old_status="{old_status}",
            new_status="{new_status}",
            application_id="{application_id}",
        )

    def _get_magic_link_expiry_template(self) -> str:
        """Get HTML template for magic link expiry warning."""
        return """
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1E293B;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #F59E0B; margin: 0; font-size: 24px;">⚠️ Login Link Expiring Soon</h1>
                <p style="color: #64748B; margin: 4px 0 0;">Sorce Security Notification</p>
            </div>

            <p>Hi {user_name},</p>
            <p>Your secure login link will expire in <strong>{expires_in_hours} hours</strong>.</p>

            <div style="background: #FEF3C7; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #F59E0B;">
                <p style="margin: 0;"><strong>For your security:</strong> Login links are designed to be temporary and expire after a short period for your protection.</p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{login_url}" style="background: #F59E0B; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">Use Login Link Now</a>
            </div>

            <p style="color: #94A3B8; font-size: 12px; text-align: center; margin-top: 40px;">
                If you didn't request this link, you can safely ignore this email.
            </p>
        </div>
        """

    def _get_magic_link_expired_template(self) -> str:
        """Get HTML template for magic link expired notification."""
        return """
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1E293B;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #EF4444; margin: 0; font-size: 24px;">🔒 Login Link Expired</h1>
                <p style="color: #64748B; margin: 4px 0 0;">Sorce Security Notification</p>
            </div>

            <p>Hi {user_name},</p>
            <p>Your secure login link has expired. For your security, login links are only valid for a short time.</p>

            <div style="background: #FEE2E2; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #EF4444;">
                <p style="margin: 0;"><strong>What happened:</strong> Your login link reached its time limit and is no longer valid.</p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{request_new_link_url}" style="background: #3B82F6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">Request New Login Link</a>
            </div>

            <p style="color: #94A3B8; font-size: 12px; text-align: center; margin-top: 40px;">
                If you didn't request this link, you can safely ignore this email.
            </p>
        </div>
        """

    def _get_rate_limit_warning_template(self) -> str:
        """Get HTML template for rate limit warning."""
        return """
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1E293B;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #F59E0B; margin: 0; font-size: 24px;">📊 Usage Limit Warning</h1>
                <p style="color: #64748B; margin: 4px 0 0;">Sorce Usage Alert</p>
            </div>

            <p>Hi {user_name},</p>
            <p>You're approaching your {limit_type} limit. You've used <strong>{current_usage} of {limit}</strong> allowed uses.</p>

            <div style="background: #FEF3C7; border-radius: 12px; padding: 20px; margin: 20px 0;">
                <div style="margin-bottom: 10px;"><strong>Current Usage:</strong> {current_usage}/{limit}</div>
                <div><strong>Resets on:</strong> {reset_time}</div>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{upgrade_url}" style="background: #F59E0B; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">View Plans</a>
            </div>

            <p style="color: #94A3B8; font-size: 12px; text-align: center; margin-top: 40px;">
                Manage your notification preferences in your account settings.
            </p>
        </div>
        """

    def _get_rate_limit_reached_template(self) -> str:
        """Get HTML template for rate limit reached."""
        return """
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1E293B;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #EF4444; margin: 0; font-size: 24px;">🚫 Usage Limit Reached</h1>
                <p style="color: #64748B; margin: 4px 0 0;">Sorce Usage Alert</p>
            </div>

            <p>Hi {user_name},</p>
            <p>You've reached your {limit_type} limit of <strong>{limit}</strong> uses.</p>

            <div style="background: #FEE2E2; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #EF4444;">
                <div style="margin-bottom: 10px;"><strong>Limit Reached:</strong> {limit} uses</div>
                <div><strong>Resets on:</strong> {reset_time}</div>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{upgrade_url}" style="background: #3B82F6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">Upgrade Your Plan</a>
            </div>

            <p style="color: #94A3B8; font-size: 12px; text-align: center; margin-top: 40px;">
                Need help? Contact our support team.
            </p>
        </div>
        """

    def _get_application_success_template(self) -> str:
        """Get HTML template for successful application."""
        return """
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1E293B;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #10B981; margin: 0; font-size: 24px;">✅ Application Submitted!</h1>
                <p style="color: #64748B; margin: 4px 0 0;">Sorce Success</p>
            </div>

            <p>Hi {user_name},</p>
            <p>Congratulations! Your application to <strong>{company}</strong> for the <strong>{job_title}</strong> position has been successfully submitted.</p>

            <div style="background: #D1FAE5; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #10B981;">
                <p style="margin: 0;"><strong>What's next?</strong> Keep an eye on your email for updates from the employer, and check your Sorce dashboard for application status changes.</p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{next_steps_url}" style="background: #10B981; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">View Application</a>
            </div>

            <p style="color: #94A3B8; font-size: 12px; text-align: center; margin-top: 40px;">
                Good luck with your application!
            </p>
        </div>
        """

    def _get_application_failed_template(self) -> str:
        """Get HTML template for failed application."""
        return """
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1E293B;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #EF4444; margin: 0; font-size: 24px;">⚠️ Application Issue</h1>
                <p style="color: #64748B; margin: 4px 0 0;">Sorce Alert</p>
            </div>

            <p>Hi {user_name},</p>
            <p>We encountered an issue while submitting your application to <strong>{company}</strong> for the <strong>{job_title}</strong> position.</p>

            <div style="background: #FEE2E2; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #EF4444;">
                <p style="margin: 0;"><strong>Error Details:</strong> {error_message}</p>
            </div>

            <p>Don't worry - we'll automatically retry the submission. You don't need to take any action right now.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{retry_url}" style="background: #3B82F6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">View Application Status</a>
            </div>

            <p style="color: #94A3B8; font-size: 12px; text-align: center; margin-top: 40px;">
                If the issue persists, our team is here to help.
            </p>
        </div>
        """

    def _get_hold_questions_template(self) -> str:
        """Get HTML template for hold questions."""
        return """
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1E293B;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #F59E0B; margin: 0; font-size: 24px;">❓ Action Required</h1>
                <p style="color: #64748B; margin: 4px 0 0;">Complete Your Application</p>
            </div>

            <p>Hi {user_name},</p>
            <p>Your application to <strong>{company}</strong> for the <strong>{job_title}</strong> position needs your input to proceed.</p>

            <div style="background: #FEF3C7; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #F59E0B;">
                <p style="margin: 0;"><strong>Questions waiting:</strong> {question_count} question(s) need your answers</p>
            </div>

            <p>Your answers will help us complete the application accurately and increase your chances of success.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{answer_url}" style="background: #F59E0B; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">Answer Questions Now</a>
            </div>

            <p style="color: #94A3B8; font-size: 12px; text-align: center; margin-top: 40px;">
                Quick responses help maintain momentum with employers.
            </p>
        </div>
        """


# Global instance
_email_manager: Optional[EmailCommunicationManager] = None


def get_email_communication_manager(pool: asyncpg.Pool) -> EmailCommunicationManager:
    """Get or create the email communication manager."""
    global _email_manager
    if _email_manager is None:
        _email_manager = EmailCommunicationManager(pool)
    return _email_manager
