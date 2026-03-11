"""
Follow-up reminders system for application tracking and engagement.

Provides:
  - Automated follow-up reminders for applications
  - Customizable reminder schedules and templates
  - Smart timing based on application status and company
  - Integration with calendar and email systems
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from shared.logging_config import get_logger

logger = get_logger("sorce.follow_up_reminders")

# Reminder types
REMINDER_TYPES = [
    "application_submitted",
    "one_week_follow_up",
    "two_week_follow_up",
    "interview_scheduled",
    "interview_preparation",
    "post_interview_thank_you",
    "offer_received",
    "offer_response",
    "rejection_follow_up",
    "custom",
]

# Default reminder schedules (days after event)
DEFAULT_SCHEDULES = {
    "application_submitted": 7,  # 1 week
    "one_week_follow_up": 14,  # 2 weeks
    "two_week_follow_up": 21,  # 3 weeks
    "interview_preparation": 1,  # 1 day before
    "post_interview_thank_you": 1,  # 1 day after
    "offer_response": 3,  # 3 days after offer
    "rejection_follow_up": 7,  # 1 week after rejection
}


class ReminderTemplate(BaseModel):
    """Reminder message template."""

    id: str
    name: str
    subject: str
    body_template: str
    variables: List[str] = []
    reminder_type: str
    is_default: bool = False


class FollowUpReminder(BaseModel):
    """Individual follow-up reminder."""

    id: str
    application_id: str
    user_id: str
    tenant_id: str
    reminder_type: str
    scheduled_for: datetime
    message: str
    status: str = "pending"  # pending, sent, cancelled, completed
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class ReminderSchedule(BaseModel):
    """Reminder schedule configuration."""

    reminder_type: str
    days_after_event: int
    is_active: bool = True
    conditions: Dict[str, Any] = {}
    template_id: Optional[str] = None


class FollowUpManager:
    """Manages follow-up reminders and scheduling."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.templates = self._initialize_templates()

    async def create_reminder(
        self,
        tenant_id: str,
        user_id: str,
        application_id: str,
        reminder_type: str,
        scheduled_for: datetime,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FollowUpReminder:
        """Create a new follow-up reminder."""

        reminder_id = str(uuid.uuid4())

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO follow_up_reminders (
                    id, application_id, user_id, tenant_id, reminder_type,
                    scheduled_for, message, status, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                """,
                reminder_id,
                application_id,
                user_id,
                tenant_id,
                reminder_type,
                scheduled_for,
                message,
                "pending",
                metadata or {},
            )

            reminder = FollowUpReminder(
                id=reminder_id,
                application_id=application_id,
                user_id=user_id,
                tenant_id=tenant_id,
                reminder_type=reminder_type,
                scheduled_for=scheduled_for,
                message=message,
                status="pending",
                metadata=metadata or {},
            )

            logger.info(
                "Created follow-up reminder %s for application %s",
                reminder_id,
                application_id,
            )

            return reminder

    async def schedule_application_reminders(
        self,
        tenant_id: str,
        user_id: str,
        application_id: str,
        application_status: str,
        schedules: Optional[List[ReminderSchedule]] = None,
    ) -> List[FollowUpReminder]:
        """Schedule reminders for a new application."""

        if schedules is None:
            schedules = self._get_default_schedules()

        reminders = []

        async with self.db_pool.acquire() as conn:
            # Get application details
            app_data = await conn.fetchrow(
                """
                SELECT a.*, j.title as job_title, c.name as company_name
                FROM applications a
                LEFT JOIN jobs j ON a.job_id = j.id
                LEFT JOIN companies c ON j.company_id = c.id
                WHERE a.id = $1 AND a.tenant_id = $2 AND a.user_id = $3
                """,
                application_id,
                tenant_id,
                user_id,
            )

            if not app_data:
                return reminders

        for schedule in schedules:
            if not schedule.is_active:
                continue

            # Check if reminder type matches current status
            if not self._should_schedule_reminder(
                schedule.reminder_type, application_status
            ):
                continue

            # Calculate scheduled time
            scheduled_for = datetime.now(timezone.utc) + timedelta(
                days=schedule.days_after_event
            )

            # Generate message
            message = await self._generate_message(
                schedule.reminder_type,
                schedule.template_id,
                dict(app_data),
            )

            reminder = await self.create_reminder(
                tenant_id=tenant_id,
                user_id=user_id,
                application_id=application_id,
                reminder_type=schedule.reminder_type,
                scheduled_for=scheduled_for,
                message=message,
                metadata={"schedule_id": schedule.reminder_type},
            )

            reminders.append(reminder)

        return reminders

    async def get_pending_reminders(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[FollowUpReminder]:
        """Get pending reminders that are due (no claim - for backward compatibility)."""

        async with self.db_pool.acquire() as conn:
            query = """
            SELECT * FROM follow_up_reminders
            WHERE status = 'pending' AND scheduled_for <= NOW()
            """
            params = []
            param_idx = 1

            if tenant_id:
                query += f" AND tenant_id = ${param_idx}"
                params.append(tenant_id)
                param_idx += 1

            if user_id:
                query += f" AND user_id = ${param_idx}"
                params.append(user_id)
                param_idx += 1

            query += " ORDER BY scheduled_for ASC LIMIT $" + str(param_idx)
            params.append(limit)

            rows = await conn.fetch(query, *params)

            reminders = []
            for row in rows:
                reminder = FollowUpReminder(
                    id=row["id"],
                    application_id=row["application_id"],
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    reminder_type=row["reminder_type"],
                    scheduled_for=row["scheduled_for"],
                    message=row["message"],
                    status=row["status"],
                    sent_at=row["sent_at"],
                    completed_at=row["completed_at"],
                    metadata=row.get("metadata", {}),
                )
                reminders.append(reminder)

            return reminders

    async def claim_pending_reminders(
        self,
        conn,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[FollowUpReminder]:
        """Atomically claim pending reminders using FOR UPDATE SKIP LOCKED.
        Must be called within an open transaction. Returns claimed rows.
        WORK-001: Prevents duplicate sends when multiple workers run."""
        query = """
            SELECT * FROM follow_up_reminders
            WHERE status = 'pending' AND scheduled_for <= NOW()
            """
        params = []
        param_idx = 1  # WORK-007: integer only — values go in params; never interpolate user input

        if tenant_id:
            query += f" AND tenant_id = ${param_idx}"
            params.append(tenant_id)
            param_idx += 1

        if user_id:
            query += f" AND user_id = ${param_idx}"
            params.append(user_id)
            param_idx += 1

        query += f" ORDER BY scheduled_for ASC LIMIT ${param_idx} FOR UPDATE SKIP LOCKED"
        params.append(limit)

        rows = await conn.fetch(query, *params)

        reminders = []
        for row in rows:
            reminder = FollowUpReminder(
                id=row["id"],
                application_id=row["application_id"],
                user_id=row["user_id"],
                tenant_id=row["tenant_id"],
                reminder_type=row["reminder_type"],
                scheduled_for=row["scheduled_for"],
                message=row["message"],
                status=row["status"],
                sent_at=row["sent_at"],
                completed_at=row["completed_at"],
                metadata=row.get("metadata", {}),
            )
            reminders.append(reminder)

        return reminders

    async def send_reminder(self, reminder_id: str, conn=None) -> bool:
        """Send a follow-up reminder. If conn is provided, use it (must be in transaction)."""

        async def _do_send(c) -> bool:
            reminder_data = await c.fetchrow(
                """
                SELECT * FROM follow_up_reminders
                WHERE id = $1 AND status = 'pending'
                """,
                reminder_id,
            )

            if not reminder_data:
                return False

            user_data = await c.fetchrow(
                """
                SELECT email FROM users WHERE id = $1
                """,
                reminder_data["user_id"],
            )

            if not user_data:
                return False

            try:
                logger.info(
                    "Sending reminder %s to %s: %s",
                    reminder_id,
                    user_data["email"],
                    reminder_data["message"],
                )

                await c.execute(
                    """
                    UPDATE follow_up_reminders
                    SET status = 'sent', sent_at = NOW(), updated_at = NOW()
                    WHERE id = $1
                    """,
                    reminder_id,
                )

                return True

            except Exception as e:
                logger.error("Failed to send reminder %s: %s", reminder_id, e)
                return False

        if conn is not None:
            return await _do_send(conn)
        async with self.db_pool.acquire() as conn:
            return await _do_send(conn)

    async def complete_reminder(self, reminder_id: str, user_id: str) -> bool:
        """Mark a reminder as completed."""

        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE follow_up_reminders
                SET status = 'completed', completed_at = NOW(), updated_at = NOW()
                WHERE id = $1 AND user_id = $2
                """,
                reminder_id,
                user_id,
            )

            return result == "UPDATE 1"

    async def snooze_reminder(
        self,
        reminder_id: str,
        user_id: str,
        days: int = 1,
    ) -> bool:
        """Snooze a reminder by specified days."""

        async with self.db_pool.acquire() as conn:
            new_time = datetime.now(timezone.utc) + timedelta(days=days)

            result = await conn.execute(
                """
                UPDATE follow_up_reminders
                SET scheduled_for = $1, updated_at = NOW()
                WHERE id = $2 AND user_id = $3
                """,
                new_time,
                reminder_id,
                user_id,
            )

            return result == "UPDATE 1"

    async def get_user_reminders(
        self,
        tenant_id: str,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[FollowUpReminder]:
        """Get reminders for a specific user."""

        async with self.db_pool.acquire() as conn:
            query = """
            SELECT * FROM follow_up_reminders
            WHERE tenant_id = $1 AND user_id = $2
            """
            params = [tenant_id, user_id]
            param_idx = 3

            if status:
                query += f" AND status = ${param_idx}"
                params.append(status)
                param_idx += 1

            query += " ORDER BY scheduled_for DESC LIMIT $" + str(param_idx)
            params.append(limit)

            rows = await conn.fetch(query, *params)

            reminders = []
            for row in rows:
                reminder = FollowUpReminder(
                    id=row["id"],
                    application_id=row["application_id"],
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    reminder_type=row["reminder_type"],
                    scheduled_for=row["scheduled_for"],
                    message=row["message"],
                    status=row["status"],
                    sent_at=row["sent_at"],
                    completed_at=row["completed_at"],
                    metadata=row.get("metadata", {}),
                )
                reminders.append(reminder)

            return reminders

    def _initialize_templates(self) -> Dict[str, ReminderTemplate]:
        """Initialize default reminder templates."""

        templates = {}

        # Application submitted
        templates["application_submitted"] = ReminderTemplate(
            id="application_submitted",
            name="Application Submitted Follow-up",
            subject="Following up on my application for {job_title}",
            body_template="""
Hello {company_name},

I hope you're doing well. I recently submitted my application for the {job_title} position and wanted to follow up to express my continued interest in this opportunity.

My background in {relevant_experience} aligns well with the requirements, and I'm excited about the possibility of contributing to your team.

Please let me know if there's any additional information I can provide. I look forward to hearing from you soon.

Best regards,
{user_name}
""",
            variables=["company_name", "job_title", "relevant_experience", "user_name"],
            reminder_type="application_submitted",
            is_default=True,
        )

        # Interview preparation
        templates["interview_preparation"] = ReminderTemplate(
            id="interview_preparation",
            name="Interview Preparation Reminder",
            subject="Interview Preparation: {job_title} at {company_name}",
            body_template="""
Interview Reminder:

Position: {job_title}
Company: {company_name}
Date: {interview_date}
Time: {interview_time}
Location: {interview_location}

Preparation Checklist:
- Research company values and recent news
- Prepare answers to common questions
- Have questions ready for the interviewer
- Test technology (if virtual interview)
- Plan your outfit and travel time

Good luck!
""",
            variables=[
                "job_title",
                "company_name",
                "interview_date",
                "interview_time",
                "interview_location",
            ],
            reminder_type="interview_preparation",
            is_default=True,
        )

        # Post-interview thank you
        templates["post_interview_thank_you"] = ReminderTemplate(
            id="post_interview_thank_you",
            name="Post-Interview Thank You",
            subject="Thank you - {job_title} Interview",
            body_template="""
Dear {interviewer_name},

Thank you so much for taking the time to speak with me today about the {job_title} position at {company_name}.

I really enjoyed learning more about {specific_topic_discussed} and am even more excited about this opportunity after our conversation. My experience in {relevant_experience} seems like a great fit for what you're looking for.

Please don't hesitate to reach out if you need any additional information. I look forward to hearing about the next steps.

Best regards,
{user_name}
""",
            variables=[
                "interviewer_name",
                "job_title",
                "company_name",
                "specific_topic_discussed",
                "relevant_experience",
                "user_name",
            ],
            reminder_type="post_interview_thank_you",
            is_default=True,
        )

        return templates

    def _get_default_schedules(self) -> List[ReminderSchedule]:
        """Get default reminder schedules."""

        schedules = []

        for reminder_type, days in DEFAULT_SCHEDULES.items():
            schedule = ReminderSchedule(
                reminder_type=reminder_type,
                days_after_event=days,
                is_active=True,
            )
            schedules.append(schedule)

        return schedules

    def _should_schedule_reminder(
        self, reminder_type: str, application_status: str
    ) -> bool:
        """Check if reminder should be scheduled for current status."""

        # Define which reminders apply to which statuses
        status_reminder_map = {
            "APPLIED": [
                "application_submitted",
                "one_week_follow_up",
                "two_week_follow_up",
            ],
            "SUCCESS": [
                "interview_scheduled",
                "interview_preparation",
                "post_interview_thank_you",
            ],
            "FAILED": ["rejection_follow_up"],
            "REJECTED": ["rejection_follow_up"],
        }

        applicable_reminders = status_reminder_map.get(application_status, [])
        return reminder_type in applicable_reminders

    async def _generate_message(
        self,
        reminder_type: str,
        template_id: Optional[str],
        context: Dict[str, Any],
    ) -> str:
        """Generate reminder message from template."""

        template = self.templates.get(template_id or reminder_type)
        if not template:
            return f"Follow-up reminder for {reminder_type}"

        # Simple template variable substitution
        message = template.body_template

        for variable in template.variables:
            value = context.get(variable, f"[{variable}]")
            message = message.replace(f"{{{variable}}}", str(value))

        return message


# Factory function
def create_follow_up_manager(db_pool) -> FollowUpManager:
    """Create follow-up manager instance."""
    return FollowUpManager(db_pool)
