# ---------------------------------------------------------------------------
# Sorce-specific models (backward-compatible)
# ---------------------------------------------------------------------------
from backend.domain.models import (
    ApplicationStatus,
    CanonicalContact,
    CanonicalEducation,
    CanonicalExperience,
    CanonicalProfile,
    CanonicalSkills,
    Application,
    ApplicationInput,
    ApplicationEvent,
    Job,
    Tenant,
    TenantMember,
    TenantPlan,
    TenantRole,
    FormFieldOption,
    FormField,
    LLMMapping,
    UnresolvedField,
    ErrorResponse,
    normalize_profile,
)

# ---------------------------------------------------------------------------
# Generic core models (agent-core vocabulary)
# ---------------------------------------------------------------------------
from backend.domain.core_models import (
    ActorIdentity,
    ActorProfile,
    ActorQualification,
    ActorHistoryEntry,
    TaskStatus,
    TaskEventType,
    Task,
    TaskInput,
    TaskEvent,
    TargetForm,
    DomMappingResult,
    FormField as CoreFormField,
    FormFieldOption as CoreFormFieldOption,
    UnresolvedField as CoreUnresolvedField,
    is_terminal,
    to_generic_status,
    COMPLETION_STATUS_ALIASES,
)

# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------
from backend.domain.repositories import (
    ApplicationRepo,
    ProfileRepo,
    JobRepo,
    InputRepo,
    EventRepo,
    TenantRepo,
    db_transaction,
)

# ---------------------------------------------------------------------------
# Tenant context and guards
# ---------------------------------------------------------------------------
from backend.domain.tenant import (
    TenantContext,
    TenantScopeError,
    resolve_tenant_context,
    assert_tenant_owns,
    require_role,
    require_system_admin,
    require_tenant_admin_or_system,
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
]
