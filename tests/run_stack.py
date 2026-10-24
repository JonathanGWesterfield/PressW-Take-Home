"""Bounded readiness, then established pytest execution inside the test network."""
import os
from pathlib import Path
import subprocess
import sys
import time

import httpx
import psycopg


def wait_ready(timeout=60):
    deadline = time.monotonic() + timeout
    urls = [(os.environ["LEGACY_URL"] + "/callboard/crew/list", {"X-Org-Id": "3"}),
            (os.environ["ENCORE_URL"] + "/healthz", {}),
            (os.environ["GATEWAY_URL"] + "/gateway/healthz", {})]
    last = "not attempted"
    while time.monotonic() < deadline:
        try:
            with psycopg.connect(os.environ["SHOWCALL_DATABASE_URL"], connect_timeout=2) as connection:
                connection.execute("SELECT 1").fetchone()
            with httpx.Client(timeout=2, follow_redirects=False) as client:
                for url, headers in urls:
                    response = client.get(url, headers=headers)
                    response.raise_for_status()
            return
        except (httpx.HTTPError, psycopg.Error) as exc:
            last = str(exc)
            time.sleep(0.5)
    raise RuntimeError(f"Database/HTTP readiness timed out after {timeout}s: {last}")


def pytest_command(extra_args: list[str]) -> list[str]:
    """Name the test root so its conftest registers runner-specific options."""
    tests = ["tests"]
    if os.environ["SHOWCALL_BACKEND"] == "gateway":
        # Gateway ingress has an independently observed oracle.  The frozen
        # direct-backend corpus still runs in the legacy/Encore matrix.
        tests = [
            "tests/unit",
            "tests/e2e/test_gateway_ingress.py",
            "tests/e2e/test_smoke.py",
            "tests/e2e/test_v3_crew_e2e.py",
        ]
    return [
        sys.executable,
        "-m",
        "pytest",
        "--e2e",
        "--run-writes",
        "--backend",
        os.environ["SHOWCALL_BACKEND"],
        "--maxfail=1",
        "--junitxml=/reports/junit.xml",
        "-p",
        "no:cacheprovider",
        *tests,
        *extra_args,
    ]


if __name__ == "__main__":
    try:
        wait_ready()
    except RuntimeError as exc:
        Path("/reports/readiness-error.txt").write_text(str(exc) + "\n")
        raise
    sys.exit(subprocess.call(pytest_command(sys.argv[1:])))
