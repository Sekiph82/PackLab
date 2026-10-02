"""Deterministic axis-aligned dimensions for normalized captured geometry."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .calibration.scale_provenance import ScaleProvenance
from .coordinate_frame import PACKLAB_NORMALIZED_FRAME
from .normalization_transform import (
    GeometryNormalizationTransform,
    NormalizedGeometryView,
)
from .reconstruction import ScaleState

DIMENSION_METHOD_VERSION = "canonical_axis_aligned_bounds_v1"
Point3 = tuple[float, float, float]


class BoundingDimensionError(ValueError):
    """Raised when normalized geometry or scale provenance is unsafe or stale."""


@dataclass(frozen=True, slots=True)
class NormalizedMeasurementGeometry:
    normalized_geometry_revision: str
    source_geometry_id: str
    points: tuple[Point3, ...]
    scale_state: ScaleState
    coordinate_unit: str
    scale_provenance_id: str | None
    scale_factor_uncertainty: float | None
    scale_factor_uncertainty_unit: str | None
    authority_class: str = "OBJECT_CAPTURE_GEOMETRY"
    generated: bool = False
    scale_provenance_record: ScaleProvenance | None = None
    coordinate_frame_id: str = PACKLAB_NORMALIZED_FRAME

    def __post_init__(self) -> None:
        for name in ("normalized_geometry_revision", "source_geometry_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise BoundingDimensionError(f"{name}_required")
        if not isinstance(self.scale_state, ScaleState):
            raise BoundingDimensionError("scale_state_invalid")
        expected_unit = {
            ScaleState.RELATIVE: "reconstruction_units",
            ScaleState.METRIC_UNVERIFIED: "mm_unverified",
            ScaleState.METRIC_VERIFIED: "mm",
        }[self.scale_state]
        if self.coordinate_unit != expected_unit:
            raise BoundingDimensionError("coordinate_unit_conflicts_with_scale_state")
        if self.coordinate_frame_id != PACKLAB_NORMALIZED_FRAME:
            raise BoundingDimensionError("normalized_geometry_frame_not_canonical")
        if self.scale_state is ScaleState.RELATIVE:
            if self.scale_provenance_id is not None:
                raise BoundingDimensionError("relative_geometry_cannot_claim_scale_provenance")
            if self.scale_factor_uncertainty is not None:
                raise BoundingDimensionError("relative_geometry_cannot_claim_scale_uncertainty")
            if self.scale_provenance_record is not None:
                raise BoundingDimensionError("relative_geometry_cannot_claim_scale_record")
        else:
            if (
                not isinstance(self.scale_provenance_id, str)
                or not self.scale_provenance_id.strip()
            ):
                raise BoundingDimensionError("metric_geometry_scale_provenance_required")
            if not _positive_finite(self.scale_factor_uncertainty):
                raise BoundingDimensionError("metric_geometry_scale_uncertainty_required")
            if self.scale_factor_uncertainty_unit != "mm_per_reconstruction_unit":
                raise BoundingDimensionError("scale_uncertainty_unit_invalid")
            if self.scale_provenance_record is not None and (
                self.scale_provenance_record.provenance_id != self.scale_provenance_id
                or self.scale_provenance_record.scale_state is not self.scale_state
            ):
                raise BoundingDimensionError("scale_provenance_record_mismatch")
            if (
                self.scale_state is ScaleState.METRIC_VERIFIED
                and self.scale_provenance_record is None
            ):
                raise BoundingDimensionError("verified_scale_provenance_record_required")
        if not isinstance(self.points, tuple):
            raise BoundingDimensionError("normalized_points_must_be_immutable_tuple")
        for point in self.points:
            if len(point) != 3 or any(not _finite(value) for value in point):
                raise BoundingDimensionError("normalized_geometry_contains_non_finite_point")
        if self.authority_class != "OBJECT_CAPTURE_GEOMETRY" or self.generated is not False:
            raise BoundingDimensionError("dimensions_require_captured_geometry_authority")


@dataclass(frozen=True, slots=True)
class BoundingDimensions:
    measurement_id: str
    normalized_geometry_revision: str
    source_geometry_id: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    coordinate_unit: str
    height: float
    width: float
    depth: float
    axis_bounds: Mapping[str, tuple[float, float]]
    uncertainty_inputs: Mapping[str, object]
    method_version: str = DIMENSION_METHOD_VERSION

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.bounding-dimensions.v1",
            "measurement_id": self.measurement_id,
            "method_version": self.method_version,
            "normalized_geometry_revision": self.normalized_geometry_revision,
            "source_geometry_id": self.source_geometry_id,
            "scale_provenance_id": self.scale_provenance_id,
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "dimensions": {
                "height": self.height,
                "width": self.width,
                "depth": self.depth,
            },
            "axis_bounds": {key: list(value) for key, value in self.axis_bounds.items()},
            "uncertainty_inputs": dict(self.uncertainty_inputs),
            "authority_class": "OBJECT_CAPTURE_GEOMETRY",
            "generated": False,
            "dimension_uncertainty_propagated": False,
            "physical_accuracy_claimed": False,
        }


def measurement_geometry_from_normalized_view(
    view: NormalizedGeometryView,
    transform: GeometryNormalizationTransform,
    *,
    scale_provenance: ScaleProvenance | None = None,
) -> NormalizedMeasurementGeometry:
    """Bind a normalized view to the current transform and optional persisted scale record."""

    if (
        view.transform_id != transform.transform_id
        or view.source_geometry_id != transform.geometry_id
        or transform.transform.target_frame != "packlab_right_handed_x_right_y_front_z_up_v1"
    ):
        raise BoundingDimensionError("normalized_geometry_or_transform_parent_stale")
    state = transform.transform.scale_state
    scale_provenance_id = transform.transform.scale_provenance_id
    uncertainty = transform.scale_uncertainty_mm_per_reconstruction_unit
    if scale_provenance is not None:
        if (
            scale_provenance.input_reconstruction_revision
            != transform.transform.reconstruction_revision
            or scale_provenance.estimated_scale_factor_mm_per_reconstruction_unit
            != transform.scale_factor_mm_per_reconstruction_unit
            or scale_provenance.scale_state
            not in {ScaleState.METRIC_UNVERIFIED, ScaleState.METRIC_VERIFIED}
            or scale_provenance.uncertainty is None
            or scale_provenance.uncertainty.get("value") != uncertainty
        ):
            raise BoundingDimensionError("scale_provenance_parent_or_factor_stale")
        state = scale_provenance.scale_state
        scale_provenance_id = scale_provenance.provenance_id
    coordinate_unit = {
        ScaleState.RELATIVE: "reconstruction_units",
        ScaleState.METRIC_UNVERIFIED: "mm_unverified",
        ScaleState.METRIC_VERIFIED: "mm",
    }[state]
    return NormalizedMeasurementGeometry(
        transform.transform_id,
        transform.geometry_id,
        view.filtered_points,
        state,
        coordinate_unit,
        None if state is ScaleState.RELATIVE else scale_provenance_id,
        None if state is ScaleState.RELATIVE else uncertainty,
        None if state is ScaleState.RELATIVE else "mm_per_reconstruction_unit",
        view.authority_class,
        view.generated,
        scale_provenance,
    )


def measure_bounding_dimensions(
    geometry: NormalizedMeasurementGeometry,
    *,
    current_geometry_id: str,
    current_normalized_geometry_revision: str,
    current_scale_provenance_id: str | None,
) -> BoundingDimensions:
    """Measure width (+X), depth (+Y), and height (+Z) by canonical min/max bounds."""

    if geometry.source_geometry_id != current_geometry_id:
        raise BoundingDimensionError("normalized_geometry_source_parent_stale")
    if geometry.normalized_geometry_revision != current_normalized_geometry_revision:
        raise BoundingDimensionError("normalized_geometry_revision_stale")
    if geometry.scale_provenance_id != current_scale_provenance_id:
        raise BoundingDimensionError("normalized_geometry_scale_provenance_stale")
    if not geometry.points:
        raise BoundingDimensionError("normalized_geometry_empty")
    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY" or geometry.generated:
        raise BoundingDimensionError("dimensions_require_captured_geometry_authority")
    lows = tuple(min(point[axis] for point in geometry.points) for axis in range(3))
    highs = tuple(max(point[axis] for point in geometry.points) for axis in range(3))
    spans = tuple(highs[axis] - lows[axis] for axis in range(3))
    if not all(_finite(value) for value in (*lows, *highs, *spans)):
        raise BoundingDimensionError("bounding_dimensions_non_finite")
    bounds = {axis: (lows[index], highs[index]) for index, axis in enumerate(("x", "y", "z"))}
    uncertainty_inputs: dict[str, object] = {
        "scale_factor_uncertainty": geometry.scale_factor_uncertainty,
        "scale_factor_uncertainty_unit": geometry.scale_factor_uncertainty_unit,
        "propagation_status": "preserved_for_PL-0217",
    }
    body: dict[str, object] = {
        "method_version": DIMENSION_METHOD_VERSION,
        "normalized_geometry_revision": geometry.normalized_geometry_revision,
        "source_geometry_id": geometry.source_geometry_id,
        "scale_provenance_id": geometry.scale_provenance_id,
        "scale_state": geometry.scale_state.value,
        "coordinate_unit": geometry.coordinate_unit,
        "height": spans[2],
        "width": spans[0],
        "depth": spans[1],
        "axis_bounds": {key: list(value) for key, value in bounds.items()},
        "uncertainty_inputs": uncertainty_inputs,
    }
    measurement_id = (
        "bounding-dimensions:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return BoundingDimensions(
        measurement_id,
        geometry.normalized_geometry_revision,
        geometry.source_geometry_id,
        geometry.scale_provenance_id,
        geometry.scale_state,
        geometry.coordinate_unit,
        spans[2],
        spans[0],
        spans[1],
        MappingProxyType(bounds),
        MappingProxyType(uncertainty_inputs),
    )


def serialize_bounding_dimensions(result: BoundingDimensions) -> bytes:
    return json.dumps(
        result.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0.0
    )
