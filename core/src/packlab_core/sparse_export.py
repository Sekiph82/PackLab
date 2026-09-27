"""Deterministic, in-memory COLMAP text export for a validated sparse run.

The export boundary deliberately accepts all sparse records as an explicit
immutable payload.  It never reads a working directory, invokes an engine, or
turns a sparse asset identity into evidence that a file exists.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final, cast

from .reconstruction import RunStatus, StageStatus
from .sparse_mapping import (
    SPARSE_MAPPING_STAGE_ID,
    RegisteredImageStatistics,
    SparseMappingRequest,
    SparseMappingRun,
)

SPARSE_EXPORT_CONTRACT: Final = "packlab.sparse-export.v1"
SPARSE_EXPORT_MANIFEST_CONTRACT: Final = "packlab.sparse-export-debug-manifest.v1"
COLMAP_TEXT_EXPORT_FORMAT: Final = "colmap-text-v1"
COLMAP_CAMERA_CONVENTION: Final = "colmap-world-to-camera-qvec-tvec-v1"
MAX_EXPORT_RECORDS: Final = 10_000_000
MAX_REPROJECTION_ERROR: Final = 1_000_000.0

_HEX_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_REVISION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")

# These are the camera models whose parameter counts are defined by COLMAP's
# text format.  Keeping the allowlist here prevents arbitrary third-party
# model syntax from crossing the PackLab export boundary.
_CAMERA_PARAMETER_COUNTS: Final[dict[str, int]] = {
    "SIMPLE_PINHOLE": 3,
    "PINHOLE": 4,
    "SIMPLE_RADIAL": 4,
    "RADIAL": 5,
    "OPENCV": 8,
    "OPENCV_FISHEYE": 8,
    "FULL_OPENCV": 12,
    "FOV": 5,
    "SIMPLE_RADIAL_FISHEYE": 4,
    "RADIAL_FISHEYE": 5,
    "THIN_PRISM_FISHEYE": 12,
}


class SparseExportError(ValueError):
    """Base error for invalid sparse-export inputs or unsupported options."""


class InvalidSparseExportPayload(SparseExportError):
    """Raised when an explicit payload is malformed or internally inconsistent."""


class UnsupportedSparseExportOption(SparseExportError):
    """Raised when the bounded exporter cannot represent an option."""


class SparseExportArtifactName(StrEnum):
    CAMERAS = "cameras.txt"
    IMAGES = "images.txt"
    POINTS3D = "points3D.txt"
    DEBUG_MANIFEST = "debug_manifest.json"


def _safe_relative_name(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidSparseExportPayload(f"{field_name} must be a non-empty relative name")
    if _CONTROL.search(value) or "\\" in value or value.startswith("/"):
        raise InvalidSparseExportPayload(f"{field_name} must be a safe relative name")
    if value.startswith("//") or re.match(r"^[A-Za-z]:", value):
        raise InvalidSparseExportPayload(f"{field_name} must be a safe relative name")
    parts = value.split("/")
    if ":" in value or any(part in {"", ".", ".."} for part in parts):
        raise InvalidSparseExportPayload(f"{field_name} must be a safe relative name")
    return value


def _safe_revision(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SAFE_REVISION.fullmatch(value) is None:
        raise InvalidSparseExportPayload(f"{field_name} must be a safe portable identifier")
    return value


def _digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _HEX_DIGEST.fullmatch(value) is None:
        raise InvalidSparseExportPayload(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _positive_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InvalidSparseExportPayload(f"{field_name} must be a positive integer")
    if value > MAX_EXPORT_RECORDS:
        raise InvalidSparseExportPayload(f"{field_name} exceeds the bounded export limit")
    return value


def _nonnegative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InvalidSparseExportPayload(f"{field_name} must be a non-negative integer")
    if value > MAX_EXPORT_RECORDS:
        raise InvalidSparseExportPayload(f"{field_name} exceeds the bounded export limit")
    return value


def _finite_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidSparseExportPayload(f"{field_name} must be a finite number")
    try:
        converted = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise InvalidSparseExportPayload(f"{field_name} must be a finite number") from error
    if not math.isfinite(converted):
        raise InvalidSparseExportPayload(f"{field_name} must be a finite number")
    return converted


def _finite_tuple(value: object, length: int, field_name: str) -> tuple[float, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise InvalidSparseExportPayload(f"{field_name} must be a sequence of {length} numbers")
    values = tuple(
        _finite_float(item, f"{field_name}[{index}]") for index, item in enumerate(value)
    )
    if len(values) != length:
        raise InvalidSparseExportPayload(f"{field_name} must contain exactly {length} numbers")
    return values


def _immutable_sequence(value: object, field_name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise InvalidSparseExportPayload(f"{field_name} must be an explicit sequence")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class SparseExportPoint2D:
    """One COLMAP image observation; ``None`` means it is not triangulated."""

    x: float
    y: float
    point3d_id: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", _finite_float(self.x, "point2d.x"))
        object.__setattr__(self, "y", _finite_float(self.y, "point2d.y"))
        if self.point3d_id is not None:
            object.__setattr__(
                self, "point3d_id", _positive_integer(self.point3d_id, "point2d.point3d_id")
            )


@dataclass(frozen=True, slots=True)
class SparseExportTrack:
    """A COLMAP POINT3D track reference: image ID and zero-based 2D index."""

    image_id: int
    point2d_index: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "image_id", _positive_integer(self.image_id, "track.image_id"))
        object.__setattr__(
            self, "point2d_index", _nonnegative_integer(self.point2d_index, "track.point2d_index")
        )


@dataclass(frozen=True, slots=True)
class SparseExportCamera:
    """A validated COLMAP camera record."""

    camera_id: int
    model: str
    width: int
    height: int
    params: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "camera_id", _positive_integer(self.camera_id, "camera_id"))
        if self.model not in _CAMERA_PARAMETER_COUNTS:
            raise UnsupportedSparseExportOption(f"unsupported COLMAP camera model: {self.model!r}")
        object.__setattr__(self, "width", _positive_integer(self.width, "camera.width"))
        object.__setattr__(self, "height", _positive_integer(self.height, "camera.height"))
        params = _finite_tuple(self.params, _CAMERA_PARAMETER_COUNTS[self.model], "camera.params")
        focal_count = (
            2 if self.model in {"PINHOLE", "OPENCV", "OPENCV_FISHEYE", "FULL_OPENCV"} else 1
        )
        if any(params[index] <= 0.0 for index in range(focal_count)):
            raise InvalidSparseExportPayload("camera focal parameters must be positive")
        object.__setattr__(self, "params", params)


@dataclass(frozen=True, slots=True)
class SparseExportImage:
    """A COLMAP image record and its required second-line observations."""

    image_id: int
    camera_id: int
    name: str
    qvec: tuple[float, ...]
    tvec: tuple[float, ...]
    points2d: tuple[SparseExportPoint2D, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "image_id", _positive_integer(self.image_id, "image_id"))
        object.__setattr__(self, "camera_id", _positive_integer(self.camera_id, "image.camera_id"))
        object.__setattr__(self, "name", _safe_relative_name(self.name, "image.name"))
        qvec = _finite_tuple(self.qvec, 4, "image.qvec")
        if sum(value * value for value in qvec) <= 0.0:
            raise InvalidSparseExportPayload("image.qvec must not be the zero quaternion")
        object.__setattr__(self, "qvec", qvec)
        object.__setattr__(self, "tvec", _finite_tuple(self.tvec, 3, "image.tvec"))
        raw_points = _immutable_sequence(self.points2d, "image.points2d")
        if len(raw_points) > MAX_EXPORT_RECORDS:
            raise InvalidSparseExportPayload("image.points2d exceeds the bounded export limit")
        if not all(isinstance(point, SparseExportPoint2D) for point in raw_points):
            raise InvalidSparseExportPayload("image.points2d contains an invalid record")
        object.__setattr__(self, "points2d", raw_points)


@dataclass(frozen=True, slots=True)
class SparseExportPoint3D:
    """A validated COLMAP 3D point and its non-dangling track."""

    point3d_id: int
    xyz: tuple[float, ...]
    rgb: tuple[int, ...]
    error: float
    track: tuple[SparseExportTrack, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "point3d_id", _positive_integer(self.point3d_id, "point3d_id"))
        object.__setattr__(self, "xyz", _finite_tuple(self.xyz, 3, "point3d.xyz"))
        raw_rgb = _immutable_sequence(self.rgb, "point3d.rgb")
        if len(raw_rgb) != 3 or any(
            isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255
            for value in raw_rgb
        ):
            raise InvalidSparseExportPayload(
                "point3d.rgb must contain three integers from 0 to 255"
            )
        object.__setattr__(self, "rgb", raw_rgb)
        error = _finite_float(self.error, "point3d.error")
        if not 0.0 <= error <= MAX_REPROJECTION_ERROR:
            raise InvalidSparseExportPayload(
                "point3d.error must be within the supported reprojection-error bounds"
            )
        object.__setattr__(self, "error", error)
        raw_track = _immutable_sequence(self.track, "point3d.track")
        if not raw_track or len(raw_track) > MAX_EXPORT_RECORDS:
            raise InvalidSparseExportPayload("point3d.track must contain one or more records")
        if not all(isinstance(item, SparseExportTrack) for item in raw_track):
            raise InvalidSparseExportPayload("point3d.track contains an invalid record")
        object.__setattr__(self, "track", raw_track)


@dataclass(frozen=True, slots=True)
class SparseExportPayload:
    """Explicit immutable sparse records plus their provenance binding."""

    source_revision: str
    source_digest: str
    request_digest: str
    output_asset_id: str
    engine_id: str
    engine_version: str
    camera_convention: str
    cameras: tuple[SparseExportCamera, ...]
    images: tuple[SparseExportImage, ...]
    points3d: tuple[SparseExportPoint3D, ...]
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_revision", _safe_revision(self.source_revision, "source_revision")
        )
        object.__setattr__(self, "source_digest", _digest(self.source_digest, "source_digest"))
        object.__setattr__(self, "request_digest", _digest(self.request_digest, "request_digest"))
        object.__setattr__(
            self, "output_asset_id", _safe_relative_name(self.output_asset_id, "output_asset_id")
        )
        for field_name in ("engine_id", "engine_version", "camera_convention"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value or _CONTROL.search(value):
                raise InvalidSparseExportPayload(f"{field_name} must be an explicit portable value")
        cameras = _immutable_sequence(self.cameras, "cameras")
        images = _immutable_sequence(self.images, "images")
        points = _immutable_sequence(self.points3d, "points3d")
        if not cameras or not images:
            raise InvalidSparseExportPayload("an export payload requires cameras and images")
        if len(cameras) > MAX_EXPORT_RECORDS or len(images) > MAX_EXPORT_RECORDS:
            raise InvalidSparseExportPayload("export payload exceeds the bounded record limit")
        if not all(isinstance(item, SparseExportCamera) for item in cameras):
            raise InvalidSparseExportPayload("cameras contains an invalid record")
        if not all(isinstance(item, SparseExportImage) for item in images):
            raise InvalidSparseExportPayload("images contains an invalid record")
        if not all(isinstance(item, SparseExportPoint3D) for item in points):
            raise InvalidSparseExportPayload("points3d contains an invalid record")
        if len(points) > MAX_EXPORT_RECORDS:
            raise InvalidSparseExportPayload("points3d exceeds the bounded record limit")
        raw_limitations = _immutable_sequence(self.limitations, "limitations")
        if not all(
            isinstance(item, str) and item.strip() and not _CONTROL.search(item)
            for item in raw_limitations
        ):
            raise InvalidSparseExportPayload("limitations must be non-empty portable strings")
        object.__setattr__(self, "cameras", cameras)
        object.__setattr__(self, "images", images)
        object.__setattr__(self, "points3d", points)
        object.__setattr__(self, "limitations", raw_limitations)


@dataclass(frozen=True, slots=True)
class SparseExportOptions:
    """Only the documented in-memory COLMAP text format is supported."""

    format: str = COLMAP_TEXT_EXPORT_FORMAT
    include_debug_manifest: bool = True

    def __post_init__(self) -> None:
        if self.format != COLMAP_TEXT_EXPORT_FORMAT or self.include_debug_manifest is not True:
            raise UnsupportedSparseExportOption(
                "only COLMAP text v1 with a debug manifest is supported"
            )


@dataclass(frozen=True, slots=True)
class SparseExportArtifact:
    """One relative UTF-8 artifact returned without filesystem materialization."""

    name: str
    content: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _safe_relative_name(self.name, "artifact.name"))
        if not isinstance(self.content, str):
            raise InvalidSparseExportPayload("artifact.content must be text")
        try:
            self.content.encode("utf-8")
        except UnicodeError as error:
            raise InvalidSparseExportPayload("artifact.content must be UTF-8") from error


@dataclass(frozen=True, slots=True)
class SparseExportBundle:
    """Immutable relative-name/content bundle for later, separately owned conversion."""

    artifacts: tuple[SparseExportArtifact, ...]

    def __post_init__(self) -> None:
        artifacts = _immutable_sequence(self.artifacts, "artifacts")
        if len(artifacts) != 4 or not all(
            isinstance(item, SparseExportArtifact) for item in artifacts
        ):
            raise InvalidSparseExportPayload(
                "a sparse export bundle requires exactly four artifacts"
            )
        typed_artifacts = tuple(cast(SparseExportArtifact, item) for item in artifacts)
        names = tuple(item.name for item in typed_artifacts)
        if len(set(names)) != len(names):
            raise InvalidSparseExportPayload("sparse export artifact names must be unique")
        expected = tuple(item.value for item in SparseExportArtifactName)
        if set(names) != set(expected):
            raise InvalidSparseExportPayload("sparse export artifact names are incomplete")
        object.__setattr__(self, "artifacts", typed_artifacts)

    @property
    def files(self) -> MappingProxyType[str, str]:
        return MappingProxyType({artifact.name: artifact.content for artifact in self.artifacts})

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(artifact.name for artifact in self.artifacts)

    def content(self, name: str) -> str:
        for artifact in self.artifacts:
            if artifact.name == name:
                return artifact.content
        raise KeyError(name)


def _validate_unique_ids(
    values: Sequence[object], field_name: str, attribute: str
) -> dict[int, object]:
    result: dict[int, object] = {}
    for value in values:
        identifier = getattr(value, attribute)
        if identifier in result:
            raise InvalidSparseExportPayload(f"{field_name} IDs must be unique")
        result[identifier] = value
    return result


def _validate_payload(payload: SparseExportPayload) -> None:
    cameras = _validate_unique_ids(payload.cameras, "camera", "camera_id")
    images = _validate_unique_ids(payload.images, "image", "image_id")
    points = _validate_unique_ids(payload.points3d, "point3d", "point3d_id")
    point_observations: set[tuple[int, int, int]] = set()
    image_observations: set[tuple[int, int]] = set()
    image_names: set[str] = set()
    for image in payload.images:
        if image.camera_id not in cameras:
            raise InvalidSparseExportPayload("image references a missing camera")
        if image.name in image_names:
            raise InvalidSparseExportPayload("image names must be unique")
        image_names.add(image.name)
        for index, observation in enumerate(image.points2d):
            if observation.point3d_id is None:
                continue
            key = (image.image_id, index)
            if key in image_observations:
                raise InvalidSparseExportPayload("image track references must be unique")
            image_observations.add(key)
            if observation.point3d_id not in points:
                raise InvalidSparseExportPayload("image references a missing point3d")
            point_observations.add((observation.point3d_id, image.image_id, index))
    for point in payload.points3d:
        seen_track: set[tuple[int, int]] = set()
        for track in point.track:
            key = (track.image_id, track.point2d_index)
            if key in seen_track:
                raise InvalidSparseExportPayload("point3d track references must be unique")
            seen_track.add(key)
            image_record = images.get(track.image_id)
            if image_record is None or track.point2d_index >= len(
                cast(SparseExportImage, image_record).points2d
            ):
                raise InvalidSparseExportPayload("point3d track contains a dangling reference")
            observation = cast(SparseExportImage, image_record).points2d[track.point2d_index]
            if observation.point3d_id != point.point3d_id:
                raise InvalidSparseExportPayload(
                    "point3d track does not match its image observation"
                )
            if (point.point3d_id, track.image_id, track.point2d_index) not in point_observations:
                raise InvalidSparseExportPayload(
                    "point3d track is not bound to an image observation"
                )
    expected_observations = {
        (point_id, image_id, index) for point_id, image_id, index in point_observations
    }
    actual_observations = {
        (point.point3d_id, track.image_id, track.point2d_index)
        for point in payload.points3d
        for track in point.track
    }
    if expected_observations != actual_observations:
        raise InvalidSparseExportPayload(
            "image and point3d track references are not mutually complete"
        )


def _validate_run(run: object) -> tuple[SparseMappingRequest, RegisteredImageStatistics, str]:
    if not isinstance(run, SparseMappingRun):
        raise SparseExportError("export requires an explicit SparseMappingRun")
    if not isinstance(run.request, SparseMappingRequest) or run.status is not RunStatus.SUCCEEDED:
        raise SparseExportError("export requires a successful sparse-mapping run")
    stage = run.stage_result
    if (
        stage.stage_id != SPARSE_MAPPING_STAGE_ID
        or stage.status is not StageStatus.SUCCEEDED
        or stage.cancelled
        or stage.exit_code != 0
    ):
        raise SparseExportError("sparse-mapping run has an invalid success result")
    if not isinstance(run.statistics, RegisteredImageStatistics):
        raise SparseExportError("successful sparse-mapping run has invalid statistics")
    if run.statistics.total_images != len(run.request.image_asset_ids):
        raise SparseExportError("sparse-mapping statistics are not bound to the request")
    if not isinstance(run.sparse_model_asset_id, str):
        raise SparseExportError("successful sparse-mapping run has no output identity")
    return run.request, run.statistics, run.sparse_model_asset_id


def _bind_payload(run: SparseMappingRun, payload: SparseExportPayload) -> None:
    request, _, output_asset_id = _validate_run(run)
    if payload.camera_convention != COLMAP_CAMERA_CONVENTION:
        raise UnsupportedSparseExportOption(
            f"unsupported camera convention: {payload.camera_convention!r}"
        )
    if (
        payload.source_revision != request.source_revision
        or payload.source_digest != request.source_digest
        or payload.request_digest != request.request_digest()
        or payload.output_asset_id != output_asset_id
        or payload.engine_id != request.engine_id
        or payload.engine_version != request.engine_version
    ):
        raise InvalidSparseExportPayload("export payload provenance does not match the sparse run")
    _validate_payload(payload)


def _format_float(value: float) -> str:
    if value == 0.0:
        return "0"
    return format(value, ".17g")


def _camera_text(cameras: Sequence[SparseExportCamera]) -> str:
    lines = [
        "# Camera list with one line of data per camera:",
        "#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]",
    ]
    for camera in sorted(cameras, key=lambda item: item.camera_id):
        fields = [
            str(camera.camera_id),
            camera.model,
            str(camera.width),
            str(camera.height),
            *(_format_float(value) for value in camera.params),
        ]
        lines.append(" ".join(fields))
    return "\n".join(lines) + "\n"


def _image_text(images: Sequence[SparseExportImage]) -> str:
    lines = [
        "# Image list with two lines of data per image:",
        "#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, IMAGE_NAME",
        "#   POINTS2D[] as (X, Y, POINT3D_ID)",
    ]
    for image in sorted(images, key=lambda item: item.image_id):
        pose = [_format_float(value) for value in (*image.qvec, *image.tvec)]
        lines.append(" ".join([str(image.image_id), *pose, str(image.camera_id), image.name]))
        lines.append(
            " ".join(
                token
                for observation in image.points2d
                for token in (
                    _format_float(observation.x),
                    _format_float(observation.y),
                    str(-1 if observation.point3d_id is None else observation.point3d_id),
                )
            )
        )
    return "\n".join(lines) + "\n"


def _points_text(points: Sequence[SparseExportPoint3D]) -> str:
    lines = [
        "# 3D point list with one line of data per point:",
        "#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)",
    ]
    for point in sorted(points, key=lambda item: item.point3d_id):
        fields = [
            str(point.point3d_id),
            *(_format_float(value) for value in point.xyz),
            *(str(value) for value in point.rgb),
            _format_float(point.error),
            *(
                token
                for track in point.track
                for token in (str(track.image_id), str(track.point2d_index))
            ),
        ]
        lines.append(" ".join(fields))
    return "\n".join(lines) + "\n"


def _manifest_text(payload: SparseExportPayload) -> str:
    artifact_names = [item.value for item in SparseExportArtifactName]
    manifest = {
        "artifact_names": artifact_names,
        "camera_convention": payload.camera_convention,
        "contract": SPARSE_EXPORT_MANIFEST_CONTRACT,
        "engine": {"id": payload.engine_id, "version": payload.engine_version},
        "export_contract": SPARSE_EXPORT_CONTRACT,
        "limitations": [
            "Artifacts are UTF-8 in-memory contents; no filesystem materialization is claimed.",
            "This export has no metric calibration authority.",
            "This export does not perform dense reconstruction or OpenMVS conversion.",
            "This export is not engineering or CAD authority.",
            *payload.limitations,
        ],
        "output_asset_id": payload.output_asset_id,
        "record_counts": {
            "cameras": len(payload.cameras),
            "images": len(payload.images),
            "points3d": len(payload.points3d),
            "tracks": sum(len(point.track) for point in payload.points3d),
        },
        "request_digest": payload.request_digest,
        "source_digest": payload.source_digest,
        "source_revision": payload.source_revision,
    }
    return json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def export_sparse_mapping(
    run: SparseMappingRun,
    payload: SparseExportPayload,
    options: SparseExportOptions | None = None,
) -> SparseExportBundle:
    """Serialize one explicit successful sparse run into four in-memory artifacts."""

    if options is not None and not isinstance(options, SparseExportOptions):
        raise UnsupportedSparseExportOption("export options must be SparseExportOptions")
    resolved_options = SparseExportOptions() if options is None else options
    if not isinstance(payload, SparseExportPayload):
        raise SparseExportError("export requires an explicit SparseExportPayload")
    _bind_payload(run, payload)
    artifacts = (
        SparseExportArtifact(SparseExportArtifactName.CAMERAS.value, _camera_text(payload.cameras)),
        SparseExportArtifact(SparseExportArtifactName.IMAGES.value, _image_text(payload.images)),
        SparseExportArtifact(
            SparseExportArtifactName.POINTS3D.value, _points_text(payload.points3d)
        ),
    )
    if not resolved_options.include_debug_manifest:
        raise UnsupportedSparseExportOption("the debug manifest is mandatory")
    return SparseExportBundle(
        artifacts=artifacts
        + (
            SparseExportArtifact(
                SparseExportArtifactName.DEBUG_MANIFEST.value, _manifest_text(payload)
            ),
        )
    )


export_sparse_mapping_bundle = export_sparse_mapping
export_sparse_model = export_sparse_mapping
SparseCamera = SparseExportCamera
SparseImage = SparseExportImage
SparsePoint2D = SparseExportPoint2D
SparsePoint3D = SparseExportPoint3D
SparseTrack = SparseExportTrack


__all__ = [
    "COLMAP_CAMERA_CONVENTION",
    "COLMAP_TEXT_EXPORT_FORMAT",
    "InvalidSparseExportPayload",
    "MAX_REPROJECTION_ERROR",
    "SPARSE_EXPORT_CONTRACT",
    "SPARSE_EXPORT_MANIFEST_CONTRACT",
    "SparseCamera",
    "SparseExportArtifact",
    "SparseExportArtifactName",
    "SparseExportBundle",
    "SparseExportCamera",
    "SparseExportError",
    "SparseExportImage",
    "SparseExportOptions",
    "SparseExportPayload",
    "SparseExportPoint2D",
    "SparseExportPoint3D",
    "SparseExportTrack",
    "SparseImage",
    "SparsePoint2D",
    "SparsePoint3D",
    "SparseTrack",
    "UnsupportedSparseExportOption",
    "export_sparse_mapping",
    "export_sparse_mapping_bundle",
    "export_sparse_model",
]
