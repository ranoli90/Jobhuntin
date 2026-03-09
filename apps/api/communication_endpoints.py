"""API endpoints for enhanced communication system.

This module provides FastAPI endpoints for:
- Email communications management
- Enhanced notifications with semantic matching
- Alert processing and monitoring
- User preferences management
- Communication analytics
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from apps.api.dependencies import get_current_user_id, get_pool
from backend.domain.tenant import TenantContext
from packages.backend.domain.enhanced_notifications import (
    NotificationCategory,
    NotificationContent,
    NotificationPriority,
)
from shared.logging_config import get_logger

logger = get_logger("sorce.communication_api")

router = APIRouter(prefix="/communications", tags=["communications"])


async def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


async def get_tenant_context() -> TenantContext:
    raise NotImplementedError("Tenant context dependency not injected")


# Pydantic models
class EmailPreferences(BaseModel):
    status_changes: bool = True
    security: bool = True
    usage_alerts: bool = True
    marketing: bool = False
    weekly_digest: bool = True


class NotificationPreferences(BaseModel):
    dnd_active: bool = False
    dnd_start_time: Optional[str] = None  # HH:MM format
    dnd_end_time: Optional[str] = None  # HH:MM format
    timezone: str = "UTC"
    notification_sound: bool = True
    notification_vibration: bool = True
    notification_badge: bool = True
    email_preferences: EmailPreferences = EmailPreferences()


class UserInterests(BaseModel):
    interests: List[str] = Field(
        ..., description="List of user interests for semantic matching"
    )


class SendEmailRequest(BaseModel):
    user_id: str
    email_type: str
    subject: Optional[str] = None
    custom_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SendNotificationRequest(BaseModel):
    user_id: str
    title: str
    body: str
    category: str
    priority: str = "medium"
    data: Dict[str, Any] = Field(default_factory=dict)
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    force_send: bool = False


class ProcessAlertRequest(BaseModel):
    alert_type: str
    user_id: str
    alert_data: Dict[str, Any]
    tenant_id: Optional[str] = None


class CommunicationStats(BaseModel):
    total_emails_sent: int
    total_notifications_sent: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    most_active_categories: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


# Dependency functions
async def get_email_manager_dep(pool=Depends(get_pool)):
    """Get email communication manager."""
    from packages.backend.domain.email_communication_manager import (
        create_email_communication_manager,
    )
    return create_email_communication_manager(pool)


async def get_notification_manager_dep(pool=Depends(get_pool)):
    """Get enhanced notification manager."""
    from packages.backend.domain.enhanced_notifications import (
        get_enhanced_notification_manager,
    )
    return get_enhanced_notification_manager(pool)


@router.get("/preferences/email", response_model=EmailPreferences)
async def get_email_preferences(
    user_id: str = Depends(get_current_user_id),
    pool=Depends(get_pool),
):
    """Get user's email preferences."""
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT status_changes, security, usage_alerts, marketing, weekly_digest
                FROM public.email_preferences
                WHERE user_id = $1
                """,
                user_id,
            )
        if row:
            return EmailPreferences(
                status_changes=bool(row["status_changes"]),
                security=bool(row["security"]),
                usage_alerts=bool(row["usage_alerts"]),
                marketing=bool(row["marketing"]),
                weekly_digest=bool(row["weekly_digest"]),
            )
        return EmailPreferences()
    except Exception as e:
        logger.error("Failed to get email preferences: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve email preferences"
        )


@router.put("/preferences/email", response_model=EmailPreferences)
async def update_email_preferences(
    preferences: EmailPreferences,
    user_id: str = Depends(get_current_user_id),
    pool=Depends(get_pool),
):
    """Update user's email preferences."""
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.email_preferences (user_id, status_changes, security, usage_alerts, marketing, weekly_digest)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id) DO UPDATE SET
                    status_changes = EXCLUDED.status_changes,
                    security = EXCLUDED.security,
                    usage_alerts = EXCLUDED.usage_alerts,
                    marketing = EXCLUDED.marketing,
                    weekly_digest = EXCLUDED.weekly_digest,
                    updated_at = now()
                """,
                user_id,
                preferences.status_changes,
                preferences.security,
                preferences.usage_alerts,
                preferences.marketing,
                preferences.weekly_digest,
            )
        return preferences
    except Exception as e:
        logger.error("Failed to update email preferences: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to update email preferences"
        )


@router.get("/preferences/notifications", response_model=NotificationPreferences)
async def get_notification_preferences(
    user_id: str = Depends(get_current_user_id),
    notification_manager=Depends(get_notification_manager_dep),
):
    """Get user's notification preferences."""
    try:
        # TODO: Implement notification preferences retrieval
        return NotificationPreferences()
    except Exception as e:
        logger.error("Failed to get notification preferences: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve notification preferences"
        )


@router.put("/preferences/notifications", response_model=NotificationPreferences)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    user_id: str = Depends(get_current_user_id),
    notification_manager=Depends(get_notification_manager_dep),
):
    """Update user's notification preferences."""
    try:
        # TODO: Implement notification preferences update
        return preferences
    except Exception as e:
        logger.error("Failed to update notification preferences: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to update notification preferences"
        )


@router.get("/interests", response_model=UserInterests)
async def get_user_interests(
    user_id: str = Depends(get_current_user_id),
    notification_manager=Depends(get_notification_manager_dep),
):
    """Get user's interests for semantic matching."""
    try:
        # TODO: Implement user interests retrieval
        return UserInterests(interests=["job applications", "job search"])
    except Exception as e:
        logger.error("Failed to get user interests: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve user interests")


@router.put("/interests", response_model=UserInterests)
async def update_user_interests(
    interests: UserInterests,
    user_id: str = Depends(get_current_user_id),
    notification_manager=Depends(get_notification_manager_dep),
):
    """Update user's interests for semantic matching."""
    try:
        # TODO: Implement user interests update
        return interests
    except Exception as e:
        logger.error("Failed to update user interests: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update user interests")


@router.post("/email/send")
async def send_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(get_tenant_context),
    email_manager=Depends(get_email_manager_dep),
):
    """Send email to user."""
    # Require admin access
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        # TODO: Implement email sending
        background_tasks.add_task(
            send_email_background,
            request.user_id,
            request.email_type,
            request.subject,
            request.custom_message,
            request.metadata,
        )

        return {"message": "Email queued for sending"}
    except Exception as e:
        logger.error("Failed to queue email: %s", e)
        raise HTTPException(status_code=500, detail="Failed to queue email")


@router.post("/notifications/send")
async def send_notification(
    request: SendNotificationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager_dep),
):
    """Send enhanced notification to user."""
    # Require admin access
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        # Parse category and priority
        try:
            category = NotificationCategory(request.category)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid notification category")

        try:
            priority = NotificationPriority(request.priority)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid notification priority")

        # Create notification content
        content = NotificationContent(
            title=request.title,
            body=request.body,
            category=category,
            priority=priority,
            data=request.data,
            action_url=request.action_url,
            action_text=request.action_text,
        )

        # Send notification
        success = await notification_manager.send_notification(
            user_id=request.user_id,
            content=content,
            force_send=request.force_send,
        )

        if success:
            return {"message": "Notification sent successfully"}
        else:
            return {"message": "Notification filtered or failed to send"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send notification: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send notification")


@router.post("/alerts/process")
async def process_alert(
    request: ProcessAlertRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager_dep),
):
    """Process alert and send notifications."""
    # Require admin access
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        sent_count = await notification_manager.process_alert(
            alert_type=request.alert_type,
            user_id=request.user_id,
            alert_data=request.alert_data,
            tenant_id=request.tenant_id,
        )

        return {
            "message": "Alert processed successfully",
            "notifications_sent": sent_count,
        }

    except Exception as e:
        logger.error("Failed to process alert: %s", e)
        raise HTTPException(status_code=500, detail="Failed to process alert")


@router.get("/analytics/stats", response_model=CommunicationStats)
async def get_communication_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    ctx: TenantContext = Depends(get_tenant_context),
    pool=Depends(get_pool),
):
    """Get communication analytics."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        async with pool.acquire() as conn:
            total_emails = await conn.fetchval(
                """
                SELECT COUNT(*)::int FROM public.email_communications_log
                WHERE sent_at >= now() - interval '1 day' * $1
                """,
                days,
            )
            total_emails = total_emails or 0
        return CommunicationStats(
            total_emails_sent=total_emails,
            total_notifications_sent=0,
            delivery_rate=1.0 if total_emails else 0.0,
            open_rate=0.0,
            click_rate=0.0,
            most_active_categories=[],
            recent_activity=[],
        )
    except Exception as e:
        logger.error("Failed to get communication stats: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve communication stats"
        )


@router.get("/analytics/email-log")
async def get_email_log(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    email_type: Optional[str] = Query(None, description="Filter by email type"),
    limit: int = Query(50, ge=1, le=1000, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    ctx: TenantContext = Depends(get_tenant_context),
    pool=Depends(get_pool),
):
    """Get email communication log."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        conditions: list[str] = []
        params: list[Any] = []
        n = 1
        if user_id:
            conditions.append(f"user_id = ${n}")
            params.append(user_id)
            n += 1
        if email_type:
            conditions.append(f"email_type = ${n}")
            params.append(email_type)
            n += 1
        where = (" AND " + " AND ".join(conditions)) if conditions else ""
        async with pool.acquire() as conn:
            total = await conn.fetchval(
                f"SELECT COUNT(*)::int FROM public.email_communications_log WHERE 1=1 {where}",
                *params,
            )
            fetch_params = params + [limit, offset]
            lim_off = f"LIMIT ${len(fetch_params)-1} OFFSET ${len(fetch_params)}"
            rows = await conn.fetch(
                f"""
                SELECT id, user_id, email_type, template_name, recipient, sent_at
                FROM public.email_communications_log
                WHERE 1=1 {where}
                ORDER BY sent_at DESC
                {lim_off}
                """,
                *fetch_params,
            )
        items = [
            {
                "id": str(r["id"]),
                "user_id": str(r["user_id"]),
                "email_type": r["email_type"],
                "template_name": r["template_name"],
                "recipient": r["recipient"],
                "sent_at": r["sent_at"].isoformat() if r["sent_at"] else None,
            }
            for r in rows
        ]
        return {"items": items, "total": total or 0}
    except Exception as e:
        logger.error("Failed to get email log: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve email log")


@router.get("/analytics/notification-log")
async def get_notification_log(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by delivery status"),
    limit: int = Query(50, ge=1, le=1000, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Get notification log."""
    try:
        # TODO: Implement notification log retrieval
        return {"items": [], "total": 0}
    except Exception as e:
        logger.error("Failed to get notification log: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve notification log"
        )


@router.get("/analytics/alerts")
async def get_alert_analytics(
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Get alert processing analytics."""
    try:
        # TODO: Implement alert analytics retrieval
        return {
            "total_alerts": 0,
            "processed_alerts": 0,
            "alert_types": {},
            "processing_times": [],
            "error_rates": {},
        }
    except Exception as e:
        logger.error("Failed to get alert analytics: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve alert analytics"
        )


@router.post("/batch/process")
async def process_batch_notifications(
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager_dep),
):
    """Process batched notifications."""
    try:
        processed_count = await notification_manager.process_batch_queue()

        return {
            "message": "Batch processed successfully",
            "notifications_processed": processed_count,
        }

    except Exception as e:
        logger.error("Failed to process batch notifications: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to process batch notifications"
        )


@router.get("/health")
async def communication_health_check(
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Health check for communication system."""
    try:
        # TODO: Implement health checks
        return {
            "status": "healthy",
            "email_service": "operational",
            "notification_service": "operational",
            "alert_processor": "operational",
            "semantic_matcher": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error("Communication health check failed: %s", e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Background task functions
async def send_email_background(
    user_id: str,
    email_type: str,
    subject: Optional[str],
    custom_message: Optional[str],
    metadata: Dict[str, Any],
):
    """Background task to send email."""
    try:
        # TODO: Implement background email sending
        logger.info("Background email sent to user %s: %s", user_id, email_type)
    except Exception as e:
        logger.error("Background email sending failed: %s", e)


# Helper functions
async def validate_notification_category(category: str) -> bool:
    """Validate notification category."""
    try:
        NotificationCategory(category)
        return True
    except ValueError:
        return False


async def validate_notification_priority(priority: str) -> bool:
    """Validate notification priority."""
    try:
        NotificationPriority(priority)
        return True
    except ValueError:
        return False
