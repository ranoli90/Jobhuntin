"""File storage service interface for handling uploads/downloads
Supports: Local filesystem, S3-compatible (AWS S3, Cloudflare R2, Render Disks).
"""

import hashlib
import hmac
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse

import httpx

from shared.logging_config import get_logger

logger = get_logger("sorce.storage")


class StorageService:
    """Abstract base class for file storage services."""

    async def upload_file(
        self, bucket: str, path: str, data: bytes, content_type: str = "application/pdf"
    ) -> str:
        """Upload a file to storage and return its storage path."""
        raise NotImplementedError

    async def generate_signed_url(
        self, storage_path: str, ttl_seconds: int | None = None
    ) -> str:
        """Generate a time-limited signed URL for accessing a stored file."""
        raise NotImplementedError

    async def download_file(self, storage_path: str) -> bytes:
        """Download a file from storage."""
        raise NotImplementedError


class LocalStorageService(StorageService):
    """Basic local filesystem storage implementation for development."""

    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self, bucket: str, path: str, data: bytes, content_type: str = "application/pdf"
    ) -> str:
        """Save file to local filesystem."""
        full_path = self.base_path / bucket / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)
        return f"{bucket}/{path}"

    async def generate_signed_url(
        self, storage_path: str, ttl_seconds: int | None = None
    ) -> str:
        """For local storage, just return a file:// URL."""
        bucket, path = storage_path.split("/", 1)
        full_path = self.base_path / bucket / path
        return f"file://{full_path.absolute()}"

    async def download_file(self, storage_path: str) -> bytes:
        """Read file from local filesystem."""
        bucket, path = storage_path.split("/", 1)
        full_path = self.base_path / bucket / path
        return full_path.read_bytes()


class S3CompatibleStorageService(StorageService):
    """S3-compatible storage implementation for AWS S3, Cloudflare R2, Render Disks, etc.
    Uses boto3-style signing for maximum compatibility.
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region: str = "auto",
        bucket_name: str = "resumes",
        public_url_base: str | None = None,
    ):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.bucket_name = bucket_name
        self.public_url_base = public_url_base or endpoint_url

    def _sign_request(
        self, method: str, path: str, headers: dict, body: bytes = b""
    ) -> str:
        """Sign request using AWS Signature Version 4."""
        service = "s3"
        now = datetime.utcnow()
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        canonical_headers = "".join(
            f"{k.lower()}:{v}\n" for k, v in sorted(headers.items())
        )
        signed_headers = ";".join(k.lower() for k in sorted(headers.keys()))

        payload_hash = hashlib.sha256(body).hexdigest()

        canonical_request = "\n".join(
            [
                method,
                path,
                "",
                canonical_headers,
                signed_headers,
                payload_hash,
            ]
        )

        credential_scope = f"{date_stamp}/{self.region}/{service}/aws4_request"

        string_to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                amz_date,
                credential_scope,
                hashlib.sha256(canonical_request.encode()).hexdigest(),
            ]
        )

        def sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()

        k_date = sign(("AWS4" + self.secret_key).encode(), date_stamp)
        k_region = sign(k_date, self.region)
        k_service = sign(k_region, service)
        k_signing = sign(k_service, "aws4_request")
        signature = hmac.new(
            k_signing, string_to_sign.encode(), hashlib.sha256
        ).hexdigest()

        authorization = (
            f"AWS4-HMAC-SHA256 "
            f"Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        return authorization

    async def upload_file(
        self, bucket: str, path: str, data: bytes, content_type: str = "application/pdf"
    ) -> str:
        """Upload file to S3-compatible storage."""
        object_path = f"/{bucket}/{path}"
        url = f"{self.endpoint_url}{object_path}"

        headers = {
            "Host": urlparse(self.endpoint_url).netloc,
            "Content-Type": content_type,
            "Content-Length": str(len(data)),
            "x-amz-content-sha256": hashlib.sha256(data).hexdigest(),
            "x-amz-date": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
        }

        authorization = self._sign_request("PUT", object_path, headers, data)
        headers["Authorization"] = authorization

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(url, content=data, headers=headers)
            if resp.status_code not in (200, 204):
                logger.error(f"S3 upload failed: {resp.status_code} - {resp.text}")
                raise RuntimeError(f"Failed to upload to storage: {resp.status_code}")

        logger.info(f"Uploaded {len(data)} bytes to {bucket}/{path}")
        return f"{bucket}/{path}"

    async def generate_signed_url(
        self, storage_path: str, ttl_seconds: int | None = None
    ) -> str:
        """Generate a pre-signed URL for object access using AWS Signature V4."""
        ttl = ttl_seconds or 3600
        bucket, path = storage_path.split("/", 1)

        # Use AWS Signature Version 4 (more secure than V2)
        from datetime import datetime

        now = datetime.utcnow()
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        credential_scope = f"{date_stamp}/{self.region}/s3/aws4_request"
        credential = f"{self.access_key}/{credential_scope}"

        # Build query parameters
        query_params = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": credential,
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(ttl),
            "X-Amz-SignedHeaders": "host",
        }

        # Create canonical request
        host = urlparse(self.endpoint_url).netloc
        canonical_headers = f"host:{host}\n"
        canonical_request = (
            f"GET\n/{bucket}/{path}\n"
            + "&".join(
                f"{k}={quote(v, safe='')}" for k, v in sorted(query_params.items())
            )
            + f"\n{canonical_headers}\nhost\nUNSIGNED-PAYLOAD"
        )

        # Create string to sign
        string_to_sign = (
            f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n"
            + hashlib.sha256(canonical_request.encode()).hexdigest()
        )

        # Calculate signature
        def sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()

        k_date = sign(("AWS4" + self.secret_key).encode(), date_stamp)
        k_region = sign(k_date, self.region)
        k_service = sign(k_region, "s3")
        k_signing = sign(k_service, "aws4_request")
        signature = hmac.new(
            k_signing, string_to_sign.encode(), hashlib.sha256
        ).hexdigest()

        # Build final URL
        query_params["X-Amz-Signature"] = signature
        query_string = "&".join(
            f"{k}={quote(v, safe='')}" for k, v in sorted(query_params.items())
        )
        url = f"{self.public_url_base}/{bucket}/{path}?{query_string}"

        return url

    async def download_file(self, storage_path: str) -> bytes:
        """Download file from S3-compatible storage."""
        bucket, path = storage_path.split("/", 1)
        object_path = f"/{bucket}/{path}"
        url = f"{self.endpoint_url}{object_path}"

        headers = {
            "Host": urlparse(self.endpoint_url).netloc,
            "x-amz-content-sha256": "UNSIGNED-PAYLOAD",
            "x-amz-date": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
        }

        authorization = self._sign_request("GET", object_path, headers)
        headers["Authorization"] = authorization

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to download from storage: {resp.status_code}"
                )
            return resp.content


class RenderDiskStorageService(StorageService):
    """Storage service using Render persistent disk
    Files are stored on the disk mounted at /opt/render/project/data/storage.
    """

    def __init__(
        self,
        disk_path: str = "/opt/render/project/data/storage",
        public_url_base: str | None = None,
    ):
        self.disk_path = Path(disk_path)
        self.disk_path.mkdir(parents=True, exist_ok=True)
        self.public_url_base = public_url_base

    async def upload_file(
        self, bucket: str, path: str, data: bytes, content_type: str = "application/pdf"
    ) -> str:
        """Save file to Render persistent disk."""
        full_path = self.disk_path / bucket / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)
        logger.info(f"Saved {len(data)} bytes to {full_path}")
        return f"{bucket}/{path}"

    async def generate_signed_url(
        self, storage_path: str, ttl_seconds: int | None = None
    ) -> str:
        """For Render disk storage, return API URL that serves the file
        Requires serving endpoint to be configured in the API.
        """
        if self.public_url_base:
            return f"{self.public_url_base}/storage/{storage_path}"
        return f"/api/storage/{storage_path}"

    async def download_file(self, storage_path: str) -> bytes:
        """Read file from Render persistent disk."""
        bucket, path = storage_path.split("/", 1)
        full_path = self.disk_path / bucket / path
        return full_path.read_bytes()


def get_storage_service() -> StorageService:
    """Factory function to get the appropriate storage service based on config."""
    from shared.config import get_settings

    s = get_settings()

    if s.storage_type == "s3" and s.s3_endpoint_url:
        return S3CompatibleStorageService(
            endpoint_url=s.s3_endpoint_url,
            access_key=s.s3_access_key or "",
            secret_key=s.s3_secret_key or "",
            region=s.s3_region or "auto",
            bucket_name=s.s3_bucket or "resumes",
            public_url_base=s.s3_public_url,
        )
    elif s.storage_type == "render_disk":
        return RenderDiskStorageService(
            disk_path=s.render_disk_path or "/opt/render/project/data/storage",
            public_url_base=s.app_base_url,
        )
    else:
        return LocalStorageService(base_path=s.local_storage_path or "./storage")
