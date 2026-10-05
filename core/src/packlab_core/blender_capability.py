"""Offline Blender executable discovery and privacy-safe headless capability probe."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

BLENDER_SUPPORTED_MAJOR = 5
BLENDER_PROBE_TIMEOUT_SECONDS = 20.0
_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:\s|$)")
_MARKER = "PACKLAB_BLENDER_BUILD:"
_QUERY = (
    "import bpy,json; "
    "decode=lambda value: value.decode('utf-8','replace') if isinstance(value,bytes) else str(value); "
    "facts={'version':bpy.app.version_string,'build_hash':decode(bpy.app.build_hash),"
    "'build_branch':decode(bpy.app.build_branch),'build_date':decode(bpy.app.build_date)}; "
    "print('PACKLAB_BLENDER_BUILD:'+json.dumps(facts,sort_keys=True,separators=(',',':')))"
)


class BlenderCapabilityStatus(StrEnum):
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"
    INCOMPATIBLE = "INCOMPATIBLE"


class BlenderCapabilityError(ValueError):
    """Raised when probe configuration is invalid before process launch."""


@dataclass(frozen=True, slots=True)
class BlenderCapability:
    status: BlenderCapabilityStatus
    version: str | None
    build_hash: str | None
    build_branch: str | None
    build_date: str | None
    discovery_source: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        """Return capability facts only; executable paths and raw process output are excluded."""
        return asdict(self) | {"status": self.status.value}


def discover_blender(
    configured_path: str | os.PathLike[str] | None = None,
    *,
    timeout_seconds: float = BLENDER_PROBE_TIMEOUT_SECONDS,
    runner=subprocess.run,
    which=shutil.which,
    system: str = sys.platform,
    environ: dict[str, str] | None = None,
) -> BlenderCapability:
    """Find one Blender executable and query its version/build in offline headless mode.

    An explicit path is authoritative: an invalid configured path does not silently fall
    back to another installation. Automatic discovery checks PATH and fixed platform
    locations only; it never scans arbitrary drives or downloads software.
    """
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not 1.0 <= timeout_seconds <= 60.0
    ):
        raise BlenderCapabilityError("blender_probe_timeout_invalid")
    environment = os.environ if environ is None else environ
    selected = _select_executable(configured_path, which, system, environment)
    if selected is None:
        source = "configured" if configured_path is not None else "automatic"
        detail = (
            "configured_executable_not_found"
            if configured_path is not None
            else "executable_not_found"
        )
        return _result(BlenderCapabilityStatus.UNAVAILABLE, source, detail)
    path, source = selected
    if not path.is_file():
        return _result(BlenderCapabilityStatus.UNAVAILABLE, source, "executable_not_file")
    if not _looks_executable(path, system):
        return _result(BlenderCapabilityStatus.INCOMPATIBLE, source, "executable_not_runnable")

    command = [
        str(path),
        "--background",
        "--factory-startup",
        "--disable-autoexec",
        "--python-expr",
        _QUERY,
    ]
    try:
        completed = runner(
            command,
            capture_output=True,
            text=True,
            shell=False,
            timeout=float(timeout_seconds),
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _result(BlenderCapabilityStatus.INCOMPATIBLE, source, "headless_probe_timed_out")
    except OSError as error:
        detail = (
            "executable_permission_denied"
            if isinstance(error, PermissionError)
            else "executable_launch_failed"
        )
        return _result(BlenderCapabilityStatus.INCOMPATIBLE, source, detail)
    if completed.returncode != 0:
        return _result(BlenderCapabilityStatus.INCOMPATIBLE, source, "headless_probe_failed")

    facts = _parse_build_facts((completed.stdout or "") + "\n" + (completed.stderr or ""))
    if facts is None:
        return _result(
            BlenderCapabilityStatus.INCOMPATIBLE, source, "headless_version_output_invalid"
        )
    version, major, build_hash, build_branch, build_date = facts
    if major != BLENDER_SUPPORTED_MAJOR:
        return BlenderCapability(
            BlenderCapabilityStatus.INCOMPATIBLE,
            version,
            build_hash,
            build_branch,
            build_date,
            source,
            "supported_major_policy_mismatch",
        )
    return BlenderCapability(
        BlenderCapabilityStatus.READY,
        version,
        build_hash,
        build_branch,
        build_date,
        source,
        "headless_probe_passed",
    )


def _select_executable(
    configured_path: str | os.PathLike[str] | None,
    which,
    system: str,
    environ: Mapping[str, str],
) -> tuple[Path, str] | None:
    if configured_path is not None:
        try:
            configured = Path(configured_path).expanduser()
        except (TypeError, ValueError, OSError):
            return None
        if "\x00" in str(configured):
            return None
        if not configured.exists():
            return None
        return configured, "configured"

    command_path = which("blender")
    if command_path:
        return Path(command_path), "PATH"
    for candidate in _platform_candidates(system, environ):
        if candidate.is_file():
            return candidate, "platform-standard"
    return None


def _platform_candidates(system: str, environ: Mapping[str, str]) -> tuple[Path, ...]:
    if system == "win32":
        candidates: list[Path] = []
        for key in ("ProgramFiles", "ProgramFiles(x86)"):
            base = environ.get(key)
            if not base:
                continue
            install_root = Path(base) / "Blender Foundation"
            if not install_root.is_dir():
                continue
            try:
                folders = sorted(
                    (item for item in install_root.iterdir() if item.is_dir()),
                    key=lambda item: item.name,
                    reverse=True,
                )
            except OSError:
                continue
            candidates.extend(item / "blender.exe" for item in folders)
        return tuple(candidates)
    if system == "darwin":
        home = environ.get("HOME")
        candidates = [Path("/Applications/Blender.app/Contents/MacOS/Blender")]
        if home:
            candidates.append(Path(home) / "Applications/Blender.app/Contents/MacOS/Blender")
        return tuple(candidates)
    candidates = [
        Path("/usr/bin/blender"),
        Path("/usr/local/bin/blender"),
        Path("/snap/bin/blender"),
    ]
    home = environ.get("HOME")
    if home:
        candidates.append(Path(home) / ".local/bin/blender")
    return tuple(candidates)


def _looks_executable(path: Path, system: str) -> bool:
    if system == "win32":
        return path.suffix.lower() == ".exe"
    return os.access(path, os.X_OK)


def _parse_build_facts(
    output: str,
) -> tuple[str, int, str, str, str] | None:
    for line in output.splitlines():
        marker = line.find(_MARKER)
        if marker < 0:
            continue
        try:
            value = json.loads(line[marker + len(_MARKER) :])
        except json.JSONDecodeError:
            return None
        if not isinstance(value, dict) or set(value) != {
            "version",
            "build_hash",
            "build_branch",
            "build_date",
        }:
            return None
        version = value["version"]
        match = _VERSION.match(version) if isinstance(version, str) else None
        build_fields = tuple(value[name] for name in ("build_hash", "build_branch", "build_date"))
        if match is None or any(
            not isinstance(item, str)
            or not item
            or len(item) > 128
            or any(ord(c) < 32 for c in item)
            for item in build_fields
        ):
            return None
        return version, int(match.group(1)), build_fields[0], build_fields[1], build_fields[2]
    return None


def _result(status: BlenderCapabilityStatus, source: str, detail: str) -> BlenderCapability:
    return BlenderCapability(status, None, None, None, None, source, detail)


__all__ = [
    "BLENDER_PROBE_TIMEOUT_SECONDS",
    "BLENDER_SUPPORTED_MAJOR",
    "BlenderCapability",
    "BlenderCapabilityError",
    "BlenderCapabilityStatus",
    "discover_blender",
]
