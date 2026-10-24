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
    routes = yaml.safe_load((ROOT / "tests/routes.yaml").read_text())
    assert routes["routes"]["/callboard/crew/"]["default"] == "encore"
