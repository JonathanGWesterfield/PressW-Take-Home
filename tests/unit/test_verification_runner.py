"""Exercise ownership and exit semantics without starting containers."""
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
loader = SourceFileLoader("verify_runner", str(ROOT / "scripts/verify"))
spec = spec_from_loader(loader.name, loader)
verify = module_from_spec(spec)
loader.exec_module(verify)


@pytest.mark.parametrize("test_exit,cleanup_exit,expected", [(0, 0, 0), (7, 0, 7), (7, 1, 7), (0, 1, 1)])
def test_exit_and_owned_cleanup(tmp_path, test_exit, cleanup_exit, expected):
    calls = []
    def runner(command, **kwargs):
        calls.append((command, kwargs))
        result = test_exit if "run" in command else cleanup_exit if "down" in command else 0
        return subprocess.CompletedProcess(command, result)
    assert verify.run_verification("legacy", runner=runner, report_root=tmp_path) == expected
    projects = {command[command.index("-p")+1] for command, _ in calls}
    assert len(projects) == 1
    assert next(iter(projects)).startswith("showcall-verify-")
    assert all(command[3] == str(ROOT / "tests/compose.yml") for command, _ in calls)
    assert "down" in calls[-1][0]
    assert "--volumes" in calls[-1][0]
    assert next(tmp_path.glob("*/exit-code.txt")).read_text().strip() == str(expected)


@pytest.mark.parametrize("failure", [subprocess.CalledProcessError(9, "up"),
                                    subprocess.TimeoutExpired("up", 1), KeyboardInterrupt()])
def test_startup_failure_and_interruption_still_clean_up(tmp_path, failure):
    calls = []
    def runner(command, **kwargs):
        calls.append(command)
        if "up" in command:
            raise failure
        return subprocess.CompletedProcess(command, 0)
    if isinstance(failure, KeyboardInterrupt):
        assert verify.run_verification("legacy", runner=runner, report_root=tmp_path) == 130
        assert next(tmp_path.glob("*/exit-code.txt")).read_text() == "130\n"
    else:
        assert verify.run_verification("legacy", runner=runner, report_root=tmp_path) != 0
    assert "logs" in calls[-2]
    assert "down" in calls[-1]


def test_topology_does_not_publish_ports_or_mount_dev_database():
    services = yaml.safe_load((ROOT / "tests/compose.yml").read_text())["services"]
    assert not any(service.get("ports") for service in services.values())
    assert services["db"]["tmpfs"] == ["/var/lib/postgresql/data"]
    assert all(".venv" not in str(service.get("volumes", [])) for service in services.values())
    assert services["gateway"]["environment"]["ROUTES_FILE"] == "/srv/routes/routes.yaml"
    assert "route_state:/srv/routes:ro" in services["gateway"]["volumes"]
    assert "route_state:/routes" in services["tests"]["volumes"]


def test_mixed_route_fixture_only_migrates_org7_crew_reads():
    routes = yaml.safe_load((ROOT / "tests/routes/mixed-org7.yaml").read_text())["routes"]

    assert routes["/callboard/"] == {"default": "callboard"}
    assert routes["/callboard/crew/list"] == {
        "default": "callboard", "orgs": {"7": "encore"},
    }
    assert routes["/callboard/crew/show"] == {
        "default": "callboard", "orgs": {"7": "encore"},
    }
    assert set(routes) == {"/callboard/", "/callboard/crew/list", "/callboard/crew/show"}


def test_development_gateway_uses_read_only_route_directory():
    services = yaml.safe_load((ROOT / "docker-compose.yml").read_text())["services"]
    gateway = services["gateway"]

    assert gateway["environment"]["ROUTES_FILE"] == "/srv/routes/routes.yaml"
    assert "./proxy:/srv/routes:ro" in gateway["volumes"]


@pytest.mark.parametrize("statuses,expected", [((0, 0), 0), ((7, 0), 7), ((0, 8), 8), ((7, 8), 7)])
def test_both_targets_run_in_order_with_identical_test_arguments(statuses, expected):
    calls = []
    options = ["--maxfail=0", "-m", "characterization"]
    def verifier(backend, pytest_args):
        calls.append((backend, pytest_args))
        return statuses[len(calls)-1]
    assert verify.run_targets(("legacy", "encore"), options, verifier=verifier) == expected
    assert calls == [("legacy", options), ("encore", options)]


def test_both_targets_stop_after_interruption():
    calls = []
    def verifier(backend, pytest_args):
        calls.append(backend)
        return 130
    assert verify.run_targets(("legacy", "encore"), verifier=verifier) == 130
    assert calls == ["legacy"]


def test_both_targets_use_different_owned_projects_and_databases(tmp_path):
    runs = []
    def runner(command, **kwargs):
        if "run" in command:
            runs.append((command[command.index("-p")+1], kwargs["env"]["SHOWCALL_BACKEND"]))
        return subprocess.CompletedProcess(command, 0)
    def verifier(backend, pytest_args):
        return verify.run_verification(backend, pytest_args, runner=runner, report_root=tmp_path)
    assert verify.run_targets(("legacy", "encore"), verifier=verifier) == 0
    assert [backend for _, backend in runs] == ["legacy", "encore"]
    assert runs[0][0] != runs[1][0]
    assert len(list(tmp_path.glob("*/exit-code.txt"))) == 2


def test_both_cli_runs_the_complete_identical_suite(monkeypatch):
    calls = []
    monkeypatch.setattr(verify.sys, "argv", ["verify", "--backend", "both", "--", "-m", "characterization"])
    monkeypatch.setattr(verify.signal, "signal", lambda *args: None)
    def run_targets(backends, pytest_args):
        calls.append((backends, pytest_args))
        return 9
    monkeypatch.setattr(verify, "run_targets", run_targets)
    assert verify.main() == 9
    assert calls == [(("legacy", "encore"), ["--maxfail=0", "-m", "characterization"])]
