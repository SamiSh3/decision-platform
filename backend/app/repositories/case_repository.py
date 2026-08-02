"""Case repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.response import Response
from app.repositories.base import BaseRepository


class CaseRepository(BaseRepository[Case]):
    model = Case

    def get_with_responses(self, entity_id: uuid.UUID) -> Case | None:
        stmt = (
            select(Case)
            .where(Case.id == entity_id, Case.is_deleted.is_(False))
            .options(selectinload(Case.responses).selectinload(Response.evidence_items))
        )
        return self.db.execute(stmt).scalar_one_or_none()
