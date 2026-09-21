import subprocess

import pytest

from tools import tasks


def test_routine_commands_use_locked_uv_without_global_lookup(monkeypatch):
    def fail_global_lookup(name):
        raise AssertionError(f"global lookup should not run for {name}")

    monkeypatch.setattr(tasks, "platform", object())
    commands = {
        name: tasks.command_for(name)[0]
        for name in ("diagnostics", "test", "lint", "type-check")
    }

    assert all(command[:3] == ["uv", "run", "--locked"] for command in commands.values())
    assert commands["test"][-1] == "pytest"
    assert commands["lint"][-3:] == ["ruff", "check", "."]
    assert commands["type-check"][-4:] == ["mypy", "core", "apps", "tools"]


def test_windows_bootstrap_is_an_argument_array(monkeypatch):
    monkeypatch.setattr(tasks.platform, "system", lambda: "Windows")
    command, status = tasks.command_for("bootstrap")

    assert status == "available"
    assert command is not None
    assert command[:5] == [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
    ]
    assert command[-2:] == ["-File", str(tasks.ROOT / "scripts" / "bootstrap_windows.ps1")]


def test_unsupported_bootstrap_is_explicitly_deferred(monkeypatch):
    monkeypatch.setattr(tasks.platform, "system", lambda: "Linux")
    command, status = tasks.command_for("bootstrap")

    assert command is None
    assert status.startswith("deferred:")


@pytest.mark.parametrize("command_name", ["lint", "type-check"])
def test_quality_commands_fail_clearly_when_uv_missing(monkeypatch, capsys, command_name):
    def missing(*args, **kwargs):
        raise FileNotFoundError("uv")

    monkeypatch.setattr(tasks.subprocess, "run", missing)
    assert tasks.run([command_name]) == 2
    assert "unavailable" in capsys.readouterr().err


def test_test_command_fails_clearly_when_uv_missing(monkeypatch, capsys):
    def missing(*args, **kwargs):
        raise FileNotFoundError("uv")

    monkeypatch.setattr(tasks.subprocess, "run", missing)
    assert tasks.run(["test"]) == 2
    assert "unavailable" in capsys.readouterr().err


def test_child_exit_code_is_propagated(monkeypatch):
    observed = {}

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, 17)

    monkeypatch.setattr(tasks, "command_for", lambda name: (["uv", "run", "--locked", "pytest"], "pytest"))
    monkeypatch.setattr(tasks.subprocess, "run", fake_run)

    assert tasks.run(["test"]) == 17
    assert observed["kwargs"]["shell"] is False
    assert observed["kwargs"]["cwd"] == tasks.ROOT


def test_build_remains_deferred():
    command, status = tasks.command_for("build")

    assert command is None
    assert status.startswith("deferred:")


def test_unknown_command_is_rejected():
    with pytest.raises(ValueError):
        tasks.command_for("not-a-command")
