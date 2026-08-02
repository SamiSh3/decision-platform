"""Rule, RuleCondition and RuleOutcome repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.constants import RuleStatus
from app.models.rule import Rule, RuleCondition, RuleOutcome
from app.repositories.base import BaseRepository


class RuleRepository(BaseRepository[Rule]):
    model = Rule

    def get_with_details(self, entity_id: uuid.UUID) -> Rule | None:
        stmt = (
            select(Rule)
            .where(Rule.id == entity_id, Rule.is_deleted.is_(False))
            .options(selectinload(Rule.conditions), selectinload(Rule.outcomes))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_active_for_domain(self, domain_id: uuid.UUID) -> list[Rule]:
        stmt = (
            select(Rule)
            .where(
                Rule.domain_id == domain_id,
                Rule.status == RuleStatus.ACTIVE,
                Rule.is_deleted.is_(False),
            )
            .options(selectinload(Rule.conditions), selectinload(Rule.outcomes))
            .order_by(Rule.priority.asc())
        )
        return list(self.db.execute(stmt).scalars().all())


class RuleConditionRepository(BaseRepository[RuleCondition]):
    model = RuleCondition


class RuleOutcomeRepository(BaseRepository[RuleOutcome]):
    model = RuleOutcome
