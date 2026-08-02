"""Import all ORM models so they register with the shared declarative Base metadata.

This module must be imported before Alembic autogeneration or `Base.metadata.create_all`
so every table and relationship is known to SQLAlchemy.
"""

from app.database.base import Base
from app.models.attachment import Attachment
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.confidence_score import ConfidenceScore
from app.models.decision_result import DecisionResult
from app.models.domain import Domain
from app.models.evidence import Evidence, KnowledgeSource
from app.models.expert import Expert
from app.models.expert_session import ExpertSession
from app.models.permission import Permission, RolePermission
from app.models.question import Question, QuestionOption
from app.models.questionnaire import Questionnaire
from app.models.response import Response
from app.models.rule import Rule, RuleCondition, RuleOutcome
from app.models.user import Role, User
from app.models.version_history import VersionHistory

__all__ = [
    "Base",
    "Attachment",
    "AuditLog",
    "Case",
    "ConfidenceScore",
    "DecisionResult",
    "Domain",
    "Evidence",
    "KnowledgeSource",
    "Expert",
    "ExpertSession",
    "Permission",
    "RolePermission",
    "Question",
    "QuestionOption",
    "Questionnaire",
    "Response",
    "Rule",
    "RuleCondition",
    "RuleOutcome",
    "Role",
    "User",
    "VersionHistory",
]
