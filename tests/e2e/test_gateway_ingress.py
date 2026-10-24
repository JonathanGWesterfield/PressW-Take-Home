"""Gateway ingress parity for the org-7 crew-read cutover.

The direct-characterization corpus deliberately does not run through this
boundary: the supplied gateway has its own observed behavior for duplicate
headers, decoded paths, methods, and redirect hosts.  This test captures an
all-Callboard response from the fresh isolated stack, switches only the two
read prefixes, then compares the same ingress requests before rolling back by
an atomic route-file rename.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import uuid

import pytest
import yaml

from investigation.crew_support import CrewFixture, FIRST, ORG, OTHER, database_state, db, send


ROOT = Path(__file__).resolve().parents[2]
ROUTE_FIXTURES = ROOT / "tests" / "routes"
ROUTE_DIRECTORY = Path(os.getenv("SHOWCALL_ROUTE_DIRECTORY", "/routes"))
ROUTE_FILE = ROUTE_DIRECTORY / "routes.yaml"
TRACE = "slice-d-gateway-ingress"

pytestmark = [pytest.mark.e2e, pytest.mark.mutates_db]


def _publish_routes(name: str) -> None:
    """Validate a fixture before atomically making it visible to the gateway."""
    contents = (ROUTE_FIXTURES / name).read_text()
    parsed = yaml.safe_load(contents)
    assert isinstance(parsed, dict) and isinstance(parsed.get("routes"), dict)
    ROUTE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    replacement = ROUTE_DIRECTORY / f".{name}.{uuid.uuid4().hex}.tmp"
    replacement.write_text(contents)
    os.replace(replacement, ROUTE_FILE)


@pytest.fixture
def legacy_routes():
    # The named Compose volume starts empty.  Initializing it here keeps the
    # gateway image read-only and makes the publisher's atomic rename explicit.
    _publish_routes("legacy.yaml")
    try:
        yield
    finally:
        _publish_routes("legacy.yaml")


@pytest.fixture
def crew_fixture():
    CrewFixture.install_fixture()
    try:
        yield
    finally:
        CrewFixture.cleanup_fixture()


def _request(path: str, *, org: str | None = "7", method: str = "GET", raw_query: str | None = None,
             header_pairs: list[list[str]] | None = None) -> dict[str, object]:
    if header_pairs is None:
        header_pairs = [["X-Trace-Id", TRACE]]
        if org is not None:
            header_pairs.insert(0, ["X-Org-Id", org])
    return send(
        {
            "method": method,
            "path": path,
            "query": [],
            "raw_query": raw_query if raw_query is not None else "",
            "header_pairs": header_pairs,
            "body": None,
        },
        base=os.environ["GATEWAY_URL"],
    )


def _with_served_by(response: dict[str, object], backend: str) -> dict[str, object]:
    expected = copy.deepcopy(response)
    expected["headers"]["x-served-by"] = backend
    return expected


def _assert_served(response: dict[str, object], backend: str) -> None:
    assert response["headers"]["x-served-by"] == backend
    assert response["headers"]["x-trace-id"] == TRACE


def _crew_state() -> list[dict[str, object]]:
    return json.loads(db("SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id), '[]'::jsonb) FROM tg_crew t;"))


def test_org7_read_cutover_preserves_gateway_ingress_contract(
    gateway_client, encore_client, legacy_routes, crew_fixture
):
    """Exercise the original all-legacy ingress, cutover, and no-restart rollback."""
    initial_health = gateway_client.get("/gateway/healthz")
    assert initial_health.status_code == 200
    instance_id = initial_health.json()["instance_id"]
    state_before_reads = database_state()

    # This matrix is observed against the original all-Callboard gateway in the
    # same fresh database, rather than applying a direct-backend golden file to
    # an ingress with different transport behavior.
    requests = {
        "list_org7": {"path": "/callboard/crew/list"},
        "show_org7": {"path": "/callboard/crew/show", "raw_query": "crew_id=2"},
        "list_padded_org": {"path": "/callboard/crew/list", "org": "07"},
        "list_org3": {"path": "/callboard/crew/list", "org": "3"},
        "list_org12": {"path": "/callboard/crew/list", "org": "12"},
        "list_org19": {"path": "/callboard/crew/list", "org": "19"},
        "show_padded_org": {"path": "/callboard/crew/show", "org": "07", "raw_query": "crew_id=2"},
        "owned_fixture_list": {"path": "/callboard/crew/list", "org": str(ORG)},
        "owned_fixture_show": {"path": "/callboard/crew/show", "org": str(ORG), "raw_query": f"crew_id={FIRST}"},
        "owned_fixture_foreign": {"path": "/callboard/crew/show", "org": str(OTHER), "raw_query": f"crew_id={FIRST}"},
        "list_missing_org": {"path": "/callboard/crew/list", "org": None},
        "list_bad_org": {"path": "/callboard/crew/list", "org": "not-an-org"},
        "shift_org7": {"path": "/callboard/shift/list", "raw_query": "per_page=0"},
        "message_org7": {"path": "/callboard/message/list", "raw_query": "crew_id=6"},
        "show_foreign": {"path": "/callboard/crew/show", "raw_query": "crew_id=1"},
        "show_missing": {"path": "/callboard/crew/show", "raw_query": "crew_id=999999"},
        "list_wrong_method": {"path": "/callboard/crew/list", "method": "POST"},
        "duplicate_page": {"path": "/callboard/crew/list", "raw_query": "page=2&page=1&per_page=1"},
        "duplicate_id": {"path": "/callboard/crew/show", "raw_query": "crew_id=2&crew_id=1"},
        "bad_page_before_size": {"path": "/callboard/crew/list", "raw_query": "page=bad&per_page=bad"},
        "missing_id": {"path": "/callboard/crew/show"},
        "encoded_path": {"path": "/callboard/%63rew/list"},
        "encoded_separator": {"path": "/callboard/crew%2Flist"},
        "suffix": {"path": "/callboard/crew/list/extra"},
        "double_slash": {"path": "/callboard//crew/show", "raw_query": "crew_id=2"},
        "malformed_percent": {"path": "/callboard/crew/show", "raw_query": "crew_id=%FF"},
        "first7_last3": {
            "path": "/callboard/crew/list",
            "header_pairs": [["X-Org-Id", "7"], ["X-Org-Id", "3"], ["X-Trace-Id", TRACE]],
        },
        "first3_last7": {
            "path": "/callboard/crew/list",
            "header_pairs": [["X-Org-Id", "3"], ["X-Org-Id", "7"], ["X-Trace-Id", TRACE]],
        },
        "head": {"path": "/callboard/crew/list", "method": "HEAD"},
        "options": {"path": "/callboard/crew/list", "method": "OPTIONS"},
    }
    # Each migrated prefix needs its own wrong-method and suffix checks: routing
    # is by prefix, so even requests that fail validation may move to Encore.
    for endpoint in ("list", "show"):
        for method in ("POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
            requests[f"{endpoint}_{method}"] = {
                "path": f"/callboard/crew/{endpoint}", "method": method,
                "raw_query": "crew_id=2" if endpoint == "show" else "",
            }
        for suffix in ("/", "/extra"):
            requests[f"{endpoint}_suffix_{suffix}"] = {
                "path": f"/callboard/crew/{endpoint}{suffix}",
                "raw_query": "crew_id=2" if endpoint == "show" else "",
            }
    baseline = {name: _request(**spec) for name, spec in requests.items()}
    gateway_methods = {name for name, spec in requests.items() if spec.get("method") in {"HEAD", "OPTIONS"}}
    for name, response in baseline.items():
        if name in gateway_methods:
            assert response["status"] == 405
            assert "x-served-by" not in response["headers"]
            assert "x-trace-id" not in response["headers"]
            continue
        _assert_served(response, "callboard")

    # These are the independently observed quirks of the unmodified ingress.
    assert baseline["head"] == {
        "status": 405,
        "headers": {
            "content-length": "31",
            "content-type": "application/json",
            "allow": ["DELETE", "GET", "PATCH", "POST", "PUT"],
        },
        "body": "",
    }
    assert baseline["options"]["body"] == '{"detail":"Method Not Allowed"}'
    assert baseline["double_slash"]["status"] == 308
    assert baseline["double_slash"]["headers"]["location"] == (
        "http://callboard:8080/callboard/crew/show?crew_id=2"
    )
    assert "callboard:8080" in baseline["double_slash"]["body"]
    assert "\ufffd" in json.loads(baseline["malformed_percent"]["body"])["error"]
    assert json.loads(baseline["first7_last3"]["body"])["data"]["crew"][0]["org"] == 3
    assert json.loads(baseline["first3_last7"]["body"])["data"]["crew"][0]["org"] == 7
    assert json.loads(baseline["owned_fixture_foreign"]["body"]) == {"error": "not found", "result": "fail"}

    assert database_state() == state_before_reads
    state_before_write = state_before_reads
    crew_before = _crew_state()
    _publish_routes("mixed-org7.yaml")

    # Org 7 requests selected by the first header now use Encore's wrapper;
    # all payload and transport fields from the all-legacy ingress stay exact
    # except the deliberately controlled served-by marker.
    migrated_names = {
        "list_org7", "show_org7", "show_foreign", "show_missing", "list_wrong_method",
        "encoded_path", "encoded_separator", "suffix", "malformed_percent", "first7_last3",
        "duplicate_page", "duplicate_id", "bad_page_before_size", "missing_id",
    }
    migrated_names.update(
        name for name in requests
        if name.startswith(("list_suffix_", "show_suffix_"))
        or name in {f"{endpoint}_{method}" for endpoint in ("list", "show") for method in ("POST", "PUT", "PATCH", "DELETE")}
    )
    migrated = {name: _request(**requests[name]) for name in migrated_names}
    for name, response in migrated.items():
        assert response == _with_served_by(baseline[name], "encore"), name

    # Header routing deliberately retains the supplied gateway's ambiguity:
    # first duplicate chooses a route, while the collapsed forwarded mapping
    # carries the final value to the selected upstream.
    fallback_names = {
        "first3_last7", "list_padded_org", "list_org3", "list_missing_org", "list_bad_org",
        "shift_org7", "message_org7", "double_slash", "head", "options",
        "list_org12", "list_org19", "show_padded_org", "owned_fixture_list",
        "owned_fixture_show", "owned_fixture_foreign",
    } | gateway_methods
    assert set(migrated_names).isdisjoint(fallback_names)
    assert set(migrated_names) | set(fallback_names) == set(requests)
    for name in fallback_names:
        assert _request(**requests[name]) == baseline[name], name
    assert database_state() == state_before_write

    marker = "slice-d legacy write visible through migrated read"
    try:
        update = gateway_client.post(
            "/callboard/crew/update",
            headers={"X-Org-Id": "7", "X-Trace-Id": TRACE},
            data={"crew_id": "2", "notes": marker},
        )
        assert update.status_code == 200
        assert update.headers["x-served-by"] == "callboard"
        assert update.headers["x-trace-id"] == TRACE
        assert update.json()["data"]["notes"] == marker
        assert db("SELECT notes FROM tg_crew WHERE id=2 AND org=7;") == marker
        expected_after_write = copy.deepcopy(state_before_write)
        next(row for row in expected_after_write["tg_crew"] if row["id"] == 2)["notes"] = marker
        assert database_state() == expected_after_write

        show = _request("/callboard/crew/show", raw_query="crew_id=2")
        _assert_served(show, "encore")
        assert json.loads(show["body"])["data"]["notes"] == marker
        listing = _request("/callboard/crew/list")
        _assert_served(listing, "encore")
        assert next(row for row in json.loads(listing["body"])["data"]["crew"] if row["crew_id"] == 2)["notes"] == marker
        modern = encore_client.get("/v3/crew/2", headers={"X-Org-Id": "7"})
        assert modern.status_code == 200
        assert modern.json()["notes"] == marker
        modern_list = encore_client.get("/v3/crew", headers={"X-Org-Id": "7"})
        assert modern_list.status_code == 200
        assert next(row for row in modern_list.json()["items"] if row["id"] == 2)["notes"] == marker
        # Global crew + six tables for owned fixture orgs. Seeded scheduling and
        # messaging may change under Callboard maintenance and are not claimed
        # to be globally quiescent by this read-only check.
        assert database_state() == expected_after_write
    finally:
        restore = gateway_client.post(
            "/callboard/crew/update",
            headers={"X-Org-Id": "7", "X-Trace-Id": TRACE},
            data={"crew_id": "2", "notes": json.loads(baseline["show_org7"]["body"])["data"]["notes"]},
        )
        assert restore.status_code == 200
        assert restore.headers["x-served-by"] == "callboard"
        assert restore.json()["result"] == "ok"
    assert _crew_state() == crew_before
    assert database_state() == state_before_write

    _publish_routes("legacy.yaml")
    for name, spec in requests.items():
        assert _request(**spec) == baseline[name], name
    assert database_state() == state_before_write
    final_health = gateway_client.get("/gateway/healthz")
    assert final_health.status_code == 200
    assert final_health.json()["instance_id"] == instance_id


def test_gateway_preserves_supplied_trace_and_generates_missing_trace(gateway_client, legacy_routes):
    """Trace IDs are an ingress contract independent of response parity bodies."""
    supplied = gateway_client.get(
        "/callboard/crew/list", headers={"X-Org-Id": "7", "X-Trace-Id": TRACE}
    )
    assert supplied.status_code == 200
    assert supplied.headers["x-served-by"] == "callboard"
    assert supplied.headers["x-trace-id"] == TRACE
    generated = [gateway_client.get("/callboard/crew/list", headers={"X-Org-Id": "7"}) for _ in range(2)]
    traces = []
    for response in generated:
        assert response.status_code == 200
        assert response.headers["x-served-by"] == "callboard"
        trace = response.headers["x-trace-id"]
        assert uuid.UUID(hex=trace).hex == trace
        traces.append(trace)
    assert traces[0] != traces[1]
