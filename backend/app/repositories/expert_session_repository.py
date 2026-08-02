"""ExpertSession repository."""

from __future__ import annotations

from app.models.expert_session import ExpertSession
from app.repositories.base import BaseRepository


class ExpertSessionRepository(BaseRepository[ExpertSession]):
    model = ExpertSession
