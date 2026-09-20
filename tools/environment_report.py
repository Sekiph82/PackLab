"""Safe, machine-readable environment diagnostics for PackLab development."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

CommandRunner = Callable[[Sequence[str], float], dict[str, Any]]

TOOL_COMMANDS: dict[str, tuple[str, ...]] = {
    "python": (sys.executable, "--version"),
    "colmap": ("colmap", "--version"),
    "openmvs": ("DensifyPointCloud", "--version"),
    "blender": ("blender", "--version"),
    "nvidia_smi": (
        "nvidia-smi",
        "--query-gpu=name,memory.total",
        "--format=csv,noheader,nounits",
    ),
}


def _missing(message: str = "not found") -> dict[str, Any]:
    return {"status": "missing", "version": None, "detail": message}


def run_command(args: Sequence[str], timeout: float = 2.0) -> dict[str, Any]:
    """Run one executable without a shell and return a bounded diagnostic record."""

    executable = shutil.which(args[0]) if args else None
    if not executable:
        return _missing()
    try:
        completed = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "version": None, "detail": "probe timed out"}
    except OSError as exc:
        return {"status": "error", "version": None, "detail": type(exc).__name__}
    stdout = completed.stdout.strip().splitlines()
    stderr = completed.stderr.strip().splitlines()
    detail = (stdout or stderr or ["no output"])[0][:240]
    return {
        "status": "available" if completed.returncode == 0 else "error",
        "version": detail if completed.returncode == 0 else None,
        "detail": detail,
        "returncode": completed.returncode,
    }


def _memory_bytes() -> int | None:
    if hasattr(os, "sysconf"):
        try:
            return int(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
        except (ValueError, OSError):
            return None
    if platform.system() == "Windows":
        try:
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                            ("total", ctypes.c_ulonglong), ("available", ctypes.c_ulonglong),
                            ("pagefile", ctypes.c_ulonglong), ("available_pagefile", ctypes.c_ulonglong),
                            ("virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
                            ("available_extended", ctypes.c_ulonglong)]

            status = MemoryStatus()
            status.length = ctypes.sizeof(MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.total)
        except (AttributeError, OSError, TypeError):
            return None
    return None


def _gpu_probe(command_runner: CommandRunner) -> dict[str, Any]:
    result = command_runner(TOOL_COMMANDS["nvidia_smi"], 2.0)
    if result.get("status") == "available":
        adapters = []
        for line in str(result.get("version") or result.get("detail") or "").splitlines():
            name, _, memory = line.partition(",")
            adapters.append({"name": name.strip()[:120], "reported_memory": memory.strip()[:40]})
        return {"adapters": adapters, "cuda": {"status": "available", "provenance": "nvidia-smi"}}
    return {"adapters": [], "cuda": {"status": "unknown", "provenance": "nvidia-smi probe unavailable"}}


def collect_report(command_runner: CommandRunner = run_command) -> dict[str, Any]:
    """Collect diagnostics without exposing usernames, home paths, or identifiers."""

    tools = {
        name: command_runner(command, 2.0)
        for name, command in TOOL_COMMANDS.items()
        if name != "python"
    }
    tools["python"] = {
        "status": "available",
        "version": platform.python_version(),
        "detail": platform.python_implementation(),
    }
    return {
        "schema": "packlab.environment-report.v1",
        "os": {"name": platform.system(), "release": platform.release(), "architecture": platform.machine()},
        "cpu": {
            "logical_cores": os.cpu_count(),
            "physical_cores": None,
            "note": "physical core count is omitted unless safely available without extra dependencies",
        },
        "memory": {"total_bytes": _memory_bytes()},
        "gpu": _gpu_probe(command_runner),
        "python": tools.pop("python"),
        "external_tools": tools,
        "privacy": {"identifiers": "omitted", "paths": "omitted", "credentials": "omitted"},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a redacted PackLab environment report as JSON.")
    parser.add_argument("--pretty", action="store_true", help="indent JSON for human reading")
    args = parser.parse_args()
    report = collect_report()
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
