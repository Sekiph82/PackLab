"""Bind detected marker pixels to exact reconstructed source cameras."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .marker_detection import DetectionBatch

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class MarkerAssociationError(ValueError):
    """Raised when marker evidence cannot be bound to one current camera."""


@dataclass(frozen=True, slots=True)
class CameraImageBinding:
    """Identity and dimensions carried by one reconstructed camera solution."""

    camera_id: str
    source_image_asset_id: str
    source_digest: str
    image_width: int
    image_height: int
    camera_solution_revision: str

    def __post_init__(self) -> None:
        for field in ("camera_id", "source_image_asset_id", "camera_solution_revision"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise MarkerAssociationError(f"{field}_required")
        if not isinstance(self.source_digest, str) or not _SHA256.fullmatch(self.source_digest):
            raise MarkerAssociationError("source_digest_must_be_lowercase_sha256")
        for field in ("image_width", "image_height"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise MarkerAssociationError(f"{field}_must_be_positive_integer")


@dataclass(frozen=True, slots=True)
class AssociatedMarkerObservation:
    """One detector observation with immutable source and camera provenance."""

    marker_id: int
    corners_px: tuple[tuple[float, float], ...]
    quality: dict[str, object]
    detector_provenance: dict[str, str]
    source_image_asset_id: str
    source_digest: str
    image_width: int
    image_height: int
    camera_id: str
    camera_solution_revision: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.associated-marker-observation.v1",
            "marker_id": self.marker_id,
            "corners_px": [list(point) for point in self.corners_px],
            "quality": dict(self.quality),
            "detector_provenance": dict(self.detector_provenance),
            "source_image": {
                "asset_id": self.source_image_asset_id,
                "sha256": self.source_digest,
                "dimensions": {"width": self.image_width, "height": self.image_height},
            },
            "camera": {
                "camera_id": self.camera_id,
                "camera_solution_revision": self.camera_solution_revision,
            },
            "authority": "image_pixel_marker_detection_only_no_scale_inference",
        }


def associate_marker_detections(
    batch: DetectionBatch,
    *,
    source_image_asset_id: str,
    source_digest: str,
    image_width: int,
    image_height: int,
    camera_solution_revision: str,
    cameras: tuple[CameraImageBinding, ...],
) -> tuple[AssociatedMarkerObservation, ...]:
    """Associate one image's detections with its unique current camera record.

    The source digest is supplied by the immutable source-asset authority, not
    computed from a decoded or transformed raster. No geometry or scale is
    inferred here.
    """

    if batch.status != "detected":
        if batch.status in {"no_markers", "unavailable"}:
            return ()
        raise MarkerAssociationError(f"detection_batch_not_associable:{batch.status}")
    if not source_image_asset_id or not isinstance(source_image_asset_id, str):
        raise MarkerAssociationError("source_image_asset_id_required")
    if not isinstance(source_digest, str) or not _SHA256.fullmatch(source_digest):
        raise MarkerAssociationError("source_digest_must_be_lowercase_sha256")
    for name, value in (("image_width", image_width), ("image_height", image_height)):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise MarkerAssociationError(f"{name}_must_be_positive_integer")
    if not isinstance(camera_solution_revision, str) or not camera_solution_revision.strip():
        raise MarkerAssociationError("camera_solution_revision_required")

    if len({camera.camera_id for camera in cameras}) != len(cameras):
        raise MarkerAssociationError("duplicate_camera_identity")
    matches = tuple(
        camera for camera in cameras if camera.source_image_asset_id == source_image_asset_id
    )
    if not matches:
        raise MarkerAssociationError("camera_identity_missing_for_source_image")
    if len(matches) != 1:
        raise MarkerAssociationError("ambiguous_camera_identity_for_source_image")
    camera = matches[0]
    if camera.camera_solution_revision != camera_solution_revision:
        raise MarkerAssociationError("stale_camera_solution_revision")
    if camera.source_digest != source_digest:
        raise MarkerAssociationError("source_digest_mismatch")
    if (camera.image_width, camera.image_height) != (image_width, image_height):
        raise MarkerAssociationError("source_image_dimensions_mismatch")

    for observation in batch.observations:
        if len(observation.corners_px) != 4:
            raise MarkerAssociationError("marker_corner_count_invalid")
    marker_ids = tuple(observation.marker_id for observation in batch.observations)
    if len(set(marker_ids)) != len(marker_ids):
        raise MarkerAssociationError("duplicate_marker_id")

    result = []
    for observation in batch.observations:
        result.append(
            AssociatedMarkerObservation(
                marker_id=observation.marker_id,
                corners_px=tuple((float(x), float(y)) for x, y in observation.corners_px),
                quality=dict(observation.quality),
                detector_provenance=dict(observation.provenance),
                source_image_asset_id=source_image_asset_id,
                source_digest=source_digest,
                image_width=image_width,
                image_height=image_height,
                camera_id=camera.camera_id,
                camera_solution_revision=camera_solution_revision,
            )
        )
    return tuple(sorted(result, key=lambda item: item.marker_id))


def serialize_associated_observations(
    observations: tuple[AssociatedMarkerObservation, ...],
) -> bytes:
    """Serialize observations deterministically for evidence hashing/storage."""

    payload: dict[str, object] = {
        "contract": "packlab.marker-observation-set.v1",
        "observations": [item.as_dict() for item in observations],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "ascii"
    )


def associated_observations_digest(
    observations: tuple[AssociatedMarkerObservation, ...],
) -> str:
    return hashlib.sha256(serialize_associated_observations(observations)).hexdigest()
