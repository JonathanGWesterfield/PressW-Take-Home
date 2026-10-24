"""Read-only checks against the running Compose stack."""
import pytest

pytestmark = pytest.mark.smoke


def test_gateway_health(gateway_client):
    response = gateway_client.get("/gateway/healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_encore_database_health(encore_client):
    response = encore_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_legacy_crew_read(legacy_client):
    response = legacy_client.get("/callboard/crew/list", headers={"X-Org-Id": "3"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "ok"
    assert isinstance(payload["data"]["crew"], list)
    assert all(row["org"] == 3 for row in payload["data"]["crew"])
