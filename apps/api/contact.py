"""Public contact form endpoint for marketing site.

No authentication required. Rate-limited by IP.
"""

from __future__ import annotations

from api.dependencies import get_pool
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from shared.logging_config import get_logger
from shared.metrics import get_rate_limiter, incr
from shared.middleware import get_client_ip

logger = get_logger("sorce.contact")
router = APIRouter(prefix="/contact", tags=["contact"])


class ContactRequest(BaseModel):
    """Contact form submission."""

    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=1, max_length=255)
    company: str = Field(default="", max_length=200)
    type: str = Field(
        default="general",
        pattern="^(general|support|sales|partnership)$",
    )
    message: str = Field(..., min_length=1, max_length=5000)

    @field_validator("name", "email", "company", "message")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Sanitize user input to prevent XSS and injection."""
        from packages.backend.domain.sanitization import sanitize_text_input

        if not v:
            return v
        return sanitize_text_input(v, max_length=5000)


@router.post("")
async def submit_contact(
    request: Request,
    body: ContactRequest,
    db=Depends(get_pool),
) -> dict:
    """Submit contact form. Public endpoint; no auth required."""
    client_ip = get_client_ip(request)
    limiter = get_rate_limiter(
        f"contact:{client_ip}",
        max_calls=5,
        window_seconds=300,
    )
    if not await limiter.acquire():
        retry_after = max(1, int(limiter.next_available_in()))
        incr("api.contact.rate_limited")
        raise HTTPException(
            status_code=429,
            detail="Too many contact form submissions. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    incr("api.contact.submissions", tags={"type": body.type})
    try:
        async with db.acquire() as conn:
            await conn.execute(
                """INSERT INTO public.contact_messages
                   (name, email, company, inquiry_type, message)
                   VALUES ($1, $2, $3, $4, $5)""",
                body.name.strip(),
                body.email.strip(),
                (body.company or "").strip() or None,
                body.type,
                body.message.strip(),
            )
        logger.info(
            "Contact form submitted",
            extra={
                "email": body.email[:3] + "***",
                "type": body.type,
            },
        )
        return {"status": "ok", "message": "Thank you for your message. We'll get back to you within 24 hours."}
    except Exception as e:
        logger.exception("Contact form submission failed")
        incr("api.contact.errors")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit. Please try again or email support@jobhuntin.com.",
        ) from e
