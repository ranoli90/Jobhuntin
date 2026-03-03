"""Notion Integration — export applications to Notion workspace.

Features:
  - Export applications to Notion database
  - Sync application status
  - Custom database templates
  - OAuth authentication
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timezone, UTC, datetime
from typing import Any

import asyncpg
from shared.logging_config import get_logger

from shared.metrics import incr

logger = get_logger("sorce.notion")


@dataclass
class NotionConfig:
    tenant_id: str
    access_token: str
    workspace_id: str | None = None
    database_id: str | None = None
    is_active: bool = True


@dataclass
class NotionPage:
    page_id: str
    title: str
    properties: dict[str, Any] = field(default_factory=dict)
    url: str | None = None


APPLICATION_DATABASE_SCHEMA = {
    "Title": {"title": {}},
    "Company": {"rich_text": {}},
    "Position": {"rich_text": {}},
    "Status": {
        "select": {
            "options": [
                {"name": "Saved", "color": "gray"},
                {"name": "Applied", "color": "blue"},
                {"name": "Interview", "color": "yellow"},
                {"name": "Offer", "color": "green"},
                {"name": "Rejected", "color": "red"},
            ]
        }
    },
    "Applied Date": {"date": {}},
    "Location": {"rich_text": {}},
    "Salary": {"number": {"format": "dollar"}},
    "Match Score": {"number": {}},
    "URL": {"url": {}},
    "Notes": {"rich_text": {}},
}


class NotionClient:
    API_BASE = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, access_token: str):
        self.access_token = access_token

    async def create_database(
        self,
        parent_page_id: str,
        title: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        import httpx

        properties = {k: v for k, v in schema.items()}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.API_BASE}/databases",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "Notion-Version": self.NOTION_VERSION,
                },
                json={
                    "parent": {"page_id": parent_page_id},
                    "title": [{"type": "text", "text": {"content": title}}],
                    "properties": properties,
                },
            )

            data = response.json()
            if response.status_code not in (200, 201):
                logger.error("Notion API error: %s", data)
                raise Exception(f"Notion API error: {data.get('message')}")

            incr("notion.database_created")
            return data

    async def create_page(
        self,
        database_id: str,
        properties: dict[str, Any],
    ) -> NotionPage:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.API_BASE}/pages",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "Notion-Version": self.NOTION_VERSION,
                },
                json={
                    "parent": {"database_id": database_id},
                    "properties": properties,
                },
            )

            data = response.json()
            if response.status_code not in (200, 201):
                logger.error("Notion create page error: %s", data)
                raise Exception(f"Notion API error: {data.get('message')}")

            incr("notion.page_created")
            return NotionPage(
                page_id=data["id"],
                title=data.get("properties", {})
                .get("Title", {})
                .get("title", [{}])[0]
                .get("plain_text", ""),
                properties=data.get("properties", {}),
                url=data.get("url"),
            )

    async def update_page(
        self,
        page_id: str,
        properties: dict[str, Any],
    ) -> NotionPage:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.patch(
                f"{self.API_BASE}/pages/{page_id}",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "Notion-Version": self.NOTION_VERSION,
                },
                json={"properties": properties},
            )

            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Notion API error: {data.get('message')}")

            incr("notion.page_updated")
            return NotionPage(
                page_id=data["id"],
                title="",
                properties=data.get("properties", {}),
            )

    async def query_database(
        self,
        database_id: str,
        filter_query: dict[str, Any] | None = None,
    ) -> list[NotionPage]:
        import httpx

        payload = {}
        if filter_query:
            payload["filter"] = filter_query

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.API_BASE}/databases/{database_id}/query",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "Notion-Version": self.NOTION_VERSION,
                },
                json=payload,
            )

            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Notion API error: {data.get('message')}")

            pages = []
            for result in data.get("results", []):
                pages.append(
                    NotionPage(
                        page_id=result["id"],
                        title="",
                        properties=result.get("properties", {}),
                        url=result.get("url"),
                    )
                )

            return pages


class NotionIntegrationManager:
    def __init__(self, db_pool: asyncpg.Pool):
        self._pool = db_pool

    async def configure(
        self,
        tenant_id: str,
        access_token: str,
        workspace_id: str | None = None,
        database_id: str | None = None,
    ) -> NotionConfig:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.notion_integrations
                    (tenant_id, access_token, workspace_id, database_id, is_active)
                VALUES ($1, $2, $3, $4, true)
                ON CONFLICT (tenant_id) DO UPDATE SET
                    access_token = $2,
                    workspace_id = $3,
                    database_id = $4,
                    is_active = true,
                    updated_at = now()
                """,
                tenant_id,
                access_token,
                workspace_id,
                database_id,
            )

        incr("notion.configured")
        return NotionConfig(
            tenant_id=tenant_id,
            access_token=access_token,
            workspace_id=workspace_id,
            database_id=database_id,
        )

    async def get_config(self, tenant_id: str) -> NotionConfig | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT access_token, workspace_id, database_id, is_active
                FROM public.notion_integrations
                WHERE tenant_id = $1 AND is_active = true
                """,
                tenant_id,
            )

            if not row:
                return None

            return NotionConfig(
                tenant_id=tenant_id,
                access_token=row["access_token"],
                workspace_id=row["workspace_id"],
                database_id=row["database_id"],
                is_active=row["is_active"],
            )

    async def export_application(
        self,
        tenant_id: str,
        application: dict[str, Any],
    ) -> NotionPage | None:
        config = await self.get_config(tenant_id)
        if not config or not config.database_id:
            logger.warning("Notion not configured for tenant: %s", tenant_id)
            return None

        client = NotionClient(config.access_token)

        properties = {
            "Title": {
                "title": [
                    {"text": {"content": application.get("job_title", "Untitled")}}
                ]
            },
            "Company": {
                "rich_text": [{"text": {"content": application.get("company", "")}}]
            },
            "Position": {
                "rich_text": [{"text": {"content": application.get("job_title", "")}}]
            },
            "Status": {
                "select": {"name": self._map_status(application.get("status", "saved"))}
            },
            "Applied Date": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
            "Location": {
                "rich_text": [{"text": {"content": application.get("location", "")}}]
            },
            "URL": {"url": application.get("job_url")},
        }

        if application.get("salary"):
            properties["Salary"] = {"number": application["salary"]}

        if application.get("match_score"):
            properties["Match Score"] = {"number": application["match_score"]}

        page = await client.create_page(config.database_id, properties)
        incr("notion.application_exported")

        await self._save_export_record(tenant_id, application.get("id"), page.page_id)

        return page

    async def sync_application_status(
        self,
        tenant_id: str,
        application_id: str,
        new_status: str,
    ) -> bool:
        config = await self.get_config(tenant_id)
        if not config:
            return False

        notion_page_id = await self._get_notion_page_id(tenant_id, application_id)
        if not notion_page_id:
            return False

        client = NotionClient(config.access_token)
        properties = {
            "Status": {"select": {"name": self._map_status(new_status)}},
        }

        await client.update_page(notion_page_id, properties)
        incr("notion.status_synced")
        return True

    async def export_applications_batch(
        self,
        tenant_id: str,
        applications: list[dict[str, Any]],
    ) -> list[NotionPage]:
        results = []
        for app in applications:
            try:
                page = await self.export_application(tenant_id, app)
                if page:
                    results.append(page)
            except Exception as e:
                logger.error("Failed to export application: %s", e)

        incr("notion.batch_exported", None, len(results))
        return results

    def _map_status(self, status: str) -> str:
        status_map = {
            "saved": "Saved",
            "queued": "Saved",
            "applied": "Applied",
            "submitted": "Applied",
            "interview": "Interview",
            "interview_scheduled": "Interview",
            "offer": "Offer",
            "rejected": "Rejected",
            "failed": "Rejected",
        }
        return status_map.get(status.lower(), "Saved")

    async def _save_export_record(
        self,
        tenant_id: str,
        application_id: str | None,
        notion_page_id: str,
    ) -> None:
        if not application_id:
            return

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.notion_exports
                    (tenant_id, application_id, notion_page_id, exported_at)
                VALUES ($1, $2, $3, now())
                ON CONFLICT (application_id) DO UPDATE SET
                    notion_page_id = $3,
                    exported_at = now()
                """,
                tenant_id,
                application_id,
                notion_page_id,
            )

    async def _get_notion_page_id(
        self,
        tenant_id: str,
        application_id: str,
    ) -> str | None:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                """
                SELECT notion_page_id FROM public.notion_exports
                WHERE tenant_id = $1 AND application_id = $2
                """,
                tenant_id,
                application_id,
            )


async def init_notion_tables(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.notion_integrations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID UNIQUE NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            access_token TEXT NOT NULL,
            workspace_id TEXT,
            database_id TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS public.notion_exports (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            application_id UUID UNIQUE REFERENCES public.applications(id) ON DELETE CASCADE,
            notion_page_id TEXT NOT NULL,
            exported_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_notion_tenant_id
            ON public.notion_integrations(tenant_id);

        CREATE INDEX IF NOT EXISTS idx_notion_exports_application_id
            ON public.notion_exports(application_id);
        """
    )
    logger.info("Notion tables initialized")
