"""
Integrations API endpoints — Slack, Notion, Google Drive, Zapier.
"""

from __future__ import annotations

import base64
from typing import Any

import asyncpg
from backend.domain.google_drive_integration import GoogleDriveIntegrationManager
from backend.domain.notion_integration import (
    APPLICATION_DATABASE_SCHEMA,
    NotionClient,
    NotionIntegrationManager,
)
from backend.domain.slack_integration import SlackIntegrationManager, SlackMessageType
from backend.domain.zapier_integration import ZapierIntegrationManager
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from shared.logging_config import get_logger

logger = get_logger("sorce.api.integrations")

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


async def _get_user_id() -> str:
    raise NotImplementedError("User ID dependency not injected")


async def _get_tenant_id() -> str:
    raise NotImplementedError("Tenant ID dependency not injected")


# ============ SLACK ============

slack_router = APIRouter(prefix="/slack", tags=["slack"])


class SlackConnectRequest(BaseModel):
    team_id: str
    access_token: str
    bot_user_id: str | None = None
    default_channel: str | None = None


class SlackNotificationRequest(BaseModel):
    message_type: str
    template_vars: dict[str, Any]
    channel: str | None = None


class SlackEnabledNotificationsRequest(BaseModel):
    notification_types: list[str]


@slack_router.post("/connect")
async def connect_slack(
    body: SlackConnectRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    manager = SlackIntegrationManager(db)

    await manager.register_team(
        tenant_id=tenant_id,
        team_id=body.team_id,
        access_token=body.access_token,
        bot_user_id=body.bot_user_id,
        default_channel=body.default_channel,
    )

    return {"status": "connected"}


@slack_router.get("/status")
async def get_slack_status(
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = SlackIntegrationManager(db)
    config = await manager.get_team_config(tenant_id)

    if not config:
        return {"connected": False}

    return {
        "connected": True,
        "team_id": config.team_id,
        "default_channel": config.default_channel,
        "enabled_notifications": config.enabled_notifications,
    }


@slack_router.post("/notify")
async def send_slack_notification(
    body: SlackNotificationRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = SlackIntegrationManager(db)

    try:
        message_type = SlackMessageType(body.message_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message type")

    success = await manager.send_notification(
        tenant_id=tenant_id,
        message_type=message_type,
        template_vars=body.template_vars,
        channel=body.channel,
    )

    return {"success": success}


@slack_router.put("/notifications")
async def set_slack_notifications(
    body: SlackEnabledNotificationsRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    manager = SlackIntegrationManager(db)

    await manager.set_enabled_notifications(tenant_id, body.notification_types)

    return {"status": "updated"}


@slack_router.delete("/disconnect")
async def disconnect_slack(
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    manager = SlackIntegrationManager(db)

    await manager.disconnect_team(tenant_id)

    return {"status": "disconnected"}


# ============ NOTION ============

notion_router = APIRouter(prefix="/notion", tags=["notion"])


class NotionConnectRequest(BaseModel):
    access_token: str
    workspace_id: str | None = None
    database_id: str | None = None


class NotionExportRequest(BaseModel):
    application: dict[str, Any]


class NotionCreateDatabaseRequest(BaseModel):
    parent_page_id: str
    title: str = "Job Applications"


@notion_router.post("/connect")
async def connect_notion(
    body: NotionConnectRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    manager = NotionIntegrationManager(db)

    await manager.configure(
        tenant_id=tenant_id,
        access_token=body.access_token,
        workspace_id=body.workspace_id,
        database_id=body.database_id,
    )

    return {"status": "connected"}


@notion_router.get("/status")
async def get_notion_status(
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = NotionIntegrationManager(db)
    config = await manager.get_config(tenant_id)

    if not config:
        return {"connected": False}

    return {
        "connected": True,
        "workspace_id": config.workspace_id,
        "database_id": config.database_id,
    }


@notion_router.post("/export")
async def export_to_notion(
    body: NotionExportRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = NotionIntegrationManager(db)

    page = await manager.export_application(tenant_id, body.application)

    if not page:
        raise HTTPException(status_code=500, detail="Failed to export to Notion")

    return {
        "success": True,
        "page_id": page.page_id,
        "url": page.url,
    }


@notion_router.post("/databases")
async def create_notion_database(
    body: NotionCreateDatabaseRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = NotionIntegrationManager(db)
    config = await manager.get_config(tenant_id)

    if not config:
        raise HTTPException(status_code=404, detail="Notion not connected")

    client = NotionClient(config.access_token)
    result = await client.create_database(
        parent_page_id=body.parent_page_id,
        title=body.title,
        schema=APPLICATION_DATABASE_SCHEMA,
    )

    await manager.configure(
        tenant_id=tenant_id,
        access_token=config.access_token,
        workspace_id=config.workspace_id,
        database_id=result["id"],
    )

    return {
        "database_id": result["id"],
        "title": body.title,
    }


@notion_router.delete("/disconnect")
async def disconnect_notion(
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE public.notion_integrations SET is_active = false WHERE tenant_id = $1",
            tenant_id,
        )

    return {"status": "disconnected"}


# ============ GOOGLE DRIVE ============

gdrive_router = APIRouter(prefix="/google-drive", tags=["google-drive"])


class GoogleDriveConnectRequest(BaseModel):
    access_token: str
    refresh_token: str | None = None


class GoogleDriveBackupRequest(BaseModel):
    file_name: str = "resume.pdf"
    content_base64: str


@gdrive_router.post("/connect")
async def connect_google_drive(
    body: GoogleDriveConnectRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    manager = GoogleDriveIntegrationManager(db)

    await manager.configure(
        tenant_id=tenant_id,
        user_id=user_id,
        access_token=body.access_token,
        refresh_token=body.refresh_token,
    )

    return {"status": "connected"}


@gdrive_router.get("/status")
async def get_google_drive_status(
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = GoogleDriveIntegrationManager(db)
    config = await manager.get_config(tenant_id, user_id)

    if not config:
        return {"connected": False}

    backups = await manager.list_backups(tenant_id, user_id)

    return {
        "connected": True,
        "folder_id": config.folder_id,
        "backups": backups,
    }


@gdrive_router.post("/backup")
async def backup_to_google_drive(
    body: GoogleDriveBackupRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = GoogleDriveIntegrationManager(db)

    try:
        content = base64.b64decode(body.content_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")

    result = await manager.backup_resume(
        tenant_id=tenant_id,
        user_id=user_id,
        resume_content=content,
        file_name=body.file_name,
    )

    return {
        "success": result.success,
        "file_id": result.file_id,
        "bytes_synced": result.bytes_synced,
        "error": result.error,
    }


@gdrive_router.get("/backups")
async def list_google_drive_backups(
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> list[dict[str, Any]]:
    manager = GoogleDriveIntegrationManager(db)

    return await manager.list_backups(tenant_id, user_id)


@gdrive_router.delete("/disconnect")
async def disconnect_google_drive(
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    manager = GoogleDriveIntegrationManager(db)

    await manager.disconnect(tenant_id, user_id)

    return {"status": "disconnected"}


# ============ ZAPIER ============

zapier_router = APIRouter(prefix="/zapier", tags=["zapier"])


class ZapierSubscribeRequest(BaseModel):
    webhook_url: str
    event_types: list[str]


class ZapierTriggerRequest(BaseModel):
    event_type: str
    payload: dict[str, Any]


@zapier_router.post("/hooks")
async def create_zapier_hook(
    body: ZapierSubscribeRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = ZapierIntegrationManager(db)

    hook = await manager.subscribe(
        tenant_id=tenant_id,
        user_id=user_id,
        webhook_url=body.webhook_url,
        event_types=body.event_types,
    )

    return {
        "hook_id": hook.hook_id,
        "event_types": hook.event_types,
        "created_at": hook.created_at.isoformat() if hook.created_at else None,
    }


@zapier_router.get("/hooks")
async def list_zapier_hooks(
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> list[dict[str, Any]]:
    manager = ZapierIntegrationManager(db)

    hooks = await manager.list_hooks(tenant_id)

    return [
        {
            "hook_id": h.hook_id,
            "webhook_url": h.webhook_url,
            "event_types": h.event_types,
            "is_active": h.is_active,
            "created_at": h.created_at.isoformat() if h.created_at else None,
            "last_triggered_at": h.last_triggered_at.isoformat()
            if h.last_triggered_at
            else None,
        }
        for h in hooks
    ]


@zapier_router.delete("/hooks/{hook_id}")
async def delete_zapier_hook(
    hook_id: str,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),  # SECURITY: Require authentication and validate ownership
) -> dict[str, str]:
    manager = ZapierIntegrationManager(db)

    # SECURITY: Validate hook ownership before deletion
    success = await manager.unsubscribe(hook_id, tenant_id=tenant_id)

    if not success:
        raise HTTPException(status_code=404, detail="Hook not found")

    return {"status": "deleted"}


@zapier_router.post("/trigger")
async def trigger_zapier_event(
    body: ZapierTriggerRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = ZapierIntegrationManager(db)

    triggered = await manager.trigger_event(
        tenant_id=tenant_id,
        event_type=body.event_type,
        payload=body.payload,
    )

    return {
        "event_type": body.event_type,
        "hooks_triggered": triggered,
    }


@zapier_router.get("/triggers")
async def list_zapier_triggers() -> list[dict[str, Any]]:
    return ZapierIntegrationManager.get_available_triggers()


@zapier_router.get("/templates")
async def list_zap_templates() -> list[dict[str, Any]]:
    return ZapierIntegrationManager.get_zap_templates()


# Register sub-routers
router.include_router(slack_router)
router.include_router(notion_router)
router.include_router(gdrive_router)
router.include_router(zapier_router)
