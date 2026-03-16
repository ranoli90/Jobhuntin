# ---------------------------------------------------------------------------
# Sorce-specific models (backward-compatible)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Generic core models (agent-core vocabulary)
# ---------------------------------------------------------------------------
from packages.backend.domain.core_models import (
    COMPLETION_STATUS_ALIASES,
    ActorHistoryEntry,
    ActorIdentity,
    ActorProfile,
    ActorQualification,
    DomMappingResult,
    TargetForm,
    Task,
    TaskEvent,
    TaskEventType,
    TaskInput,
    TaskStatus,
    is_terminal,
    to_generic_status,
)
from packages.backend.domain.core_models import FormField as CoreFormField
from packages.backend.domain.core_models import FormFieldOption as CoreFormFieldOption
from packages.backend.domain.core_models import UnresolvedField as CoreUnresolvedField
from packages.backend.domain.models import (
    Application,
    ApplicationEvent,
    ApplicationInput,
    ApplicationStatus,
    CanonicalContact,
    CanonicalEducation,
    CanonicalExperience,
    CanonicalProfile,
    CanonicalSkills,
    ErrorResponse,
    FormField,
    FormFieldOption,
    Job,
    LLMMapping,
    Tenant,
    TenantMember,
    TenantPlan,
    TenantRole,
    UnresolvedField,
    normalize_profile,
)

# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------
from packages.backend.domain.repositories import (
    ApplicationRepo,
    EventRepo,
    InputRepo,
    JobRepo,
    ProfileRepo,
    TenantRepo,
    db_transaction,
)

# ---------------------------------------------------------------------------
# Tenant context and guards
# ---------------------------------------------------------------------------
from packages.backend.domain.tenant import (
    TenantContext,
    TenantScopeError,
    assert_tenant_owns,
    require_role,
    require_system_admin,
    require_tenant_admin_or_system,
    resolve_tenant_context,
)

__all__ = [
    # Sorce-specific (backward-compat)
    "ApplicationStatus",
    "CanonicalContact",
    "CanonicalEducation",
    "CanonicalExperience",
    "CanonicalProfile",
    "CanonicalSkills",
    "Application",
    "ApplicationInput",
    "ApplicationEvent",
    "Job",
    "Tenant",
    "TenantMember",
    "TenantPlan",
    "TenantRole",
    "FormFieldOption",
    "FormField",
    "LLMMapping",
    "UnresolvedField",
    "ErrorResponse",
    "normalize_profile",
    # Generic core
    "ActorIdentity",
    "ActorProfile",
    "ActorQualification",
    "ActorHistoryEntry",
    "TaskStatus",
    "TaskEventType",
    "Task",
    "TaskInput",
    "TaskEvent",
    "TargetForm",
    "DomMappingResult",
    "CoreFormField",
    "CoreFormFieldOption",
    "CoreUnresolvedField",
    "is_terminal",
    "to_generic_status",
    "COMPLETION_STATUS_ALIASES",
    # Repositories
    "ApplicationRepo",
    "ProfileRepo",
    "JobRepo",
    "InputRepo",
    "EventRepo",
    "TenantRepo",
    "db_transaction",
    # Tenant
    "TenantContext",
    "TenantScopeError",
    "resolve_tenant_context",
    "assert_tenant_owns",
    "require_role",
    "require_system_admin",
    "require_tenant_admin_or_system",
    # Session management
    "SessionManager",
]

# Session management
from packages.backend.domain.session_manager import SessionManager
