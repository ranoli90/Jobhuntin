"""
Phase 12.1 Agent Improvements - Enhanced button detection, OAuth/SSO handling, document types, concurrent usage
tracking, DLQ inspection, screenshot capture.

This module provides comprehensive agent improvements for better form filling, error handling, and monitoring.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from shared.logging_config import get_logger

logger = get_logger("sorce.agent_improvements")


class ButtonType(str, Enum):
    """Types of buttons the agent can detect and interact with."""

    SUBMIT = "submit"
    APPLY = "apply"
    NEXT = "next"
    CONTINUE = "continue"
    SAVE = "save"
    CANCEL = "cancel"
    BACK = "back"
    SKIP = "skip"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    LOGIN = "login"
    SIGN_IN = "sign_in"
    REGISTER = "register"
    SIGN_UP = "sign_up"
    ACCEPT = "accept"
    DECLINE = "decline"
    AGREE = "agree"
    DISAGREE = "disagree"
    CONFIRM = "confirm"
    YES = "yes"
    NO = "no"
    CUSTOM = "custom"


class DocumentType(str, Enum):
    """Supported document types for upload and processing."""

    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    RTF = "rtf"
    ODT = "odt"
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    TIFF = "tiff"
    BMP = "bmp"
    GIF = "gif"


class ButtonDetection(BaseModel):
    """Enhanced button detection result."""

    button_id: str
    button_type: ButtonType
    text: str
    selector: str
    xpath: str
    coordinates: Dict[str, float]  # x, y, width, height
    is_visible: bool
    is_enabled: bool
    confidence_score: float
    attributes: Dict[str, Any] = {}


class FormFieldDetection(BaseModel):
    """Enhanced form field detection."""

    field_id: str
    field_type: str  # text, email, password, file, select, checkbox, radio, textarea
    label: str
    selector: str
    xpath: str
    is_required: bool
    is_visible: bool
    is_enabled: bool
    validation_rules: List[str] = []
    placeholder: Optional[str] = None
    max_length: Optional[int] = None
    accepted_file_types: Optional[List[DocumentType]] = None


class ScreenshotCapture(BaseModel):
    """Screenshot capture metadata."""

    capture_id: str
    application_id: str
    step_number: int
    step_description: str
    timestamp: datetime
    screenshot_path: str
    thumbnail_path: Optional[str]
    viewport_size: Dict[str, int]
    full_page: bool
    elements_highlighted: List[str] = []
    error_detected: bool = False
    error_message: Optional[str] = None


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""

    GOOGLE = "google"
    LINKEDIN = "linkedin"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    SALESFORCE = "salesforce"
    WORKDAY = "workday"
    ULTIMATEPROCURER = "ultimateprocurer"
    CUSTOM = "custom"


class OAuthCredentials(BaseModel):
    """OAuth credentials for SSO integration."""

    provider: OAuthProvider
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str]
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    tenant_id: Optional[str] = None


class ConcurrentUsageSession(BaseModel):
    """Concurrent usage tracking session."""

    session_id: str
    user_id: str
    tenant_id: str
    application_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # active, completed, failed, cancelled
    steps_completed: int = 0
    total_steps: int = 0
    error_count: int = 0
    screenshots_captured: int = 0
    buttons_detected: int = 0
    forms_processed: int = 0


class DLQItem(BaseModel):
    """Dead Letter Queue item for failed applications."""

    id: str
    application_id: str
    tenant_id: str
    failure_reason: str
    error_details: Dict[str, Any]
    attempt_count: int
    max_retries: int
    next_retry_at: Optional[datetime]
    payload: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    priority: int = 0  # Higher priority = retry sooner


class RetryResult(BaseModel):
    """Result of retrying a DLQ item."""

    success: bool
    message: str
    new_attempt_count: int
    next_retry_at: Optional[datetime] = None
    error_details: Optional[Dict[str, Any]] = None


class AgentImprovementsManager:
    """Manages all Phase 12.1 agent improvements."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._oauth_handlers = {}
        self._concurrent_tracker = None
        self._dlq_manager = None

    async def detect_buttons(
        self,
        page_source: str,
        screenshot_data: Optional[bytes] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ButtonDetection]:
        """Enhanced button detection with multiple strategies."""
        logger.info("Starting enhanced button detection")

        buttons = []

        # Strategy 1: Text-based detection
        text_buttons = await self._detect_buttons_by_text(page_source, context)
        buttons.extend(text_buttons)

        # Strategy 2: Attribute-based detection
        attr_buttons = await self._detect_buttons_by_attributes(page_source, context)
        buttons.extend(attr_buttons)

        # Strategy 3: Visual detection (if screenshot provided)
        if screenshot_data:
            visual_buttons = await self._detect_buttons_visually(
                screenshot_data, context
            )
            buttons.extend(visual_buttons)

        # Strategy 4: Machine learning detection
        ml_buttons = await self._detect_buttons_with_ml(
            page_source, screenshot_data, context
        )
        buttons.extend(ml_buttons)

        # Deduplicate and rank results
        unique_buttons = await self._deduplicate_buttons(buttons)
        ranked_buttons = await self._rank_buttons_by_relevance(unique_buttons, context)

        logger.info(f"Detected {len(ranked_buttons)} buttons")
        return ranked_buttons

    async def detect_form_fields(
        self,
        page_source: str,
        form_context: Optional[Dict[str, Any]] = None,
    ) -> List[FormFieldDetection]:
        """Enhanced form field detection."""
        logger.info("Starting enhanced form field detection")

        fields = []

        # Strategy 1: Standard HTML form elements
        html_fields = await self._detect_html_form_fields(page_source, form_context)
        fields.extend(html_fields)

        # Strategy 2: Custom form implementations
        custom_fields = await self._detect_custom_form_fields(page_source, form_context)
        fields.extend(custom_fields)

        # Strategy 3: Dynamic forms (React, Vue, etc.)
        dynamic_fields = await self._detect_dynamic_form_fields(
            page_source, form_context
        )
        fields.extend(dynamic_fields)

        # Deduplicate and enhance with validation rules
        unique_fields = await self._deduplicate_fields(fields)
        enhanced_fields = await self._enhance_fields_with_validation(
            unique_fields, form_context
        )

        logger.info(f"Detected {len(enhanced_fields)} form fields")
        return enhanced_fields

    async def handle_oauth_flow(
        self,
        provider: OAuthProvider,
        redirect_url: str,
        tenant_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle OAuth/SSO flow integration."""
        logger.info(f"Starting OAuth flow for provider: {provider}")

        try:
            # Get OAuth credentials for tenant
            credentials = await self._get_oauth_credentials(provider, tenant_id)

            # Initialize OAuth handler
            handler = await self._get_oauth_handler(provider)

            # Start OAuth flow
            auth_url = await handler.initiate_flow(
                client_id=credentials.client_id,
                redirect_uri=credentials.redirect_uri,
                scopes=credentials.scopes,
                context=context,
            )

            # Exchange authorization code for tokens
            tokens = await handler.exchange_code_for_tokens(
                authorization_code=context.get("auth_code"),
                client_id=credentials.client_id,
                client_secret=credentials.client_secret,
                redirect_uri=credentials.redirect_uri,
            )

            # Store tokens securely
            await self._store_oauth_tokens(
                tenant_id=tenant_id,
                provider=provider,
                tokens=tokens,
            )

            return {
                "success": True,
                "auth_url": auth_url,
                "tokens": tokens,
                "provider": provider,
            }

        except Exception as e:
            logger.error(f"OAuth flow failed for {provider}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider,
            }

    async def capture_screenshot(
        self,
        application_id: str,
        step_number: int,
        step_description: str,
        page_context: Optional[Dict[str, Any]] = None,
        full_page: bool = False,
        highlight_elements: Optional[List[str]] = None,
    ) -> ScreenshotCapture:
        """Capture and store screenshot with metadata."""
        logger.info(
            f"Capturing screenshot for application {application_id}, step {step_number}"
        )

        capture_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)

        # Generate file paths
        screenshot_path = f"screenshots/{application_id}/{capture_id}.png"
        thumbnail_path = f"screenshots/{application_id}/thumbnails/{capture_id}.png"

        # Store screenshot metadata
        await self._store_screenshot_metadata(
            capture_id=capture_id,
            application_id=application_id,
            step_number=step_number,
            step_description=step_description,
            timestamp=timestamp,
            screenshot_path=screenshot_path,
            thumbnail_path=thumbnail_path,
            full_page=full_page,
            elements_highlighted=highlight_elements or [],
            viewport_size=page_context.get("viewport", {"width": 1920, "height": 1080}),
        )

        return ScreenshotCapture(
            capture_id=capture_id,
            application_id=application_id,
            step_number=step_number,
            step_description=step_description,
            timestamp=timestamp,
            screenshot_path=screenshot_path,
            thumbnail_path=thumbnail_path,
            viewport_size=page_context.get("viewport", {"width": 1920, "height": 1080}),
            full_page=full_page,
            elements_highlighted=highlight_elements or [],
        )

    async def track_concurrent_usage(
        self,
        session_data: Dict[str, Any],
    ) -> ConcurrentUsageSession:
        """Track concurrent usage sessions."""
        logger.info("Tracking concurrent usage session")

        session_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        # Store session
        await self._store_concurrent_session(
            session_id=session_id,
            user_id=session_data["user_id"],
            tenant_id=session_data["tenant_id"],
            application_id=session_data.get("application_id"),
            start_time=start_time,
            total_steps=session_data.get("total_steps", 0),
        )

        return ConcurrentUsageSession(
            session_id=session_id,
            user_id=session_data["user_id"],
            tenant_id=session_data["tenant_id"],
            application_id=session_data.get("application_id"),
            start_time=start_time,
            total_steps=session_data.get("total_steps", 0),
        )

    async def add_to_dlq(
        self,
        application_id: str,
        tenant_id: str,
        failure_reason: str,
        error_details: Dict[str, Any],
        payload: Dict[str, Any],
        max_retries: int = 3,
        priority: int = 0,
    ) -> DLQItem:
        """Add failed application to Dead Letter Queue."""
        logger.info(f"Adding application {application_id} to DLQ")

        dlq_item = DLQItem(
            id=str(uuid.uuid4()),
            application_id=application_id,
            tenant_id=tenant_id,
            failure_reason=failure_reason,
            error_details=error_details,
            attempt_count=1,
            max_retries=max_retries,
            payload=payload,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            priority=priority,
        )

        # Store DLQ item
        await self._store_dlq_item(dlq_item)

        return dlq_item

    async def retry_dlq_item(
        self,
        dlq_item_id: str,
        force_retry: bool = False,
    ) -> RetryResult:
        """Retry a DLQ item."""
        logger.info(f"Retrying DLQ item {dlq_item_id}")

        # Get DLQ item
        dlq_item = await self._get_dlq_item(dlq_item_id)
        if not dlq_item:
            return RetryResult(
                success=False,
                message="DLQ item not found",
                new_attempt_count=0,
            )

        # Check if retry is allowed
        if not force_retry and dlq_item.attempt_count >= dlq_item.max_retries:
            return RetryResult(
                success=False,
                message="Max retries exceeded",
                new_attempt_count=dlq_item.attempt_count,
            )

        # Check if retry time has arrived
        if dlq_item.next_retry_at and dlq_item.next_retry_at > datetime.now(
            timezone.utc
        ):
            return RetryResult(
                success=False,
                message="Retry time not reached",
                new_attempt_count=dlq_item.attempt_count,
                next_retry_at=dlq_item.next_retry_at,
            )

        try:
            # Attempt retry
            success = await self._execute_retry(dlq_item)

            if success:
                # Remove from DLQ on success
                await self._remove_dlq_item(dlq_item_id)
                return RetryResult(
                    success=True,
                    message="Retry successful",
                    new_attempt_count=dlq_item.attempt_count + 1,
                )
            else:
                # Update DLQ item for next retry
                next_retry_at = self._calculate_next_retry_time(dlq_item.attempt_count)
                await self._update_dlq_item_retry(
                    dlq_item_id,
                    dlq_item.attempt_count + 1,
                    next_retry_at,
                )

                return RetryResult(
                    success=False,
                    message="Retry failed, scheduled for next attempt",
                    new_attempt_count=dlq_item.attempt_count + 1,
                    next_retry_at=next_retry_at,
                )

        except Exception as e:
            logger.error(f"Retry execution failed: {e}")
            return RetryResult(
                success=False,
                message=f"Retry execution failed: {str(e)}",
                new_attempt_count=dlq_item.attempt_count + 1,
                error_details={"error": str(e)},
            )

    # Private helper methods
    async def _detect_buttons_by_text(
        self, page_source: str, context: Optional[Dict[str, Any]]
    ) -> List[ButtonDetection]:
        """Detect buttons by analyzing text content."""
        # Implementation for text-based button detection
        return []

    async def _detect_buttons_by_attributes(
        self, page_source: str, context: Optional[Dict[str, Any]]
    ) -> List[ButtonDetection]:
        """Detect buttons by analyzing HTML attributes."""
        # Implementation for attribute-based button detection
        return []

    async def _detect_buttons_visually(
        self, screenshot_data: bytes, context: Optional[Dict[str, Any]]
    ) -> List[ButtonDetection]:
        """Detect buttons using computer vision on screenshot."""
        # Implementation for visual button detection
        return []

    async def _detect_buttons_with_ml(
        self,
        page_source: str,
        screenshot_data: Optional[bytes],
        context: Optional[Dict[str, Any]],
    ) -> List[ButtonDetection]:
        """Detect buttons using machine learning models."""
        # Implementation for ML-based button detection
        return []

    async def _deduplicate_buttons(
        self, buttons: List[ButtonDetection]
    ) -> List[ButtonDetection]:
        """Remove duplicate button detections."""
        # Implementation for deduplication logic
        return buttons

    async def _rank_buttons_by_relevance(
        self, buttons: List[ButtonDetection], context: Optional[Dict[str, Any]]
    ) -> List[ButtonDetection]:
        """Rank buttons by relevance to current context."""
        # Implementation for relevance ranking
        return buttons

    async def _detect_html_form_fields(
        self, page_source: str, context: Optional[Dict[str, Any]]
    ) -> List[FormFieldDetection]:
        """Detect standard HTML form fields."""
        # Implementation for HTML form field detection
        return []

    async def _detect_custom_form_fields(
        self, page_source: str, context: Optional[Dict[str, Any]]
    ) -> List[FormFieldDetection]:
        """Detect custom form implementations."""
        # Implementation for custom form field detection
        return []

    async def _detect_dynamic_form_fields(
        self, page_source: str, context: Optional[Dict[str, Any]]
    ) -> List[FormFieldDetection]:
        """Detect dynamic form fields (React, Vue, etc.)."""
        # Implementation for dynamic form field detection
        return []

    async def _deduplicate_fields(
        self, fields: List[FormFieldDetection]
    ) -> List[FormFieldDetection]:
        """Remove duplicate field detections."""
        # Implementation for field deduplication
        return fields

    async def _enhance_fields_with_validation(
        self, fields: List[FormFieldDetection], context: Optional[Dict[str, Any]]
    ) -> List[FormFieldDetection]:
        """Enhance fields with validation rules."""
        # Implementation for validation enhancement
        return fields

    async def _get_oauth_credentials(
        self, provider: OAuthProvider, tenant_id: str
    ) -> OAuthCredentials:
        """Get OAuth credentials for provider and tenant."""
        # Implementation for OAuth credential retrieval
        pass

    async def _get_oauth_handler(self, provider: OAuthProvider):
        """Get OAuth handler for provider."""
        # Implementation for OAuth handler retrieval
        pass

    async def _store_oauth_tokens(
        self, tenant_id: str, provider: OAuthProvider, tokens: Dict[str, Any]
    ):
        """Store OAuth tokens securely."""
        # Implementation for token storage
        pass

    async def _store_screenshot_metadata(self, **kwargs):
        """Store screenshot metadata in database."""
        # Implementation for screenshot metadata storage
        pass

    async def _store_concurrent_session(self, **kwargs):
        """Store concurrent usage session."""
        # Implementation for session storage
        pass

    async def _store_dlq_item(self, dlq_item: DLQItem):
        """Store DLQ item in database."""
        # Implementation for DLQ item storage
        pass

    async def _get_dlq_item(self, dlq_item_id: str) -> Optional[DLQItem]:
        """Get DLQ item from database."""
        # Implementation for DLQ item retrieval
        pass

    async def _remove_dlq_item(self, dlq_item_id: str):
        """Remove DLQ item from database."""
        # Implementation for DLQ item removal
        pass

    async def _update_dlq_item_retry(
        self, dlq_item_id: str, attempt_count: int, next_retry_at: datetime
    ):
        """Update DLQ item retry information."""
        # Implementation for DLQ item update
        pass

    async def _execute_retry(self, dlq_item: DLQItem) -> bool:
        """Execute retry logic for DLQ item."""
        # Implementation for retry execution
        return True

    def _calculate_next_retry_time(self, attempt_count: int) -> datetime:
        """Calculate next retry time using exponential backoff."""
        from datetime import timedelta

        # Exponential backoff: 1min, 5min, 25min, 2h, 10h...
        delay_minutes = min(5 ** (attempt_count - 1), 600)  # Max 10 hours
        return datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)


# Factory function
def create_agent_improvements_manager(db_pool) -> AgentImprovementsManager:
    """Create agent improvements manager instance."""
    return AgentImprovementsManager(db_pool)
