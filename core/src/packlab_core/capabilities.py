"""Explicit optional-engine capability discovery with conservative states."""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class CapabilityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProbeResult:
    status: str
    output: str = ""
    detail: str = ""


@dataclass(frozen=True)
class Capability:
    name: str
    status: CapabilityStatus
    version: str | None
    provenance: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self) | {"status": self.status.value}


Probe = Callable[[Sequence[str]], ProbeResult]
_VERSION = re.compile(r"\b\d+(?:\.\d+){1,3}\b")
COMMANDS: dict[str, tuple[str, ...] | None] = {
    "nvidia_driver": ("nvidia-smi", "--version"),
    "cuda": ("nvcc", "--version"),
    "colmap": ("colmap", "version"),
    "openmvs": ("DensifyPointCloud", "--version"),
    "blender": ("blender", "--version"),
    "opencascade": None,
}


def default_probe(args: Sequence[str]) -> ProbeResult:
    if not args or not shutil.which(args[0]):
        return ProbeResult("missing", detail="executable not found")
    try:
        completed = subprocess.run(
            list(args), capture_output=True, text=True, check=False, shell=False, timeout=2
        )
    except subprocess.TimeoutExpired:
        return ProbeResult("error", detail="probe timed out")
    except OSError as exc:
        return ProbeResult("error", detail=type(exc).__name__)
    return ProbeResult(
        "ok" if completed.returncode == 0 else "error",
        output=(completed.stdout or completed.stderr).strip()[:240],
        detail=f"exit code {completed.returncode}",
    )


def _record(name: str, result: ProbeResult, provenance: str) -> Capability:
    if result.status == "missing":
        return Capability(name, CapabilityStatus.UNAVAILABLE, None, provenance, result.detail)
    if result.status != "ok":
        return Capability(
            name, CapabilityStatus.UNKNOWN, None, provenance, result.detail or "probe failed"
        )
    match = _VERSION.search(result.output)
    if not match:
        return Capability(
            name, CapabilityStatus.UNKNOWN, None, provenance, "probe returned no parseable version"
        )
    return Capability(name, CapabilityStatus.AVAILABLE, match.group(0), provenance, result.detail)


def _record_cuda(result: ProbeResult) -> Capability:
    provenance = "direct CUDA toolkit probe: nvcc --version"
    if result.status == "missing":
        return Capability("cuda", CapabilityStatus.UNAVAILABLE, None, provenance, result.detail)
    if result.status != "ok":
        return Capability("cuda", CapabilityStatus.UNKNOWN, None, provenance, result.detail)
    output = result.output.lower()
    if "cuda compilation tools" not in output and "cuda toolkit" not in output:
        return Capability(
            "cuda",
            CapabilityStatus.UNKNOWN,
            None,
            provenance,
            "probe output did not identify the CUDA toolkit",
        )
    match = _VERSION.search(result.output)
    if not match:
        return Capability("cuda", CapabilityStatus.UNKNOWN, None, provenance, "no CUDA version found")
    return Capability("cuda", CapabilityStatus.AVAILABLE, match.group(0), provenance, result.detail)


def discover_capabilities(probe: Probe = default_probe) -> dict[str, Capability]:
    """Discover optional executables without inferring capabilities from hardware labels."""

    records: dict[str, Capability] = {}
    for name, command in COMMANDS.items():
        if command is None:
            records[name] = Capability(
                name,
                CapabilityStatus.UNKNOWN,
                None,
                "Python OpenCascade binding deliberately not selected; PL-0289 owns the decision",
                "no executable probe configured",
            )
        else:
            result = probe(command)
            records[name] = (
                _record_cuda(result)
                if name == "cuda"
                else _record(name, result, f"executable probe: {command[0]}")
            )
    return records
