"""
Resume processing domain logic: PDF upload, text extraction, and LLM parsing.
"""

import os
import tempfile
import time
import uuid

import fitz  # PyMuPDF
from fastapi import HTTPException
from shared.config import get_settings
from shared.logging_config import get_logger
from shared.storage import StorageService

from backend.domain.analytics_events import (
    RESUME_PARSED_FAILED,
    RESUME_PARSED_SUCCESS,
    emit_analytics_event,
)
from backend.domain.models import CanonicalProfile, normalize_profile
from backend.domain.repositories import ProfileRepo
from backend.llm.client import LLMClient, LLMError
from backend.llm.contracts import ResumeParseResponse_V2, build_resume_parse_prompt_v2
from shared.metrics import incr, observe

logger = get_logger("sorce.resume")


async def download_resume_from_storage(
    storage_path: str, storage: StorageService
) -> str:
    """
    Download a resume from storage to a temp file. Returns local file path.
    """
    suffix = ".pdf"
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    try:
        data = await storage.download_file(storage_path)
        with open(tmp_path, "wb") as f:
            f.write(data)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    logger.info(
        "Downloaded resume to %s (%d bytes)", tmp_path, os.path.getsize(tmp_path)
    )
    return tmp_path


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text_parts: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
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
    user_id: str, tenant_id: str, pdf_bytes: bytes, db_pool, storage: StorageService
) -> tuple[str, CanonicalProfile]:
    """
    Orchestrates the full resume upload flow:
    1. Upload to storage
    2. Extract text
    3. Parse with LLM
    4. Normalize
    5. DB Upsert
    """
    storage_path = f"{user_id}/{uuid.uuid4()}.pdf"

    # 1. Upload
    resume_url = await storage.upload_file(
        "resumes", storage_path, pdf_bytes, "application/pdf"
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
