"""Bounded exploration complements the immutable, individually named regressions."""
import importlib.util
import json
import os
from pathlib import Path

from hypothesis import given, settings, strategies as st
import httpx
import pytest

pytestmark = [pytest.mark.mutates_db, pytest.mark.fuzz]


@pytest.fixture(scope="module")
def controlled_crew(pytestconfig):
    source = Path(__file__).resolve().parents[1] / "characterization/test_crew_contract.py"
    spec = importlib.util.spec_from_file_location("property_fixture_contract", source)
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    try:
        contract.CrewContract.install_fixture()
        yield contract
        assert contract.database_state() == contract.CrewContract.before
    finally:
        contract.CrewContract.cleanup_fixture()


@settings(max_examples=int(os.getenv("SHOWCALL_FUZZ_EXAMPLES", "30")), derandomize=True, deadline=None,
          database=None)
@given(page=st.integers(min_value=-20, max_value=20), size=st.integers(min_value=-40, max_value=50),
       tenant=st.sampled_from([900071, 900072, 900073]))
def test_crew_pagination_and_tenant_boundary(controlled_crew, page, size, tenant):
    contract = controlled_crew
    url = os.environ["SHOWCALL_CONTRACT_URL"]
    with httpx.Client(base_url=url, timeout=10, follow_redirects=False) as client:
        response = client.get("/callboard/crew/list", params={"page": page, "per_page": size},
                              headers={"X-Org-Id": str(tenant)})
    assert response.status_code == 200, f"Backend {url} has no compatible crew list wrapper"
    payload = response.json()
    assert payload["result"] == "ok", payload
    ids = sorted(row["id"] for row in contract.fixtures() if row["org"] == tenant)
    # Preserve the observed clamping and Python slicing oddities, including
    # negative sizes and zero meaning "all", rather than imposing v3 bounds.
    effective_page = max(1, page)
    expected = ids[(effective_page-1)*size:effective_page*size] if size else ids
    assert payload["data"]["page"] == effective_page
    assert payload["data"]["total"] == len(ids)
    assert [row["crew_id"] for row in payload["data"]["crew"]] == expected
    assert all(row["org"] == tenant for row in payload["data"]["crew"])
    assert "password" not in response.text
    assert "DO-NOT-EXPOSE" not in response.text


@settings(max_examples=int(os.getenv("SHOWCALL_FUZZ_EXAMPLES", "30")), derandomize=True, deadline=None,
          database=None)
@given(index=st.integers(min_value=1, max_value=32),
       representation=st.sampled_from(["decimal", "padded", "signed", "hex", "octal", "binary", "underscore"]),
       tenant=st.sampled_from([900071, 900072, 900073]))
def test_documented_id_formats_preserve_exact_detail_response(controlled_crew, index, representation, tenant):
    """Apply observed unusual ID formats to every row, including null/Unicode data."""
    contract = controlled_crew
    crew_id = 910000+index
    value = {"decimal": str(crew_id), "padded": f"{crew_id:010d}", "signed": f"+{crew_id:010d}",
             "hex": hex(crew_id), "octal": oct(crew_id), "binary": bin(crew_id),
             "underscore": f"{crew_id:,}".replace(",", "_")}[representation]
    reference = json.loads(contract.GOLDEN.read_text())["cases"]
    name = f"show_fixture_{index:02}" if tenant == contract.ORG else "show_foreign_inverse"
    actual = contract.send(contract.request("/callboard/crew/show", org=tenant, query=[["crew_id", value]]))
    assert actual == reference[name]["response"], (tenant, representation, value)
