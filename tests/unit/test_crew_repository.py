from decimal import Decimal

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

    def execute(self, statement, parameters):
        self.executions.append((statement.text, parameters))
        return FakeResult(self.rows)

    def close(self):
        self.closed = True


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
