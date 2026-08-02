"""Expert repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.expert import Expert
from app.repositories.base import BaseRepository


class ExpertRepository(BaseRepository[Expert]):
    model = Expert

    def get_by_user_id(self, user_id: uuid.UUID) -> Expert | None:
        stmt = select(Expert).where(Expert.user_id == user_id, Expert.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()
