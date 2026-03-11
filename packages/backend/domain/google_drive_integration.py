"""Google Drive Integration — resume backup and file storage.

Features:
  - OAuth authentication with Google
  - Resume backup to Google Drive
  - File sync and management
  - Folder organization
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.google_drive")


@dataclass
class GoogleDriveConfig:
    tenant_id: str
    user_id: str
    access_token: str
    refresh_token: str | None = None
    folder_id: str | None = None
    is_active: bool = True


@dataclass
class DriveFile:
    file_id: str
    name: str
    mime_type: str
    size: int
    created_time: datetime
    modified_time: datetime
    web_view_link: str | None = None
    download_link: str | None = None


@dataclass
class SyncResult:
    success: bool
    file_id: str | None = None
    error: str | None = None
    bytes_synced: int = 0


RESUME_FOLDER_NAME = "JobHuntin Resumes"
APPLICATION_FOLDER_NAME = "JobHuntin Applications"


class GoogleDriveClient:
    API_BASE = "https://www.googleapis.com/drive/v3"
    UPLOAD_BASE = "https://www.googleapis.com/upload/drive/v3"

    def __init__(self, access_token: str):
        self.access_token = access_token

    async def get_or_create_folder(
        self,
        folder_name: str,
        parent_id: str | None = None,
    ) -> str:
        import httpx

        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        else:
            query += " and 'root' in parents"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.API_BASE}/files",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={"q": query, "spaces": "drive", "fields": "files(id, name)"},
            )

            data = response.json()
            files = data.get("files", [])

            if files:
                fid = files[0].get("id") if isinstance(files[0], dict) else None
                if fid:
                    return fid

            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                folder_metadata["parents"] = [parent_id]

            response = await client.post(
                f"{self.API_BASE}/files",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=folder_metadata,
            )

            data = response.json()
            incr("google_drive.folder_created")
            return data["id"]

    async def upload_file(
        self,
        file_name: str,
        file_content: bytes,
        mime_type: str,
        folder_id: str | None = None,
    ) -> DriveFile:
        import httpx

        metadata = {"name": file_name}
        if folder_id:
            metadata["parents"] = [folder_id]

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.UPLOAD_BASE}/files?uploadType=multipart",
                headers={"Authorization": f"Bearer {self.access_token}"},
                files={
                    "metadata": (None, json.dumps(metadata), "application/json"),
                    "file": (file_name, file_content, mime_type),
                },
            )

            data = response.json()
            if response.status_code not in (200, 201):
                raise Exception(
                    f"Google Drive upload error: {data.get('error', {}).get('message')}"
                )

            incr("google_drive.file_uploaded")
            return DriveFile(
                file_id=data["id"],
                name=data["name"],
                mime_type=data.get("mimeType", mime_type),
                size=len(file_content),
                created_time=datetime.now(timezone.utc),
                modified_time=datetime.now(timezone.utc),
                web_view_link=data.get("webViewLink"),
            )

    async def get_file(self, file_id: str) -> DriveFile | None:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.API_BASE}/files/{file_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={
                    "fields": "id, name, mimeType, size, createdTime, modifiedTime, webViewLink, webContentLink"
                },
            )

            if response.status_code == 404:
                return None

            data = response.json()
            return DriveFile(
                file_id=data["id"],
                name=data["name"],
                mime_type=data.get("mimeType", ""),
                size=data.get("size", 0),
                created_time=datetime.fromisoformat(
                    data["createdTime"].replace("Z", "+00:00")
                ),
                modified_time=datetime.fromisoformat(
                    data["modifiedTime"].replace("Z", "+00:00")
                ),
                web_view_link=data.get("webViewLink"),
                download_link=data.get("webContentLink"),
            )

    async def download_file(self, file_id: str) -> bytes | None:
        import httpx

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{self.API_BASE}/files/{file_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={"alt": "media"},
            )

            if response.status_code != 200:
                return None

            incr("google_drive.file_downloaded")
            return response.content

    async def delete_file(self, file_id: str) -> bool:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                f"{self.API_BASE}/files/{file_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            success = response.status_code == 204
            if success:
                incr("google_drive.file_deleted")

            return success

    async def list_files(
        self,
        folder_id: str | None = None,
        limit: int = 100,
    ) -> list[DriveFile]:
        import httpx

        query = "trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.API_BASE}/files",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={
                    "q": query,
                    "pageSize": limit,
                    "fields": "files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
                },
            )

            data = response.json()
            files = []
            for f in data.get("files", []):
                files.append(
                    DriveFile(
                        file_id=f["id"],
                        name=f["name"],
                        mime_type=f.get("mimeType", ""),
                        size=f.get("size", 0),
                        created_time=datetime.fromisoformat(
                            f["createdTime"].replace("Z", "+00:00")
                        ),
                        modified_time=datetime.fromisoformat(
                            f["modifiedTime"].replace("Z", "+00:00")
                        ),
                        web_view_link=f.get("webViewLink"),
                    )
                )

            return files


class GoogleDriveIntegrationManager:
    def __init__(self, db_pool: asyncpg.Pool):
        self._pool = db_pool

    async def configure(
        self,
        tenant_id: str,
        user_id: str,
        access_token: str,
        refresh_token: str | None = None,
    ) -> GoogleDriveConfig:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.google_drive_integrations
                    (tenant_id, user_id, access_token, refresh_token, is_active)
                VALUES ($1, $2, $3, $4, true)
                ON CONFLICT (tenant_id, user_id) DO UPDATE SET
                    access_token = $3,
                    refresh_token = COALESCE($4, google_drive_integrations.refresh_token),
                    is_active = true,
                    updated_at = now()
                """,
                tenant_id,
                user_id,
                access_token,
                refresh_token,
            )

        incr("google_drive.configured")
        return GoogleDriveConfig(
            tenant_id=tenant_id,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def get_config(
        self, tenant_id: str, user_id: str
    ) -> GoogleDriveConfig | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT access_token, refresh_token, folder_id, is_active
                FROM public.google_drive_integrations
                WHERE tenant_id = $1 AND user_id = $2 AND is_active = true
                """,
                tenant_id,
                user_id,
            )

            if not row:
                return None

            return GoogleDriveConfig(
                tenant_id=tenant_id,
                user_id=user_id,
                access_token=row["access_token"],
                refresh_token=row["refresh_token"],
                folder_id=row["folder_id"],
                is_active=row["is_active"],
            )

    async def backup_resume(
        self,
        tenant_id: str,
        user_id: str,
        resume_content: bytes,
        file_name: str = "resume.pdf",
    ) -> SyncResult:
        config = await self.get_config(tenant_id, user_id)
        if not config:
            return SyncResult(success=False, error="Google Drive not configured")

        client = GoogleDriveClient(config.access_token)

        try:
            folder_id = config.folder_id
            if not folder_id:
                folder_id = await client.get_or_create_folder(RESUME_FOLDER_NAME)
                await self._save_folder_id(tenant_id, user_id, folder_id)

            existing = await self._find_existing_resume(client, folder_id, "resume")
            if existing:
                await client.delete_file(existing.file_id)

            file = await client.upload_file(
                file_name,
                resume_content,
                "application/pdf",
                folder_id,
            )

            await self._save_backup_record(
                tenant_id,
                user_id,
                file.file_id,
                file.name,
                len(resume_content),
                "resume",
            )

            incr("google_drive.resume_backed_up")
            return SyncResult(
                success=True,
                file_id=file.file_id,
                bytes_synced=len(resume_content),
            )

        except Exception as e:
            logger.error("Failed to backup resume: %s", e)
            return SyncResult(success=False, error=str(e))

    async def get_resume(self, tenant_id: str, user_id: str) -> bytes | None:
        config = await self.get_config(tenant_id, user_id)
        if not config:
            return None

        file_id = await self._get_backup_file_id(tenant_id, user_id, "resume")
        if not file_id:
            return None

        client = GoogleDriveClient(config.access_token)
        return await client.download_file(file_id)

    async def list_backups(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT file_id, file_name, file_size, backup_type, backed_up_at
                FROM public.google_drive_backups
                WHERE tenant_id = $1 AND user_id = $2
                ORDER BY backed_up_at DESC
                """,
                tenant_id,
                user_id,
            )

            return [dict(r) for r in rows]

    async def disconnect(self, tenant_id: str, user_id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.google_drive_integrations
                SET is_active = false
                WHERE tenant_id = $1 AND user_id = $2
                """,
                tenant_id,
                user_id,
            )

        incr("google_drive.disconnected")

    async def _save_folder_id(
        self,
        tenant_id: str,
        user_id: str,
        folder_id: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.google_drive_integrations
                SET folder_id = $3
                WHERE tenant_id = $1 AND user_id = $2
                """,
                tenant_id,
                user_id,
                folder_id,
            )

    async def _find_existing_resume(
        self,
        client: GoogleDriveClient,
        folder_id: str,
        prefix: str,
    ) -> DriveFile | None:
        files = await client.list_files(folder_id)
        for f in files:
            if f.name.lower().startswith(prefix.lower()):
                return f
        return None

    async def _save_backup_record(
        self,
        tenant_id: str,
        user_id: str,
        file_id: str,
        file_name: str,
        file_size: int,
        backup_type: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.google_drive_backups
                    (tenant_id, user_id, file_id, file_name, file_size, backup_type)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (tenant_id, user_id, backup_type) DO UPDATE SET
                    file_id = $3,
                    file_name = $4,
                    file_size = $5,
                    backed_up_at = now()
                """,
                tenant_id,
                user_id,
                file_id,
                file_name,
                file_size,
                backup_type,
            )

    async def _get_backup_file_id(
        self,
        tenant_id: str,
        user_id: str,
        backup_type: str,
    ) -> str | None:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                """
                SELECT file_id FROM public.google_drive_backups
                WHERE tenant_id = $1 AND user_id = $2 AND backup_type = $3
                """,
                tenant_id,
                user_id,
                backup_type,
            )


async def init_google_drive_tables(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.google_drive_integrations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            folder_id TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(tenant_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS public.google_drive_backups (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            file_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_size BIGINT NOT NULL DEFAULT 0,
            backup_type TEXT NOT NULL,
            backed_up_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(tenant_id, user_id, backup_type)
        );

        CREATE INDEX IF NOT EXISTS idx_google_drive_tenant_user
            ON public.google_drive_integrations(tenant_id, user_id);

        CREATE INDEX IF NOT EXISTS idx_google_drive_backups_user
            ON public.google_drive_backups(user_id);
        """
    )
    logger.info("Google Drive tables initialized")
