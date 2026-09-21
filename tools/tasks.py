"""Thin cross-platform entry point for PackLab developer commands."""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _python(*args: str) -> list[str]:
    return [sys.executable, *args]


def _uv(*args: str) -> list[str]:
    return ["uv", "run", "--locked", *args]


def command_for(name: str) -> tuple[list[str] | None, str]:
    if name == "diagnostics":
        return _uv("python", str(ROOT / "tools" / "environment_report.py"), "--pretty"), "available"
    if name == "test":
        return _uv("pytest"), "pytest"
    if name == "lint":
        return _uv("ruff", "check", "."), "ruff"
    if name == "type-check":
        return _uv("mypy", "core", "apps", "tools"), "mypy"
    if name == "bootstrap":
        script = ROOT / "scripts" / "bootstrap_windows.ps1"
        if platform.system() != "Windows":
            return None, "deferred: Windows bootstrap is unavailable on this platform"
        if not script.exists():
            return None, "deferred: scripts/bootstrap_windows.ps1 is missing"
        return (
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ],
            "available",
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
    try:
        completed = subprocess.run(argv, cwd=ROOT, check=False, shell=False)
    except FileNotFoundError:
        print(f"{command}: required executable is unavailable: {argv[0]}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"{command}: unable to start {argv[0]} ({type(exc).__name__})", file=sys.stderr)
        return 2
    return int(completed.returncode)


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
