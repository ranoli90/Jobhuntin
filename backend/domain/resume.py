"""
Resume processing domain logic: PDF upload, text extraction, and LLM parsing.
"""
import uuid
import time
from typing import Any

from fastapi import HTTPException
import httpx
import fitz  # PyMuPDF

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import observe, incr
from backend.domain.models import normalize_profile, CanonicalProfile
from backend.domain.repositories import ProfileRepo
from backend.llm.client import LLMClient, LLMError
from backend.llm.contracts import ResumeParseResponse_V1, build_resume_parse_prompt
from backend.domain.analytics_events import (
    RESUME_PARSED_SUCCESS,
    RESUME_PARSED_FAILED,
    emit_analytics_event,
)

logger = get_logger("sorce.resume")

async def upload_to_supabase_storage(
    bucket: str,
    path: str,
    data: bytes,
    content_type: str = "application/pdf",
) -> str:
    s = get_settings()
    url = f"{s.supabase_url}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {s.supabase_service_key}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, content=data, headers=headers)
        resp.raise_for_status()

    return f"{s.supabase_url}/storage/v1/object/public/{bucket}/{path}"


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text_parts: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


async def parse_resume_to_profile(resume_text: str) -> dict:
    """Use the LLM client with the versioned resume parse contract."""
    s = get_settings()
    llm_client = LLMClient(s)
    prompt = build_resume_parse_prompt(resume_text)
    result = await llm_client.call(
        prompt=prompt,
        response_format=ResumeParseResponse_V1,
    )
    return result.model_dump()

async def process_resume_upload(
    user_id: str,
    tenant_id: str,
    pdf_bytes: bytes,
    db_pool,
) -> tuple[str, CanonicalProfile]:
    """
    Orchestrates the full resume upload flow:
    1. Upload to storage
    2. Extract text
    3. Parse with LLM
    4. Normalize
    5. DB Upsert
    """
    s = get_settings()
    storage_path = f"{user_id}/{uuid.uuid4()}.pdf"
    
    # 1. Upload
    resume_url = await upload_to_supabase_storage(
        s.supabase_storage_bucket, storage_path, pdf_bytes
    )

    # 2. Extract
    resume_text = extract_text_from_pdf(pdf_bytes)
    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from PDF")

    # 3. LLM Parse
    t0 = time.monotonic()
    try:
        raw_profile = await parse_resume_to_profile(resume_text)
    except LLMError as exc:
        observe("api.llm_latency_seconds", time.monotonic() - t0, {"endpoint": "resume_parse"})
        incr("api.resume_parse.llm_error")
        await emit_analytics_event(
            db_pool, RESUME_PARSED_FAILED,
            tenant_id=tenant_id, user_id=user_id,
            properties={"error": str(exc)[:200]},
        )
        raise HTTPException(status_code=502, detail=f"Resume parsing failed: {exc}")
    
    observe("api.llm_latency_seconds", time.monotonic() - t0, {"endpoint": "resume_parse"})

    # 4. Normalize
    canonical = normalize_profile(raw_profile)

    # 5. Upsert
    async with db_pool.acquire() as conn:
        await ProfileRepo.upsert(conn, user_id, canonical.model_dump(), resume_url, tenant_id=tenant_id)

    await emit_analytics_event(
        db_pool, RESUME_PARSED_SUCCESS,
        tenant_id=tenant_id, user_id=user_id,
        properties={"resume_url": resume_url},
    )

    return resume_url, canonical
