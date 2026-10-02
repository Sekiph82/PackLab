"""Compose accepted scale, upright, and front evidence non-destructively."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .base_plane import BasePlaneSelection
from .calibration.reconstruction_scale import ReconstructionScaleEstimate
from .coordinate_frame import (
    PACKLAB_NORMALIZED_FRAME,
    NormalizedFrameTransform,
)
from .front_direction import (
    FrontDirectionRecord,
    select_front_direction,
)
from .object_mask_lifting import ObjectCaptureGeometry
from .reconstruction import ScaleState
from .upright_alignment import UprightAlignmentResult

NORMALIZATION_METHOD_VERSION = "scale_upright_front_normalization_v1"
SOURCE_GEOMETRY_FRAME = "object_capture_reconstruction_frame_v1"
SCALED_GEOMETRY_FRAME = "object_capture_scaled_frame_v1"
UPRIGHT_GEOMETRY_FRAME = "object_capture_upright_frame_v1"
Matrix4 = tuple[float, ...]
Point3 = tuple[float, float, float]


class NormalizationError(ValueError):
    """Raised when normalization evidence is rejected, stale, or inconsistent."""


@dataclass(frozen=True, slots=True)
class GeometryNormalizationTransform:
    transform: NormalizedFrameTransform
    geometry_id: str
    scale_estimate_sha256: str
    scale_factor_mm_per_reconstruction_unit: float
    scale_uncertainty_mm_per_reconstruction_unit: float
    base_plane_selection_id: str
    upright_alignment_id: str
    front_direction_revision_id: str
    original_scale_state: ScaleState

    @property
    def transform_id(self) -> str:
        return self.transform.transform_id

    @property
    def matrix(self) -> Matrix4:
        return self.transform.matrix

    def apply_point(self, point: Point3) -> Point3:
        return self.transform.apply_point(point)

    def inverse_point(self, point: Point3) -> Point3:
        return self.transform.inverse().apply_point(point)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.geometry-normalization-transform.v1",
            "method_version": NORMALIZATION_METHOD_VERSION,
            "transform": self.transform.as_dict(),
            "parents": {
                "object_capture_geometry_id": self.geometry_id,
                "scale_estimate_sha256": self.scale_estimate_sha256,
                "base_plane_selection_id": self.base_plane_selection_id,
                "upright_alignment_id": self.upright_alignment_id,
                "front_direction_revision_id": self.front_direction_revision_id,
            },
            "scale": {
                "factor_mm_per_reconstruction_unit": self.scale_factor_mm_per_reconstruction_unit,
                "uncertainty_mm_per_reconstruction_unit": self.scale_uncertainty_mm_per_reconstruction_unit,
                "input_state": self.original_scale_state.value,
                "output_state": ScaleState.METRIC_UNVERIFIED.value,
            },
            "authority_class": "OBJECT_CAPTURE_GEOMETRY",
            "generated": False,
            "mutates_source_geometry": False,
            "baked_geometry_created": False,
            "physical_scale_verified": False,
        }


@dataclass(frozen=True, slots=True)
class NormalizedGeometryView:
    """An in-memory transformed view that retains its captured-geometry parent."""

    source_geometry_id: str
    transform_id: str
    filtered_points: tuple[Point3, ...]
    unfiltered_points: tuple[Point3, ...]
    authority_class: str = "OBJECT_CAPTURE_GEOMETRY"
    generated: bool = False
    scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED
    coordinate_unit: str = "mm_unverified"
    baked_geometry_created: bool = False


def compose_normalization_transform(
    geometry: ObjectCaptureGeometry,
    scale_estimate: ReconstructionScaleEstimate,
    base_plane_selection: BasePlaneSelection,
    upright_alignment: UprightAlignmentResult,
    front_direction: FrontDirectionRecord,
) -> GeometryNormalizationTransform:
    """Compose scale, upright rotation, and front rotation for captured geometry.

    For column vectors the final matrix is ``R_front * R_upright * S``. The
    result references its immutable geometry parent and never writes or bakes it.
    """

    _require_geometry(geometry)
    try:
        base_plane_selection.require_current_geometry(geometry)
        upright_alignment.require_current_selection(base_plane_selection)
    except ValueError as error:
        raise NormalizationError("normalization_stale_geometry_or_upright_parent") from error
    if (
        upright_alignment.geometry_id != geometry.geometry_id
        or upright_alignment.reconstruction_revision != geometry.reconstruction_revision
        or upright_alignment.camera_solution_revision != geometry.camera_solution_revision
    ):
        raise NormalizationError("normalization_upright_parent_revision_mismatch")
    if (
        front_direction.geometry_id != geometry.geometry_id
        or front_direction.base_plane_selection_id != base_plane_selection.selection_id
        or front_direction.upright_alignment_id != upright_alignment.alignment_id
        or front_direction.reconstruction_revision != geometry.reconstruction_revision
        or front_direction.camera_solution_revision != geometry.camera_solution_revision
        or front_direction.coordinate_unit != upright_alignment.coordinate_unit
    ):
        raise NormalizationError("normalization_front_direction_parent_revision_mismatch")
    _validate_front_record(front_direction)
    factor, uncertainty, estimate_digest = _validate_scale_estimate(geometry, scale_estimate)

    scale_provenance_id = f"scale-estimate:{estimate_digest}"
    scale = NormalizedFrameTransform(
        transform_id=f"normalization-scale:{estimate_digest}",
        source_frame=SOURCE_GEOMETRY_FRAME,
        target_frame=SCALED_GEOMETRY_FRAME,
        reconstruction_revision=geometry.reconstruction_revision,
        scale_state=ScaleState.METRIC_UNVERIFIED,
        input_unit="reconstruction_units",
        coordinate_unit="mm_unverified",
        matrix=_scale_matrix(factor),
        method="accepted_reconstruction_scale_estimate",
        scale_provenance_id=scale_provenance_id,
    )
    upright = NormalizedFrameTransform(
        transform_id=f"upright:{upright_alignment.alignment_id}",
        source_frame=SCALED_GEOMETRY_FRAME,
        target_frame=UPRIGHT_GEOMETRY_FRAME,
        reconstruction_revision=geometry.reconstruction_revision,
        scale_state=ScaleState.METRIC_UNVERIFIED,
        input_unit="mm_unverified",
        coordinate_unit="mm_unverified",
        matrix=upright_alignment.rotation_matrix,
        method=upright_alignment.method_version,
        scale_provenance_id=scale_provenance_id,
        parent_transform_ids=(f"base-plane:{base_plane_selection.selection_id}",),
    )
    front = NormalizedFrameTransform(
        transform_id=f"front:{front_direction.revision_id.removeprefix('front:')}",
        source_frame=UPRIGHT_GEOMETRY_FRAME,
        target_frame=PACKLAB_NORMALIZED_FRAME,
        reconstruction_revision=geometry.reconstruction_revision,
        scale_state=ScaleState.METRIC_UNVERIFIED,
        input_unit="mm_unverified",
        coordinate_unit="mm_unverified",
        matrix=_front_rotation(front_direction.direction),
        method="align_selected_front_to_positive_y_v1",
        scale_provenance_id=scale_provenance_id,
        parent_transform_ids=(f"front-direction:{front_direction.revision_id}",),
    )
    composed = scale.then(upright).then(front)
    return GeometryNormalizationTransform(
        composed,
        geometry.geometry_id,
        estimate_digest,
        factor,
        uncertainty,
        base_plane_selection.selection_id,
        upright_alignment.alignment_id,
        front_direction.revision_id,
        geometry.scale_state,
    )


def apply_normalization_transform(
    geometry: ObjectCaptureGeometry,
    transform: GeometryNormalizationTransform,
) -> NormalizedGeometryView:
    """Return transformed points in memory without modifying or replacing geometry."""

    _require_geometry(geometry)
    if geometry.geometry_id != transform.geometry_id:
        raise NormalizationError("normalization_transform_stale_geometry_parent")
    filtered = tuple(transform.apply_point(point) for point in geometry.filtered_points)
    unfiltered = tuple(transform.apply_point(point) for point in geometry.unfiltered_points)
    if any(not all(math.isfinite(value) for value in point) for point in (*filtered, *unfiltered)):
        raise NormalizationError("normalization_produced_non_finite_geometry")
    return NormalizedGeometryView(
        geometry.geometry_id, transform.transform_id, filtered, unfiltered
    )


def serialize_normalization_transform(transform: GeometryNormalizationTransform) -> bytes:
    return json.dumps(
        transform.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _require_geometry(geometry: ObjectCaptureGeometry) -> None:
    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY" or geometry.generated:
        raise NormalizationError("normalization_requires_non_generated_object_capture_geometry")
    if geometry.scale_state is ScaleState.METRIC_VERIFIED:
        raise NormalizationError("normalization_cannot_assert_metric_verified")


def _validate_scale_estimate(
    geometry: ObjectCaptureGeometry, estimate: ReconstructionScaleEstimate
) -> tuple[float, float, str]:
    factor = estimate.reconstruction_units_to_mm
    uncertainty = estimate.uncertainty_mm_per_reconstruction_unit
    if (
        estimate.status != "estimated"
        or estimate.metric_state != "METRIC_UNVERIFIED"
        or factor is None
        or not _positive_finite(factor)
        or uncertainty is None
        or not _positive_finite(uncertainty)
        or estimate.provenance.get("input_geometry_unit") != "reconstruction_units"
        or estimate.provenance.get("output_unit") != "mm_per_reconstruction_unit"
        or estimate.provenance.get("metric_state") != "METRIC_UNVERIFIED"
        or estimate.provenance.get("reconstruction_revision") != geometry.reconstruction_revision
        or estimate.provenance.get("camera_solution_revision") != geometry.camera_solution_revision
    ):
        raise NormalizationError("normalization_scale_estimate_invalid_or_stale")
    encoded = json.dumps(
        estimate.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    return factor, uncertainty, hashlib.sha256(encoded).hexdigest()


def _validate_front_record(record: FrontDirectionRecord) -> None:
    try:
        regenerated = select_front_direction(
            record.direction,
            source=record.source,
            actor_id=record.actor_id,
            evidence_id=record.evidence_id,
            base_plane_selection_id=record.base_plane_selection_id,
            upright_alignment_id=record.upright_alignment_id,
            geometry_id=record.geometry_id,
            reconstruction_revision=record.reconstruction_revision,
            camera_solution_revision=record.camera_solution_revision,
            coordinate_unit=record.coordinate_unit,
        )
    except ValueError as error:
        raise NormalizationError("normalization_front_direction_invalid") from error
    if regenerated.revision_id != record.revision_id or regenerated.direction != record.direction:
        raise NormalizationError("normalization_front_direction_identity_mismatch")


def _scale_matrix(factor: float) -> Matrix4:
    return (
        factor,
        0.0,
        0.0,
        0.0,
        0.0,
        factor,
        0.0,
        0.0,
        0.0,
        0.0,
        factor,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )


def _front_rotation(direction: Point3) -> Matrix4:
    x, y, z = direction
    if not all(math.isfinite(value) for value in direction) or abs(z) > 1e-9:
        raise NormalizationError("normalization_front_direction_must_be_horizontal")
    magnitude = math.hypot(x, y)
    if magnitude <= 1e-12:
        raise NormalizationError("normalization_front_direction_degenerate")
    cosine = y / magnitude
    sine = x / magnitude
    return (
        cosine,
        -sine,
        0.0,
        0.0,
        sine,
        cosine,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0.0
    )
