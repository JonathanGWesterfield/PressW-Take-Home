from decimal import Decimal

import pytest
from sqlalchemy.exc import DataError

from encore.app.crew.models import CrewRecord
from encore.app.crew.repository import CrewRepository
from encore.app.crew.service import CrewService


class FakeMappings:
    def __init__(self, rows):
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)

    def first(self):
        return self.rows[0] if self.rows else None


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return FakeMappings(self.rows)


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.executions = []
        self.closed = False
        self.rolled_back = False

    def execute(self, statement, parameters):
        self.executions.append((statement.text, parameters))
        return FakeResult(self.rows)

    def close(self):
        self.closed = True

    def rollback(self):
        self.rolled_back = True


def row(**overrides):
    values = {
        "id": 9,
        "org": 7,
        "user_name": "marta@example.test",
        "display_name": "Marta",
        "rate": Decimal("31.00"),
        "is_lead": "Y",
        "notes": "head rigger",
        "prefs_blob": "{broken",
    }
    values.update(overrides)
    return values


def test_repository_list_uses_one_bound_tenant_query_and_safe_columns():
    session = FakeSession([row()])

    records = CrewRepository().list_for_org(session, 7)

    assert len(session.executions) == 1
    statement, parameters = session.executions[0]
    assert "WHERE org = :org_id" in statement
    assert "ORDER BY id ASC" in statement
    assert parameters == {"org_id": 7}
    assert "password" not in statement.lower()
    assert "org_name" not in statement.lower()
    assert records == [
        CrewRecord(
            id=9,
            org_id=7,
            user_name="marta@example.test",
            display_name="Marta",
            rate=Decimal("31.00"),
            is_lead="Y",
            notes="head rigger",
            preferences_raw="{broken",
        )
    ]


def test_repository_detail_binds_organization_and_id_in_one_predicate():
    session = FakeSession([])

    record = CrewRepository().get_for_org(session, 7, 9)

    statement, parameters = session.executions[0]
    assert "WHERE org = :org_id AND id = :crew_id" in statement
    assert parameters == {"org_id": 7, "crew_id": 9}
    assert record is None


def test_repository_legacy_detail_binds_raw_text_to_database_cast_and_tenant():
    session = FakeSession([])

    record = CrewRepository().get_for_org_raw_id(session, 7, "0009")

    statement, parameters = session.executions[0]
    assert "id = CAST(:crew_id AS integer) AND org = :org_id" in statement
    assert parameters == {"crew_id": "0009", "org_id": 7}
    assert "password" not in statement.lower()
    assert record is None


class StubRepository:
    def __init__(self):
        self.sessions = []

    def list_for_org(self, session, org_id):
        self.sessions.append((session, org_id))
        return []

    def get_for_org(self, session, org_id, crew_id):
        self.sessions.append((session, org_id, crew_id))
        return None


def test_service_uses_and_closes_a_fresh_session_for_each_request():
    created = []
    repository = StubRepository()

    def session_factory():
        session = FakeSession([])
        created.append(session)
        return session

    service = CrewService(repository=repository, session_factory=session_factory)
    service.list_for_org(7)
    service.get_for_org(7, 9)

    assert len(created) == 2
    assert created[0] is not created[1]
    assert all(session.closed for session in created)
    assert repository.sessions == [(created[0], 7), (created[1], 7, 9)]


class FailingLegacyRepository:
    def get_for_org_raw_id(self, session, org_id, crew_id):
        raise DataError("SELECT", {"crew_id": crew_id}, ValueError("bad integer"))


def test_legacy_raw_id_conversion_failure_rolls_back_and_closes_session():
    session = FakeSession([])
    service = CrewService(repository=FailingLegacyRepository(), session_factory=lambda: session)

    with pytest.raises(DataError):
        service.get_for_org_raw_id(7, "bad")

    assert session.rolled_back
    assert session.closed
