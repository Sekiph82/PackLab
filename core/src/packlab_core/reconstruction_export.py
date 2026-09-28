"""Atomic derived export for successful textured reconstruction observations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .reconstruction import RunStatus, StageStatus
from .texture_reconstruction import TextureReconstructionRun

SUPPORTED_TEXTURE_EXPORT_FORMATS = frozenset({"ply", "obj", "glb", "gltf"})
RECONSTRUCTION_EXPORT_CONTRACT = "packlab.reconstruction-export.v1"
RECONSTRUCTION_AUTHORITY_CLASS = "RECONSTRUCTION_OBSERVATION"
_DIGEST = re.compile(r"[0-9a-f]{64}")
_PRIVATE_SEGMENTS = frozenset({"private", "secret", "secrets"})


class ReconstructionExportError(ValueError):
    """Raised when a derived export cannot be published safely."""


def _portable_relative(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ReconstructionExportError(f"{field_name} must be a non-empty relative path")
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        raise ReconstructionExportError(f"{field_name} must be relative")
    if any(part in {"", ".", ".."} for part in normalized.split("/")):
        raise ReconstructionExportError(f"{field_name} contains an unsafe path component")
    return normalized


def _digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ReconstructionExportError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _contains_private_segment(value: str) -> bool:
    return any(part.casefold() in _PRIVATE_SEGMENTS for part in value.split("/"))


@dataclass(frozen=True, slots=True)
class TexturedMeshExportRequest:
    run: TextureReconstructionRun
    project_root: Path
    source_path: Path
    source_asset_id: str
    source_output_digest: str
    destination_relative_dir: str
    output_name: str
    format: str
    overwrite: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.run, TextureReconstructionRun):
            raise ReconstructionExportError("export requires a TextureReconstructionRun")
        if self.run.status is not RunStatus.SUCCEEDED:
            raise ReconstructionExportError("export requires a successful textured-mesh run")
        if self.run.stage_result.status is not StageStatus.SUCCEEDED:
            raise ReconstructionExportError("export requires a successful texture stage")
        if self.run.output_asset_id is None:
            raise ReconstructionExportError("successful texture run has no output identity")
        if not isinstance(self.project_root, Path) or not self.project_root.is_absolute():
            raise ReconstructionExportError("project_root must be an absolute project path")
        source_id = _portable_relative(self.source_asset_id, "source_asset_id")
        destination = _portable_relative(self.destination_relative_dir, "destination_relative_dir")
        if not destination.startswith("derived/") and not destination.startswith("export/"):
            raise ReconstructionExportError("derived export must be below derived/ or export/")
        name = _portable_relative(self.output_name, "output_name")
        if "/" in name:
            raise ReconstructionExportError("output_name must be a single file name")
        fmt = self.format.lower() if isinstance(self.format, str) else ""
        if fmt not in SUPPORTED_TEXTURE_EXPORT_FORMATS:
            raise ReconstructionExportError(f"unsupported textured-mesh format: {self.format!r}")
        if Path(name).suffix.lower().lstrip(".") != fmt:
            raise ReconstructionExportError("output_name extension does not match format")
        if self.overwrite:
            raise ReconstructionExportError(
                "overwrite requests are ambiguous; choose a new derived destination"
            )
        if _contains_private_segment(source_id) or _contains_private_segment(destination):
            raise ReconstructionExportError("private export paths are forbidden")
        _digest(self.source_output_digest, "source_output_digest")
        expected_base = Path(source_id).with_suffix("").as_posix()
        if expected_base != self.run.output_asset_id and source_id != self.run.output_asset_id:
            raise ReconstructionExportError(
                "source identity does not match the successful texture run"
            )
        object.__setattr__(self, "source_asset_id", source_id)
        object.__setattr__(self, "destination_relative_dir", destination)
        object.__setattr__(self, "output_name", name)
        object.__setattr__(self, "format", fmt)


@dataclass(frozen=True, slots=True)
class TexturedMeshExportResult:
    output_path: Path
    manifest_path: Path
    output_asset_id: str
    output_digest: str
    source_output_digest: str
    source_revision: str
    request_digest: str
    configuration_digest: str
    conversion_digest: str
    format: str
    authority_class: str = RECONSTRUCTION_AUTHORITY_CLASS
    scale_state: str = "relative"

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": RECONSTRUCTION_EXPORT_CONTRACT,
            "output_asset_id": self.output_asset_id,
            "output_digest": self.output_digest,
            "source_output_digest": self.source_output_digest,
            "source_revision": self.source_revision,
            "request_digest": self.request_digest,
            "configuration_digest": self.configuration_digest,
            "conversion_digest": self.conversion_digest,
            "format": self.format,
            "authority_class": self.authority_class,
            "scale_state": self.scale_state,
            "limitations": [
                "Derived reconstruction observation only; not Scan Master, metric, CAD, BREP, or engineering authority.",
                "Publication preserves bytes only when the existing texture output format matches the requested format.",
            ],
        }


def _inside(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(candidate))) == str(root)
    except ValueError:
        return False


def _reject_symlink_components(root: Path, relative: str) -> None:
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ReconstructionExportError("export path contains a symlink component")


def export_textured_mesh(request: TexturedMeshExportRequest) -> TexturedMeshExportResult:
    """Publish one deterministic output and sidecar as one derived directory."""

    root = request.project_root.resolve()
    source = request.source_path.resolve(strict=False)
    if not _inside(root, source) or request.source_asset_id.casefold().startswith("raw/"):
        raise ReconstructionExportError(
            "source must remain inside the project and outside RAW_CAPTURE"
        )
    if not source.is_file():
        raise ReconstructionExportError("successful textured-mesh source is missing")
    declared_source = (root / request.source_asset_id).resolve(strict=False)
    if source != declared_source:
        raise ReconstructionExportError("source path does not match its portable asset identity")
    source_bytes = source.read_bytes()
    if _sha256(source_bytes) != request.source_output_digest:
        raise ReconstructionExportError("textured-mesh source digest does not match")
    source_format = source.suffix.lower().lstrip(".")
    if source_format != request.format:
        raise ReconstructionExportError(
            "format conversion is unavailable without a reviewed geometry converter; source is preserved"
        )

    _reject_symlink_components(root, request.destination_relative_dir)
    destination_dir = (root / request.destination_relative_dir).resolve(strict=False)
    if not _inside(root, destination_dir) or destination_dir == root:
        raise ReconstructionExportError("derived destination escapes the project")
    if destination_dir.exists() or destination_dir.is_symlink():
        raise ReconstructionExportError("derived export destination already exists")
    output_asset_id = f"{request.destination_relative_dir}/{request.output_name}"
    output_digest = _sha256(source_bytes)
    conversion_digest = _sha256(
        json.dumps(
            {
                "contract": RECONSTRUCTION_EXPORT_CONTRACT,
                "source_asset_id": request.source_asset_id,
                "source_output_digest": request.source_output_digest,
                "output_asset_id": output_asset_id,
                "format": request.format,
                "request_digest": request.run.request_digest,
                "configuration_digest": request.run.configuration_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    manifest = {
        "contract": RECONSTRUCTION_EXPORT_CONTRACT,
        "source_asset_id": request.source_asset_id,
        "source_output_digest": request.source_output_digest,
        "source_revision": request.run.source_revision,
        "source_request_digest": request.run.request_digest,
        "source_configuration_digest": request.run.configuration_digest,
        "output_asset_id": output_asset_id,
        "output_digest": output_digest,
        "format": request.format,
        "conversion_digest": conversion_digest,
        "authority_class": RECONSTRUCTION_AUTHORITY_CLASS,
        "scale_state": request.run.scale_state.value,
        "limitations": [
            "Derived reconstruction observation only; not Scan Master, metric, CAD, BREP, or engineering authority.",
            "No geometry parser or quality claim is applied by this byte-preserving publication seam.",
        ],
    }

    parent = destination_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination_dir.name}-", dir=parent))
    try:
        output_path = staging / request.output_name
        manifest_path = staging / "manifest.json"
        output_path.write_bytes(source_bytes)
        with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staging, destination_dir)
    except (OSError, ValueError, TypeError) as error:
        shutil.rmtree(staging, ignore_errors=True)
        raise ReconstructionExportError("atomic derived export publication failed") from error
    return TexturedMeshExportResult(
        destination_dir / request.output_name,
        destination_dir / "manifest.json",
        output_asset_id,
        output_digest,
        request.source_output_digest,
        request.run.source_revision,
        request.run.request_digest,
        request.run.configuration_digest,
        conversion_digest,
        request.format,
    )


__all__ = [
    "RECONSTRUCTION_EXPORT_CONTRACT",
    "SUPPORTED_TEXTURE_EXPORT_FORMATS",
    "ReconstructionExportError",
    "TexturedMeshExportRequest",
    "TexturedMeshExportResult",
    "export_textured_mesh",
]
