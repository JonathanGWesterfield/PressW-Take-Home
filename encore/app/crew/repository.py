"""Tenant-scoped read access to the existing Callboard crew table."""
from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import CrewRecord


_SAFE_COLUMNS = """
    id,
    org,
    user_name,
    display_name,
    rate,
    is_lead,
    notes,
    prefs_blob
"""


class CrewRepository:
    """Read only the stored columns approved for the first migration wave."""

    def list_for_org(self, session: Session, org_id: int) -> list[CrewRecord]:
        """Return one deterministic, tenant-scoped list query.

        Pagination belongs to the caller so the returned total and page use the
        same in-memory snapshot.  This intentionally has no count query or
        cache in the first wave.
        """
        result = session.execute(
            text(
                f"""
                SELECT {_SAFE_COLUMNS}
                FROM tg_crew
                WHERE org = :org_id
                ORDER BY id ASC
                """
            ),
            {"org_id": org_id},
        )
        return [self._record(row) for row in result.mappings()]

    def get_for_org(
        self, session: Session, org_id: int, crew_id: int
    ) -> CrewRecord | None:
        """Look up an owned record without ever fetching it unscoped first."""
        result = session.execute(
            text(
                f"""
                SELECT {_SAFE_COLUMNS}
                FROM tg_crew
                WHERE org = :org_id AND id = :crew_id
                """
            ),
            {"org_id": org_id, "crew_id": crew_id},
        )
        row = result.mappings().first()
        return self._record(row) if row is not None else None

    @staticmethod
    def _record(row: dict[str, object]) -> CrewRecord:
        return CrewRecord(
            id=row["id"],
            org_id=row["org"],
            user_name=row["user_name"],
            display_name=row["display_name"],
            rate=row["rate"],
            is_lead=row["is_lead"],
            notes=row["notes"],
            preferences_raw=row["prefs_blob"],
        )
