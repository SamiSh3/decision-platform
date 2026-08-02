"""Rule service - CRUD plus versioning for the decision engine's rule base."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.audit_repository import VersionHistoryRepository
from app.repositories.domain_repository import DomainRepository
from app.repositories.rule_repository import (
    RuleConditionRepository,
    RuleOutcomeRepository,
    RuleRepository,
)
from app.schemas.common import Page, PageParams
from app.schemas.rule import RuleCreate, RuleRead, RuleUpdate


class RuleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RuleRepository(db)
        self.domain_repo = DomainRepository(db)
        self.condition_repo = RuleConditionRepository(db)
        self.outcome_repo = RuleOutcomeRepository(db)
        self.version_repo = VersionHistoryRepository(db)

    def create(self, payload: RuleCreate, actor_id: uuid.UUID | None) -> RuleRead:
        if self.domain_repo.get(payload.domain_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
        data = payload.model_dump(exclude={"conditions", "outcomes"})
        rule = self.repo.create(data, actor_id=actor_id)
        for condition in payload.conditions:
            cdata = condition.model_dump()
            cdata["rule_id"] = rule.id
            self.condition_repo.create(cdata, actor_id=actor_id)
        for outcome in payload.outcomes:
            odata = outcome.model_dump()
            odata["rule_id"] = rule.id
            self.outcome_repo.create(odata, actor_id=actor_id)
        self.version_repo.create(
            {
                "entity_type": "rule",
                "entity_id": rule.id,
                "version": rule.version,
                "snapshot": payload.model_dump(mode="json"),
                "change_summary": "Initial version created",
            },
            actor_id=actor_id,
        )
        self.db.commit()
        refreshed = self.repo.get_with_details(rule.id)
        return RuleRead.model_validate(refreshed)

    def get(self, entity_id: uuid.UUID) -> RuleRead:
        instance = self.repo.get_with_details(entity_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        return RuleRead.model_validate(instance)

    def list(self, params: PageParams, filters: dict | None = None) -> Page[RuleRead]:
        items, total = self.repo.list(
            filters=filters,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        detailed = [self.repo.get_with_details(i.id) for i in items]
        return Page.create(
            [RuleRead.model_validate(i) for i in detailed if i is not None],
            total,
            params.page,
            params.page_size,
        )

    def update(
        self, entity_id: uuid.UUID, payload: RuleUpdate, actor_id: uuid.UUID | None
    ) -> RuleRead:
        instance = self.repo.get_or_404(entity_id)
        update_data = payload.model_dump(exclude_unset=True)
        instance = self.repo.update(instance, update_data, actor_id=actor_id)
        self.db.commit()
        return self.get(entity_id)

    def create_new_version(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> RuleRead:
        """Creates a new draft version of an existing rule, copying its conditions
        and outcomes, leaving the prior version untouched (immutable history)."""
        existing = self.repo.get_with_details(entity_id)
        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

        from app.core.constants import RuleStatus

        new_rule = self.repo.create(
            {
                "domain_id": existing.domain_id,
                "code": existing.code,
                "name": existing.name,
                "description": existing.description,
                "version": existing.version + 1,
                "status": RuleStatus.DRAFT,
                "priority": existing.priority,
                "weight": existing.weight,
            },
            actor_id=actor_id,
        )
        for condition in existing.conditions:
            self.condition_repo.create(
                {
                    "rule_id": new_rule.id,
                    "attribute_path": condition.attribute_path,
                    "operator": condition.operator,
                    "value": condition.value,
                    "group_id": condition.group_id,
                },
                actor_id=actor_id,
            )
        for outcome in existing.outcomes:
            self.outcome_repo.create(
                {
                    "rule_id": new_rule.id,
                    "direction": outcome.direction,
                    "score_impact": outcome.score_impact,
                    "explanation_template": outcome.explanation_template,
                },
                actor_id=actor_id,
            )
        self.version_repo.create(
            {
                "entity_type": "rule",
                "entity_id": new_rule.id,
                "version": new_rule.version,
                "snapshot": {
                    "code": existing.code,
                    "name": existing.name,
                    "based_on_version": existing.version,
                },
                "change_summary": f"Forked from version {existing.version}",
            },
            actor_id=actor_id,
        )
        self.db.commit()
        return self.get(new_rule.id)

    def soft_delete(self, entity_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        instance = self.repo.get_or_404(entity_id)
        self.repo.soft_delete(instance, actor_id=actor_id)
        self.db.commit()
