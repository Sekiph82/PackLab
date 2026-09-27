"""Deterministic, non-destructive external-engine capability probes."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

from .engine_baseline import COLMAP_BASELINE, OPENMVS_BASELINE


class EngineProbeStatus(StrEnum):
    CONFIGURED = "configured"
    MISSING = "missing"
    UNEXECUTABLE = "unexecutable"
    INVALID = "invalid"
    UNSUPPORTED = "unsupported"
    VALID = "valid"


class EngineId(StrEnum):
    COLMAP = "colmap"
    OPENMVS = "openmvs"


@dataclass(frozen=True, slots=True, order=True)
class EngineVersion:
    major: int
    minor: int
    patch: int

    @property
    def text(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True, slots=True)
class EngineProbeResult:
    engine_id: str
    executable: str | None
    status: EngineProbeStatus
    version: EngineVersion | None
    detail: str
    output: str = ""
    configured: bool = False

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["status"] = self.status.value
        value["version"] = None if self.version is None else self.version.text
        return value


VersionParser = Callable[[str], EngineVersion | None]
VersionRunner = Callable[[Path], tuple[int, str, str]]

_VERSION = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)")


def _parse_version(pattern: re.Pattern[str], output: str) -> EngineVersion | None:
    match = pattern.search(output)
    if match is None:
        return None
    return EngineVersion(*(int(group) for group in match.groups()))


def parse_colmap_version(output: str) -> EngineVersion | None:
    """Parse only a version attached to a COLMAP identity line."""

    match = re.search(r"(?i)\bCOLMAP\s+(?:version\s+)?" + _VERSION.pattern, output)
    if match is None:
        return None
    return EngineVersion(*(int(group) for group in match.groups()))


def parse_openmvs_version(output: str) -> EngineVersion | None:
    """Parse the OpenMVS application banner, including the Windows x64 form."""

    match = re.search(r"(?i)\bOpenMVS(?:\s+x64)?\s+v?" + _VERSION.pattern, output)
    if match is None:
        return None
    return EngineVersion(*(int(group) for group in match.groups()))


def _default_runner(executable: Path) -> tuple[int, str, str]:
    completed = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        text=True,
        check=False,
        shell=False,
        timeout=2.0,
    )
    return completed.returncode, (completed.stdout or "")[:4096], (completed.stderr or "")[:4096]


def _resolve_executable(value: str | Path) -> Path | None:
    candidate = Path(value)
    if candidate.exists():
        return candidate
    located = shutil.which(str(value))
    return None if located is None else Path(located)


def probe_engine(
    engine_id: EngineId | str,
    executable: str | Path | None,
    parser: VersionParser,
    *,
    supported_versions: Sequence[str],
    runner: VersionRunner = _default_runner,
) -> EngineProbeResult:
    """Probe one configured executable without installing, downloading or mutating it."""

    name = str(engine_id)
    if executable is None or not str(executable).strip():
        return EngineProbeResult(name, None, EngineProbeStatus.MISSING, None, "no executable configured")
    configured = True
    path = _resolve_executable(executable)
    if path is None:
        return EngineProbeResult(
            name, str(executable), EngineProbeStatus.MISSING, None, "configured executable was not found", configured=configured
        )
    if not path.is_file() or (os.name != "nt" and not os.access(path, os.X_OK)):
        return EngineProbeResult(
            name, str(path), EngineProbeStatus.UNEXECUTABLE, None, "configured path is not executable", configured=configured
        )
    try:
        returncode, stdout, stderr = runner(path)
    except (OSError, subprocess.SubprocessError) as error:
        return EngineProbeResult(
            name, str(path), EngineProbeStatus.UNEXECUTABLE, None, f"version probe failed: {type(error).__name__}", configured=configured
        )
    output = (stdout + "\n" + stderr).strip()[:4096]
    if returncode != 0:
        return EngineProbeResult(
            name, str(path), EngineProbeStatus.UNEXECUTABLE, None, f"version probe exited {returncode}", output, configured
        )
    version = parser(output)
    if version is None:
        return EngineProbeResult(name, str(path), EngineProbeStatus.INVALID, None, "version banner was not parseable", output, configured)
    if version.text not in set(supported_versions):
        return EngineProbeResult(name, str(path), EngineProbeStatus.UNSUPPORTED, version, "version is outside the selected baseline", output, configured)
    return EngineProbeResult(name, str(path), EngineProbeStatus.VALID, version, "version matches the selected baseline", output, configured)


def probe_colmap(
    executable: str | Path | None,
    *,
    runner: VersionRunner = _default_runner,
) -> EngineProbeResult:
    return probe_engine(
        EngineId.COLMAP,
        executable,
        parse_colmap_version,
        supported_versions=(COLMAP_BASELINE.version,),
        runner=runner,
    )


def probe_openmvs(
    executable: str | Path | None,
    *,
    runner: VersionRunner = _default_runner,
) -> EngineProbeResult:
    return probe_engine(
        EngineId.OPENMVS,
        executable,
        parse_openmvs_version,
        supported_versions=(OPENMVS_BASELINE.version,),
        runner=runner,
    )
