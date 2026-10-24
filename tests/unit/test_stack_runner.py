"""Regression tests for the isolated stack's pytest invocation."""
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
loader = SourceFileLoader("stack_runner", str(ROOT / "tests/run_stack.py"))
spec = spec_from_loader(loader.name, loader)
stack_runner = module_from_spec(spec)
loader.exec_module(stack_runner)


def test_pytest_command_names_the_test_root(monkeypatch):
    monkeypatch.setenv("SHOWCALL_BACKEND", "encore")
    command = stack_runner.pytest_command(["--maxfail=0"])

    assert command[0:3] == [stack_runner.sys.executable, "-m", "pytest"]
    assert command[command.index("--backend") + 1] == "encore"
    assert "tests" in command
    assert command.index("tests") < command.index("--maxfail=0")


def test_gateway_command_uses_boundary_aware_suite(monkeypatch):
    monkeypatch.setenv("SHOWCALL_BACKEND", "gateway")

    command = stack_runner.pytest_command([])

    assert "tests" not in command
    assert "tests/unit" in command
    assert "tests/e2e/test_gateway_ingress.py" in command
    assert "tests/characterization" not in command
