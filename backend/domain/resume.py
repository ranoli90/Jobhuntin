"""Resume processing domain logic: PDF upload, text extraction, and LLM parsing."""

import time
import uuid

import fitz  # PyMuPDF
import httpx
from fastapi import HTTPException
from shared.config import get_settings
from shared.logging_config import get_logger

from packages.backend.domain.analytics_events import (
    RESUME_PARSED_FAILED,
    RESUME_PARSED_SUCCESS,
    emit_analytics_event,
)
from packages.backend.domain.models import CanonicalProfile, normalize_profile
from packages.backend.domain.repositories import ProfileRepo
from backend.llm.client import LLMClient, LLMError
from backend.llm.contracts import ResumeParseResponse_V2, build_resume_parse_prompt_v2
from shared.metrics import incr, observe

logger = get_logger("sorce.resume")


async def upload_to_supabase_storage(
    bucket: str,
    path: str,
    data: bytes,
    content_type: str = "application/pdf",
) -> str:
    s = get_settings()

    if not s.supabase_url or "supabase" not in s.supabase_url:  # basic check
        # Fallback: Validation/Storage disabled
        if not s.supabase_url or not s.supabase_service_key:
            logger.warning(
                "Supabase storage not configured; skipping upload for %s", path
            )
            return f"local-skipped/{bucket}/{path}"

    url = f"{s.supabase_url}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {s.supabase_service_key}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, content=data, headers=headers)
        resp.raise_for_status()

    # Return the internal storage path (not a public URL) — use generate_signed_url() for access
    return f"{bucket}/{path}"


async def generate_signed_url(storage_path: str, ttl_seconds: int | None = None) -> str:
    """Generate a time-limited signed URL for accessing a file in Supabase Storage.

    Args:
        storage_path: The internal storage path returned by upload_to_supabase_storage
                      (format: "bucket/path/to/file.pdf").
        ttl_seconds: Override for URL validity duration. Defaults to config value.

    Returns:
        A signed URL that expires after ttl_seconds.

    """
    s = get_settings()

    if "local-skipped" in storage_path:
        return ""  # No URL available

    ttl = ttl_seconds or s.resume_signed_url_ttl_seconds

    # Split bucket from path
    parts = storage_path.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid storage path format: {storage_path}")
    bucket, file_path = parts

    url = f"{s.supabase_url}/storage/v1/object/sign/{bucket}/{file_path}"
    headers = {
        "Authorization": f"Bearer {s.supabase_service_key}",
        "Content-Type": "application/json",
    }
    payload = {"expiresIn": ttl}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()

    data = resp.json()
    signed_path = data.get("signedURL", "")
    if not signed_path:
        raise RuntimeError(f"Supabase signed URL response missing signedURL: {data}")

    return f"{s.supabase_url}/storage/v1{signed_path}"


async def download_from_supabase_storage(resume_url: str) -> str:
    """Download a file from Supabase Storage to a temp path. Returns local file path.

    Accepts either a full URL or an internal storage path (bucket/path).
    """
    import os
    import tempfile

    s = get_settings()
    headers = {"Authorization": f"Bearer {s.supabase_service_key}"}

    # If it's an internal storage path (no scheme), build the authenticated URL
    if not resume_url.startswith("http"):
        parts = resume_url.split("/", 1)
        if len(parts) == 2:
            resume_url = f"{s.supabase_url}/storage/v1/object/authenticated/{parts[0]}/{parts[1]}"

    suffix = ".pdf"
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(resume_url, headers=headers, follow_redirects=True)
            resp.raise_for_status()
            with open(tmp_path, "wb") as f:
                f.write(resp.content)
    except Exception:
        # Clean up on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    logger.info(
        "Downloaded resume to %s (%d bytes)", tmp_path, os.path.getsize(tmp_path)
    )
    return tmp_path


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes. Handles corruption and invalid file formats."""
    text_parts: list[str] = []
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            if doc.page_count == 0:
                raise HTTPException(
                    status_code=422, detail="The PDF file appears to be empty."
                )
            for page in doc:
                text_parts.append(page.get_text())
    except fitz.FileDataError:
        logger.error("Failed to open PDF: Invalid or corrupted file")
        raise HTTPException(
            status_code=422,
            detail="Invalid PDF format or corrupted file. Please ensure you're uploading a valid PDF.",
        )
    except Exception as e:
        logger.error(f"Unexpected error during PDF extraction: {e}")
        raise HTTPException(
            status_code=422,
            detail="Failed to process PDF. Please try a different version of your resume.",
        )

    return "\n".join(text_parts)


async def parse_resume_to_profile(resume_text: str) -> dict:
    """Use the LLM client with the V2 resume parse contract for rich skills."""
    s = get_settings()
    llm_client = LLMClient(s)
    prompt = build_resume_parse_prompt_v2(resume_text)
    result = await llm_client.call(
        prompt=prompt,
        response_format=ResumeParseResponse_V2,
    )
    return result.model_dump()


async def process_resume_upload(
    user_id: str,
    tenant_id: str,
    pdf_bytes: bytes,
    db_pool,
    storage=None,  # StorageService instance - uses Render Disk when configured
) -> tuple[str, CanonicalProfile]:
    """Orchestrates the full resume upload flow:
    1. Upload to storage
    2. Extract text
    3. Parse with LLM
    4. Normalize
    5. DB Upsert.
    """
    # 1. Upload to storage (supports Render Disk, S3, or local)

    get_settings()
    storage_path = f"{user_id}/{uuid.uuid4()}.pdf"
    bucket = "resumes"  # bucket name for the storage service

    if storage is None:
        # Fallback: import and create default storage service
        from shared.storage import get_storage_service

        storage = get_storage_service()

    resume_url = await storage.upload_file(bucket, storage_path, pdf_bytes)

    # 2. Extract
    resume_text = extract_text_from_pdf(pdf_bytes)
    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from PDF")

    # 3. LLM Parse
    t0 = time.monotonic()
    try:
        raw_profile = await parse_resume_to_profile(resume_text)
    except LLMError as exc:
        observe(
            "api.llm_latency_seconds",
            time.monotonic() - t0,
            {"endpoint": "resume_parse"},
        )
        incr("api.resume_parse.llm_error")
        await emit_analytics_event(
            db_pool,
            RESUME_PARSED_FAILED,
            tenant_id=tenant_id,
            user_id=user_id,
            properties={"error": str(exc)[:200]},
        )
        raise HTTPException(
            status_code=502, detail=f"Resume parsing failed: {exc}"
        ) from exc

    observe(
        "api.llm_latency_seconds", time.monotonic() - t0, {"endpoint": "resume_parse"}
    )

    # 4. Normalize
    canonical = normalize_profile(raw_profile)

    # 5. Upsert
    async with db_pool.acquire() as conn:
        await ProfileRepo.upsert(
            conn, user_id, canonical.model_dump(), resume_url, tenant_id=tenant_id
        )

    await emit_analytics_event(
        db_pool,
        RESUME_PARSED_SUCCESS,
        tenant_id=tenant_id,
        user_id=user_id,
        properties={"resume_url": resume_url},
    )

    return resume_url, canonical
