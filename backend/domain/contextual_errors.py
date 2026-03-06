"""Contextual error help service.

Provides helpful, actionable error messages with:
- Error code classification
- Contextual suggestions
- Resolution steps
- Related documentation links
"""

import logging
from dataclasses import dataclass, field
from enum import StrEnum

logger = logging.getLogger(__name__)


class ErrorCategory(StrEnum):
    """Categories of errors."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NETWORK = "network"
    DATABASE = "database"
    RATE_LIMIT = "rate_limit"
    PAYMENT = "payment"
    FILE_UPLOAD = "file_upload"
    AI_SERVICE = "ai_service"
    EXTERNAL_API = "external_api"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class ErrorSeverity(StrEnum):
    """Error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorSolution:
    """A potential solution for an error."""

    title: str
    description: str
    action: str | None = None  # e.g., "retry", "redirect", "contact_support"
    action_url: str | None = None
    action_label: str | None = None


@dataclass
class ContextualError:
    """An error with contextual help."""

    code: str
    title: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    solutions: list[ErrorSolution] = field(default_factory=list)
    documentation_url: str | None = None
    support_ticket: bool = False
    retry_possible: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "code": self.code,
            "title": self.title,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "solutions": [
                {
                    "title": s.title,
                    "description": s.description,
                    "action": s.action,
                    "action_url": s.action_url,
                    "action_label": s.action_label,
                }
                for s in self.solutions
            ],
            "documentation_url": self.documentation_url,
            "support_ticket": self.support_ticket,
            "retry_possible": self.retry_possible,
        }


# Error registry with contextual help
ERROR_REGISTRY: dict[str, ContextualError] = {
    # Authentication errors
    "AUTH_001": ContextualError(
        code="AUTH_001",
        title="Invalid Credentials",
        message="The email or password you entered is incorrect.",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Check your credentials",
                description="Make sure you're using the correct email address and password.",
            ),
            ErrorSolution(
                title="Reset your password",
                description="If you've forgotten your password, use the reset link below.",
                action="redirect",
                action_url="/forgot-password",
                action_label="Reset Password",
            ),
        ],
        documentation_url="/docs/authentication#troubleshooting",
    ),
    "AUTH_002": ContextualError(
        code="AUTH_002",
        title="Account Locked",
        message="Your account has been temporarily locked due to too many failed login attempts.",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Wait and try again",
                description="Your account will be unlocked in 15 minutes.",
            ),
            ErrorSolution(
                title="Contact support",
                description="If this is urgent, contact our support team.",
                action="contact_support",
            ),
        ],
        support_ticket=True,
    ),
    "AUTH_003": ContextualError(
        code="AUTH_003",
        title="Session Expired",
        message="Your session has expired. Please log in again.",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.INFO,
        solutions=[
            ErrorSolution(
                title="Log in again",
                description="Click below to return to the login page.",
                action="redirect",
                action_url="/login",
                action_label="Log In",
            ),
        ],
        retry_possible=True,
    ),
    "AUTH_004": ContextualError(
        code="AUTH_004",
        title="Email Not Verified",
        message="Please verify your email address before logging in.",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Check your inbox",
                description="Look for a verification email from us.",
            ),
            ErrorSolution(
                title="Resend verification",
                description="Request a new verification email.",
                action="resend_verification",
                action_label="Resend Email",
            ),
        ],
    ),
    # Authorization errors
    "AUTHZ_001": ContextualError(
        code="AUTHZ_001",
        title="Access Denied",
        message="You don't have permission to access this resource.",
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Check your subscription",
                description="This feature may require a higher subscription tier.",
                action="redirect",
                action_url="/pricing",
                action_label="View Plans",
            ),
            ErrorSolution(
                title="Contact administrator",
                description="If you believe this is an error, contact your team administrator.",
            ),
        ],
    ),
    "AUTHZ_002": ContextualError(
        code="AUTHZ_002",
        title="Feature Not Available",
        message="This feature is not available on your current plan.",
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.INFO,
        solutions=[
            ErrorSolution(
                title="Upgrade your plan",
                description="Unlock this feature by upgrading to a higher tier.",
                action="redirect",
                action_url="/pricing",
                action_label="Upgrade Now",
            ),
        ],
    ),
    # Validation errors
    "VAL_001": ContextualError(
        code="VAL_001",
        title="Invalid Email Format",
        message="Please enter a valid email address.",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.INFO,
        solutions=[
            ErrorSolution(
                title="Check email format",
                description="Make sure your email follows the format: name@domain.com",
            ),
        ],
    ),
    "VAL_002": ContextualError(
        code="VAL_002",
        title="Password Requirements Not Met",
        message="Your password doesn't meet the security requirements.",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.INFO,
        solutions=[
            ErrorSolution(
                title="Password requirements",
                description="Your password must be at least 8 characters and include uppercase, lowercase, number, and special character.",
            ),
        ],
    ),
    "VAL_003": ContextualError(
        code="VAL_003",
        title="File Too Large",
        message="The file you're trying to upload exceeds the size limit.",
        category=ErrorCategory.FILE_UPLOAD,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Check file size",
                description="Maximum file size is 10MB for resumes and 5MB for images.",
            ),
            ErrorSolution(
                title="Compress your file",
                description="Try compressing your file or converting to a smaller format.",
            ),
        ],
    ),
    "VAL_004": ContextualError(
        code="VAL_004",
        title="Invalid File Type",
        message="This file type is not supported.",
        category=ErrorCategory.FILE_UPLOAD,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Supported formats",
                description="For resumes: PDF, DOC, DOCX. For images: JPG, PNG, GIF.",
            ),
        ],
    ),
    # Network errors
    "NET_001": ContextualError(
        code="NET_001",
        title="Connection Failed",
        message="Unable to connect to the server. Please check your internet connection.",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Check your connection",
                description="Make sure you're connected to the internet.",
            ),
            ErrorSolution(
                title="Try again",
                description="Click retry to attempt the request again.",
                action="retry",
                action_label="Retry",
            ),
        ],
        retry_possible=True,
    ),
    "NET_002": ContextualError(
        code="NET_002",
        title="Request Timeout",
        message="The request took too long to complete.",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Try again",
                description="The server might be busy. Please try again.",
                action="retry",
                action_label="Retry",
            ),
        ],
        retry_possible=True,
    ),
    # Rate limit errors
    "RATE_001": ContextualError(
        code="RATE_001",
        title="Too Many Requests",
        message="You've made too many requests. Please wait before trying again.",
        category=ErrorCategory.RATE_LIMIT,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Wait and retry",
                description="Please wait 60 seconds before making another request.",
            ),
        ],
        retry_possible=True,
    ),
    "RATE_002": ContextualError(
        code="RATE_002",
        title="AI Usage Limit Reached",
        message="You've reached your AI suggestions limit for this billing period.",
        category=ErrorCategory.RATE_LIMIT,
        severity=ErrorSeverity.INFO,
        solutions=[
            ErrorSolution(
                title="Upgrade your plan",
                description="Get more AI suggestions with a higher tier.",
                action="redirect",
                action_url="/pricing",
                action_label="Upgrade",
            ),
            ErrorSolution(
                title="Wait for reset",
                description="Your limit will reset at the start of your next billing cycle.",
            ),
        ],
    ),
    # Payment errors
    "PAY_001": ContextualError(
        code="PAY_001",
        title="Payment Failed",
        message="Your payment could not be processed.",
        category=ErrorCategory.PAYMENT,
        severity=ErrorSeverity.ERROR,
        solutions=[
            ErrorSolution(
                title="Check card details",
                description="Make sure your card number, expiry, and CVV are correct.",
            ),
            ErrorSolution(
                title="Try another card",
                description="Your card might not support online payments.",
            ),
            ErrorSolution(
                title="Contact your bank",
                description="Your bank might have declined the transaction.",
            ),
        ],
    ),
    "PAY_002": ContextualError(
        code="PAY_002",
        title="Subscription Cancelled",
        message="Your subscription has been cancelled.",
        category=ErrorCategory.PAYMENT,
        severity=ErrorSeverity.INFO,
        solutions=[
            ErrorSolution(
                title="Reactivate subscription",
                description="You can reactivate your subscription anytime.",
                action="redirect",
                action_url="/settings/billing",
                action_label="Reactivate",
            ),
        ],
    ),
    # AI Service errors
    "AI_001": ContextualError(
        code="AI_001",
        title="AI Service Unavailable",
        message="Our AI service is temporarily unavailable.",
        category=ErrorCategory.AI_SERVICE,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Try again later",
                description="The AI service should be back shortly.",
                action="retry",
                action_label="Retry",
            ),
        ],
        retry_possible=True,
    ),
    "AI_002": ContextualError(
        code="AI_002",
        title="AI Response Timeout",
        message="The AI took too long to respond.",
        category=ErrorCategory.AI_SERVICE,
        severity=ErrorSeverity.WARNING,
        solutions=[
            ErrorSolution(
                title="Simplify your request",
                description="Try breaking down complex requests into smaller parts.",
            ),
            ErrorSolution(
                title="Try again",
                description="Click retry to generate a new response.",
                action="retry",
                action_label="Retry",
            ),
        ],
        retry_possible=True,
    ),
    # Database errors
    "DB_001": ContextualError(
        code="DB_001",
        title="Data Save Failed",
        message="Unable to save your changes. Please try again.",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        solutions=[
            ErrorSolution(
                title="Retry save",
                description="Click retry to save your changes again.",
                action="retry",
                action_label="Retry",
            ),
            ErrorSolution(
                title="Check your connection",
                description="Make sure you have a stable internet connection.",
            ),
        ],
        retry_possible=True,
    ),
    # Generic errors
    "GEN_001": ContextualError(
        code="GEN_001",
        title="Something Went Wrong",
        message="An unexpected error occurred. Our team has been notified.",
        category=ErrorCategory.UNKNOWN,
        severity=ErrorSeverity.ERROR,
        solutions=[
            ErrorSolution(
                title="Try again",
                description="Sometimes a simple retry fixes the issue.",
                action="retry",
                action_label="Retry",
            ),
            ErrorSolution(
                title="Contact support",
                description="If the problem persists, contact our support team.",
                action="contact_support",
            ),
        ],
        support_ticket=True,
    ),
}


def get_error(code: str) -> ContextualError | None:
    """Get an error by its code."""
    return ERROR_REGISTRY.get(code)


def get_error_message(code: str, fallback: str = "An error occurred") -> str:
    """Get a user-friendly error message by code."""
    error = ERROR_REGISTRY.get(code)
    return error.message if error else fallback


def get_error_solutions(code: str) -> list[ErrorSolution]:
    """Get solutions for an error code."""
    error = ERROR_REGISTRY.get(code)
    return error.solutions if error else []


def create_error_response(
    code: str,
    custom_message: str | None = None,
    additional_context: dict | None = None,
) -> dict:
    """Create a full error response for the API."""
    error = ERROR_REGISTRY.get(code)

    if not error:
        # Return generic error for unknown codes
        error = ERROR_REGISTRY["GEN_001"]

    response = error.to_dict()

    if custom_message:
        response["message"] = custom_message

    if additional_context:
        response["context"] = additional_context

    return response


def classify_exception(exc: Exception) -> ContextualError:
    """Classify an exception into a contextual error."""
    type(exc).__name__
    exc_message = str(exc).lower()

    # Map common exceptions to error codes
    if "authentication" in exc_message or "unauthorized" in exc_message:
        return ERROR_REGISTRY.get("AUTH_001", ERROR_REGISTRY["GEN_001"])

    if "permission" in exc_message or "forbidden" in exc_message:
        return ERROR_REGISTRY.get("AUTHZ_001", ERROR_REGISTRY["GEN_001"])

    if "timeout" in exc_message:
        return ERROR_REGISTRY.get("NET_002", ERROR_REGISTRY["GEN_001"])

    if "connection" in exc_message or "network" in exc_message:
        return ERROR_REGISTRY.get("NET_001", ERROR_REGISTRY["GEN_001"])

    if "rate limit" in exc_message or "too many" in exc_message:
        return ERROR_REGISTRY.get("RATE_001", ERROR_REGISTRY["GEN_001"])

    if "validation" in exc_message or "invalid" in exc_message:
        return ERROR_REGISTRY.get("VAL_001", ERROR_REGISTRY["GEN_001"])

    if "payment" in exc_message or "billing" in exc_message:
        return ERROR_REGISTRY.get("PAY_001", ERROR_REGISTRY["GEN_001"])

    # Default to generic error
    return ERROR_REGISTRY["GEN_001"]
