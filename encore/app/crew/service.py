"""Shared read use cases for modern and future compatibility adapters."""
from collections.abc import Callable

from sqlalchemy.orm import Session

from .. import db
from .models import CrewRecord
from .repository import CrewRepository


class CrewService:
    """Open a fresh session for each retrieval; do not cache Callboard rows."""

    def __init__(
        self,
        repository: CrewRepository | None = None,
        session_factory: Callable[[], Session] = db.session,
    ) -> None:
        self._repository = repository or CrewRepository()
        self._session_factory = session_factory

    def list_for_org(self, org_id: int) -> list[CrewRecord]:
        session = self._session_factory()
        try:
            return self._repository.list_for_org(session, org_id)
        finally:
            session.close()

    def get_for_org(self, org_id: int, crew_id: int) -> CrewRecord | None:
        session = self._session_factory()
        try:
            return self._repository.get_for_org(session, org_id, crew_id)
        finally:
            session.close()

    def get_for_org_raw_id(self, org_id: int, crew_id: str) -> CrewRecord | None:
        """Run the legacy wrapper lookup and reset a failed DB transaction."""
        session = self._session_factory()
        try:
            return self._repository.get_for_org_raw_id(session, org_id, crew_id)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
