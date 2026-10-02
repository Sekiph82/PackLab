"""Estimate enclosed volume from an explicit, topologically closed interior shell."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .bounding_dimensions import NormalizedMeasurementGeometry
from .reconstruction import ScaleState

CAPACITY_METHOD_VERSION = "oriented_triangle_shell_signed_volume_v1"
INTERIOR_CLOSURE_ASSUMPTION = "explicit_interior_shell_complete_watertight_v1"
MAX_INTERIOR_VERTICES = 1_000_000
MAX_INTERIOR_FACES = 2_000_000
Point3 = tuple[float, float, float]
Triangle = tuple[int, int, int]


class CapacityEstimationError(ValueError):
    """Raised when the explicit interior representation cannot support a volume estimate."""


@dataclass(frozen=True, slots=True)
class InteriorVolumeRepresentation:
    representation_id: str
    representation_revision: str
    source_geometry_id: str
    normalized_geometry_revision: str
    scale_provenance_id: str | None
    coordinate_unit: str
    vertices: tuple[Point3, ...]
    triangles: tuple[Triangle, ...]
    assumption_evidence_id: str
    closure_assumption: str = INTERIOR_CLOSURE_ASSUMPTION
    authority_class: str = "EXPLICIT_INTERIOR_ASSUMPTION"
    generated: bool = False

    def __post_init__(self) -> None:
        for name in (
            "representation_id",
            "representation_revision",
            "source_geometry_id",
            "normalized_geometry_revision",
            "coordinate_unit",
            "assumption_evidence_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise CapacityEstimationError(f"interior_{name}_required")
        if self.closure_assumption != INTERIOR_CLOSURE_ASSUMPTION:
            raise CapacityEstimationError("interior_closure_assumption_unknown")
        if self.authority_class != "EXPLICIT_INTERIOR_ASSUMPTION" or self.generated:
            raise CapacityEstimationError("interior_representation_must_be_explicit_non_generated")
        if not isinstance(self.vertices, tuple) or not isinstance(self.triangles, tuple):
            raise CapacityEstimationError("interior_mesh_arrays_must_be_immutable_tuples")
        if not 4 <= len(self.vertices) <= MAX_INTERIOR_VERTICES:
            raise CapacityEstimationError("interior_vertex_count_out_of_bounds")
        if not 4 <= len(self.triangles) <= MAX_INTERIOR_FACES:
            raise CapacityEstimationError("interior_face_count_out_of_bounds")
        for point in self.vertices:
            if len(point) != 3 or any(not _finite(value) for value in point):
                raise CapacityEstimationError("interior_mesh_vertex_non_finite_or_invalid")
        for triangle in self.triangles:
            if (
                len(triangle) != 3
                or any(not _index(index) or index >= len(self.vertices) for index in triangle)
                or len(set(triangle)) != 3
            ):
                raise CapacityEstimationError("interior_mesh_triangle_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "representation_id": self.representation_id,
            "representation_revision": self.representation_revision,
            "source_geometry_id": self.source_geometry_id,
            "normalized_geometry_revision": self.normalized_geometry_revision,
            "scale_provenance_id": self.scale_provenance_id,
            "coordinate_unit": self.coordinate_unit,
            "vertex_count": len(self.vertices),
            "triangle_count": len(self.triangles),
            "assumption_evidence_id": self.assumption_evidence_id,
            "closure_assumption": self.closure_assumption,
            "authority_class": self.authority_class,
            "generated": self.generated,
        }


@dataclass(frozen=True, slots=True)
class CapacityEstimate:
    estimate_id: str
    source_geometry_id: str
    normalized_geometry_revision: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    interior_representation_id: str
    interior_representation_revision: str
    assumption_evidence_id: str
    method_version: str
    capacity: float
    capacity_unit: str
    source_volume: float
    source_volume_unit: str
    signed_volume_orientation: str
    watertight_edge_count: int
    triangle_count: int
    uncertainty_inputs: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.capacity-estimate.v1",
            "estimate_id": self.estimate_id,
            "source_geometry_id": self.source_geometry_id,
            "normalized_geometry_revision": self.normalized_geometry_revision,
            "scale_provenance_id": self.scale_provenance_id,
            "scale_state": self.scale_state.value,
            "interior_representation": {
                "representation_id": self.interior_representation_id,
                "representation_revision": self.interior_representation_revision,
                "assumption_evidence_id": self.assumption_evidence_id,
                "closure_assumption": INTERIOR_CLOSURE_ASSUMPTION,
                "authority_class": "EXPLICIT_INTERIOR_ASSUMPTION",
            },
            "algorithm": {
                "method_version": self.method_version,
                "formula": "absolute signed sum of origin-relative triangle tetrahedra",
                "closure_validation": "each undirected edge occurs exactly twice with opposite orientation",
                "watertight_edge_count": self.watertight_edge_count,
                "triangle_count": self.triangle_count,
            },
            "capacity": self.capacity,
            "capacity_unit": self.capacity_unit,
            "source_volume": self.source_volume,
            "source_volume_unit": self.source_volume_unit,
            "signed_volume_orientation": self.signed_volume_orientation,
            "uncertainty_and_limitations": dict(self.uncertainty_inputs),
            "exterior_geometry_used_as_interior": False,
            "wall_thickness_inferred": False,
            "certified_volume_claimed": False,
            "physical_accuracy_claimed": False,
            "authority_class": "EXPLICIT_INTERIOR_ASSUMPTION",
            "generated": False,
        }


def estimate_capacity(
    geometry: NormalizedMeasurementGeometry,
    interior: InteriorVolumeRepresentation,
    *,
    requested_unit: str = "native_cubed",
    current_geometry_id: str,
    current_normalized_geometry_revision: str,
    current_scale_provenance_id: str | None,
) -> CapacityEstimate:
    """Estimate volume from an explicit closed interior shell; never infer cavity geometry."""

    if geometry.source_geometry_id != current_geometry_id:
        raise CapacityEstimationError("capacity_source_geometry_parent_stale")
    if geometry.normalized_geometry_revision != current_normalized_geometry_revision:
        raise CapacityEstimationError("capacity_normalized_geometry_parent_stale")
    if geometry.scale_provenance_id != current_scale_provenance_id:
        raise CapacityEstimationError("capacity_scale_provenance_parent_stale")
    if geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY" or geometry.generated:
        raise CapacityEstimationError("capacity_requires_captured_geometry_parent")
    if (
        interior.source_geometry_id != geometry.source_geometry_id
        or interior.normalized_geometry_revision != geometry.normalized_geometry_revision
        or interior.scale_provenance_id != geometry.scale_provenance_id
    ):
        raise CapacityEstimationError("capacity_interior_geometry_parent_mismatch")
    if interior.coordinate_unit != geometry.coordinate_unit:
        raise CapacityEstimationError("capacity_interior_coordinate_unit_mismatch")
    if requested_unit not in {"native_cubed", "litre", "millilitre"}:
        raise CapacityEstimationError("capacity_requested_unit_unsupported")
    if (
        requested_unit in {"litre", "millilitre"}
        and geometry.scale_state is not ScaleState.METRIC_VERIFIED
    ):
        raise CapacityEstimationError("capacity_litre_units_require_verified_metric_scale")
    watertight_edges = _validate_closed_oriented_shell(interior.triangles)
    signed_volume = _signed_mesh_volume(interior.vertices, interior.triangles)
    if not math.isfinite(signed_volume):
        raise CapacityEstimationError("capacity_volume_non_finite")
    bounds = tuple(
        max(point[axis] for point in interior.vertices)
        - min(point[axis] for point in interior.vertices)
        for axis in range(3)
    )
    characteristic_length = max(bounds)
    if characteristic_length <= 0.0 or abs(signed_volume) <= 1e-12 * characteristic_length**3:
        raise CapacityEstimationError("capacity_interior_volume_degenerate")
    source_volume = abs(signed_volume)
    if requested_unit == "litre":
        capacity, capacity_unit = source_volume / 1_000_000.0, "L"
    elif requested_unit == "millilitre":
        capacity, capacity_unit = source_volume / 1_000.0, "mL"
    else:
        capacity = source_volume
        capacity_unit = f"{geometry.coordinate_unit}^3"
    uncertainty_inputs: dict[str, object] = {
        "scale_factor_uncertainty": geometry.scale_factor_uncertainty,
        "scale_factor_uncertainty_unit": geometry.scale_factor_uncertainty_unit,
        "scale_uncertainty_propagated_to_volume": False,
        "mesh_discretization_uncertainty": "not quantified",
        "interior_shape_and_closure": "supplied assumption; not established from exterior capture",
        "self_intersection_validation": "not performed",
        "confidence_interval_estimated": False,
    }
    body: dict[str, object] = {
        "source_geometry_id": geometry.source_geometry_id,
        "normalized_geometry_revision": geometry.normalized_geometry_revision,
        "scale_provenance_id": geometry.scale_provenance_id,
        "scale_state": geometry.scale_state.value,
        "interior": interior.as_dict(),
        "method_version": CAPACITY_METHOD_VERSION,
        "source_volume": source_volume,
        "source_volume_unit": f"{geometry.coordinate_unit}^3",
        "capacity": capacity,
        "capacity_unit": capacity_unit,
        "requested_unit": requested_unit,
        "uncertainty_inputs": uncertainty_inputs,
    }
    estimate_id = (
        "capacity-estimate:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return CapacityEstimate(
        estimate_id,
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        geometry.scale_provenance_id,
        geometry.scale_state,
        interior.representation_id,
        interior.representation_revision,
        interior.assumption_evidence_id,
        CAPACITY_METHOD_VERSION,
        capacity,
        capacity_unit,
        source_volume,
        f"{geometry.coordinate_unit}^3",
        "outward" if signed_volume > 0.0 else "inward",
        watertight_edges,
        len(interior.triangles),
        uncertainty_inputs,
    )


def serialize_capacity_estimate(estimate: CapacityEstimate) -> bytes:
    return json.dumps(
        estimate.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _validate_closed_oriented_shell(triangles: tuple[Triangle, ...]) -> int:
    edge_directions: dict[tuple[int, int], list[int]] = {}
    for triangle in triangles:
        for start, end in (
            (triangle[0], triangle[1]),
            (triangle[1], triangle[2]),
            (triangle[2], triangle[0]),
        ):
            key = (min(start, end), max(start, end))
            direction = 1 if (start, end) == key else -1
            directions = edge_directions.setdefault(key, [])
            directions.append(direction)
            if len(directions) > 2:
                raise CapacityEstimationError("capacity_interior_shell_non_manifold_edge")
    if not edge_directions or any(len(directions) != 2 for directions in edge_directions.values()):
        raise CapacityEstimationError("capacity_interior_shell_open_or_non_watertight")
    if any(sum(directions) != 0 for directions in edge_directions.values()):
        raise CapacityEstimationError("capacity_interior_shell_inconsistent_face_orientation")
    return len(edge_directions)


def _signed_mesh_volume(vertices: tuple[Point3, ...], triangles: tuple[Triangle, ...]) -> float:
    origin = vertices[0]
    tetra_volumes = []
    for first, second, third in triangles:
        a = tuple(vertices[first][axis] - origin[axis] for axis in range(3))
        b = tuple(vertices[second][axis] - origin[axis] for axis in range(3))
        c = tuple(vertices[third][axis] - origin[axis] for axis in range(3))
        cross = (
            b[1] * c[2] - b[2] * c[1],
            b[2] * c[0] - b[0] * c[2],
            b[0] * c[1] - b[1] * c[0],
        )
        tetra_volumes.append((a[0] * cross[0] + a[1] * cross[1] + a[2] * cross[2]) / 6.0)
    return math.fsum(tetra_volumes)


def _index(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
