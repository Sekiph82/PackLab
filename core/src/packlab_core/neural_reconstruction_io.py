"""Safe PackLab input/output and coordinate seams for neural reconstruction.

This module is framework-neutral: it does not import VGGT, PyTorch, Pillow, or
NumPy, and never opens a checkpoint. Paths are private runtime details and are
excluded from portable records.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import stat
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath

from .reconstruction import (
    PACKSCAN_CAMERA_CONVENTION,
    PACKSCAN_INTRINSICS_CONVENTION,
    PACKSCAN_PIXEL_ORIGIN,
    PACKSCAN_POSE_CONVENTION,
    ReconstructionBackendId,
    ReconstructionInputSet,
    ReconstructionOutputManifest,
    ScaleState,
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REVISION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_ARTIFACT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_CAMERA_AUTHORITY = "RECONSTRUCTION_OBSERVATION"


class NeuralReconstructionIOError(ValueError):
    """Raised when neural reconstruction inputs or outputs are unsafe."""


def _safe_asset_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise NeuralReconstructionIOError(f"{field_name} must be a non-empty relative asset ID")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in normalized.split("/")):
        raise NeuralReconstructionIOError(f"{field_name} contains an unsafe path component")
    if re.match(r"^[A-Za-z]:", normalized):
        raise NeuralReconstructionIOError(f"{field_name} must be relative")
    return normalized


def _is_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if callable(is_junction) and is_junction():
        return True
    try:
        return bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, OSError):
        return False


def _inside(root: Path, candidate: Path) -> bool:
    try:
        return os.path.normcase(
            os.path.commonpath((str(root), str(candidate)))
        ) == os.path.normcase(str(root))
    except ValueError:
        return False


def _reject_reparse_components(root: Path, relative: str) -> None:
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink() or (current.exists() and _is_reparse(current)):
            raise NeuralReconstructionIOError("asset path contains a symlink or reparse component")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class VGGTResolvedImage:
    """A verified image path for runtime use; the absolute path is never portable."""

    asset_id: str
    path: Path = field(repr=False)
    sha256: str
    size_bytes: int

    def portable_record(self) -> dict[str, object]:
        return {"asset_id": self.asset_id, "sha256": self.sha256, "size_bytes": self.size_bytes}


def resolve_vggt_image_assets(
    inputs: ReconstructionInputSet,
    project_root: str | Path,
    expected_sha256: Mapping[str, str],
) -> tuple[VGGTResolvedImage, ...]:
    """Resolve ordered images read-only against digests from the source manifest.

    ``source_digest`` binds the PackLab input set. Individual digests must come
    from the matching authoritative source manifest; this function verifies
    the bytes against those values and does not invent that binding itself.
    """

    if not isinstance(inputs, ReconstructionInputSet):
        raise NeuralReconstructionIOError("inputs must be ReconstructionInputSet")
    if len(set(inputs.image_asset_ids)) != len(inputs.image_asset_ids):
        raise NeuralReconstructionIOError("duplicate image asset IDs are not allowed")
    normalized_digests = {
        _safe_asset_id(key, "image asset ID"): value for key, value in expected_sha256.items()
    }
    if len(normalized_digests) != len(expected_sha256):
        raise NeuralReconstructionIOError("image digest index contains duplicate normalized IDs")
    expected_ids = {
        _safe_asset_id(asset_id, "image asset ID") for asset_id in inputs.image_asset_ids
    }
    if len(expected_ids) != len(inputs.image_asset_ids) or set(normalized_digests) != expected_ids:
        raise NeuralReconstructionIOError("image digest index must exactly match the input assets")
    for digest in normalized_digests.values():
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise NeuralReconstructionIOError("image digest index contains an invalid SHA-256")

    try:
        root = Path(project_root).resolve(strict=True)
    except (OSError, RuntimeError, TypeError) as error:
        raise NeuralReconstructionIOError("project root is unavailable") from error
    if not root.is_dir():
        raise NeuralReconstructionIOError("project root is not a directory")

    resolved: list[VGGTResolvedImage] = []
    for asset_id in inputs.image_asset_ids:
        normalized = _safe_asset_id(asset_id, "image asset ID")
        _reject_reparse_components(root, normalized)
        candidate = root.joinpath(*PurePosixPath(normalized).parts)
        try:
            path = candidate.resolve(strict=True)
            before = path.stat()
        except (OSError, RuntimeError) as error:
            raise NeuralReconstructionIOError("declared image asset is unavailable") from error
        if not _inside(root, path) or not stat.S_ISREG(before.st_mode):
            raise NeuralReconstructionIOError(
                "image asset is not a regular file inside the project"
            )
        digest = _file_sha256(path)
        after = path.stat()
        stable_before = (before.st_size, before.st_mtime_ns, before.st_ino)
        stable_after = (after.st_size, after.st_mtime_ns, after.st_ino)
        if stable_before != stable_after:
            raise NeuralReconstructionIOError("image asset changed while it was being verified")
        if digest != normalized_digests[normalized]:
            raise NeuralReconstructionIOError(
                "image asset SHA-256 does not match the source manifest"
            )
        resolved.append(VGGTResolvedImage(normalized, path, digest, after.st_size))
    return tuple(resolved)


@dataclass(frozen=True, slots=True)
class VGGTImagePreprocessTransform:
    """Map original image edge coordinates into VGGT's processed pixel grid.

    ``scale`` is the VGGT loader's final isotropic resize factor. Padding is
    expressed in original-image pixels before that resize. VGGT camera
    intrinsics use top-left edge-origin pixels; PackScan uses top-left
    pixel-center-origin pixels.
    """

    source_width: int
    source_height: int
    pad_left: float
    pad_top: float
    scale: float

    def __post_init__(self) -> None:
        numbers = (self.pad_left, self.pad_top, self.scale)
        try:
            valid_numbers = all(
                not isinstance(value, bool)
                and isinstance(value, (int, float))
                and math.isfinite(value)
                for value in numbers
            )
        except (OverflowError, TypeError, ValueError):
            valid_numbers = False
        if (
            isinstance(self.source_width, bool)
            or isinstance(self.source_height, bool)
            or not isinstance(self.source_width, int)
            or not isinstance(self.source_height, int)
            or self.source_width <= 0
            or self.source_height <= 0
            or not valid_numbers
            or self.pad_left < 0
            or self.pad_top < 0
            or self.scale <= 0
        ):
            raise NeuralReconstructionIOError("image preprocessing transform is invalid")


@dataclass(frozen=True, slots=True)
class VGGTNormalizedCamera:
    image_asset_id: str
    width: int
    height: int
    intrinsics: tuple[float, ...]
    camera_to_world: tuple[float, ...]
    camera_convention: str = PACKSCAN_CAMERA_CONVENTION
    intrinsics_convention: str = PACKSCAN_INTRINSICS_CONVENTION
    pixel_coordinate_origin: str = PACKSCAN_PIXEL_ORIGIN
    pose_convention: str = PACKSCAN_POSE_CONVENTION


def _matrix(values: Sequence[float], rows: int, columns: int, label: str) -> list[list[float]]:
    try:
        valid_values = all(not isinstance(value, bool) and math.isfinite(value) for value in values)
    except TypeError:
        valid_values = False
    if len(values) != rows * columns or not valid_values:
        raise NeuralReconstructionIOError(f"{label} has invalid shape or non-finite values")
    return [list(values[row * columns : (row + 1) * columns]) for row in range(rows)]


def normalize_vggt_camera(
    image_asset_id: str,
    world_to_camera_opencv: Sequence[float],
    intrinsics_vggt_pixels: Sequence[float],
    transform: VGGTImagePreprocessTransform,
) -> VGGTNormalizedCamera:
    """Convert VGGT OpenCV camera-from-world matrices to PackScan camera-to-world.

    VGGT uses x-right/y-down/z-forward for both camera and world axes. PackScan
    uses x-right/y-up/z-out-of-screen, with camera forward along negative Z.
    Applying ``diag(1,-1,-1)`` on both sides preserves a proper rotation; the
    converted world-to-camera transform is then inverted to camera-to-world.
    """

    asset_id = _safe_asset_id(image_asset_id, "image asset ID")
    extrinsic = _matrix(world_to_camera_opencv, 3, 4, "VGGT extrinsic")
    intrinsics = _matrix(intrinsics_vggt_pixels, 3, 3, "VGGT intrinsics")
    if any(
        abs(intrinsics[2][column] - expected) > 1e-6 for column, expected in enumerate((0, 0, 1))
    ):
        raise NeuralReconstructionIOError("VGGT intrinsics must be homogeneous row-major 3x3")
    if intrinsics[0][0] <= 0 or intrinsics[1][1] <= 0:
        raise NeuralReconstructionIOError("VGGT focal lengths must be positive")
    if abs(intrinsics[0][1]) > 1e-6 or abs(intrinsics[1][0]) > 1e-6:
        raise NeuralReconstructionIOError("VGGT intrinsics with skew are unsupported")

    rotation = [row[:3] for row in extrinsic]
    for row in range(3):
        for column in range(3):
            dot = sum(rotation[k][row] * rotation[k][column] for k in range(3))
            if abs(dot - (1.0 if row == column else 0.0)) > 1e-3:
                raise NeuralReconstructionIOError("VGGT rotation is not orthonormal")
    determinant = (
        rotation[0][0] * (rotation[1][1] * rotation[2][2] - rotation[1][2] * rotation[2][1])
        - rotation[0][1] * (rotation[1][0] * rotation[2][2] - rotation[1][2] * rotation[2][0])
        + rotation[0][2] * (rotation[1][0] * rotation[2][1] - rotation[1][1] * rotation[2][0])
    )
    if abs(determinant - 1.0) > 1e-3:
        raise NeuralReconstructionIOError("VGGT rotation must be a proper rotation")

    axis = (1.0, -1.0, -1.0)
    pack_world_to_camera_rotation = [
        [axis[row] * rotation[row][column] * axis[column] for column in range(3)]
        for row in range(3)
    ]
    pack_translation = [axis[index] * extrinsic[index][3] for index in range(3)]
    camera_to_world_rotation = [
        [pack_world_to_camera_rotation[column][row] for column in range(3)] for row in range(3)
    ]
    camera_position = [
        -sum(
            camera_to_world_rotation[row][column] * pack_translation[column] for column in range(3)
        )
        for row in range(3)
    ]
    camera_to_world_rows = [
        camera_to_world_rotation[row] + [camera_position[row]] for row in range(3)
    ] + [[0.0, 0.0, 0.0, 1.0]]
    camera_to_world = tuple(value for row in camera_to_world_rows for value in row)

    scale = transform.scale
    source_fx = intrinsics[0][0] / scale
    source_fy = intrinsics[1][1] / scale
    source_cx = intrinsics[0][2] / scale - transform.pad_left
    source_cy = intrinsics[1][2] / scale - transform.pad_top
    # Convert top-left edge-origin coordinates to PackScan pixel-center origin.
    source_cx -= 0.5
    source_cy -= 0.5
    source_intrinsics = (
        source_fx,
        0.0,
        source_cx,
        0.0,
        source_fy,
        source_cy,
        0.0,
        0.0,
        1.0,
    )
    if not all(math.isfinite(value) for value in (*camera_to_world, *source_intrinsics)):
        raise NeuralReconstructionIOError("normalized VGGT camera contains non-finite values")
    return VGGTNormalizedCamera(
        asset_id,
        transform.source_width,
        transform.source_height,
        source_intrinsics,
        camera_to_world,
    )


def normalize_vggt_world_point(point_opencv: Sequence[float]) -> tuple[float, float, float]:
    """Map a VGGT world point from x-right/y-down/z-forward to PackScan axes."""

    try:
        valid = len(point_opencv) == 3 and all(
            not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
            for value in point_opencv
        )
    except (OverflowError, TypeError, ValueError):
        valid = False
    if not valid:
        raise NeuralReconstructionIOError("VGGT world point must contain three finite values")
    return float(point_opencv[0]), -float(point_opencv[1]), -float(point_opencv[2])


@dataclass(frozen=True, slots=True)
class VGGTOutputArtifact:
    name: str
    filename: str
    source_path: Path = field(repr=False)
    cleanup_after_publish: bool = False


@dataclass(frozen=True, slots=True)
class VGGTOutputPublication:
    manifest: ReconstructionOutputManifest
    directory: Path = field(repr=False)
    manifest_path: Path = field(repr=False)
    artifact_sha256: Mapping[str, str]


def publish_vggt_artifacts(
    project_root: str | Path,
    revision_id: str,
    manifest: ReconstructionOutputManifest,
    runtime_output_root: str | Path,
    artifacts: Sequence[VGGTOutputArtifact],
) -> VGGTOutputPublication:
    """Publish outputs, then remove only explicitly owned runtime artifacts."""

    try:
        return _publish_vggt_artifacts_impl(
            project_root, revision_id, manifest, runtime_output_root, artifacts
        )
    finally:
        _cleanup_owned_vggt_artifacts(runtime_output_root, artifacts)


def _cleanup_owned_vggt_artifacts(
    runtime_output_root: str | Path, artifacts: Sequence[VGGTOutputArtifact]
) -> None:
    """Delete explicitly marked regular files only when rooted beneath runtime output."""

    try:
        root = Path(runtime_output_root).resolve(strict=True)
        if not root.is_dir():
            return
    except (OSError, RuntimeError, TypeError):
        return
    for artifact in artifacts:
        if (
            not isinstance(artifact, VGGTOutputArtifact)
            or artifact.cleanup_after_publish is not True
        ):
            continue
        source = artifact.source_path
        if not isinstance(source, Path) or not source.is_absolute():
            continue
        try:
            relative = source.relative_to(root)
            if any(part in {"", ".", ".."} for part in relative.parts):
                continue
            _reject_reparse_components(root, relative.as_posix())
            actual = source.resolve(strict=True)
            metadata = actual.lstat()
        except (OSError, RuntimeError, ValueError):
            continue
        if _inside(root, actual) and stat.S_ISREG(metadata.st_mode) and not _is_reparse(actual):
            try:
                actual.unlink()
            except OSError:
                pass


def _publish_vggt_artifacts_impl(
    project_root: str | Path,
    revision_id: str,
    manifest: ReconstructionOutputManifest,
    runtime_output_root: str | Path,
    artifacts: Sequence[VGGTOutputArtifact],
) -> VGGTOutputPublication:
    """Atomically publish verified runtime files below a new derived directory."""

    if not isinstance(manifest, ReconstructionOutputManifest):
        raise NeuralReconstructionIOError("a reconstruction output manifest is required")
    if (
        manifest.backend_id is not ReconstructionBackendId.NEURAL_EXPERIMENTAL
        or manifest.authority_class != _CAMERA_AUTHORITY
        or manifest.scale_state is ScaleState.METRIC_VERIFIED
    ):
        raise NeuralReconstructionIOError("VGGT output authority or scale state is invalid")
    if manifest.asset_paths:
        raise NeuralReconstructionIOError("base VGGT manifest must not contain published assets")
    if not isinstance(revision_id, str) or _REVISION.fullmatch(revision_id) is None:
        raise NeuralReconstructionIOError("reconstruction revision ID is invalid")
    if manifest.reconstruction_revision != revision_id:
        raise NeuralReconstructionIOError("output revision does not match its destination")
    if not artifacts:
        raise NeuralReconstructionIOError("at least one VGGT output artifact is required")
    names = [item.name for item in artifacts]
    filenames = [item.filename for item in artifacts]
    if (
        len(set(names)) != len(names)
        or len(set(filenames)) != len(filenames)
        or any(_ARTIFACT_NAME.fullmatch(name) is None for name in names)
        or any(_ARTIFACT_NAME.fullmatch(filename) is None for filename in filenames)
        or any("/" in filename or "\\" in filename for filename in filenames)
    ):
        raise NeuralReconstructionIOError("output artifact names must be unique portable tokens")

    try:
        root = Path(project_root).resolve(strict=True)
        source_root = Path(runtime_output_root).resolve(strict=True)
    except (OSError, RuntimeError, TypeError) as error:
        raise NeuralReconstructionIOError(
            "project or runtime output root is unavailable"
        ) from error
    if not root.is_dir() or not source_root.is_dir():
        raise NeuralReconstructionIOError("project and runtime output roots must be directories")

    relative_directory = f"derived/reconstruction/{revision_id}"
    _reject_reparse_components(root, relative_directory)
    destination = (root / relative_directory).resolve(strict=False)
    if not _inside(root, destination) or destination == root:
        raise NeuralReconstructionIOError("derived output escapes the project")
    if destination.exists() or _is_reparse(destination):
        raise NeuralReconstructionIOError("derived output destination already exists")

    source_files: list[tuple[VGGTOutputArtifact, Path, os.stat_result]] = []
    for item in artifacts:
        relative_source = item.source_path
        if not isinstance(relative_source, Path) or not relative_source.is_absolute():
            raise NeuralReconstructionIOError("runtime artifact source must be an absolute Path")
        try:
            relative = relative_source.relative_to(source_root).as_posix()
            _reject_reparse_components(source_root, relative)
            source = relative_source.resolve(strict=True)
            source_stat = source.stat()
        except (OSError, RuntimeError, ValueError) as error:
            raise NeuralReconstructionIOError("runtime output artifact is unavailable") from error
        if not _inside(source_root, source) or not stat.S_ISREG(source_stat.st_mode):
            raise NeuralReconstructionIOError(
                "runtime artifact must be a regular file inside its output root"
            )
        source_files.append((item, source, source_stat))

    asset_paths = {
        artifact.name: f"{relative_directory}/{artifact.filename}"
        for artifact, _, _ in sorted(source_files, key=lambda value: value[0].name)
    }
    published_manifest = replace(manifest, asset_paths=asset_paths)
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{revision_id}-", dir=parent))
    digests: dict[str, str] = {}
    try:
        for artifact, source, before in source_files:
            destination_file = staging / artifact.filename
            digest = hashlib.sha256()
            with source.open("rb") as input_handle, destination_file.open("xb") as output_handle:
                for block in iter(lambda: input_handle.read(1024 * 1024), b""):
                    digest.update(block)
                    output_handle.write(block)
                output_handle.flush()
                os.fsync(output_handle.fileno())
            after = source.stat()
            if (before.st_size, before.st_mtime_ns, before.st_ino) != (
                after.st_size,
                after.st_mtime_ns,
                after.st_ino,
            ):
                raise NeuralReconstructionIOError("runtime artifact changed during publication")
            digests[artifact.name] = digest.hexdigest()

        manifest_value = published_manifest.as_dict()
        manifest_value.update(
            {
                "contract": "packlab.neural-reconstruction-output.v1",
                "artifact_sha256": digests,
                "limitations": [
                    *published_manifest.limitations,
                    "Experimental reconstruction observation only; not Scan Master, CAD, or engineering authority.",
                    "Scale remains relative or metric-unverified; no metric verification is implied.",
                ],
            }
        )
        manifest_bytes = (
            json.dumps(
                manifest_value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("ascii")
        manifest_path = staging / "manifest.json"
        with manifest_path.open("xb") as handle:
            handle.write(manifest_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        if destination.exists() or _is_reparse(destination):
            raise NeuralReconstructionIOError("derived output destination was created concurrently")
        os.rename(staging, destination)
    except (OSError, ValueError, TypeError) as error:
        shutil.rmtree(staging, ignore_errors=True)
        if isinstance(error, NeuralReconstructionIOError):
            raise
        raise NeuralReconstructionIOError("atomic VGGT output publication failed") from error
    return VGGTOutputPublication(
        published_manifest,
        destination,
        destination / "manifest.json",
        digests,
    )


__all__ = [
    "NeuralReconstructionIOError",
    "VGGTImagePreprocessTransform",
    "VGGTNormalizedCamera",
    "VGGTOutputArtifact",
    "VGGTOutputPublication",
    "VGGTResolvedImage",
    "normalize_vggt_camera",
    "normalize_vggt_world_point",
    "publish_vggt_artifacts",
    "resolve_vggt_image_assets",
]
