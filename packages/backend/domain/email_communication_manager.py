"""
Email Communication Manager for Phase 13.1 Communication System
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from shared.logging_config import get_logger

logger = get_logger("sorce.email_communication_manager")


@dataclass
class EmailTemplate:
    """Email template for dynamic content generation."""

    id: str
    name: str
    subject_template: str
    body_template: str
    variables: List[str] = field(default_factory=list)
    category: str = "general"
    is_active: bool = True
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class EmailCommunication:
    """Email communication record."""

    id: str
    user_id: str
    tenant_id: str
    template_id: Optional[str]
    subject: str
    body: str
    to_email: str
    from_email: str
    reply_to: Optional[str]
    category: str
    status: str = "pending"  # pending, sent, failed, bounced
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    delivery_provider: str = "resend"
    external_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class EmailPreferences:
    """User email preferences."""

    user_id: str
    tenant_id: str
    email_enabled: bool = True
    categories: Dict[str, bool] = field(default_factory=dict)
    frequency_limits: Dict[str, int] = field(default_factory=dict)
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None  # HH:MM format
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class EmailCommunicationManager:
    """Email communication management system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._templates: Dict[str, EmailTemplate] = {}
        self._delivery_provider = "resend"
        self._rate_limits: Dict[str, Dict[str, int]] = {}

    async def send_email(
        self,
        user_id: str,
        tenant_id: str,
        to_email: str,
        subject: str,
        body: str,
        category: str = "general",
        template_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        reply_to: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> EmailCommunication:
        """Send an email to a user."""
        try:
            # Check user preferences
            preferences = await self.get_email_preferences(user_id, tenant_id)
            if not preferences.email_enabled:
                raise Exception("User has disabled email communications")

            if not preferences.categories.get(category, True):
                raise Exception(f"User has disabled {category} emails")

            # Check quiet hours
            if preferences.quiet_hours_enabled:
                current_time = datetime.now().strftime("%H:%M")
                if (
                    preferences.quiet_hours_start
                    and preferences.quiet_hours_end
                    and self._is_in_quiet_hours(
                        current_time,
                        preferences.quiet_hours_start,
                        preferences.quiet_hours_end,
                    )
                ):
                    raise Exception("Email sent during quiet hours")

            # Check rate limits
            if not await self._check_rate_limit(user_id, tenant_id, category):
                raise Exception("Rate limit exceeded")

            # Create email communication record
            email = EmailCommunication(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                template_id=template_id,
                subject=subject,
                body=body,
                to_email=to_email,
                from_email=from_email or "noreply@jobhuntin.com",
                reply_to=reply_to,
                category=category,
                variables=variables or {},
            )

            # Send email via provider
            external_id = await self._send_via_provider(email)
            email.external_id = external_id
            email.status = "sent"
            email.sent_at = datetime.now(timezone.utc)

            # Save to database
            await self._save_email_communication(email)

            logger.info(f"Email sent successfully to {to_email} for user {user_id}")
            return email

        except Exception as e:
            # Log failed email
            error_email = EmailCommunication(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                template_id=template_id,
                subject=subject,
                body=body,
                to_email=to_email,
                from_email=from_email or "noreply@jobhuntin.com",
                reply_to=reply_to,
                category=category,
                status="failed",
                error_message=str(e),
                variables=variables or {},
            )
            await self._save_email_communication(error_email)

            logger.error(f"Failed to send email to {to_email}: {e}")
            raise

    async def send_template_email(
        self,
        user_id: str,
        tenant_id: str,
        template_id: str,
        variables: Dict[str, Any],
        to_email: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailCommunication:
        """Send an email using a template."""
        try:
            # Get template
            template = await self.get_template(template_id)
            if not template:
                raise Exception(f"Template {template_id} not found")

            # Get user email if not provided
            if not to_email:
                user_data = await self._get_user_data(user_id)
                to_email = user_data.get("email")
                if not to_email:
                    raise Exception("User email not found")

            # Render template
            subject = self._render_template(template.subject_template, variables)
            body = self._render_template(template.body_template, variables)

            # Send email
            return await self.send_email(
                user_id=user_id,
                tenant_id=tenant_id,
                to_email=to_email,
                subject=subject,
                body=body,
                category=template.category,
                template_id=template_id,
                variables=variables,
                reply_to=reply_to,
            )

        except Exception as e:
            logger.error(f"Failed to send template email {template_id}: {e}")
            raise

    async def get_email_preferences(
        self, user_id: str, tenant_id: str
    ) -> EmailPreferences:
        """Get user email preferences."""
        try:
            query = """
                SELECT * FROM email_preferences
                WHERE user_id = $1 AND tenant_id = $2
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query, user_id, tenant_id)

                if not result:
                    # Create default preferences
                    preferences = EmailPreferences(
                        user_id=user_id,
                        tenant_id=tenant_id,
                        categories={
                            "application_status": True,
                            "job_matches": True,
                            "security": True,
                            "marketing": False,
                            "usage_limits": True,
                            "reminders": True,
                        },
                        frequency_limits={
                            "marketing": 1,  # 1 per week
                            "job_matches": 5,  # 5 per day
                            "reminders": 3,  # 3 per day
                        },
                    )
                    await self._save_email_preferences(preferences)
                    return preferences

                row = result[0]
                return EmailPreferences(
                    user_id=row[0],
                    tenant_id=row[1],
                    email_enabled=row[2],
                    categories=row[3] or {},
                    frequency_limits=row[4] or {},
                    quiet_hours_enabled=row[5] or False,
                    quiet_hours_start=row[6],
                    quiet_hours_end=row[7],
                    created_at=row[8],
                    updated_at=row[9],
                )

        except Exception as e:
            logger.error(f"Failed to get email preferences for {user_id}: {e}")
            # Return default preferences
            return EmailPreferences(
                user_id=user_id,
                tenant_id=tenant_id,
            )

    async def update_email_preferences(
        self,
        user_id: str,
        tenant_id: str,
        email_enabled: Optional[bool] = None,
        categories: Optional[Dict[str, bool]] = None,
        frequency_limits: Optional[Dict[str, int]] = None,
        quiet_hours_enabled: Optional[bool] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
    ) -> EmailPreferences:
        """Update user email preferences."""
        try:
            # Get current preferences
            preferences = await self.get_email_preferences(user_id, tenant_id)

            # Update fields
            if email_enabled is not None:
                preferences.email_enabled = email_enabled

            if categories is not None:
                preferences.categories.update(categories)

            if frequency_limits is not None:
                preferences.frequency_limits.update(frequency_limits)

            if quiet_hours_enabled is not None:
                preferences.quiet_hours_enabled = quiet_hours_enabled

            if quiet_hours_start is not None:
                preferences.quiet_hours_start = quiet_hours_start

            if quiet_hours_end is not None:
                preferences.quiet_hours_end = quiet_hours_end

            preferences.updated_at = datetime.now(timezone.utc)

            # Save to database
            await self._save_email_preferences(preferences)

            logger.info(f"Updated email preferences for user {user_id}")
            return preferences

        except Exception as e:
            logger.error(f"Failed to update email preferences for {user_id}: {e}")
            raise

    async def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get email template by ID."""
        try:
            query = """
                SELECT * FROM email_templates
                WHERE id = $1 AND is_active = true
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query, template_id)

                if not result:
                    return None

                row = result[0]
                return EmailTemplate(
                    id=row[0],
                    name=row[1],
                    subject_template=row[2],
                    body_template=row[3],
                    variables=row[4] or [],
                    category=row[5],
                    is_active=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                )

        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {e}")
            return None

    async def create_template(
        self,
        name: str,
        subject_template: str,
        body_template: str,
        category: str = "general",
        variables: Optional[List[str]] = None,
    ) -> EmailTemplate:
        """Create a new email template."""
        try:
            template = EmailTemplate(
                id=str(uuid.uuid4()),
                name=name,
                subject_template=subject_template,
                body_template=body_template,
                category=category,
                variables=variables or [],
            )

            # Save to database
            await self._save_template(template)

            logger.info(f"Created email template: {name}")
            return template

        except Exception as e:
            logger.error(f"Failed to create email template: {e}")
            raise

    async def get_email_history(
        self,
        user_id: str,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
    ) -> List[EmailCommunication]:
        """Get email communication history."""
        try:
            query = """
                SELECT * FROM email_communications_log
                WHERE user_id = $1 AND tenant_id = $2
            """
            params = [user_id, tenant_id]

            if category:
                query += " AND category = $3"
                params.append(category)

            query += " ORDER BY created_at DESC LIMIT $4 OFFSET $5"
            params.extend([limit, offset])

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                emails = []
                for row in results:
                    email = EmailCommunication(
                        id=row[0],
                        user_id=row[1],
                        tenant_id=row[2],
                        template_id=row[3],
                        subject=row[4],
                        body=row[5],
                        to_email=row[6],
                        from_email=row[7],
                        reply_to=row[8],
                        category=row[9],
                        status=row[10],
                        sent_at=row[11],
                        error_message=row[12],
                        delivery_provider=row[13],
                        external_id=row[14],
                        variables=row[15] or {},
                        created_at=row[16],
                        updated_at=row[17],
                    )
                    emails.append(email)

                return emails

        except Exception as e:
            logger.error(f"Failed to get email history for {user_id}: {e}")
            return []

    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables."""
        try:
            # Simple template rendering
            rendered = template
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                rendered = rendered.replace(placeholder, str(value))

            return rendered

        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            return template

    async def _send_via_provider(self, email: EmailCommunication) -> str:
        """Send email via delivery provider."""
        try:
            # In a real implementation, this would use Resend API
            # For now, we'll simulate the response
            external_id = f"resend_{uuid.uuid4().hex[:8]}"

            logger.info(
                f"Simulated email send via {self._delivery_provider}: {external_id}"
            )
            return external_id

        except Exception as e:
            logger.error(f"Failed to send via provider: {e}")
            raise

    async def _check_rate_limit(
        self, user_id: str, tenant_id: str, category: str
    ) -> bool:
        """Check if user is within rate limits."""
        try:
            # Get user preferences
            preferences = await self.get_email_preferences(user_id, tenant_id)

            # Get rate limit for category
            limit = preferences.frequency_limits.get(category, 10)

            # Count emails in last 24 hours
            query = """
                SELECT COUNT(*) FROM email_communications_log
                WHERE user_id = $1 AND tenant_id = $2
                AND category = $3
                AND created_at > NOW() - INTERVAL '24 hours'
                AND status = 'sent'
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(query, user_id, tenant_id, category)

                return result < limit

        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return True  # Allow if check fails

    def _is_in_quiet_hours(self, current_time: str, start: str, end: str) -> bool:
        """Check if current time is in quiet hours."""
        try:
            current_hour = int(current_time.split(":")[0])
            current_minute = int(current_time.split(":")[1])
            start_hour = int(start.split(":")[0])
            start_minute = int(start.split(":")[1])
            end_hour = int(end.split(":")[0])
            end_minute = int(end.split(":")[1])

            current_minutes = current_hour * 60 + current_minute
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute

            if start_minutes <= end_minutes:
                return start_minutes <= current_minutes <= end_minutes
            else:
                # Overnight quiet hours
                return (
                    current_minutes >= start_minutes or current_minutes <= end_minutes
                )

        except Exception:
            return False

    async def _save_email_communication(self, email: EmailCommunication) -> None:
        """Save email communication to database."""
        try:
            query = """
                INSERT INTO email_communications_log (
                    id, user_id, tenant_id, template_id, subject, body,
                    to_email, from_email, reply_to, category, status,
                    sent_at, error_message, delivery_provider, external_id,
                    variables, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    sent_at = EXCLUDED.sent_at,
                    error_message = EXCLUDED.error_message,
                    external_id = EXCLUDED.external_id,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                email.id,
                email.user_id,
                email.tenant_id,
                email.template_id,
                email.subject,
                email.body,
                email.to_email,
                email.from_email,
                email.reply_to,
                email.category,
                email.status,
                email.sent_at,
                email.error_message,
                email.delivery_provider,
                email.external_id,
                email.variables,
                email.created_at,
                email.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save email communication: {e}")

    async def _save_email_preferences(self, preferences: EmailPreferences) -> None:
        """Save email preferences to database."""
        try:
            query = """
                INSERT INTO email_preferences (
                    user_id, tenant_id, email_enabled, categories,
                    frequency_limits, quiet_hours_enabled, quiet_hours_start,
                    quiet_hours_end, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (user_id, tenant_id) DO UPDATE SET
                    email_enabled = EXCLUDED.email_enabled,
                    categories = EXCLUDED.categories,
                    frequency_limits = EXCLUDED.frequency_limits,
                    quiet_hours_enabled = EXCLUDED.quiet_hours_enabled,
                    quiet_hours_start = EXCLUDED.quiet_hours_start,
                    quiet_hours_end = EXCLUDED.quiet_hours_end,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                preferences.user_id,
                preferences.tenant_id,
                preferences.email_enabled,
                preferences.categories,
                preferences.frequency_limits,
                preferences.quiet_hours_enabled,
                preferences.quiet_hours_start,
                preferences.quiet_hours_end,
                preferences.created_at,
                preferences.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save email preferences: {e}")

    async def _save_template(self, template: EmailTemplate) -> None:
        """Save email template to database."""
        try:
            query = """
                INSERT INTO email_templates (
                    id, name, subject_template, body_template, variables,
                    category, is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    subject_template = EXCLUDED.subject_template,
                    body_template = EXCLUDED.body_template,
                    variables = EXCLUDED.variables,
                    category = EXCLUDED.category,
                    is_active = EXCLUDED.is_active,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                template.id,
                template.name,
                template.subject_template,
                template.body_template,
                template.variables,
                template.category,
                template.is_active,
                template.created_at,
                template.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save email template: {e}")

    async def _get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get user data from database."""
        try:
            query = "SELECT email, first_name, last_name FROM users WHERE id = $1"

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, user_id)

                if result:
                    return {
                        "email": result[0],
                        "first_name": result[1],
                        "last_name": result[2],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get user data: {e}")
            return {}


# Factory function
def create_email_communication_manager(db_pool) -> EmailCommunicationManager:
    """Create email communication manager instance."""
    return EmailCommunicationManager(db_pool)
