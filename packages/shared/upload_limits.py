"""
File upload limits configuration per tenant tier.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import BinaryIO


class FileType(Enum):
    """Allowed file types for upload."""
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    PROFILE_IMAGE = "profile_image"
    DOCUMENT = "document"


@dataclass
class UploadLimits:
    """Upload limits for a specific tier."""
    max_file_size_mb: int
    max_files_per_day: int
    allowed_extensions: list[str]
    max_total_storage_mb: int


# Tier-based upload limits
TIER_LIMITS: dict[str, dict[FileType, UploadLimits]] = {
    "free": {
        FileType.RESUME: UploadLimits(
            max_file_size_mb=5,
            max_files_per_day=3,
            allowed_extensions=["pdf", "doc", "docx"],
            max_total_storage_mb=50,
        ),
        FileType.COVER_LETTER: UploadLimits(
            max_file_size_mb=2,
            max_files_per_day=5,
            allowed_extensions=["pdf", "doc", "docx", "txt"],
            max_total_storage_mb=20,
        ),
        FileType.PROFILE_IMAGE: UploadLimits(
            max_file_size_mb=2,
            max_files_per_day=1,
            allowed_extensions=["jpg", "jpeg", "png", "webp"],
            max_total_storage_mb=10,
        ),
        FileType.DOCUMENT: UploadLimits(
            max_file_size_mb=2,
            max_files_per_day=3,
            allowed_extensions=["pdf"],
            max_total_storage_mb=20,
        ),
    },
    "pro": {
        FileType.RESUME: UploadLimits(
            max_file_size_mb=10,
            max_files_per_day=20,
            allowed_extensions=["pdf", "doc", "docx", "txt"],
            max_total_storage_mb=500,
        ),
        FileType.COVER_LETTER: UploadLimits(
            max_file_size_mb=5,
            max_files_per_day=30,
            allowed_extensions=["pdf", "doc", "docx", "txt"],
            max_total_storage_mb=200,
        ),
        FileType.PROFILE_IMAGE: UploadLimits(
            max_file_size_mb=5,
            max_files_per_day=5,
            allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"],
            max_total_storage_mb=50,
        ),
        FileType.DOCUMENT: UploadLimits(
            max_file_size_mb=10,
            max_files_per_day=20,
            allowed_extensions=["pdf", "doc", "docx", "xls", "xlsx"],
            max_total_storage_mb=500,
        ),
    },
    "enterprise": {
        FileType.RESUME: UploadLimits(
            max_file_size_mb=25,
            max_files_per_day=-1,  # Unlimited
            allowed_extensions=["pdf", "doc", "docx", "txt", "rtf"],
            max_total_storage_mb=5000,
        ),
        FileType.COVER_LETTER: UploadLimits(
            max_file_size_mb=10,
            max_files_per_day=-1,
            allowed_extensions=["pdf", "doc", "docx", "txt", "rtf"],
            max_total_storage_mb=2000,
        ),
        FileType.PROFILE_IMAGE: UploadLimits(
            max_file_size_mb=10,
            max_files_per_day=-1,
            allowed_extensions=["jpg", "jpeg", "png", "webp", "gif", "svg"],
            max_total_storage_mb=500,
        ),
        FileType.DOCUMENT: UploadLimits(
            max_file_size_mb=50,
            max_files_per_day=-1,
            allowed_extensions=["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"],
            max_total_storage_mb=10000,
        ),
    },
}


def get_limits(tier: str, file_type: FileType) -> UploadLimits:
    """Get upload limits for a tier and file type."""
    tier_limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    return tier_limits.get(file_type, TIER_LIMITS["free"][FileType.DOCUMENT])


def validate_upload(
    file: BinaryIO,
    filename: str,
    file_type: FileType,
    tier: str,
    current_storage_mb: float = 0,
    uploads_today: int = 0,
) -> tuple[bool, str]:
    """
    Validate a file upload against tier limits.
    
    Returns:
        tuple of (is_valid, error_message)
    """
    limits = get_limits(tier, file_type)
    
    # Check extension
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in limits.allowed_extensions:
        return (
            False,
            f"File type .{extension} not allowed. Allowed: {', '.join(limits.allowed_extensions)}"
        )
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size_bytes = file.tell()
    file.seek(0)  # Reset to beginning
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if file_size_mb > limits.max_file_size_mb:
        return (
            False,
            f"File size {file_size_mb:.1f}MB exceeds limit of {limits.max_file_size_mb}MB"
        )
    
    # Check daily upload limit
    if limits.max_files_per_day > 0 and uploads_today >= limits.max_files_per_day:
        return (
            False,
            f"Daily upload limit of {limits.max_files_per_day} files reached"
        )
    
    # Check total storage
    new_total = current_storage_mb + file_size_mb
    if new_total > limits.max_total_storage_mb:
        remaining = limits.max_total_storage_mb - current_storage_mb
        return (
            False,
            f"Storage limit exceeded. Remaining: {remaining:.1f}MB, File: {file_size_mb:.1f}MB"
        )
    
    return True, ""


def get_content_type(filename: str) -> str:
    """Get MIME content type from filename."""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    
    content_types = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "txt": "text/plain",
        "rtf": "application/rtf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
    }
    
    return content_types.get(extension, "application/octet-stream")


async def scan_file_for_malware(file: BinaryIO) -> tuple[bool, str]:
    """
    Scan uploaded file for malware.
    
    This is a placeholder - integrate with ClamAV or similar.
    """
    # TODO: Integrate with actual malware scanner
    # For now, just check for suspicious patterns
    
    file.seek(0)
    header = file.read(1024)
    file.seek(0)
    
    # Check for executable signatures
    suspicious_signatures = [
        b"MZ",           # Windows executable
        b"\x7fELF",      # Linux executable
        b"\xca\xfe\xba\xbe",  # Java class
        b"PK\x03\x04",   # ZIP (could be malicious)
    ]
    
    for sig in suspicious_signatures:
        if header.startswith(sig):
            # Allow ZIP for resume bundles, block executables
            if sig == b"PK\x03\x04":
                continue
            return False, "File type not allowed - potential security risk"
    
    return True, ""
