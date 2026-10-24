"""Shared runner options. No stack startup, resets, or recordings happen here."""
import os
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    group = parser.getgroup("showcall")
    group.addoption("--e2e", action="store_true", help="Enable tests against live services")
    group.addoption("--run-writes", action="store_true", help="Allow mutates_db tests (requires --e2e)")
    group.addoption("--backend", choices=("legacy", "encore", "gateway"),
                    default=os.getenv("SHOWCALL_BACKEND", "legacy"), help="Backend for shared frozen contracts")
    for name, port in (("legacy", 8091), ("gateway", 8080), ("encore", 8092)):
        group.addoption(f"--{name}-url", default=os.getenv(f"{name.upper()}_URL", f"http://localhost:{port}"))


def pytest_configure(config):
    if config.getoption("--run-writes") and not config.getoption("--e2e"):
        raise pytest.UsageError("--run-writes requires --e2e")
    # Set before collection imports the standalone unittest adapter.
    backend = config.getoption("--backend")
    os.environ["SHOWCALL_CONTRACT_URL"] = config.getoption(f"--{backend}-url")


def pytest_collection_modifyitems(config, items):
    for item in items:
        relative = Path(item.path).relative_to(ROOT)
        if "characterization" in relative.parts:
            item.add_marker(pytest.mark.characterization)
            item.add_marker(pytest.mark.e2e)
            # Existing unittest fixture inserts/updates/deletes reserved crew rows.
            item.add_marker(pytest.mark.mutates_db)
        elif "e2e" in relative.parts:
            item.add_marker(pytest.mark.e2e)
        elif "unit" in relative.parts:
            item.add_marker(pytest.mark.unit)
        if "e2e" in item.keywords and not config.getoption("--e2e"):
            item.add_marker(pytest.mark.skip(reason="Live services require --e2e"))
        if "mutates_db" in item.keywords and not config.getoption("--run-writes"):
            item.add_marker(pytest.mark.skip(reason="Database writes require --run-writes"))


@pytest.fixture
def legacy_client(pytestconfig):
    with httpx.Client(base_url=pytestconfig.getoption("--legacy-url"), timeout=15, follow_redirects=False) as client:
        yield client


@pytest.fixture
def gateway_client(pytestconfig):
    with httpx.Client(base_url=pytestconfig.getoption("--gateway-url"), timeout=15, follow_redirects=False) as client:
        yield client


@pytest.fixture
def encore_client(pytestconfig):
    with httpx.Client(base_url=pytestconfig.getoption("--encore-url"), timeout=15, follow_redirects=False) as client:
        yield client
