"""Modern crew read contract against the real, isolated Encore service."""
import pytest

from investigation.crew_support import CrewFixture, FIRST, ORG, database_state, db


pytestmark = [pytest.mark.e2e, pytest.mark.mutates_db]


@pytest.fixture
def crew_fixture():
    CrewFixture.install_fixture()
    try:
        yield
    finally:
        CrewFixture.cleanup_fixture()


def test_v3_list_is_ordered_tenant_scoped_and_read_only(encore_client, crew_fixture):
    before = database_state()

    response = encore_client.get("/v3/crew?page=1&page_size=100", headers={"X-Org-Id": str(ORG)})

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 100
    assert payload["total"] == 32
    assert [item["id"] for item in payload["items"]] == list(range(910001, 910033))
    assert all(item["org_id"] == ORG for item in payload["items"])
    assert all("preferences_raw" not in item for item in payload["items"])
    assert "DO-NOT-EXPOSE" not in response.text
    assert "password" not in response.text.lower()
    assert database_state() == before


def test_v3_detail_preserves_nulls_unicode_rounding_and_raw_preferences(encore_client, crew_fixture):
    before = database_state()

    nulls = encore_client.get("/v3/crew/910002", headers={"X-Org-Id": str(ORG)})
    unusual = encore_client.get("/v3/crew/910003", headers={"X-Org-Id": str(ORG)})
    rounded = encore_client.get("/v3/crew/910007", headers={"X-Org-Id": str(ORG)})

    assert nulls.status_code == unusual.status_code == rounded.status_code == 200
    assert nulls.json()["display_name"] is None
    assert nulls.json()["rate"] is None
    assert nulls.json()["notes"] is None
    assert nulls.json()["preferences_raw"] is None
    assert unusual.json()["user_name"] == "zoë+测试@contract.example"
    assert unusual.json()["preferences_raw"] == "{broken"
    assert rounded.json()["rate"] == "27.34"
    assert database_state() == before


def test_v3_uses_common_not_found_for_missing_and_foreign_crew(encore_client, crew_fixture):
    before = database_state()

    foreign = encore_client.get("/v3/crew/920001", headers={"X-Org-Id": str(ORG)})
    missing = encore_client.get("/v3/crew/999999", headers={"X-Org-Id": str(ORG)})

    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json() == {"detail": "Crew not found"}
    assert database_state() == before


@pytest.mark.parametrize(
    "path",
    [
        "/v3/crew?page=0",
        "/v3/crew?page_size=101",
        "/v3/crew?page=1&page=2",
        "/v3/crew?legacy_filter=yes",
        "/v3/crew/0",
        "/v3/crew/910001?unexpected=yes",
    ],
)
def test_v3_rejects_invalid_requests_without_database_diagnostics(encore_client, crew_fixture, path):
    before = database_state()

    response = encore_client.get(path, headers={"X-Org-Id": str(ORG)})

    assert response.status_code == 422
    assert response.json()["detail"]
    assert "postgres" not in response.text.lower()
    assert "sqlalchemy" not in response.text.lower()
    assert database_state() == before


def test_v3_large_positive_page_is_an_empty_success(encore_client, crew_fixture):
    before = database_state()

    response = encore_client.get(
        "/v3/crew?page=2147483648", headers={"X-Org-Id": str(ORG)}
    )

    assert response.status_code == 200
    assert response.json() == {"items": [], "page": 2147483648, "page_size": 25, "total": 32}
    assert database_state() == before


def test_v3_next_read_sees_a_committed_legacy_table_update_without_a_cache(encore_client, crew_fixture):
    original = encore_client.get(f"/v3/crew/{FIRST}", headers={"X-Org-Id": str(ORG)})
    assert original.status_code == 200
    try:
        db(f"UPDATE tg_crew SET notes='visible through next encore read' WHERE id={FIRST};")
        detail = encore_client.get(f"/v3/crew/{FIRST}", headers={"X-Org-Id": str(ORG)})
        listing = encore_client.get("/v3/crew?page=1&page_size=100", headers={"X-Org-Id": str(ORG)})
        assert detail.json()["notes"] == "visible through next encore read"
        assert next(item for item in listing.json()["items"] if item["id"] == FIRST)["notes"] == "visible through next encore read"
    finally:
        db(f"UPDATE tg_crew SET notes='note 1' WHERE id={FIRST};")
