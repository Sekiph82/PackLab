"""Explicit-path-first configuration and safe discovery for reconstruction engines."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class DiscoveryStatus(StrEnum):
    CONFIGURED = "configured"
    PATH = "path"
    MISSING = "missing"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class EnginePathDiagnostic:
    engine_id: str
    executable: Path | None
    source: str
    status: DiscoveryStatus
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {
            "engine_id": self.engine_id,
            "executable": None if self.executable is None else str(self.executable),
            "source": self.source,
            "status": self.status.value,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class EngineConfiguration:
    colmap_path: Path | None = None
    openmvs_root: Path | None = None
    openmvs_paths: Mapping[str, Path] = field(default_factory=dict)
    allow_path_lookup: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "colmap_path", None if self.colmap_path is None else Path(self.colmap_path))
        object.__setattr__(self, "openmvs_root", None if self.openmvs_root is None else Path(self.openmvs_root))
        object.__setattr__(self, "openmvs_paths", {key: Path(value) for key, value in self.openmvs_paths.items()})


@dataclass(frozen=True, slots=True)
class EngineDiscoveryReport:
    records: tuple[EnginePathDiagnostic, ...]

    def for_engine(self, engine_id: str) -> EnginePathDiagnostic:
        return next(record for record in self.records if record.engine_id == engine_id)

    def as_dict(self) -> dict[str, object]:
        return {"engines": [record.as_dict() for record in self.records]}


_OPENMVS_EXECUTABLES = {
    "interface_colmap": "InterfaceCOLMAP",
    "densify_point_cloud": "DensifyPointCloud",
    "reconstruct_mesh": "ReconstructMesh",
    "refine_mesh": "RefineMesh",
    "texture_mesh": "TextureMesh",
}
PathLookup = Callable[[str], str | None]


def _windows_executable(name: str) -> str:
    return name + ".exe" if os.name == "nt" else name


def _record(engine_id: str, value: str | Path | None, source: str) -> EnginePathDiagnostic:
    if value is None:
        return EnginePathDiagnostic(engine_id, None, source, DiscoveryStatus.MISSING, "no executable found")
    path = Path(value)
    if not path.exists():
        return EnginePathDiagnostic(engine_id, path, source, DiscoveryStatus.MISSING, "configured executable does not exist")
    if not path.is_file():
        return EnginePathDiagnostic(engine_id, path, source, DiscoveryStatus.INVALID, "configured executable path is not a file")
    if os.name != "nt" and not os.access(path, os.X_OK):
        return EnginePathDiagnostic(engine_id, path, source, DiscoveryStatus.INVALID, "configured executable is not executable")
    return EnginePathDiagnostic(engine_id, path, source, DiscoveryStatus.CONFIGURED if source != "PATH" else DiscoveryStatus.PATH, "executable path is usable")


def _resolve(
    engine_id: str,
    explicit: str | Path | None,
    environment_value: str | None,
    command: str,
    *,
    allow_path_lookup: bool,
    which: PathLookup,
) -> EnginePathDiagnostic:
    if explicit is not None:
        return _record(engine_id, explicit, "explicit")
    if environment_value:
        return _record(engine_id, environment_value, "environment")
    if allow_path_lookup:
        located = which(command)
        return _record(engine_id, located, "PATH")
    return _record(engine_id, None, "disabled")


def discover_engines(
    configuration: EngineConfiguration | None = None,
    *,
    environment: Mapping[str, str] | None = None,
    which: PathLookup = shutil.which,
) -> EngineDiscoveryReport:
    """Discover only the known executables, preferring explicit paths and never installing."""

    config = configuration or EngineConfiguration()
    env = os.environ if environment is None else environment
    colmap = _resolve(
        "colmap",
        config.colmap_path,
        env.get("PACKLAB_COLMAP_PATH"),
        _windows_executable("colmap"),
        allow_path_lookup=config.allow_path_lookup,
        which=which,
    )
    records = [colmap]
    for key, name in _OPENMVS_EXECUTABLES.items():
        explicit = config.openmvs_paths.get(key)
        if explicit is None and config.openmvs_root is not None:
            explicit = config.openmvs_root / _windows_executable(name)
        env_key = f"PACKLAB_OPENMVS_{key.upper()}_PATH"
        environment_value = env.get(env_key)
        if explicit is None and environment_value is None and env.get("PACKLAB_OPENMVS_ROOT"):
            explicit = Path(env["PACKLAB_OPENMVS_ROOT"]) / _windows_executable(name)
        records.append(
            _resolve(
                f"openmvs.{key}",
                explicit,
                environment_value,
                _windows_executable(name),
                allow_path_lookup=config.allow_path_lookup,
                which=which,
            )
        )
    return EngineDiscoveryReport(tuple(records))
