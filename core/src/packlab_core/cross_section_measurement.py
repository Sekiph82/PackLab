"""Deterministic radius and diameter estimates for selected captured sections."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .bounding_dimensions import NormalizedMeasurementGeometry
from .reconstruction import ScaleState

CROSS_SECTION_METHOD_VERSION = "pca_covariance_ellipse_v1"
MAX_SECTION_POINTS = 100_000
MIN_SECTION_POINTS = 5
Point3 = tuple[float, float, float]


class CrossSectionMeasurementError(ValueError):
    """Raised when a selected section is invalid, stale, or degenerate."""


@dataclass(frozen=True, slots=True)
class CrossSectionSelection:
    selection_id: str
    source_geometry_id: str
    normalized_geometry_revision: str
    point_indices: tuple[int, ...]
    plane_origin: Point3
    plane_normal: Point3
    planarity_tolerance: float

    def __post_init__(self) -> None:
        if not isinstance(self.selection_id, str) or not self.selection_id.strip():
            raise CrossSectionMeasurementError("section_selection_id_required")
        if not isinstance(self.source_geometry_id, str) or not self.source_geometry_id.strip():
            raise CrossSectionMeasurementError("section_source_geometry_id_required")
        if (
            not isinstance(self.normalized_geometry_revision, str)
            or not self.normalized_geometry_revision.strip()
        ):
            raise CrossSectionMeasurementError("section_normalized_revision_required")
        if not isinstance(self.point_indices, tuple):
            raise CrossSectionMeasurementError("section_point_indices_must_be_immutable")
        if len(self.point_indices) < MIN_SECTION_POINTS:
            raise CrossSectionMeasurementError("section_insufficient_points")
        if len(self.point_indices) > MAX_SECTION_POINTS:
            raise CrossSectionMeasurementError("section_point_count_out_of_bounds")
        if any(not _is_index(index) for index in self.point_indices):
            raise CrossSectionMeasurementError("section_point_index_invalid")
        if len(set(self.point_indices)) != len(self.point_indices):
            raise CrossSectionMeasurementError("section_point_indices_duplicate")
        origin = _point3(self.plane_origin, "section_plane_origin_invalid")
        normal = _point3(self.plane_normal, "section_plane_normal_invalid")
        norm = math.sqrt(math.fsum(value * value for value in normal))
        if not math.isfinite(norm) or norm <= 0.0:
            raise CrossSectionMeasurementError("section_plane_normal_degenerate")
        if abs(norm - 1.0) > 1e-6:
            raise CrossSectionMeasurementError("section_plane_normal_must_be_unit_length")
        if not _nonnegative_finite(self.planarity_tolerance):
            raise CrossSectionMeasurementError("section_planarity_tolerance_invalid")
        object.__setattr__(self, "plane_origin", origin)
        object.__setattr__(self, "plane_normal", normal)


@dataclass(frozen=True, slots=True)
class CrossSectionMeasurement:
    measurement_id: str
    selection_id: str
    source_geometry_id: str
    normalized_geometry_revision: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    coordinate_unit: str
    method_version: str
    center: Point3
    plane_basis: tuple[Point3, Point3]
    major_radius: float
    minor_radius: float
    major_diameter: float
    minor_diameter: float
    rms_radial_residual: float
    maximum_radial_residual: float
    maximum_planarity_residual: float
    sample_count: int
    scale_factor_uncertainty: float | None
    scale_factor_uncertainty_unit: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.cross-section-measurement.v1",
            "measurement_id": self.measurement_id,
            "selection_id": self.selection_id,
            "source_geometry_id": self.source_geometry_id,
            "normalized_geometry_revision": self.normalized_geometry_revision,
            "scale_provenance_id": self.scale_provenance_id,
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "method_version": self.method_version,
            "fit_method": "project to deterministic plane basis; center by sample centroid; use 2x2 covariance principal axes; report sqrt(2 * eigenvalue) as each semi-axis",
            "center": list(self.center),
            "plane_basis": [list(axis) for axis in self.plane_basis],
            "radii": {"major": self.major_radius, "minor": self.minor_radius},
            "diameters": {"major": self.major_diameter, "minor": self.minor_diameter},
            "quality": {
                "sample_count": self.sample_count,
                "rms_radial_residual": self.rms_radial_residual,
                "maximum_radial_residual": self.maximum_radial_residual,
                "maximum_planarity_residual": self.maximum_planarity_residual,
                "residual_unit": self.coordinate_unit,
                "coverage_assumption": "approximately_uniform_section_sampling; inspect residuals for sparse or uneven coverage",
            },
            "uncertainty_inputs": {
                "scale_factor_uncertainty": self.scale_factor_uncertainty,
                "scale_factor_uncertainty_unit": self.scale_factor_uncertainty_unit,
                "propagation_status": "preserved_for_PL-0217",
                "fit_uncertainty_status": "residuals_reported; statistical confidence interval not estimated",
            },
            "authority_class": "OBJECT_CAPTURE_GEOMETRY",
            "generated": False,
            "physical_accuracy_claimed": False,
            "thread_or_finish_standard_inferred": False,
        }


def measure_cross_section(
    geometry: NormalizedMeasurementGeometry,
    selection: CrossSectionSelection,
    *,
    current_geometry_id: str,
    current_normalized_geometry_revision: str,
    current_scale_provenance_id: str | None,
) -> CrossSectionMeasurement:
    """Estimate the principal radii of an explicitly selected planar point set."""

    if geometry.source_geometry_id != current_geometry_id:
        raise CrossSectionMeasurementError("section_source_geometry_parent_stale")
    if geometry.normalized_geometry_revision != current_normalized_geometry_revision:
        raise CrossSectionMeasurementError("section_normalized_geometry_parent_stale")
    if geometry.scale_provenance_id != current_scale_provenance_id:
        raise CrossSectionMeasurementError("section_scale_provenance_parent_stale")
    if (
        selection.source_geometry_id != geometry.source_geometry_id
        or selection.normalized_geometry_revision != geometry.normalized_geometry_revision
    ):
        raise CrossSectionMeasurementError("section_selection_parent_stale")
    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY" or geometry.generated:
        raise CrossSectionMeasurementError("section_requires_captured_geometry_authority")
    if max(selection.point_indices) >= len(geometry.points):
        raise CrossSectionMeasurementError("section_point_index_out_of_range")

    selected = tuple(geometry.points[index] for index in selection.point_indices)
    plane_residuals = tuple(
        abs(
            math.fsum(
                (point[axis] - selection.plane_origin[axis]) * selection.plane_normal[axis]
                for axis in range(3)
            )
        )
        for point in selected
    )
    maximum_planarity_residual = max(plane_residuals)
    if (
        not math.isfinite(maximum_planarity_residual)
        or maximum_planarity_residual > selection.planarity_tolerance
    ):
        raise CrossSectionMeasurementError("section_points_not_planar_within_tolerance")

    basis = _plane_basis(selection.plane_normal)
    projected = tuple(
        (
            math.fsum(
                (point[axis] - selection.plane_origin[axis]) * basis[0][axis] for axis in range(3)
            ),
            math.fsum(
                (point[axis] - selection.plane_origin[axis]) * basis[1][axis] for axis in range(3)
            ),
        )
        for point in selected
    )
    center_2d = (
        math.fsum(point[0] for point in projected) / len(projected),
        math.fsum(point[1] for point in projected) / len(projected),
    )
    centered = tuple((point[0] - center_2d[0], point[1] - center_2d[1]) for point in projected)
    cxx = math.fsum(point[0] * point[0] for point in centered) / len(centered)
    cyy = math.fsum(point[1] * point[1] for point in centered) / len(centered)
    cxy = math.fsum(point[0] * point[1] for point in centered) / len(centered)
    trace = cxx + cyy
    discriminant = math.hypot(cxx - cyy, 2.0 * cxy)
    eigenvalues = ((trace + discriminant) / 2.0, (trace - discriminant) / 2.0)
    scale = max(cxx, cyy, abs(cxy))
    if not all(math.isfinite(value) for value in (*center_2d, cxx, cyy, cxy, *eigenvalues)):
        raise CrossSectionMeasurementError("section_fit_non_finite")
    if scale <= 0.0 or eigenvalues[1] <= 1e-12 * scale:
        raise CrossSectionMeasurementError("section_points_degenerate_or_collinear")
    major_radius, minor_radius = (math.sqrt(2.0 * value) for value in eigenvalues)
    if not all(math.isfinite(value) and value > 0.0 for value in (major_radius, minor_radius)):
        raise CrossSectionMeasurementError("section_radii_degenerate")

    if discriminant <= 1e-12 * scale:
        major_axis_2d = (1.0, 0.0)
    else:
        angle = 0.5 * math.atan2(2.0 * cxy, cxx - cyy)
        major_axis_2d = (math.cos(angle), math.sin(angle))
    minor_axis_2d = (-major_axis_2d[1], major_axis_2d[0])
    residuals = tuple(
        abs(
            math.hypot(
                (
                    (point[0] - center_2d[0]) * major_axis_2d[0]
                    + (point[1] - center_2d[1]) * major_axis_2d[1]
                )
                / major_radius,
                (
                    (point[0] - center_2d[0]) * minor_axis_2d[0]
                    + (point[1] - center_2d[1]) * minor_axis_2d[1]
                )
                / minor_radius,
            )
            - 1.0
        )
        * (major_radius + minor_radius)
        / 2.0
        for point in projected
    )
    rms_residual = math.sqrt(math.fsum(value * value for value in residuals) / len(residuals))
    maximum_residual = max(residuals)
    center = (
        math.fsum(
            (selection.plane_origin[0], center_2d[0] * basis[0][0], center_2d[1] * basis[1][0])
        ),
        math.fsum(
            (selection.plane_origin[1], center_2d[0] * basis[0][1], center_2d[1] * basis[1][1])
        ),
        math.fsum(
            (selection.plane_origin[2], center_2d[0] * basis[0][2], center_2d[1] * basis[1][2])
        ),
    )
    body: dict[str, object] = {
        "selection_id": selection.selection_id,
        "source_geometry_id": geometry.source_geometry_id,
        "normalized_geometry_revision": geometry.normalized_geometry_revision,
        "scale_provenance_id": geometry.scale_provenance_id,
        "scale_state": geometry.scale_state.value,
        "coordinate_unit": geometry.coordinate_unit,
        "method_version": CROSS_SECTION_METHOD_VERSION,
        "point_indices": list(selection.point_indices),
        "plane_origin": list(selection.plane_origin),
        "plane_normal": list(selection.plane_normal),
        "planarity_tolerance": selection.planarity_tolerance,
        "major_radius": major_radius,
        "minor_radius": minor_radius,
        "rms_radial_residual": rms_residual,
        "maximum_radial_residual": maximum_residual,
        "maximum_planarity_residual": maximum_planarity_residual,
    }
    measurement_id = (
        "cross-section:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return CrossSectionMeasurement(
        measurement_id,
        selection.selection_id,
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        geometry.scale_provenance_id,
        geometry.scale_state,
        geometry.coordinate_unit,
        CROSS_SECTION_METHOD_VERSION,
        center,
        (basis[0], basis[1]),
        major_radius,
        minor_radius,
        major_radius * 2.0,
        minor_radius * 2.0,
        rms_residual,
        maximum_residual,
        maximum_planarity_residual,
        len(selected),
        geometry.scale_factor_uncertainty,
        geometry.scale_factor_uncertainty_unit,
    )


def serialize_cross_section_measurement(result: CrossSectionMeasurement) -> bytes:
    return json.dumps(
        result.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _plane_basis(normal: Point3) -> tuple[Point3, Point3]:
    reference = (1.0, 0.0, 0.0) if abs(normal[0]) < 0.9 else (0.0, 1.0, 0.0)
    first = _normalize(_cross(normal, reference))
    second = _normalize(_cross(normal, first))
    return first, second


def _cross(first: Point3, second: Point3) -> Point3:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _normalize(vector: Point3) -> Point3:
    magnitude = math.sqrt(math.fsum(value * value for value in vector))
    if not math.isfinite(magnitude) or magnitude <= 0.0:
        raise CrossSectionMeasurementError("section_plane_basis_degenerate")
    return (
        vector[0] / magnitude,
        vector[1] / magnitude,
        vector[2] / magnitude,
    )


def _point3(value: Point3, error: str) -> Point3:
    if len(value) != 3 or any(not _finite(component) for component in value):
        raise CrossSectionMeasurementError(error)
    return (float(value[0]), float(value[1]), float(value[2]))


def _is_index(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _nonnegative_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0.0
    )
