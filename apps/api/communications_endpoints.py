"""
Communications API Endpoints for Phase 13.1 Communication System
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from apps.api.dependencies import get_pool
from packages.backend.domain.alert_processor import create_alert_processor
from packages.backend.domain.email_communication_manager import (
    create_email_communication_manager,
)
from packages.backend.domain.notification_batch_processor import (
    create_notification_batch_processor,
)
from packages.backend.domain.notification_manager import create_notification_manager
from packages.backend.domain.semantic_notification_matcher import (
    create_semantic_notification_matcher,
)
from packages.backend.domain.tenant import TenantContext
from packages.backend.domain.user_interest_profiler import create_user_interest_profiler
from shared.logging_config import get_logger

logger = get_logger("sorce.communications")
router = APIRouter(prefix="/communications", tags=["communications"])


async def get_tenant_context() -> TenantContext:
    """Stub; inject tenant context via Depends in main app."""
    raise NotImplementedError("Tenant context dependency not injected")


# Pydantic models
class EmailRequest(BaseModel):
    """Email request model."""

    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (HTML or plain text)")
    category: str = Field(default="general", description="Email category")
    template_id: Optional[str] = Field(None, description="Email template ID")
    variables: Optional[Dict[str, Any]] = Field(None, description="Template variables")
    reply_to: Optional[str] = Field(None, description="Reply-to email address")
    from_email: Optional[str] = Field(None, description="From email address")


class TemplateEmailRequest(BaseModel):
    """Template email request model."""

    template_id: str = Field(..., description="Email template ID")
    variables: Dict[str, Any] = Field(..., description="Template variables")
    to_email: Optional[str] = Field(
        None, description="Recipient email (will be fetched from user)"
    )
    reply_to: Optional[str] = Field(None, description="Reply-to email address")


class EmailPreferencesRequest(BaseModel):
    """Email preferences request model."""

    email_enabled: Optional[bool] = Field(
        None, description="Enable/disable email communications"
    )
    categories: Optional[Dict[str, bool]] = Field(
        None, description="Category preferences"
    )
    frequency_limits: Optional[Dict[str, int]] = Field(
        None, description="Frequency limits per category"
    )
    quiet_hours_enabled: Optional[bool] = Field(None, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field(
        None, description="Quiet hours start (HH:MM)"
    )
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")


class NotificationRequest(BaseModel):
    """Notification request model."""

    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    category: str = Field(default="general", description="Notification category")
    priority: str = Field(default="medium", description="Notification priority")
    channels: Optional[List[str]] = Field(
        default=["in_app"], description="Notification channels"
    )
    data: Optional[Dict[str, Any]] = Field(
        None, description="Additional notification data"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Notification expiration time"
    )


class BatchNotificationRequest(BaseModel):
    """Batch notification request model."""

    notifications: List[NotificationRequest] = Field(
        ..., description="List of notifications"
    )
    batch_id: Optional[str] = Field(None, description="Batch ID for tracking")


class UserInterestsRequest(BaseModel):
    """User interests request model."""

    interactions: List[Dict[str, Any]] = Field(..., description="User interaction data")


class AlertRequest(BaseModel):
    """Alert request model."""

    type: str = Field(..., description="Alert type")
    priority: str = Field(default="medium", description="Alert priority")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional alert data")
    context: Optional[Dict[str, Any]] = Field(None, description="Alert context")


# Dependency injection functions
def get_email_manager():
    """Get email communication manager instance."""
    return create_email_communication_manager(get_pool())


def get_notification_manager():
    """Get notification manager instance."""
    return create_notification_manager(get_pool())


def get_semantic_matcher():
    """Get semantic notification matcher instance."""
    return create_semantic_notification_matcher(get_pool())


def get_user_profiler():
    """Get user interest profiler instance."""
    return create_user_interest_profiler(get_pool())


def get_alert_processor():
    """Get alert processor instance."""
    return create_alert_processor(get_pool())


def get_batch_processor():
    """Get notification batch processor instance."""
    return create_notification_batch_processor(get_pool())


@router.post("/email/send")
async def send_email(
    request: EmailRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    email_manager=Depends(get_email_manager),
) -> Dict[str, str]:
    """Send an email to a user."""
    try:
        email = await email_manager.send_email(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            to_email=request.to_email,
            subject=request.subject,
            body=request.body,
            category=request.category,
            template_id=request.template_id,
            variables=request.variables or {},
            reply_to=request.reply_to,
            from_email=request.from_email,
        )

        return {
            "email_id": email.id,
            "status": email.status,
            "sent_at": email.sent_at.isoformat() if email.sent_at else None,
            "message": "Email sent successfully",
        }

    except Exception:
        logger.exception("Failed to send email")
        raise HTTPException(status_code=500, detail="Failed to send email. Please try again.")


@router.post("/email/send-template")
async def send_template_email(
    request: TemplateEmailRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    email_manager=Depends(get_email_manager),
) -> Dict[str, str]:
    """Send an email using a template."""
    try:
        email = await email_manager.send_template_email(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            template_id=request.template_id,
            variables=request.variables,
            to_email=request.to_email,
            reply_to=request.reply_to,
        )

        return {
            "email_id": email.id,
            "template_id": email.template_id,
            "status": email.status,
            "sent_at": email.sent_at.isoformat() if email.sent_at else None,
            "message": "Template email sent successfully",
        }

    except Exception:
        logger.exception("Failed to send template email")
        raise HTTPException(
            status_code=500, detail="Failed to send template email. Please try again."
        )


@router.get("/email/preferences")
async def get_email_preferences(
    ctx: TenantContext = Depends(get_tenant_context),
    email_manager=Depends(get_email_manager),
) -> Dict[str, Any]:
    """Get user email preferences."""
    try:
        preferences = await email_manager.get_email_preferences(
            ctx.user_id, ctx.tenant_id
        )

        return {
            "user_id": preferences.user_id,
            "tenant_id": preferences.tenant_id,
            "email_enabled": preferences.email_enabled,
            "categories": preferences.categories,
            "frequency_limits": preferences.frequency_limits,
            "quiet_hours_enabled": preferences.quiet_hours_enabled,
            "quiet_hours_start": preferences.quiet_hours_start,
            "quiet_hours_end": preferences.quiet_hours_end,
            "updated_at": preferences.updated_at.isoformat(),
        }

    except Exception:
        logger.exception("Failed to get email preferences")
        raise HTTPException(
            status_code=500, detail="Failed to get email preferences. Please try again."
        )


@router.put("/email/preferences")
async def update_email_preferences(
    request: EmailPreferencesRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    email_manager=Depends(get_email_manager),
) -> Dict[str, Any]:
    """Update user email preferences."""
    try:
        preferences = await email_manager.update_email_preferences(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            email_enabled=request.email_enabled,
            categories=request.categories,
            frequency_limits=request.frequency_limits,
            quiet_hours_enabled=request.quiet_hours_enabled,
            quiet_hours_start=request.quiet_hours_start,
            quiet_hours_end=request.quiet_hours_end,
        )

        return {
            "user_id": preferences.user_id,
            "tenant_id": preferences.tenant_id,
            "email_enabled": preferences.email_enabled,
            "categories": preferences.categories,
            "frequency_limits": preferences.frequency_limits,
            "quiet_hours_enabled": preferences.quiet_hours_enabled,
            "quiet_hours_start": preferences.quiet_hours_start,
            "quiet_hours_end": preferences.quiet_hours_end,
            "updated_at": preferences.updated_at.isoformat(),
            "message": "Email preferences updated successfully",
        }

    except Exception:
        logger.exception("Failed to update email preferences")
        raise HTTPException(
            status_code=500, detail="Failed to update email preferences. Please try again."
        )


@router.get("/email/history")
async def get_email_history(
    limit: int = Query(50, ge=1, le=100, description="Number of emails to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    category: Optional[str] = Query(None, description="Filter by category"),
    ctx: TenantContext = Depends(get_tenant_context),
    email_manager=Depends(get_email_manager),
) -> Dict[str, Any]:
    """Get email communication history."""
    try:
        emails = await email_manager.get_email_history(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            limit=limit,
            offset=offset,
            category=category,
        )

        return {
            "emails": [
                {
                    "id": email.id,
                    "subject": email.subject,
                    "to_email": email.to_email,
                    "category": email.category,
                    "status": email.status,
                    "sent_at": email.sent_at.isoformat() if email.sent_at else None,
                    "error_message": email.error_message,
                    "created_at": email.created_at.isoformat(),
                }
                for email in emails
            ],
            "total": len(emails),
            "limit": limit,
            "offset": offset,
        }

    except Exception:
        logger.exception("Failed to get email history")
        raise HTTPException(
            status_code=500, detail="Failed to get email history. Please try again."
        )


@router.post("/notifications/send")
async def send_notification(
    request: NotificationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager),
) -> Dict[str, str]:
    """Send a notification to a user."""
    try:
        notification = await notification_manager.send_notification(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            title=request.title,
            message=request.message,
            category=request.category,
            priority=request.priority,
            channels=request.channels,
            data=request.data or {},
            expires_at=request.expires_at,
        )

        return {
            "notification_id": notification.id,
            "status": "sent",
            "channels": notification.channels,
            "created_at": notification.created_at.isoformat(),
            "message": "Notification sent successfully",
        }

    except Exception:
        logger.exception("Failed to send notification")
        raise HTTPException(
            status_code=500, detail="Failed to send notification. Please try again."
        )


@router.post("/notifications/batch")
async def send_batch_notifications(
    request: BatchNotificationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager),
) -> Dict[str, Any]:
    """Send multiple notifications in batch."""
    try:
        # Convert to notification manager format
        notifications_data = []
        for notif_request in request.notifications:
            notifications_data.append(
                {
                    "user_id": ctx.user_id,
                    "tenant_id": ctx.tenant_id,
                    "title": notif_request.title,
                    "message": notif_request.message,
                    "category": notif_request.category,
                    "priority": notif_request.priority,
                    "channels": notif_request.channels,
                    "data": notif_request.data or {},
                }
            )

        result = await notification_manager.send_batch_notifications(
            notifications=notifications_data,
            batch_id=request.batch_id,
        )

        return {
            "batch_id": result["batch_id"],
            "total": result["total"],
            "successful": result["successful"],
            "failed": result["failed"],
            "results": result["results"],
            "message": f"Batch processing completed: {result['successful']}/{result['total']} successful",
        }

    except Exception:
        logger.exception("Failed to send batch notifications")
        raise HTTPException(
            status_code=500, detail="Failed to send batch notifications. Please try again."
        )


@router.get("/notifications")
async def get_notifications(
    limit: int = Query(
        50, ge=1, le=100, description="Number of notifications to return"
    ),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    category: Optional[str] = Query(None, description="Filter by category"),
    unread_only: bool = Query(False, description="Only return unread notifications"),
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager),
) -> Dict[str, Any]:
    """Get user notifications."""
    try:
        notifications = await notification_manager.get_notifications(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            limit=limit,
            offset=offset,
            category=category,
            unread_only=unread_only,
        )

        return {
            "notifications": [
                {
                    "id": notif.id,
                    "title": notif.title,
                    "message": notif.message,
                    "category": notif.category,
                    "priority": notif.priority,
                    "channels": notif.channels,
                    "is_read": notif.is_read,
                    "data": notif.data,
                    "expires_at": notif.expires_at.isoformat()
                    if notif.expires_at
                    else None,
                    "created_at": notif.created_at.isoformat(),
                }
                for notif in notifications
            ],
            "total": len(notifications),
            "limit": limit,
            "offset": offset,
        }

    except Exception:
        logger.exception("Failed to get notifications")
        raise HTTPException(
            status_code=500, detail="Failed to get notifications. Please try again."
        )


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager),
) -> Dict[str, str]:
    """Mark notification as read."""
    try:
        success = await notification_manager.mark_as_read(
            notification_id, ctx.user_id, ctx.tenant_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {
            "notification_id": notification_id,
            "status": "read",
            "message": "Notification marked as read",
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to mark notification as read")
        raise HTTPException(
            status_code=500, detail="Failed to mark notification as read. Please try again."
        )


@router.put("/notifications/read-all")
async def mark_all_notifications_read(
    category: Optional[str] = Query(
        None, description="Category to mark as read (all if not specified)"
    ),
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager),
) -> Dict[str, Any]:
    """Mark all notifications as read."""
    try:
        count = await notification_manager.mark_all_as_read(
            ctx.user_id, ctx.tenant_id, category
        )

        return {
            "count": count,
            "category": category or "all",
            "message": f"Marked {count} notifications as read",
        }

    except Exception:
        logger.exception("Failed to mark all notifications as read")
        raise HTTPException(
            status_code=500,
            detail="Failed to mark all notifications as read. Please try again.",
        )


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager),
) -> Dict[str, str]:
    """Delete a notification."""
    try:
        success = await notification_manager.delete_notification(
            notification_id, ctx.user_id, ctx.tenant_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {
            "notification_id": notification_id,
            "message": "Notification deleted successfully",
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete notification")
        raise HTTPException(
            status_code=500, detail="Failed to delete notification. Please try again."
        )


@router.get("/notifications/stats")
async def get_notification_stats(
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager),
) -> Dict[str, Any]:
    """Get notification statistics."""
    try:
        stats = await notification_manager.get_notification_stats(
            ctx.user_id, ctx.tenant_id
        )

        return {
            "stats": stats,
            "message": "Notification statistics retrieved successfully",
        }

    except Exception:
        logger.exception("Failed to get notification stats")
        raise HTTPException(
            status_code=500, detail="Failed to get notification stats. Please try again."
        )


@router.get("/preferences")
async def get_notification_preferences(
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager),
) -> Dict[str, Any]:
    """Get user notification preferences."""
    try:
        preferences = await notification_manager.get_user_preferences(
            ctx.user_id, ctx.tenant_id
        )

        return {
            "user_id": preferences.user_id,
            "tenant_id": preferences.tenant_id,
            "in_app_enabled": preferences.in_app_enabled,
            "email_enabled": preferences.email_enabled,
            "push_enabled": preferences.push_enabled,
            "sms_enabled": preferences.sms_enabled,
            "categories": preferences.categories,
            "do_not_disturb_enabled": preferences.do_not_disturb_enabled,
            "do_not_disturb_start": preferences.do_not_disturb_start,
            "do_not_disturb_end": preferences.do_not_disturb_end,
            "updated_at": preferences.updated_at.isoformat(),
        }

    except Exception:
        logger.exception("Failed to get notification preferences")
        raise HTTPException(
            status_code=500, detail="Failed to get notification preferences. Please try again."
        )


@router.put("/preferences")
async def update_notification_preferences(
    in_app_enabled: Optional[bool] = None,
    email_enabled: Optional[bool] = None,
    push_enabled: Optional[bool] = None,
    sms_enabled: Optional[bool] = None,
    categories: Optional[Dict[str, Dict[str, bool]]] = None,
    do_not_disturb_enabled: Optional[bool] = None,
    do_not_disturb_start: Optional[str] = None,
    do_not_disturb_end: Optional[str] = None,
    ctx: TenantContext = Depends(get_tenant_context),
    notification_manager=Depends(get_notification_manager),
) -> Dict[str, Any]:
    """Update user notification preferences."""
    try:
        preferences = await notification_manager.update_preferences(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            in_app_enabled=in_app_enabled,
            email_enabled=email_enabled,
            push_enabled=push_enabled,
            sms_enabled=sms_enabled,
            categories=categories,
            do_not_disturb_enabled=do_not_disturb_enabled,
            do_not_disturb_start=do_not_disturb_start,
            do_not_disturb_end=do_not_disturb_end,
        )

        return {
            "user_id": preferences.user_id,
            "tenant_id": preferences.tenant_id,
            "in_app_enabled": preferences.in_app_enabled,
            "email_enabled": preferences.email_enabled,
            "push_enabled": preferences.push_enabled,
            "sms_enabled": preferences.sms_enabled,
            "categories": preferences.categories,
            "do_not_disturb_enabled": preferences.do_not_disturb_enabled,
            "do_not_disturb_start": preferences.do_not_disturb_start,
            "do_not_disturb_end": preferences.do_not_disturb_end,
            "updated_at": preferences.updated_at.isoformat(),
            "message": "Notification preferences updated successfully",
        }

    except Exception:
        logger.exception("Failed to update notification preferences")
        raise HTTPException(
            status_code=500,
            detail="Failed to update notification preferences. Please try again.",
        )


@router.get("/interests")
async def get_user_interests(
    ctx: TenantContext = Depends(get_tenant_context),
    user_profiler=Depends(get_user_profiler),
) -> Dict[str, Any]:
    """Get user interest profile."""
    try:
        profile = await user_profiler.get_user_profile(ctx.user_id, ctx.tenant_id)

        return {
            "user_id": profile.user_id,
            "tenant_id": profile.tenant_id,
            "interests": profile.interests,
            "keywords": profile.keywords,
            "last_updated": profile.last_updated.isoformat(),
            "created_at": profile.created_at.isoformat(),
        }

    except Exception:
        logger.exception("Failed to get user interests")
        raise HTTPException(
            status_code=500, detail="Failed to get user interests. Please try again."
        )


@router.post("/interests/update")
async def update_user_interests(
    request: UserInterestsRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    user_profiler=Depends(get_user_profiler),
) -> Dict[str, Any]:
    """Update user interests based on interactions."""
    try:
        profile = await user_profiler.analyze_user_interactions(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            interactions=request.interactions,
        )

        return {
            "user_id": profile.user_id,
            "tenant_id": profile.tenant_id,
            "interests": profile.interests,
            "keywords": profile.keywords,
            "last_updated": profile.last_updated.isoformat(),
            "message": "User interests updated successfully",
        }

    except Exception:
        logger.exception("Failed to update user interests")
        raise HTTPException(
            status_code=500, detail="Failed to update user interests. Please try again."
        )


@router.get("/interests/top")
async def get_top_interests(
    limit: int = Query(
        10, ge=1, le=20, description="Number of top interests to return"
    ),
    min_score: float = Query(0.1, ge=0.0, le=1.0, description="Minimum interest score"),
    ctx: TenantContext = Depends(get_tenant_context),
    user_profiler=Depends(get_user_profiler),
) -> Dict[str, Any]:
    """Get user's top interests."""
    try:
        top_interests = await user_profiler.get_top_interests(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            limit=limit,
            min_score=min_score,
        )

        return {
            "top_interests": [
                {"category": category, "score": score}
                for category, score in top_interests
            ],
            "limit": limit,
            "min_score": min_score,
        }

    except Exception:
        logger.exception("Failed to get top interests")
        raise HTTPException(
            status_code=500, detail="Failed to get top interests. Please try again."
        )


@router.get("/semantic/match")
async def calculate_semantic_match(
    content: str = Query(..., description="Content to match"),
    category: str = Query(..., description="Content category"),
    ctx: TenantContext = Depends(get_tenant_context),
    semantic_matcher=Depends(get_semantic_matcher),
) -> Dict[str, Any]:
    """Calculate semantic match between content and user interests."""
    try:
        similarity = await semantic_matcher.calculate_relevance(
            notification_id="",  # Not needed for this endpoint
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            notification_content={
                "title": content[:50],
                "message": content,
                "category": category,
            },
        )

        return {
            "similarity_score": similarity.relevance_score,
            "category_scores": similarity.category_scores,
            "keyword_matches": similarity.keyword_matches,
            "semantic_factors": similarity.semantic_factors,
            "calculated_at": similarity.calculated_at.isoformat(),
        }

    except Exception:
        logger.exception("Failed to calculate semantic match")
        raise HTTPException(
            status_code=500, detail="Failed to calculate semantic match. Please try again."
        )


@router.post("/alerts/process")
async def process_alert(
    request: AlertRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    alert_processor=Depends(get_alert_processor),
) -> Dict[str, str]:
    """Process an alert through rule-based system."""
    try:
        alert_data = {
            "type": request.type,
            "priority": request.priority,
            "user_id": ctx.user_id,
            "tenant_id": ctx.tenant_id,
            "title": request.title,
            "message": request.message,
            "data": request.data or {},
            "context": request.context or {},
        }

        alert = await alert_processor.process_alert(alert_data)

        return {
            "alert_id": alert.id,
            "type": alert.type.value,
            "priority": alert.priority.value,
            "status": alert.status,
            "processed_at": alert.processed_at.isoformat()
            if alert.processed_at
            else None,
            "message": "Alert processed successfully",
        }

    except Exception:
        logger.exception("Failed to process alert")
        raise HTTPException(
            status_code=500, detail="Failed to process alert. Please try again."
        )


@router.get("/alerts/history")
async def get_alert_history(
    limit: int = Query(50, ge=1, le=100, description="Number of alerts to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    ctx: TenantContext = Depends(get_tenant_context),
    alert_processor=Depends(get_alert_processor),
) -> Dict[str, Any]:
    """Get alert processing history."""
    try:
        from packages.backend.domain.alert_processor import AlertType

        alert_type_enum = AlertType(alert_type) if alert_type else None

        alerts = await alert_processor.get_alert_history(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            alert_type=alert_type_enum,
            status=status,
            limit=limit,
            offset=offset,
        )

        return {
            "alerts": [
                {
                    "id": alert.id,
                    "type": alert.type.value,
                    "priority": alert.priority.value,
                    "title": alert.title,
                    "message": alert.message,
                    "status": alert.status,
                    "data": alert.data,
                    "processed_at": alert.processed_at.isoformat()
                    if alert.processed_at
                    else None,
                    "created_at": alert.created_at.isoformat(),
                }
                for alert in alerts
            ],
            "total": len(alerts),
            "limit": limit,
            "offset": offset,
        }

    except Exception:
        logger.exception("Failed to get alert history")
        raise HTTPException(
            status_code=500, detail="Failed to get alert history. Please try again."
        )


@router.get("/alerts/stats")
async def get_alert_stats(
    ctx: TenantContext = Depends(get_tenant_context),
    alert_processor=Depends(get_alert_processor),
) -> Dict[str, Any]:
    """Get alert processing statistics."""
    try:
        stats = await alert_processor.get_alert_stats(ctx.tenant_id)

        return {
            "stats": stats,
            "message": "Alert statistics retrieved successfully",
        }

    except Exception:
        logger.exception("Failed to get alert stats")
        raise HTTPException(
            status_code=500, detail="Failed to get alert stats. Please try again."
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for communications system."""
    return {
        "status": "healthy",
        "service": "communications",
        "features": [
            "email_communications",
            "notifications",
            "semantic_matching",
            "user_interests",
            "alert_processing",
            "batch_processing",
        ],
    }
