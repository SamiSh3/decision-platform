"""Response, Evidence and KnowledgeSource repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.evidence import Evidence, KnowledgeSource
from app.models.response import Response
from app.repositories.base import BaseRepository


class ResponseRepository(BaseRepository[Response]):
    model = Response

    def list_for_case(self, case_id: uuid.UUID) -> list[Response]:
        stmt = (
            select(Response)
            .where(Response.case_id == case_id, Response.is_deleted.is_(False))
            .options(selectinload(Response.evidence_items), selectinload(Response.expert))
        )
        return list(self.db.execute(stmt).scalars().all())


class EvidenceRepository(BaseRepository[Evidence]):
    model = Evidence


class KnowledgeSourceRepository(BaseRepository[KnowledgeSource]):
    model = KnowledgeSource
