"""Bounded, provenance-labeled local fan fill driven by a matching hole report."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .geometry_adapter import Point3, TriangleMeshData
from .hole_detection import (
    HOLE_DETECTION_CONTRACT,
    BoundaryLoopReport,
    MeshHoleReport,
)
from .reconstruction import ScaleState

HOLE_FILL_CONTRACT = "packlab.mesh-hole-fill.v1"
PHYSICAL_VALIDATION_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class HoleFillingError(ValueError):
    """Raised when the report, parent mesh, or repair policy is unsafe."""


@dataclass(frozen=True, slots=True)
class HoleFillingPolicy:
    maximum_perimeter: float = 0.2
    maximum_area: float = 0.01
    maximum_boundary_vertices: int = 16
    maximum_planarity_deviation: float = 0.001
    maximum_selected_holes: int = 32

    def __post_init__(self) -> None:
        for name in ("maximum_perimeter", "maximum_area", "maximum_planarity_deviation"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise HoleFillingError(f"{name} must be finite and positive")
        if (
            isinstance(self.maximum_boundary_vertices, bool)
            or not isinstance(self.maximum_boundary_vertices, int)
            or not 3 <= self.maximum_boundary_vertices <= 64
        ):
            raise HoleFillingError("maximum_boundary_vertices must be between 3 and 64")
        if (
            isinstance(self.maximum_selected_holes, bool)
            or not isinstance(self.maximum_selected_holes, int)
            or not 1 <= self.maximum_selected_holes <= 32
        ):
            raise HoleFillingError("maximum_selected_holes must be between 1 and 32")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": HOLE_FILL_CONTRACT,
            "maximum_perimeter": float(self.maximum_perimeter),
            "maximum_area": float(self.maximum_area),
            "maximum_boundary_vertices": self.maximum_boundary_vertices,
            "maximum_planarity_deviation": float(self.maximum_planarity_deviation),
            "maximum_selected_holes": self.maximum_selected_holes,
            "repair_method": "local_convex_planar_centroid_fan_v1",
            "derived_face_authority": "REPAIR_DERIVED_NOT_CAPTURED_EVIDENCE",
            "ai_or_generated_completion": False,
            "parent_relative_safety_rules": {
                "maximum_perimeter_at_most_bbox_diagonal": True,
                "maximum_area_at_most_5_percent_bbox_diagonal_squared": True,
                "maximum_planarity_deviation_at_most_2_percent_bbox_diagonal": True,
            },
        }


@dataclass(frozen=True, slots=True)
class FilledHoleEvidence:
    loop_id: str
    center_vertex_index: int
    derived_face_indices: tuple[int, ...]
    derived_triangles: tuple[tuple[int, int, int], ...]
    repair_method: str
    geometry_authority: str


@dataclass(frozen=True, slots=True)
class UnfilledHoleEvidence:
    loop_id: str
    reason: str
    perimeter: float
    approximate_area: float
    boundary_vertex_count: int


@dataclass(frozen=True, slots=True)
class HoleFillingRevision:
    contract: str
    parent_revision_id: str
    child_revision_id: str
    hole_report_id: str
    before_geometry_sha256: str
    after_geometry_sha256: str
    before_mesh: TriangleMeshData
    after_mesh: TriangleMeshData
    policy: HoleFillingPolicy
    selected_loop_ids: tuple[str, ...]
    filled_holes: tuple[FilledHoleEvidence, ...]
    unfilled_holes: tuple[UnfilledHoleEvidence, ...]
    scale_state: ScaleState
    scale_provenance_id: str | None
    physical_accuracy_validation_status: str
    mold_use_authorized: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "parent_revision_id": self.parent_revision_id,
            "child_revision_id": self.child_revision_id,
            "hole_report_id": self.hole_report_id,
            "before_geometry_sha256": self.before_geometry_sha256,
            "after_geometry_sha256": self.after_geometry_sha256,
            "policy": self.policy.as_dict(),
            "selected_loop_ids": self.selected_loop_ids,
            "filled_holes": [
                {
                    "loop_id": item.loop_id,
                    "center_vertex_index": item.center_vertex_index,
                    "derived_face_indices": item.derived_face_indices,
                    "derived_triangles": item.derived_triangles,
                    "repair_method": item.repair_method,
                    "geometry_authority": item.geometry_authority,
                }
                for item in self.filled_holes
            ],
            "unfilled_holes": [
                {
                    "loop_id": item.loop_id,
                    "reason": item.reason,
                    "perimeter": item.perimeter,
                    "approximate_area": item.approximate_area,
                    "boundary_vertex_count": item.boundary_vertex_count,
                }
                for item in self.unfilled_holes
            ],
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
        }


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _geometry_payload(mesh: TriangleMeshData) -> dict[str, object]:
    return {
        "vertices": mesh.vertices,
        "triangles": mesh.triangles,
        "vertex_colors": mesh.vertex_colors,
        "vertex_normals": mesh.vertex_normals,
    }


def _safe_id(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise HoleFillingError(f"{field} must be a non-empty stable identifier")
    if any(ord(char) < 32 for char in value):
        raise HoleFillingError(f"{field} must not contain control characters")
    return value


def _subtract(a: Point3, b: Point3) -> Point3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: Point3, b: Point3) -> Point3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: Point3, b: Point3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _unit(value: Point3) -> Point3 | None:
    magnitude = math.sqrt(_dot(value, value))
    if magnitude <= 1e-15 or not math.isfinite(magnitude):
        return None
    return (value[0] / magnitude, value[1] / magnitude, value[2] / magnitude)


def _loop_normal(vertices: tuple[Point3, ...], indices: tuple[int, ...]) -> Point3 | None:
    total = [0.0, 0.0, 0.0]
    for index, current_index in enumerate(indices):
        current = vertices[current_index]
        following = vertices[indices[(index + 1) % len(indices)]]
        total[0] += current[1] * following[2] - current[2] * following[1]
        total[1] += current[2] * following[0] - current[0] * following[2]
        total[2] += current[0] * following[1] - current[1] * following[0]
    return _unit((total[0], total[1], total[2]))


def _loop_metrics(vertices: tuple[Point3, ...], indices: tuple[int, ...]) -> tuple[float, float]:
    points = tuple(vertices[index] for index in indices)
    perimeter = sum(
        math.dist(points[index], points[(index + 1) % len(points)]) for index in range(len(points))
    )
    normal_sum = [0.0, 0.0, 0.0]
    for index, point in enumerate(points):
        following = points[(index + 1) % len(points)]
        normal_sum[0] += point[1] * following[2] - point[2] * following[1]
        normal_sum[1] += point[2] * following[0] - point[0] * following[2]
        normal_sum[2] += point[0] * following[1] - point[1] * following[0]
    area = 0.5 * math.sqrt(sum(value * value for value in normal_sum))
    return perimeter, area


def _centroid(points: tuple[Point3, ...]) -> Point3:
    return tuple(sum(point[axis] for point in points) / len(points) for axis in range(3))  # type: ignore[return-value]


def _planarity_deviation(points: tuple[Point3, ...], normal: Point3) -> float:
    center = _centroid(points)
    return max(abs(_dot(_subtract(point, center), normal)) for point in points)


def _is_convex(points: tuple[Point3, ...], normal: Point3) -> bool:
    center = _centroid(points)
    signs: list[float] = []
    for index, point in enumerate(points):
        following = points[(index + 1) % len(points)]
        next_point = points[(index + 2) % len(points)]
        turn = _dot(_cross(_subtract(following, point), _subtract(next_point, following)), normal)
        if abs(turn) <= 1e-14:
            return False
        signs.append(turn)
    if not signs or not (all(value > 0 for value in signs) or all(value < 0 for value in signs)):
        return False
    # The vertex centroid must lie on the interior side of every oriented edge.
    for index, point in enumerate(points):
        following = points[(index + 1) % len(points)]
        side = _dot(_cross(_subtract(following, point), _subtract(center, point)), normal)
        if side * signs[0] <= 1e-14:
            return False
    return True


def _edge_support(mesh: TriangleMeshData) -> dict[tuple[int, int], tuple[int, tuple[int, int]]]:
    result: dict[tuple[int, int], tuple[int, tuple[int, int]]] = {}
    counts: dict[tuple[int, int], int] = {}
    for face_index, face in enumerate(mesh.triangles):
        for first, second in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            key = (min(first, second), max(first, second))
            counts[key] = counts.get(key, 0) + 1
            result[key] = (face_index, (first, second))
    return {edge: result[edge] for edge in result if counts[edge] == 1}


def _eligible_reason(
    loop: BoundaryLoopReport,
    mesh: TriangleMeshData,
    support: dict[tuple[int, int], tuple[int, tuple[int, int]]],
    policy: HoleFillingPolicy,
    parent_revision_id: str,
) -> str | None:
    indices = loop.boundary_vertex_indices
    if len(indices) < 3 or len(set(indices)) != len(indices):
        return "invalid-boundary-loop"
    if any(index < 0 or index >= len(mesh.vertices) for index in indices):
        return "boundary-vertex-out-of-range"
    loop_identity = {
        "parent_revision_id": parent_revision_id,
        "boundary_vertex_indices": indices,
        "support_face_indices": loop.support_face_indices,
    }
    if loop.loop_id != f"boundary-loop:{_digest(loop_identity)[:20]}":
        return "reported-loop-identity-does-not-match-parent-evidence"
    actual_perimeter, actual_area = _loop_metrics(mesh.vertices, indices)
    if not math.isclose(loop.perimeter, actual_perimeter, rel_tol=1e-10, abs_tol=1e-12):
        return "reported-perimeter-does-not-match-parent-geometry"
    if not math.isclose(loop.approximate_area, actual_area, rel_tol=1e-10, abs_tol=1e-12):
        return "reported-area-does-not-match-parent-geometry"
    if loop.perimeter > policy.maximum_perimeter:
        return "perimeter-exceeds-limit"
    if loop.approximate_area > policy.maximum_area:
        return "area-exceeds-limit"
    if len(indices) > policy.maximum_boundary_vertices:
        return "boundary-vertex-count-exceeds-limit"
    support_face_ids: list[int] = []
    orientation_signs: list[int] = []
    for position, first in enumerate(indices):
        second = indices[(position + 1) % len(indices)]
        evidence = support.get((min(first, second), max(first, second)))
        if evidence is None:
            return "boundary-edge-no-longer-open-or-stale"
        face_id, directed = evidence
        support_face_ids.append(face_id)
        orientation_signs.append(1 if directed == (first, second) else -1)
    if tuple(sorted(support_face_ids)) != tuple(sorted(loop.support_face_indices)):
        return "boundary-support-evidence-mismatch"
    if len(set(orientation_signs)) != 1:
        return "inconsistent-boundary-winding"
    if loop.touches_uncertain_region is True:
        return "touches-uncertain-region"
    if loop.touches_coverage_gap is True:
        return "touches-known-coverage-gap"
    points = tuple(mesh.vertices[index] for index in indices)
    normal = _loop_normal(mesh.vertices, indices)
    if normal is None:
        return "degenerate-boundary-loop"
    if _planarity_deviation(points, normal) > policy.maximum_planarity_deviation:
        return "planarity-exceeds-limit"
    if not _is_convex(points, normal):
        return "boundary-is-not-strictly-convex"
    return None


def _recompute_normals(mesh: TriangleMeshData) -> tuple[Point3, ...]:
    accumulated = [[0.0, 0.0, 0.0] for _ in mesh.vertices]
    for a, b, c in mesh.triangles:
        face_vector = _cross(
            _subtract(mesh.vertices[b], mesh.vertices[a]),
            _subtract(mesh.vertices[c], mesh.vertices[a]),
        )
        for index in (a, b, c):
            for axis in range(3):
                accumulated[index][axis] += face_vector[axis]
    return tuple(
        _unit((vector[0], vector[1], vector[2])) or (0.0, 0.0, 0.0) for vector in accumulated
    )


def fill_reported_mesh_holes(
    mesh: TriangleMeshData,
    report: MeshHoleReport,
    *,
    parent_revision_id: str,
    scale_state: ScaleState,
    scale_provenance_id: str | None = None,
    policy: HoleFillingPolicy = HoleFillingPolicy(),
    selected_loop_ids: tuple[str, ...] = (),
) -> HoleFillingRevision:
    """Fill only convex, planar, locally bounded loops in the exact current hole report."""

    parent_revision_id = _safe_id(parent_revision_id, "parent_revision_id")
    if not isinstance(scale_state, ScaleState) or scale_state is ScaleState.METRIC_VERIFIED:
        raise HoleFillingError("scale_state must preserve relative or metric-unverified state")
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        scale_provenance_id = _safe_id(scale_provenance_id, "scale_provenance_id")
    elif scale_provenance_id is not None:
        scale_provenance_id = _safe_id(scale_provenance_id, "scale_provenance_id")
    if report.contract != HOLE_DETECTION_CONTRACT:
        raise HoleFillingError("a PL-0229 mesh hole report is required")
    if report.disposition != "ANALYZED":
        raise HoleFillingError("ambiguous or unsupported hole reports cannot authorize repair")
    if report.parent_revision_id != parent_revision_id:
        raise HoleFillingError("hole report parent revision does not match")
    before_digest = _digest(_geometry_payload(mesh))
    if report.parent_geometry_sha256 != before_digest:
        raise HoleFillingError("hole report geometry digest is stale or mismatched")
    if report.scale_state is not scale_state or report.scale_provenance_id != scale_provenance_id:
        raise HoleFillingError("hole report scale provenance does not match the repair request")

    if not isinstance(selected_loop_ids, tuple) or any(
        not isinstance(loop_id, str) or not loop_id for loop_id in selected_loop_ids
    ):
        raise HoleFillingError("selected_loop_ids must be a tuple of reported loop IDs")
    if len(set(selected_loop_ids)) != len(selected_loop_ids):
        raise HoleFillingError("selected_loop_ids must not contain duplicates")
    if len(selected_loop_ids) > policy.maximum_selected_holes:
        raise HoleFillingError("selected loop count exceeds configured operation bound")
    available_loop_ids = {loop.loop_id for loop in report.loops}
    if not set(selected_loop_ids) <= available_loop_ids:
        raise HoleFillingError("selected_loop_ids must come from the matching hole report")

    if mesh.vertices:
        bounds_diagonal = math.sqrt(
            sum(
                (
                    max(vertex[axis] for vertex in mesh.vertices)
                    - min(vertex[axis] for vertex in mesh.vertices)
                )
                ** 2
                for axis in range(3)
            )
        )
    else:
        bounds_diagonal = 0.0
    if (
        policy.maximum_perimeter > bounds_diagonal
        or policy.maximum_area > bounds_diagonal * bounds_diagonal * 0.05
        or policy.maximum_planarity_deviation > bounds_diagonal * 0.02
    ):
        raise HoleFillingError(
            "configured fill thresholds exceed the parent-relative safety bounds"
        )

    support = _edge_support(mesh)
    eligible: list[tuple[BoundaryLoopReport, int]] = []
    unfilled: list[UnfilledHoleEvidence] = []
    for loop in report.loops:
        if loop.loop_id not in selected_loop_ids:
            unfilled.append(
                UnfilledHoleEvidence(
                    loop.loop_id,
                    "not-explicitly-selected-for-repair",
                    loop.perimeter,
                    loop.approximate_area,
                    len(loop.boundary_vertex_indices),
                )
            )
            continue
        reason = _eligible_reason(loop, mesh, support, policy, parent_revision_id)
        if reason is None:
            # Same-direction face winding along the loop requires reverse fan winding.
            first, second = loop.boundary_vertex_indices[0], loop.boundary_vertex_indices[1]
            directed = support[(min(first, second), max(first, second))][1]
            orientation = 1 if directed == (first, second) else -1
            eligible.append((loop, orientation))
        else:
            unfilled.append(
                UnfilledHoleEvidence(
                    loop.loop_id,
                    reason,
                    loop.perimeter,
                    loop.approximate_area,
                    len(loop.boundary_vertex_indices),
                )
            )

    vertices = list(mesh.vertices)
    triangles = list(mesh.triangles)
    parent_colors = mesh.vertex_colors
    colors = list(parent_colors) if parent_colors is not None else None
    filled_evidence: list[FilledHoleEvidence] = []
    for loop, orientation in eligible:
        boundary_points = tuple(mesh.vertices[index] for index in loop.boundary_vertex_indices)
        center = _centroid(boundary_points)
        center_index = len(vertices)
        vertices.append(center)
        if colors is not None:
            assert parent_colors is not None
            count = len(loop.boundary_vertex_indices)
            colors.append(
                (
                    sum(parent_colors[index][0] for index in loop.boundary_vertex_indices) / count,
                    sum(parent_colors[index][1] for index in loop.boundary_vertex_indices) / count,
                    sum(parent_colors[index][2] for index in loop.boundary_vertex_indices) / count,
                )
            )
        derived: list[tuple[int, int, int]] = []
        for position, first in enumerate(loop.boundary_vertex_indices):
            second = loop.boundary_vertex_indices[
                (position + 1) % len(loop.boundary_vertex_indices)
            ]
            if orientation == 1:
                derived.append((second, first, center_index))
            else:
                derived.append((first, second, center_index))
        start_face = len(triangles)
        triangles.extend(derived)
        loop_evidence = FilledHoleEvidence(
            loop_id=loop.loop_id,
            center_vertex_index=center_index,
            derived_face_indices=tuple(range(start_face, start_face + len(derived))),
            derived_triangles=tuple(derived),
            repair_method="local_convex_planar_centroid_fan_v1",
            geometry_authority="REPAIR_DERIVED_NOT_CAPTURED_EVIDENCE",
        )
        # Temporarily retain in local list; immutable evidence is assembled below.
        filled_evidence.append(loop_evidence)

    after_mesh = TriangleMeshData(
        vertices=tuple(vertices),
        triangles=tuple(triangles),
        vertex_colors=tuple(colors) if colors is not None else None,
        vertex_normals=(
            _recompute_normals(
                TriangleMeshData(
                    tuple(vertices), tuple(triangles), tuple(colors) if colors is not None else None
                )
            )
            if mesh.vertex_normals is not None and eligible
            else mesh.vertex_normals
        ),
    )
    after_digest = _digest(_geometry_payload(after_mesh))
    revision_identity = {
        "contract": HOLE_FILL_CONTRACT,
        "parent_revision_id": parent_revision_id,
        "hole_report_id": report.report_id,
        "before_geometry_sha256": before_digest,
        "after_geometry_sha256": after_digest,
        "policy": policy.as_dict(),
        "selected_loop_ids": selected_loop_ids,
        "filled_holes": [
            (item.loop_id, item.derived_face_indices, item.derived_triangles)
            for item in filled_evidence
        ],
        "unfilled_holes": [(item.loop_id, item.reason) for item in unfilled],
        "scale_state": scale_state.value,
        "scale_provenance_id": scale_provenance_id,
        "physical_accuracy_validation_status": PHYSICAL_VALIDATION_DEFERRED,
        "mold_use_authorized": False,
    }
    child_id = f"mesh-hole-fill:{_digest(revision_identity)}"
    return HoleFillingRevision(
        contract=HOLE_FILL_CONTRACT,
        parent_revision_id=parent_revision_id,
        child_revision_id=child_id,
        hole_report_id=report.report_id,
        before_geometry_sha256=before_digest,
        after_geometry_sha256=after_digest,
        before_mesh=mesh,
        after_mesh=after_mesh,
        policy=policy,
        selected_loop_ids=selected_loop_ids,
        filled_holes=tuple(filled_evidence),
        unfilled_holes=tuple(unfilled),
        scale_state=scale_state,
        scale_provenance_id=scale_provenance_id,
        physical_accuracy_validation_status=PHYSICAL_VALIDATION_DEFERRED,
        mold_use_authorized=False,
    )


__all__ = [
    "HOLE_FILL_CONTRACT",
    "PHYSICAL_VALIDATION_DEFERRED",
    "FilledHoleEvidence",
    "HoleFillingError",
    "HoleFillingPolicy",
    "HoleFillingRevision",
    "UnfilledHoleEvidence",
    "fill_reported_mesh_holes",
]
