"""Routing decisions need no legacy binary or network traffic."""
import importlib.util
import os
from pathlib import Path

import pytest
from starlette.requests import Request


@pytest.fixture
def gateway(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[2] / "proxy" / "app.py"
    spec = importlib.util.spec_from_file_location("gateway_under_test", source)
    module = importlib.util.module_from_spec(spec)
    # Loading proxy/app.py creates an AsyncClient; substitute a non-network stub.
    monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: None)
    spec.loader.exec_module(module)
    routes = tmp_path / "routes.yaml"
    routes.write_text('''routes:
  /callboard/:
    default: callboard
  /callboard/crew/list:
    default: callboard
    orgs:
      7: encore
  /callboard/crew/show:
    default: callboard
    orgs:
      "7": encore
''')
    module.ROUTES_FILE = routes
    return module


@pytest.mark.parametrize("path,org,expected", [
    ("/callboard/crew/list", "7", "encore"),
    ("/callboard/crew/list", "3", "callboard"),
    ("/callboard/crew/list", "07", "callboard"),
    ("/callboard/crew/list", " 7 ", "callboard"),
    ("/callboard/crew/list", "+7", "callboard"),
    ("/callboard/crew/list", None, "callboard"),
    ("/callboard/crew/show", "7", "encore"),
    ("/callboard/crew/show", "3", "callboard"),
    ("/callboard/crew/show", "07", "callboard"),
    ("/callboard/crew/show/extra", "7", "encore"),
    ("/callboard/crew/update", "7", "callboard"),
    ("/unknown", "7", "callboard"),
    # Prefix matching also catches suffixes; endpoint-only routes are not exact.
    ("/callboard/crew/list/extra", "7", "encore"),
])
def test_longest_prefix_and_org_routing(gateway, path, org, expected):
    assert gateway.pick_backend(path, org) == expected


def test_atomic_route_rename_takes_effect_without_restart(gateway, tmp_path):
    for path in ("/callboard/crew/list", "/callboard/crew/show"):
        assert gateway.pick_backend(path, "7") == "encore"
    replacement = tmp_path / "replacement.yaml"
    replacement.write_text("routes: {}\n")
    os.replace(replacement, gateway.ROUTES_FILE)
    for path in ("/callboard/crew/list", "/callboard/crew/show"):
        assert gateway.pick_backend(path, "7") == "callboard"


def test_duplicate_org_headers_keep_first_for_routing(gateway):
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/callboard/crew/list",
            "headers": [(b"x-org-id", b"7"), (b"x-org-id", b"3")],
        }
    )

    assert gateway.routing_org(request) == "7"
