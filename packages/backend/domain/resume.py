"""Resume processing domain logic: PDF, DOCX, OCR upload, text extraction, and LLM parsing."""

import time
import uuid

import httpx
from fastapi import HTTPException

from packages.backend.domain.analytics_events import (
    RESUME_PARSED_FAILED,
    RESUME_PARSED_SUCCESS,
    emit_analytics_event,
)
from packages.backend.domain.models import normalize_profile
from packages.backend.domain.repositories import ProfileRepo
from packages.backend.llm.client import LLMClient, LLMError
from packages.backend.llm.contracts import (
    ResumeParseResponse_V2,
    build_resume_parse_prompt_v2,
)
from packages.backend.domain.document_processor import create_document_processor
from packages.backend.domain.skills_taxonomy import (
    get_skills_taxonomy,
    validate_user_skills,
)
from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr, observe

logger = get_logger("sorce.resume")


def _basic_resume_parse(resume_text: str) -> dict | None:
    """Enhanced resume parsing fallback - extracts structured info from resume text.

    This is a fallback when LLM parsing fails. It extracts basic information
    using pattern matching and heuristics for better structured output.
    """
    if not resume_text or not resume_text.strip():
        return None

    import re

    # Initialize structured data
    parsed_data = {
        "raw_text": resume_text[:5000],  # Limit text length
        "contact": {},
        "experience": [],
        "education": [],
        "skills": [],
        "summary": "",
        "headline": "",
    }

    lines = resume_text.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]

    # Extract contact information
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    phone_pattern = r"(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"
    linkedin_pattern = r"linkedin\.com/in/[\w-]+"

    emails = re.findall(email_pattern, resume_text)
    phones = re.findall(phone_pattern, resume_text)
    linkedins = re.findall(linkedin_pattern, resume_text, re.IGNORECASE)

    if emails:
        parsed_data["contact"]["email"] = emails[0]
    if phones:
        parsed_data["contact"]["phone"] = phones[0]
    if linkedins:
        parsed_data["contact"]["linkedin_url"] = f"https://{linkedins[0]}"

    # Extract name (heuristic - first line before contact info)
    name = ""
    for i, line in enumerate(cleaned_lines[:5]):  # Check first 5 lines
        if len(line.split()) <= 4 and not any(char.isdigit() for char in line):
            # Likely a name line (short, no numbers)
            if not re.search(email_pattern, line) and not re.search(
                phone_pattern, line
            ):
                name = line
                break

    if name:
        parts = name.split()
        if len(parts) >= 2:
            parsed_data["contact"]["first_name"] = parts[0]
            parsed_data["contact"]["last_name"] = " ".join(parts[1:])
        else:
            parsed_data["contact"]["full_name"] = name

    # Extract skills using common skill keywords and taxonomy
    from packages.backend.domain.skills_taxonomy import get_skills_taxonomy

    taxonomy = get_skills_taxonomy()

    # Combine taxonomy skills with common keywords for broader coverage
    taxonomy_skills = set()
    for skill_name, skill_info in taxonomy._skills_db.items():
        taxonomy_skills.add(skill_name.lower())
        taxonomy_skills.update(skill_info.aliases)

    # Additional common skill keywords not in taxonomy
    additional_skills = [
        "Excel",
        "PowerPoint",
        "Word",
        "Office",
        "Microsoft Office",
        "Agile",
        "Scrum",
        "Waterfall",
        "Lean",
        "Six Sigma",
        "Customer Service",
        "Client Relations",
        "Stakeholder Management",
        "Budget Management",
        "Financial Analysis",
        "Risk Management",
        "Quality Assurance",
        "Quality Control",
        "Process Improvement",
        "Training",
        "Mentoring",
        "Coaching",
        "Public Speaking",
        "Negotiation",
        "Conflict Resolution",
        "Decision Making",
        "Research",
        "Analysis",
        "Reporting",
        "Documentation",
        "Compliance",
        "Regulatory",
        "Audit",
        "Governance",
    ]

    all_skill_keywords = taxonomy_skills.union(
        set(skill.lower() for skill in additional_skills)
    )

    found_skills = []
    for skill in all_skill_keywords:
        if skill in resume_text.lower():
            # Normalize to canonical skill name if possible
            canonical_skill = taxonomy.normalize_skill(skill)
            if canonical_skill and canonical_skill not in found_skills:
                found_skills.append(canonical_skill)
            elif not canonical_skill and skill not in found_skills:
                # Use the raw skill if not found in taxonomy
                found_skills.append(skill.title())

    # Validate skills through taxonomy
    valid_skills, invalid_skills, skills_analysis = validate_user_skills(found_skills)

    parsed_data["skills"] = valid_skills
    parsed_data["skills_analysis"] = {
        "total_skills_extracted": len(found_skills),
        "valid_skills_count": len(valid_skills),
        "invalid_skills_count": len(invalid_skills),
        "skill_score": skills_analysis.get("skill_score", 0.0),
        "category_distribution": skills_analysis.get("category_distribution", {}),
        "top_skills": skills_analysis.get("top_skills", []),
        "invalid_skills": invalid_skills[:10],
        "parsing_method": "structured_fallback",
    }

    # Extract experience sections
    experience_section = []
    current_exp = None

    for line in cleaned_lines:
        # Look for experience indicators
        exp_indicators = [
            "experience",
            "work history",
            "employment",
            "professional experience",
        ]
        if any(indicator in line.lower() for indicator in exp_indicators):
            continue

        # Look for dates (YYYY format or month YYYY)
        date_pattern = r"\b(19|20)\d{2}\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(19|20)\d{2}\b"
        dates = re.findall(date_pattern, line, re.IGNORECASE)

        if dates and len(line.split()) > 3:  # Likely an experience entry
            if current_exp:
                experience_section.append(current_exp)
            current_exp = {
                "title": "",
                "company": "",
                "duration": line.strip(),
                "description": "",
            }
        elif current_exp and not current_exp["title"]:
            # First non-date line after dates is likely title/company
            parts = line.split("|")  # Common separator
            if len(parts) >= 2:
                current_exp["title"] = parts[0].strip()
                current_exp["company"] = parts[1].strip()
            else:
                current_exp["title"] = line.strip()
        elif current_exp and current_exp["title"]:
            # Description lines
            current_exp["description"] += line + " "

    if current_exp:
        experience_section.append(current_exp)

    parsed_data["experience"] = experience_section[:5]  # Limit to 5 most recent

    # Extract education
    education_keywords = [
        "university",
        "college",
        "school",
        "bachelor",
        "master",
        "phd",
        "degree",
    ]
    education_section = []

    for i, line in enumerate(cleaned_lines):
        if any(keyword in line.lower() for keyword in education_keywords):
            # Look for degree patterns
            degree_pattern = (
                r"(Bachelor|Master|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.|B\.Sc\.|M\.Sc\.)"
            )
            degree_match = re.search(degree_pattern, line, re.IGNORECASE)

            if degree_match:
                education_section.append(
                    {
                        "institution": line.strip(),
                        "degree": degree_match.group(1),
                        "year": "",
                    }
                )

    parsed_data["education"] = education_section[:3]  # Limit to 3 most recent

    # Extract summary/headline (first substantial text block)
    summary_lines = []
    for line in cleaned_lines[:10]:  # Check first 10 lines
        if len(line) > 20 and not any(char.isdigit() for char in line):
            if not re.search(email_pattern, line) and not re.search(
                phone_pattern, line
            ):
                summary_lines.append(line)
                if len(summary_lines) >= 3:  # Take up to 3 lines for summary
                    break

    if summary_lines:
        parsed_data["summary"] = " ".join(summary_lines)
        parsed_data["headline"] = summary_lines[0]

    # Add confidence score based on extraction quality
    confidence_score = 0.0
    if parsed_data["contact"].get("email"):
        confidence_score += 0.2
    if parsed_data["contact"].get("phone"):
        confidence_score += 0.1
    if parsed_data["skills"]:
        confidence_score += 0.2
    if parsed_data["experience"]:
        confidence_score += 0.3
    if parsed_data["summary"]:
        confidence_score += 0.2

    parsed_data["parsing_confidence"] = min(confidence_score, 1.0)
    parsed_data["parsing_method"] = "structured_fallback"

    return parsed_data


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
    """Extract text from PDF bytes. Legacy function - use DocumentProcessor instead."""
    processor = create_document_processor()
    return processor._extract_text_from_pdf(pdf_bytes)


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
    file_bytes: bytes,
    filename: str,
    content_type: str,
    db_pool,
    storage=None,  # StorageService instance - uses Render Disk when configured
) -> tuple[str, dict]:
    """Process resume upload with support for PDF, DOCX, and OCR.

    Args:
        user_id: User ID
        tenant_id: Tenant ID
        file_bytes: File content as bytes
        filename: Original filename
        content_type: MIME content type
        db_pool: Database connection pool
        storage: StorageService instance

    Returns:
        Tuple of (resume_url, canonical_profile_dict)

    Raises:
        HTTPException: If file processing fails
    """
    # Initialize document processor
    processor = create_document_processor()

    # Validate file type
    if not processor.is_supported_file(filename, content_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Supported formats: PDF, DOCX, and images.",
        )

    # Extract metadata
    metadata = await processor.extract_metadata(file_bytes, filename, content_type)
    logger.info(
        f"Processing {metadata['file_type']} file: {filename} ({metadata['file_size']} bytes)"
    )

    # Generate storage path with appropriate extension
    file_ext = {
        "pdf": "pdf",
        "docx": "docx",
        "image": "jpg",  # Default image extension
    }.get(metadata["file_type"], "pdf")

    storage_path = f"{user_id}/{uuid.uuid4()}.{file_ext}"
    bucket = "resumes"

    if storage is None:
        # Fallback: import and create default storage service
        from shared.storage import get_storage_service

        storage = get_storage_service()

    # Upload file to storage
    resume_url = await storage.upload_file(bucket, storage_path, file_bytes)

    # Extract text using enhanced processor
    try:
        resume_text = await processor.extract_text_from_document(
            file_bytes, filename, content_type, use_ocr=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document text extraction failed: {e}")
        raise HTTPException(
            status_code=422,
            detail="Failed to extract text from document. Please try a different file format.",
        )

    if not resume_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from document. Please ensure the document contains readable text.",
        )

    # LLM Parse
    t0 = time.monotonic()
    try:
        raw_profile = await parse_resume_to_profile(resume_text)
        parse_method = "llm"
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
            properties={"error": str(exc)[:200], "file_type": metadata["file_type"]},
        )

        # Try fallback parsing before failing completely
        try:
            logger.info(
                f"[RESUME] LLM parsing failed for user {user_id}, attempting basic parsing"
            )
            fallback_profile = _basic_resume_parse(resume_text)
            if fallback_profile:
                logger.info(f"[RESUME] Basic parsing succeeded for user {user_id}")
                observe(
                    "api.llm_latency_seconds",
                    time.monotonic() - t0,
                    {"endpoint": "resume_parse_fallback"},
                )
                incr("api.resume_parse.fallback_success")
                raw_profile = fallback_profile
                parse_method = "fallback"
            else:
                logger.error(
                    f"[RESUME] Both LLM and basic parsing failed for user {user_id}"
                )
                observe(
                    "api.llm_latency_seconds",
                    time.monotonic() - t0,
                    {"endpoint": "resume_parse_fallback_failed"},
                )
                incr("api.resume_parse.fallback_failed")
                raise HTTPException(
                    status_code=502,
                    detail="Resume parsing failed. Please try a different resume format.",
                )
        except Exception as fallback_exc:
            logger.error(
                f"[RESUME] Fallback parsing also failed for user {user_id}: {fallback_exc}"
            )
            raise HTTPException(
                status_code=502,
                detail="Resume parsing failed. Please try a different resume format.",
            )
        except Exception as exc:
            logger.error(f"[RESUME] Unexpected error during parsing fallback: {exc}")
            raise HTTPException(
                status_code=502,
                detail="Resume parsing failed. Please try a different resume format.",
            ) from exc

    observe(
        "api.llm_latency_seconds", time.monotonic() - t0, {"endpoint": "resume_parse"}
    )

    # Normalize profile
    canonical = normalize_profile(raw_profile)

    # Validate and normalize skills using taxonomy
    taxonomy = get_skills_taxonomy()
    skills_data = canonical.get("skills", [])

    if isinstance(skills_data, list):
        valid_skills, invalid_skills, skills_analysis = validate_user_skills(
            skills_data
        )

        # Update canonical profile with validated skills
        canonical["skills"] = valid_skills

        # Add skills analysis metadata
        if "skills_analysis" not in canonical:
            canonical["skills_analysis"] = {}

        canonical["skills_analysis"].update(
            {
                "total_skills_extracted": skills_analysis["total_skills"],
                "valid_skills_count": skills_analysis["valid_skills"],
                "invalid_skills_count": skills_analysis["invalid_skills"],
                "skill_score": skills_analysis["skill_score"],
                "category_distribution": skills_analysis["category_distribution"],
                "top_skills": skills_analysis["top_skills"],
                "invalid_skills": invalid_skills[
                    :10
                ],  # Store first 10 invalid skills for analysis
                "validation_timestamp": time.time(),
            }
        )

        logger.info(
            f"[SKILLS] Validated {skills_analysis['valid_skills']}/{skills_analysis['total_skills']} skills "
            f"with score {skills_analysis['skill_score']:.2f} for user {user_id}"
        )

        # Track skills validation metrics
        incr(
            "resume.skills.validated",
            {
                "total_skills": skills_analysis["total_skills"],
                "valid_skills": skills_analysis["valid_skills"],
                "invalid_skills": skills_analysis["invalid_skills"],
            },
        )

        observe(
            "resume.skills.score",
            skills_analysis["skill_score"],
            {
                "parsing_method": parse_method,
                "file_type": metadata.get("file_type", "unknown"),
            },
        )

    # Add file metadata to canonical profile
    canonical["file_metadata"] = {
        "filename": filename,
        "file_type": metadata["file_type"],
        "file_size": metadata["file_size"],
        "content_type": content_type,
        "parse_method": parse_method,
        "ocr_used": metadata.get("is_scanned", False),
        "page_count": metadata.get("page_count", 1),
        "has_images": metadata.get("has_images", False),
        "is_encrypted": metadata.get("is_encrypted", False),
    }

    # Upsert to database
    async with db_pool.acquire() as conn:
        await ProfileRepo.upsert(
            conn, user_id, canonical, resume_url, tenant_id=tenant_id
        )

    await emit_analytics_event(
        db_pool,
        RESUME_PARSED_SUCCESS,
        tenant_id=tenant_id,
        user_id=user_id,
        properties={
            "resume_url": resume_url,
            "file_type": metadata["file_type"],
            "parse_method": parse_method,
            "ocr_used": metadata.get("is_scanned", False),
        },
    )

    return resume_url, canonical
