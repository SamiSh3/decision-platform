"""Domain repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.domain import Domain
from app.repositories.base import BaseRepository


class DomainRepository(BaseRepository[Domain]):
    model = Domain

    def get_by_code(self, code: str) -> Domain | None:
        stmt = select(Domain).where(Domain.code == code, Domain.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()
