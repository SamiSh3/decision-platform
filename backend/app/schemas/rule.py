"""Rule, RuleCondition and RuleOutcome schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import Field

from app.core.constants import OutcomeDirection, RuleOperator, RuleStatus
from app.schemas.common import AuditFieldsSchema, ORMBase


class RuleConditionCreate(ORMBase):
    attribute_path: str = Field(min_length=1, max_length=255)
    operator: RuleOperator
    value: Any
    group_id: int = 0


class RuleConditionRead(AuditFieldsSchema):
    rule_id: uuid.UUID
    attribute_path: str
    operator: RuleOperator
    value: Any
    group_id: int


class RuleOutcomeCreate(ORMBase):
    direction: OutcomeDirection
    score_impact: float = Field(ge=-1, le=1)
    explanation_template: str = Field(min_length=1)


class RuleOutcomeRead(AuditFieldsSchema):
    rule_id: uuid.UUID
    direction: OutcomeDirection
    score_impact: float
    explanation_template: str


class RuleCreate(ORMBase):
    domain_id: uuid.UUID
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    version: int = 1
    status: RuleStatus = RuleStatus.DRAFT
    priority: int = 100
    weight: float = Field(default=1.0, ge=0, le=9.999)
    conditions: list[RuleConditionCreate] = Field(default_factory=list)
    outcomes: list[RuleOutcomeCreate] = Field(default_factory=list)


class RuleUpdate(ORMBase):
    name: str | None = None
    description: str | None = None
    status: RuleStatus | None = None
    priority: int | None = None
    weight: float | None = Field(default=None, ge=0, le=9.999)


class RuleRead(AuditFieldsSchema):
    domain_id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    version: int
    status: RuleStatus
    priority: int
    weight: float
    conditions: list[RuleConditionRead] = Field(default_factory=list)
    outcomes: list[RuleOutcomeRead] = Field(default_factory=list)
