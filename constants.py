"""Constants and enums for Skillfield Sentinel."""

import sys
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        pass


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ErrorCategory(StrEnum):
    DATABASE = "database"
    AUTH = "auth"
    API = "api"
    UI = "ui"
    INTEGRATION = "integration"
    AI = "ai"
    INFRASTRUCTURE = "infrastructure"
    UNKNOWN = "unknown"


class ErrorStatus(StrEnum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    FIX_GENERATED = "fix_generated"
    FIX_APPROVED = "fix_approved"
    FIX_DEPLOYED = "fix_deployed"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class FixStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"
    FAILED = "failed"


class FeatureStatus(StrEnum):
    SUBMITTED = "submitted"
    GENERATING = "generating"
    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"


VALID_SEVERITIES = frozenset(s.value for s in Severity)
VALID_CATEGORIES = frozenset(c.value for c in ErrorCategory)
VALID_ERROR_STATUSES = frozenset(s.value for s in ErrorStatus)
VALID_FIX_STATUSES = frozenset(s.value for s in FixStatus)
VALID_FEATURE_STATUSES = frozenset(s.value for s in FeatureStatus)

# Open error statuses (not resolved or ignored)
OPEN_ERROR_STATUSES = frozenset({
    ErrorStatus.NEW,
    ErrorStatus.ACKNOWLEDGED,
    ErrorStatus.FIX_GENERATED,
    ErrorStatus.FIX_APPROVED,
})
