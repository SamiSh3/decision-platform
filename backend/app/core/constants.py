"""Application-wide enums and constants."""

from enum import Enum


class RoleName(str, Enum):
    ADMIN = "admin"
    EXPERT = "expert"
    REVIEWER = "reviewer"
    USER = "user"


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    BOOLEAN = "boolean"
    NUMERIC = "numeric"
    TEXT = "text"
    SCALE = "scale"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImportanceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MANDATORY = "mandatory"


class CaseStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class RuleOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_THAN = "less_than"
    LESS_OR_EQUAL = "less_or_equal"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    BETWEEN = "between"


class OutcomeDirection(str, Enum):
    BUY = "buy"
    DO_NOT_BUY = "do_not_buy"
    CAUTION = "caution"
    NEGOTIATE = "negotiate"
    NEEDS_INSPECTION = "needs_inspection"
    CUSTOM = "custom"


class RecommendationLabel(str, Enum):
    STRONGLY_RECOMMENDED = "strongly_recommended"
    RECOMMENDED = "recommended"
    NEUTRAL = "neutral"
    NOT_RECOMMENDED = "not_recommended"
    STRONGLY_NOT_RECOMMENDED = "strongly_not_recommended"


class RuleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ExpertSessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SOFT_DELETE = "soft_delete"
    RESTORE = "restore"
    LOGIN = "login"
    LOGOUT = "logout"
    DECISION_COMPUTED = "decision_computed"
