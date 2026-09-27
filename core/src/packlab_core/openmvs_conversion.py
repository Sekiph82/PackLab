"""PackLab-owned COLMAP-to-OpenMVS conversion planning boundary.

This module validates an explicit in-memory sparse-export bundle and produces
immutable provenance for a later OpenMVS stage.  It does not inspect a
filesystem, discover an executable, launch an engine, or write an ``.mvs``
file.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from .sparse_export import (
    COLMAP_CAMERA_CONVENTION,
    MAX_EXPORT_RECORDS,
    SPARSE_EXPORT_CONTRACT,
    SPARSE_EXPORT_MANIFEST_CONTRACT,
    SparseExportArtifactName,
    SparseExportBundle,
)
from .sparse_mapping import COLMAP_ENGINE_ID, COLMAP_ENGINE_VERSION

OPENMVS_CONVERSION_CONTRACT: Final = "packlab.openmvs-scene-conversion.v1"
OPENMVS_SCENE_CONVERSION_CONTRACT: Final = OPENMVS_CONVERSION_CONTRACT
OPENMVS_ENGINE_ID: Final = "openmvs"
OPENMVS_ENGINE_VERSION: Final = "2.4.0"
DEFAULT_OPENMVS_SCENE_ASSET_ID: Final = "working/reconstruction/openmvs/scene"

_HEX_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_REVISION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_PRIVATE_SEGMENTS = frozenset({"private", "secret", "secrets"})
_EXPECTED_ARTIFACT_NAMES = tuple(item.value for item in SparseExportArtifactName)
_REQUIRED_EXPORT_LIMITATIONS = (
    "filesystem materialization",
    "metric calibration",
    "dense reconstruction",
    "openmvs conversion",
    "engineering or cad authority",
)


class OpenMVSConversionError(ValueError):
    """Base error for invalid or unsafe conversion-plan inputs."""


class InvalidOpenMVSConversionBundle(OpenMVSConversionError):
    """Raised when a sparse-export bundle is incomplete or contradictory."""


class UnsupportedOpenMVSConversionOption(OpenMVSConversionError):
    """Raised when an engine-specific or unsupported option crosses the seam."""


def _safe_relative_asset_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise InvalidOpenMVSConversionBundle(
            f"{field_name} must be a non-empty relative PackLab asset ID"
        )
    if _CONTROL.search(value) or "\\" in value or value.startswith("/"):
        raise InvalidOpenMVSConversionBundle(f"{field_name} must use safe relative syntax")
    if re.match(r"^[A-Za-z]:", value) or value.startswith("//") or ":" in value:
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be a safe relative asset ID")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise InvalidOpenMVSConversionBundle(f"{field_name} contains an unsafe path component")
    if any(part.lower() in _PRIVATE_SEGMENTS for part in parts):
        raise InvalidOpenMVSConversionBundle(f"{field_name} cannot target a private path")
    return value


def _safe_revision(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SAFE_REVISION.fullmatch(value) is None:
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be a safe portable revision")
    return value


def _digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _HEX_DIGEST.fullmatch(value) is None:
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _portable_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or _CONTROL.search(value):
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be a portable text value")
    try:
        value.encode("utf-8")
    except UnicodeError as error:
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be valid UTF-8") from error
    return value


def _bounded_count(value: object, field_name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= MAX_EXPORT_RECORDS
    ):
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be a bounded non-negative integer")
    return value


def _finite_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be finite")
    try:
        converted = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be finite") from error
    if not math.isfinite(converted):
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be finite")
    return converted


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidOpenMVSConversionBundle(f"duplicate manifest key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise InvalidOpenMVSConversionBundle(f"non-finite JSON value is not allowed: {value}")


def _manifest(content: str) -> dict[str, object]:
    try:
        parsed = json.loads(
            content,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        if isinstance(error, InvalidOpenMVSConversionBundle):
            raise
        raise InvalidOpenMVSConversionBundle("debug manifest must be valid finite JSON") from error
    if not isinstance(parsed, dict):
        raise InvalidOpenMVSConversionBundle("debug manifest must be a JSON object")
    return parsed


def _required_mapping(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be a JSON object")
    return dict(value)


def _required_string(mapping: Mapping[str, object], key: str) -> str:
    if key not in mapping:
        raise InvalidOpenMVSConversionBundle(f"manifest is missing {key}")
    return _portable_text(mapping[key], f"manifest.{key}")


def _required_list(mapping: Mapping[str, object], key: str) -> list[object]:
    value = mapping.get(key)
    if not isinstance(value, list):
        raise InvalidOpenMVSConversionBundle(f"manifest.{key} must be a JSON array")
    return value


def _data_lines(content: str, field_name: str) -> list[str]:
    if not isinstance(content, str) or not content:
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be non-empty UTF-8 text")
    try:
        content.encode("utf-8")
    except UnicodeError as error:
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be valid UTF-8") from error
    if re.search(r"[\x00-\x09\x0b-\x0c\x0e-\x1f\x7f]", content):
        raise InvalidOpenMVSConversionBundle(f"{field_name} contains unsafe control characters")
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines or any(line.startswith("#") is False and _CONTROL.search(line) for line in lines):
        raise InvalidOpenMVSConversionBundle(f"{field_name} contains unsafe text")
    return [line for line in lines if not line.startswith("#")]


def _integer_token(value: str, field_name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be an integer") from error
    return parsed


def _validate_camera_artifact(content: str) -> tuple[int, set[int]]:
    lines = _data_lines(content, "cameras.txt")
    identifiers: set[int] = set()
    for index, line in enumerate(lines):
        tokens = line.split()
        if len(tokens) < 5:
            raise InvalidOpenMVSConversionBundle("cameras.txt contains a malformed record")
        camera_id = _integer_token(tokens[0], f"cameras.txt[{index}].camera_id")
        if camera_id <= 0 or camera_id in identifiers:
            raise InvalidOpenMVSConversionBundle("cameras.txt contains duplicate or unsafe IDs")
        identifiers.add(camera_id)
        _portable_text(tokens[1], f"cameras.txt[{index}].model")
        for token_index, token in enumerate(tokens[2:], start=2):
            _finite_float(token, f"cameras.txt[{index}].value[{token_index}]")
    return len(lines), identifiers


def _validate_image_artifact(
    content: str,
) -> tuple[int, int, set[int], set[tuple[int, int, int]]]:
    lines = _data_lines(content, "images.txt")
    if len(lines) % 2:
        raise InvalidOpenMVSConversionBundle("images.txt must contain two lines per image")
    identifiers: set[int] = set()
    camera_ids: set[int] = set()
    observations: set[tuple[int, int, int]] = set()
    observation_count = 0
    for index in range(0, len(lines), 2):
        image_tokens = lines[index].split()
        if len(image_tokens) < 10:
            raise InvalidOpenMVSConversionBundle("images.txt contains a malformed image record")
        image_id = _integer_token(image_tokens[0], f"images.txt[{index}].image_id")
        if image_id <= 0 or image_id in identifiers:
            raise InvalidOpenMVSConversionBundle("images.txt contains duplicate or unsafe IDs")
        identifiers.add(image_id)
        for token_index, token in enumerate(image_tokens[1:9], start=1):
            _finite_float(token, f"images.txt[{index}].pose[{token_index}]")
        camera_id = _integer_token(image_tokens[8], f"images.txt[{index}].camera_id")
        if camera_id <= 0:
            raise InvalidOpenMVSConversionBundle("images.txt contains an unsafe camera ID")
        camera_ids.add(camera_id)
        _safe_relative_asset_id(image_tokens[9], f"images.txt[{index}].name")
        point_tokens = lines[index + 1].split()
        if len(point_tokens) % 3:
            raise InvalidOpenMVSConversionBundle("images.txt contains malformed 2D observations")
        for observation_index, token_index in enumerate(range(0, len(point_tokens), 3)):
            _finite_float(point_tokens[token_index], "images.txt observation.x")
            _finite_float(point_tokens[token_index + 1], "images.txt observation.y")
            point_id = _integer_token(
                point_tokens[token_index + 2], "images.txt observation.point3d_id"
            )
            if point_id < -1:
                raise InvalidOpenMVSConversionBundle("images.txt contains an unsafe point ID")
            if point_id != -1:
                observations.add((point_id, image_id, observation_index))
            observation_count += 1
    return len(identifiers), observation_count, camera_ids, observations


def _validate_points_artifact(
    content: str,
) -> tuple[int, int, set[int], set[tuple[int, int, int]]]:
    lines = _data_lines(content, "points3D.txt")
    identifiers: set[int] = set()
    tracks: set[tuple[int, int, int]] = set()
    track_count = 0
    for index, line in enumerate(lines):
        tokens = line.split()
        if len(tokens) < 8 or len(tokens[8:]) % 2:
            raise InvalidOpenMVSConversionBundle("points3D.txt contains a malformed record")
        point_id = _integer_token(tokens[0], f"points3D.txt[{index}].point3d_id")
        if point_id <= 0 or point_id in identifiers:
            raise InvalidOpenMVSConversionBundle("points3D.txt contains duplicate or unsafe IDs")
        identifiers.add(point_id)
        for token_index, token in enumerate(tokens[1:8], start=1):
            _finite_float(token, f"points3D.txt[{index}].value[{token_index}]")
        for token_index in range(8, len(tokens), 2):
            image_id = _integer_token(tokens[token_index], "points3D.txt track.image_id")
            point2d_index = _integer_token(
                tokens[token_index + 1], "points3D.txt track.point2d_index"
            )
            if image_id <= 0 or point2d_index < 0:
                raise InvalidOpenMVSConversionBundle("points3D.txt contains an unsafe track")
            track = (point_id, image_id, point2d_index)
            if track in tracks:
                raise InvalidOpenMVSConversionBundle("points3D.txt contains duplicate tracks")
            tracks.add(track)
            track_count += 1
    return len(identifiers), track_count, identifiers, tracks


@dataclass(frozen=True, slots=True)
class OpenMVSRecordCounts:
    """Record counts copied from and checked against the sparse manifest."""

    cameras: int
    images: int
    points3d: int
    tracks: int

    def __post_init__(self) -> None:
        for field_name in ("cameras", "images", "points3d", "tracks"):
            _bounded_count(getattr(self, field_name), f"record_counts.{field_name}")

    def as_dict(self) -> dict[str, int]:
        return {
            "cameras": self.cameras,
            "images": self.images,
            "points3d": self.points3d,
            "tracks": self.tracks,
        }


@dataclass(frozen=True, slots=True)
class OpenMVSInputArtifact:
    """Identity of one UTF-8 sparse-export artifact, without its contents."""

    name: str
    content_digest: str
    byte_count: int

    def __post_init__(self) -> None:
        if self.name not in _EXPECTED_ARTIFACT_NAMES:
            raise InvalidOpenMVSConversionBundle(
                "input artifact name is not in the COLMAP export contract"
            )
        _digest(self.content_digest, f"artifact.{self.name}.content_digest")
        _bounded_count(self.byte_count, f"artifact.{self.name}.byte_count")

    @property
    def digest(self) -> str:
        return self.content_digest

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "content_digest": self.content_digest,
            "byte_count": self.byte_count,
        }


def _validate_limitations(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise InvalidOpenMVSConversionBundle(f"{field_name} must be a sequence of strings")
    values = tuple(value)
    if any(
        not isinstance(item, str) or not item.strip() or _CONTROL.search(item) for item in values
    ):
        raise InvalidOpenMVSConversionBundle(f"{field_name} contains invalid text")
    return cast(tuple[str, ...], values)


@dataclass(frozen=True, slots=True)
class OpenMVSSceneConversionPlan:
    """Immutable PackLab semantic plan for a later OpenMVS conversion stage."""

    source_export_contract: str
    source_manifest_contract: str
    source_revision: str
    source_digest: str
    sparse_request_digest: str
    sparse_output_asset_id: str
    output_scene_asset_id: str
    colmap_engine_id: str
    colmap_engine_version: str
    openmvs_engine_id: str
    openmvs_engine_version: str
    camera_convention: str
    input_artifacts: tuple[OpenMVSInputArtifact, ...]
    record_counts: OpenMVSRecordCounts
    sparse_export_limitations: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.source_export_contract != SPARSE_EXPORT_CONTRACT:
            raise InvalidOpenMVSConversionBundle("unsupported sparse export contract")
        if self.source_manifest_contract != SPARSE_EXPORT_MANIFEST_CONTRACT:
            raise InvalidOpenMVSConversionBundle("unsupported sparse manifest contract")
        _safe_revision(self.source_revision, "source_revision")
        _digest(self.source_digest, "source_digest")
        _digest(self.sparse_request_digest, "sparse_request_digest")
        _safe_relative_asset_id(self.sparse_output_asset_id, "sparse_output_asset_id")
        _safe_relative_asset_id(self.output_scene_asset_id, "output_scene_asset_id")
        if (
            self.colmap_engine_id != COLMAP_ENGINE_ID
            or self.colmap_engine_version != COLMAP_ENGINE_VERSION
        ):
            raise UnsupportedOpenMVSConversionOption("only the pinned COLMAP baseline is supported")
        if (
            self.openmvs_engine_id != OPENMVS_ENGINE_ID
            or self.openmvs_engine_version != OPENMVS_ENGINE_VERSION
        ):
            raise UnsupportedOpenMVSConversionOption("only OpenMVS 2.4.0 is supported")
        if self.camera_convention != COLMAP_CAMERA_CONVENTION:
            raise UnsupportedOpenMVSConversionOption("unsupported camera convention")
        artifacts = tuple(self.input_artifacts)
        if not all(isinstance(item, OpenMVSInputArtifact) for item in artifacts):
            raise InvalidOpenMVSConversionBundle("conversion plan contains an invalid artifact")
        if tuple(item.name for item in artifacts) != _EXPECTED_ARTIFACT_NAMES:
            raise InvalidOpenMVSConversionBundle(
                "conversion plan artifacts are incomplete or unordered"
            )
        if not isinstance(self.record_counts, OpenMVSRecordCounts):
            raise InvalidOpenMVSConversionBundle("conversion plan has invalid record counts")
        object.__setattr__(self, "input_artifacts", artifacts)
        object.__setattr__(
            self,
            "sparse_export_limitations",
            _validate_limitations(self.sparse_export_limitations, "sparse_export_limitations"),
        )
        object.__setattr__(
            self, "limitations", _validate_limitations(self.limitations, "limitations")
        )

    @property
    def contract(self) -> str:
        return OPENMVS_CONVERSION_CONTRACT

    @property
    def artifact_digests(self) -> Mapping[str, str]:
        return MappingProxyType({item.name: item.content_digest for item in self.input_artifacts})

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": OPENMVS_CONVERSION_CONTRACT,
            "source_export_contract": self.source_export_contract,
            "source_manifest_contract": self.source_manifest_contract,
            "source_revision": self.source_revision,
            "source_digest": self.source_digest,
            "sparse_request_digest": self.sparse_request_digest,
            "sparse_output_asset_id": self.sparse_output_asset_id,
            "output_scene_asset_id": self.output_scene_asset_id,
            "engines": {
                "colmap": {"id": self.colmap_engine_id, "version": self.colmap_engine_version},
                "openmvs": {"id": self.openmvs_engine_id, "version": self.openmvs_engine_version},
            },
            "camera_convention": self.camera_convention,
            "input_artifacts": [item.as_dict() for item in self.input_artifacts],
            "record_counts": self.record_counts.as_dict(),
            "sparse_export_limitations": list(self.sparse_export_limitations),
            "limitations": list(self.limitations),
        }

    as_dict = to_dict

    def serialize(self) -> str:
        """Return canonical UTF-8-safe JSON for portable provenance."""

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def plan_digest(self) -> str:
        """Return the stable SHA-256 digest of the canonical plan JSON."""

        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()

    def configuration_digest(self) -> str:
        return self.plan_digest()

    @property
    def digest(self) -> str:
        return self.plan_digest()


def _validate_manifest_and_artifacts(
    bundle: SparseExportBundle,
) -> tuple[dict[str, object], tuple[OpenMVSInputArtifact, ...]]:
    if not isinstance(bundle, SparseExportBundle):
        raise OpenMVSConversionError("conversion requires an explicit SparseExportBundle")
    if (
        tuple(sorted(bundle.names)) != tuple(sorted(_EXPECTED_ARTIFACT_NAMES))
        or len(bundle.names) != 4
    ):
        raise InvalidOpenMVSConversionBundle(
            "bundle must contain exactly the four COLMAP artifacts"
        )
    try:
        artifacts_by_name = {name: bundle.content(name) for name in _EXPECTED_ARTIFACT_NAMES}
    except KeyError as error:
        raise InvalidOpenMVSConversionBundle("bundle artifact set is incomplete") from error
    manifest = _manifest(artifacts_by_name["debug_manifest.json"])
    expected_manifest_keys = {
        "artifact_names",
        "camera_convention",
        "contract",
        "engine",
        "export_contract",
        "limitations",
        "output_asset_id",
        "record_counts",
        "request_digest",
        "source_digest",
        "source_revision",
    }
    if set(manifest) != expected_manifest_keys:
        raise InvalidOpenMVSConversionBundle(
            "debug manifest fields do not match the accepted contract"
        )
    names = _required_list(manifest, "artifact_names")
    if tuple(names) != _EXPECTED_ARTIFACT_NAMES:
        raise InvalidOpenMVSConversionBundle(
            "debug manifest artifact names are incomplete or reordered"
        )
    if _required_string(manifest, "contract") != SPARSE_EXPORT_MANIFEST_CONTRACT:
        raise InvalidOpenMVSConversionBundle("unsupported sparse-export debug manifest contract")
    if _required_string(manifest, "export_contract") != SPARSE_EXPORT_CONTRACT:
        raise InvalidOpenMVSConversionBundle("unsupported sparse-export contract")
    engine = _required_mapping(manifest.get("engine"), "manifest.engine")
    if (
        set(engine) != {"id", "version"}
        or engine.get("id") != COLMAP_ENGINE_ID
        or engine.get("version") != COLMAP_ENGINE_VERSION
    ):
        raise UnsupportedOpenMVSConversionOption("sparse bundle is not from pinned COLMAP 3.12.6")
    if _required_string(manifest, "camera_convention") != COLMAP_CAMERA_CONVENTION:
        raise UnsupportedOpenMVSConversionOption(
            "sparse bundle uses an unsupported camera convention"
        )
    limitations = _validate_limitations(manifest.get("limitations"), "manifest.limitations")
    lower_limitations = " ".join(limitations).lower()
    if any(marker not in lower_limitations for marker in _REQUIRED_EXPORT_LIMITATIONS):
        raise InvalidOpenMVSConversionBundle(
            "sparse manifest limitations do not preserve authority boundaries"
        )
    _safe_revision(manifest.get("source_revision"), "manifest.source_revision")
    _digest(manifest.get("source_digest"), "manifest.source_digest")
    _digest(manifest.get("request_digest"), "manifest.request_digest")
    sparse_output_asset_id = _safe_relative_asset_id(
        manifest.get("output_asset_id"), "manifest.output_asset_id"
    )
    counts_mapping = _required_mapping(manifest.get("record_counts"), "manifest.record_counts")
    if set(counts_mapping) != {"cameras", "images", "points3d", "tracks"}:
        raise InvalidOpenMVSConversionBundle("manifest record counts are incomplete")
    counts = OpenMVSRecordCounts(
        _bounded_count(counts_mapping["cameras"], "manifest.record_counts.cameras"),
        _bounded_count(counts_mapping["images"], "manifest.record_counts.images"),
        _bounded_count(counts_mapping["points3d"], "manifest.record_counts.points3d"),
        _bounded_count(counts_mapping["tracks"], "manifest.record_counts.tracks"),
    )
    camera_count, camera_ids = _validate_camera_artifact(artifacts_by_name["cameras.txt"])
    image_count, observed_count, image_camera_ids, image_observations = _validate_image_artifact(
        artifacts_by_name["images.txt"]
    )
    point_count, track_count, point_ids, point_tracks = _validate_points_artifact(
        artifacts_by_name["points3D.txt"]
    )
    if not image_camera_ids <= camera_ids:
        raise InvalidOpenMVSConversionBundle("images.txt references a missing camera")
    if not {point_id for point_id, _, _ in image_observations} <= point_ids:
        raise InvalidOpenMVSConversionBundle("images.txt references a missing point3d")
    if point_tracks != image_observations:
        raise InvalidOpenMVSConversionBundle("image observations and point tracks disagree")
    if track_count != len(image_observations) or track_count > observed_count:
        raise InvalidOpenMVSConversionBundle("image observations and point tracks disagree")
    if (camera_count, image_count, point_count, track_count) != (
        counts.cameras,
        counts.images,
        counts.points3d,
        counts.tracks,
    ):
        raise InvalidOpenMVSConversionBundle("manifest record counts contradict artifact contents")
    manifest["output_asset_id"] = sparse_output_asset_id
    manifest["limitations"] = limitations
    manifest["record_counts"] = counts.as_dict()
    input_artifacts = tuple(
        OpenMVSInputArtifact(
            name=name,
            content_digest=hashlib.sha256(artifacts_by_name[name].encode("utf-8")).hexdigest(),
            byte_count=len(artifacts_by_name[name].encode("utf-8")),
        )
        for name in _EXPECTED_ARTIFACT_NAMES
    )
    return manifest, input_artifacts


def convert_sparse_export_to_openmvs_scene_plan(
    bundle: SparseExportBundle,
    *,
    output_scene_asset_id: str = DEFAULT_OPENMVS_SCENE_ASSET_ID,
    openmvs_options: Mapping[str, object] | None = None,
) -> OpenMVSSceneConversionPlan:
    """Validate one explicit sparse bundle and return a non-executing plan."""

    if openmvs_options is not None:
        raise UnsupportedOpenMVSConversionOption(
            "caller-controlled OpenMVS/CLI options are not part of the portable plan contract"
        )
    manifest, input_artifacts = _validate_manifest_and_artifacts(bundle)
    counts_mapping = cast(Mapping[str, object], manifest["record_counts"])
    plan_limitations = (
        "Conversion metadata only; no .mvs filesystem materialization is claimed.",
        "The OpenMVS 2.4.0 engine is neither discovered nor executed by this boundary.",
        "Dense, mesh, texture, CAD, Scan Master, and METRIC_VERIFIED authority remain later-stage contracts.",
    )
    return OpenMVSSceneConversionPlan(
        source_export_contract=cast(str, manifest["export_contract"]),
        source_manifest_contract=cast(str, manifest["contract"]),
        source_revision=cast(str, manifest["source_revision"]),
        source_digest=cast(str, manifest["source_digest"]),
        sparse_request_digest=cast(str, manifest["request_digest"]),
        sparse_output_asset_id=cast(str, manifest["output_asset_id"]),
        output_scene_asset_id=_safe_relative_asset_id(
            output_scene_asset_id, "output_scene_asset_id"
        ),
        colmap_engine_id=COLMAP_ENGINE_ID,
        colmap_engine_version=COLMAP_ENGINE_VERSION,
        openmvs_engine_id=OPENMVS_ENGINE_ID,
        openmvs_engine_version=OPENMVS_ENGINE_VERSION,
        camera_convention=cast(str, manifest["camera_convention"]),
        input_artifacts=input_artifacts,
        record_counts=OpenMVSRecordCounts(
            _bounded_count(counts_mapping["cameras"], "record_counts.cameras"),
            _bounded_count(counts_mapping["images"], "record_counts.images"),
            _bounded_count(counts_mapping["points3d"], "record_counts.points3d"),
            _bounded_count(counts_mapping["tracks"], "record_counts.tracks"),
        ),
        sparse_export_limitations=cast(tuple[str, ...], manifest["limitations"]),
        limitations=plan_limitations,
    )


build_openmvs_scene_conversion_plan = convert_sparse_export_to_openmvs_scene_plan
create_openmvs_scene_conversion_plan = convert_sparse_export_to_openmvs_scene_plan
plan_openmvs_scene_conversion = convert_sparse_export_to_openmvs_scene_plan


__all__ = [
    "DEFAULT_OPENMVS_SCENE_ASSET_ID",
    "InvalidOpenMVSConversionBundle",
    "OPENMVS_CONVERSION_CONTRACT",
    "OPENMVS_ENGINE_ID",
    "OPENMVS_ENGINE_VERSION",
    "OPENMVS_SCENE_CONVERSION_CONTRACT",
    "OpenMVSConversionError",
    "OpenMVSInputArtifact",
    "OpenMVSRecordCounts",
    "OpenMVSSceneConversionPlan",
    "UnsupportedOpenMVSConversionOption",
    "build_openmvs_scene_conversion_plan",
    "convert_sparse_export_to_openmvs_scene_plan",
    "create_openmvs_scene_conversion_plan",
    "plan_openmvs_scene_conversion",
]
