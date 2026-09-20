"""Thin cross-platform entry point for PackLab developer commands."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _python(*args: str) -> list[str]:
    return [sys.executable, *args]


def command_for(name: str) -> tuple[list[str] | None, str]:
    if name == "diagnostics":
        return _python(str(ROOT / "tools" / "environment_report.py"), "--pretty"), "available"
    if name == "test":
        return _python("-m", "pytest"), "pytest"
    if name == "lint":
        return (["ruff", "check", "."] if shutil.which("ruff") else None), "ruff"
    if name == "type-check":
        return (["mypy", "core", "apps", "tools"] if shutil.which("mypy") else None), "mypy"
    if name == "bootstrap":
        script = ROOT / "scripts" / "bootstrap_windows.ps1"
        return (
            (None, "deferred: scripts/bootstrap_windows.ps1 is not implemented")
            if not script.exists()
            else (None, "PowerShell bootstrap must be invoked explicitly")
        )
    if name == "build":
        return None, "deferred: platform build commands are not implemented in M01"
    raise ValueError(f"unknown command: {name}")


def run(args: Sequence[str]) -> int:
    command = args[0]
    if command in {"help", "list"}:
        print("commands: bootstrap, test, lint, type-check, diagnostics, build")
        return 0
    argv, status = command_for(command)
    if argv is None:
        print(f"{command}: {status}", file=sys.stderr)
        return 2
    print(f"running {command}: {' '.join(argv)}")
    completed = subprocess.run(argv, cwd=ROOT, check=False, shell=False)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run PackLab developer commands without shell-string execution."
    )
    parser.add_argument("command", nargs="?", default="help")
    parsed = parser.parse_args()
    try:
        return run([parsed.command])
    except ValueError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
