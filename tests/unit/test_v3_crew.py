from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from encore.app.crew.models import CrewRecord
from encore.app.crew.v3 import get_crew_service
from encore.app.main import app


class StubService:
    def __init__(self, records):
        self.records = records
        self.list_calls = []
        self.detail_calls = []

    def list_for_org(self, org_id):
        self.list_calls.append(org_id)
        return [record for record in self.records if record.org_id == org_id]

    def get_for_org(self, org_id, crew_id):
        self.detail_calls.append((org_id, crew_id))
        return next(
            (record for record in self.records if record.org_id == org_id and record.id == crew_id),
            None,
        )


@pytest.fixture
def v3_client():
    records = [
        CrewRecord(9, 7, "zoë@example.test", None, Decimal("27.34"), "Y", None, "{broken"),
        CrewRecord(10, 7, "crew@example.test", "Crew", None, "y", "notes", None),
        CrewRecord(11, 12, "foreign@example.test", "Foreign", Decimal("22.00"), "N", "foreign", "{}"),
    ]
    service = StubService(records)
    app.dependency_overrides[get_crew_service] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.clear()


def test_list_uses_strict_pagination_and_exposes_the_modern_field_set(v3_client):
    client, service = v3_client

    response = client.get("/v3/crew?page=1&page_size=1", headers={"X-Org-Id": "7"})

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 9,
                "org_id": 7,
                "user_name": "zoë@example.test",
                "display_name": None,
                "rate": "27.34",
                "is_lead": True,
                "notes": None,
            }
        ],
        "page": 1,
        "page_size": 1,
        "total": 2,
    }
    assert service.list_calls == [7]
    assert "preferences_raw" not in response.text


@pytest.mark.parametrize(
    ("path", "headers"),
    [
        ("/v3/crew", {}),
        ("/v3/crew", {"X-Org-Id": "0"}),
        # HTTPX permits only ASCII strings in headers. A non-ASCII byte sequence
        # still reaches ASGI here and must fail modern ASCII-only validation.
        ("/v3/crew", {"X-Org-Id": b"\xd9\xa1"}),
        ("/v3/crew?page=0", {"X-Org-Id": "7"}),
        ("/v3/crew?page_size=101", {"X-Org-Id": "7"}),
        ("/v3/crew?page=1.0", {"X-Org-Id": "7"}),
        ("/v3/crew?unknown=yes", {"X-Org-Id": "7"}),
        ("/v3/crew?page=1&page=2", {"X-Org-Id": "7"}),
        ("/v3/crew/0", {"X-Org-Id": "7"}),
        ("/v3/crew/9?unexpected=yes", {"X-Org-Id": "7"}),
    ],
)
def test_v3_rejects_malformed_or_ambiguous_input(v3_client, path, headers):
    client, service = v3_client

    response = client.get(path, headers=headers)

    assert response.status_code == 422
    assert response.json()["detail"]
    assert service.list_calls == []
    assert service.detail_calls == []
    assert "psycopg" not in response.text.lower()
    assert "sql" not in response.text.lower()


def test_v3_rejects_duplicate_organization_headers(v3_client):
    client, service = v3_client

    response = client.get("/v3/crew", headers=[("X-Org-Id", "7"), ("x-org-id", "7")])

    assert response.status_code == 422
    assert service.list_calls == []


def test_v3_accepts_a_positive_page_larger_than_the_database_id_range(v3_client):
    client, service = v3_client

    response = client.get("/v3/crew?page=2147483648", headers={"X-Org-Id": "7"})

    assert response.status_code == 200
    assert response.json() == {"items": [], "page": 2147483648, "page_size": 25, "total": 2}
    assert service.list_calls == [7]


def test_v3_accepts_zero_padded_positive_ids_and_the_int32_boundary(v3_client):
    client, service = v3_client

    padded = client.get("/v3/crew/0009", headers={"X-Org-Id": "007"})
    maximum_org = client.get("/v3/crew", headers={"X-Org-Id": "2147483647"})
    maximum_crew = client.get("/v3/crew/2147483647", headers={"X-Org-Id": "7"})
    over_org = client.get("/v3/crew", headers={"X-Org-Id": "2147483648"})
    over_crew = client.get("/v3/crew/2147483648", headers={"X-Org-Id": "7"})

    assert padded.status_code == 200
    assert padded.json()["id"] == 9
    assert maximum_org.status_code == 200
    assert maximum_org.json()["items"] == []
    assert maximum_crew.status_code == 404
    assert over_org.status_code == over_crew.status_code == 422
    assert service.list_calls == [2147483647]
    assert service.detail_calls == [(7, 9), (7, 2147483647)]


def test_v3_rejects_repeated_unknown_detail_parameters(v3_client):
    client, service = v3_client

    response = client.get("/v3/crew/9?unexpected=x&unexpected=y", headers={"X-Org-Id": "7"})

    assert response.status_code == 422
    assert service.detail_calls == []


def test_detail_hides_foreign_records_but_preserves_stored_nulls_and_raw_preferences(v3_client):
    client, service = v3_client

    detail = client.get("/v3/crew/10", headers={"X-Org-Id": "7"})
    foreign = client.get("/v3/crew/11", headers={"X-Org-Id": "7"})

    assert detail.status_code == 200
    assert detail.json()["rate"] is None
    assert detail.json()["is_lead"] is False
    assert detail.json()["preferences_raw"] is None
    assert foreign.status_code == 404
    assert foreign.json() == {"detail": "Crew not found"}
    assert service.detail_calls == [(7, 10), (7, 11)]


def test_trailing_slashes_are_not_redirects_and_wrong_methods_are_standard_405(v3_client):
    client, _ = v3_client

    trailing = client.get("/v3/crew/", headers={"X-Org-Id": "7"}, follow_redirects=False)
    method = client.post("/v3/crew", headers={"X-Org-Id": "7"})

    assert trailing.status_code == 404
    assert "location" not in trailing.headers
    assert method.status_code == 405


def test_openapi_documents_the_manual_modern_header_query_and_path_contract(v3_client):
    client, _ = v3_client
    paths = client.get("/openapi.json").json()["paths"]

    raw_list_parameters = paths["/v3/crew"]["get"]["parameters"]
    raw_detail_parameters = paths["/v3/crew/{crew_id}"]["get"]["parameters"]
    list_parameters = {
        (parameter["in"], parameter["name"]): parameter
        for parameter in raw_list_parameters
    }
    detail_parameters = {
        (parameter["in"], parameter["name"]): parameter
        for parameter in raw_detail_parameters
    }

    assert len(raw_list_parameters) == len(list_parameters)
    assert len(raw_detail_parameters) == len(detail_parameters)
    assert list_parameters[("header", "X-Org-Id")]["required"] is True
    assert "maxLength" not in list_parameters[("header", "X-Org-Id")]["schema"]
    assert list_parameters[("query", "page")]["schema"]["default"] == "1"
    assert "int32 ceiling" in list_parameters[("query", "page")]["description"]
    assert list_parameters[("query", "page_size")]["schema"]["default"] == "25"
    assert detail_parameters[("path", "crew_id")]["required"] is True
    assert detail_parameters[("path", "crew_id")]["schema"]["pattern"] == "^[0-9]*[1-9][0-9]*$"
