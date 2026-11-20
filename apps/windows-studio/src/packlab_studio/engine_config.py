"""Explicit-path-first configuration and safe discovery for reconstruction engines."""

from __future__ import annotations

import os
import shutil
import sys
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
        object.__setattr__(
            self, "colmap_path", None if self.colmap_path is None else Path(self.colmap_path)
        )
        object.__setattr__(
            self, "openmvs_root", None if self.openmvs_root is None else Path(self.openmvs_root)
        )
        object.__setattr__(
            self, "openmvs_paths", {key: Path(value) for key, value in self.openmvs_paths.items()}
        )


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
_COLMAP_BUNDLED = Path("colmap") / "bin"
_OPENMVS_BUNDLED = Path("openmvs")


def default_bundled_engine_roots() -> tuple[Path, ...]:
    """`engines/` folders PackLab ships or stages beside the application.

    Frozen build: beside PackLabStudio.exe. Source/OwnerDev runtime: beside the
    runtime root, plus the shared `OwnerDev/engines` when the root is an OwnerDev
    runtime (identified by its `owner-dev-runtime.json`).
    """

    if getattr(sys, "frozen", False):
        return (Path(sys.executable).resolve().parent / "engines",)
    runtime_root = Path(__file__).resolve().parents[4]
    roots = [runtime_root / "engines"]
    if (runtime_root / "owner-dev-runtime.json").is_file():
        roots.append(runtime_root.parent / "engines")
    return tuple(roots)


def _bundled(roots: tuple[Path, ...], relative: Path) -> Path | None:
    return next((root / relative for root in roots if (root / relative).is_file()), None)


def _windows_executable(name: str) -> str:
    return name + ".exe" if os.name == "nt" else name


def _record(engine_id: str, value: str | Path | None, source: str) -> EnginePathDiagnostic:
    if value is None:
        return EnginePathDiagnostic(
            engine_id, None, source, DiscoveryStatus.MISSING, "no executable found"
        )
    path = Path(value)
    if not path.exists():
        return EnginePathDiagnostic(
            engine_id, path, source, DiscoveryStatus.MISSING, "configured executable does not exist"
        )
    if not path.is_file():
        return EnginePathDiagnostic(
            engine_id,
            path,
            source,
            DiscoveryStatus.INVALID,
            "configured executable path is not a file",
        )
    if os.name != "nt" and not os.access(path, os.X_OK):
        return EnginePathDiagnostic(
            engine_id,
            path,
            source,
            DiscoveryStatus.INVALID,
            "configured executable is not executable",
        )
    return EnginePathDiagnostic(
        engine_id,
        path,
        source,
        DiscoveryStatus.CONFIGURED if source != "PATH" else DiscoveryStatus.PATH,
        "executable path is usable",
    )


def _resolve(
    engine_id: str,
    explicit: str | Path | None,
    environment_value: str | None,
    command: str,
    *,
    bundled: Path | None,
    allow_path_lookup: bool,
    which: PathLookup,
) -> EnginePathDiagnostic:
    if explicit is not None:
        return _record(engine_id, explicit, "explicit")
    if environment_value:
        return _record(engine_id, environment_value, "environment")
    if bundled is not None:
        return _record(engine_id, bundled, "bundled")
    if allow_path_lookup:
        located = which(command)
        return _record(engine_id, located, "PATH")
    return _record(engine_id, None, "disabled")


def discover_engines(
    configuration: EngineConfiguration | None = None,
    *,
    environment: Mapping[str, str] | None = None,
    which: PathLookup = shutil.which,
    bundled_roots: tuple[Path, ...] | None = None,
) -> EngineDiscoveryReport:
    """Discover only the known executables and never install anything.

    Precedence: explicit configuration, environment, PackLab-bundled `engines/`, PATH.
    """

    config = configuration or EngineConfiguration()
    env = os.environ if environment is None else environment
    roots = default_bundled_engine_roots() if bundled_roots is None else bundled_roots
    colmap = _resolve(
        "colmap",
        config.colmap_path,
        env.get("PACKLAB_COLMAP_PATH"),
        _windows_executable("colmap"),
        bundled=_bundled(roots, _COLMAP_BUNDLED / _windows_executable("colmap")),
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
                bundled=_bundled(roots, _OPENMVS_BUNDLED / _windows_executable(name)),
                allow_path_lookup=config.allow_path_lookup,
                which=which,
            )
        )
    return EngineDiscoveryReport(tuple(records))
