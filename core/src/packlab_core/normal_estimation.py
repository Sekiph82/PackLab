"""Bounded, deterministic point-cloud normal estimation and sign consistency."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass

from .geometry_adapter import Point3, PointCloudData
from .reconstruction import ScaleState

NORMAL_ESTIMATION_CONTRACT = "packlab.point-cloud-normal-estimation.v1"
PHYSICAL_VALIDATION_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class NormalEstimationError(ValueError):
    """Raised when normal estimation inputs exceed a safe, explicit bound."""


@dataclass(frozen=True, slots=True)
class NormalEstimationPolicy:
    radius: float = 0.02
    minimum_neighbors: int = 6
    maximum_neighbors: int = 32
    maximum_points: int = 100_000
    maximum_neighbor_candidates: int = 5_000_000
    orientation_ambiguity_cosine: float = 0.05

    def __post_init__(self) -> None:
        if (
            isinstance(self.radius, bool)
            or not isinstance(self.radius, (int, float))
            or not math.isfinite(self.radius)
            or self.radius <= 0
        ):
            raise NormalEstimationError("radius must be finite and positive")
        for name in (
            "minimum_neighbors",
            "maximum_neighbors",
            "maximum_points",
            "maximum_neighbor_candidates",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise NormalEstimationError(f"{name} must be a positive integer")
        if self.minimum_neighbors < 3 or self.maximum_neighbors < self.minimum_neighbors:
            raise NormalEstimationError(
                "neighbor limits require 3 <= minimum_neighbors <= maximum_neighbors"
            )
        if not 1 <= self.maximum_points <= 100_000:
            raise NormalEstimationError("maximum_points must be between 1 and 100000")
        if not 1 <= self.maximum_neighbor_candidates <= 5_000_000:
            raise NormalEstimationError("maximum_neighbor_candidates must be between 1 and 5000000")
        threshold = self.orientation_ambiguity_cosine
        if (
            isinstance(threshold, bool)
            or not isinstance(threshold, (int, float))
            or not math.isfinite(threshold)
            or not 0 <= threshold < 1
        ):
            raise NormalEstimationError("orientation_ambiguity_cosine must be in [0, 1)")
        object.__setattr__(self, "radius", float(self.radius))
        object.__setattr__(self, "orientation_ambiguity_cosine", float(threshold))

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": NORMAL_ESTIMATION_CONTRACT,
            "neighborhood": "uniform_grid_radius_search_v1",
            "radius": self.radius,
            "minimum_neighbors_excluding_query": self.minimum_neighbors,
            "maximum_neighbors": self.maximum_neighbors,
            "maximum_points": self.maximum_points,
            "maximum_neighbor_candidates": self.maximum_neighbor_candidates,
            "normal_estimator": "smallest_covariance_eigenvector_symmetric_jacobi_v1",
            "orientation_strategy": "nearest-neighbor_sign_consistency_with_canonical_component_seed_v1",
            "orientation_ambiguity_cosine": self.orientation_ambiguity_cosine,
            "physical_orientation_inference": False,
        }


@dataclass(frozen=True, slots=True)
class AmbiguousOrientationEdge:
    point_index_a: int
    point_index_b: int
    reason: str


@dataclass(frozen=True, slots=True)
class NormalEstimationRevision:
    contract: str
    parent_revision_id: str
    child_revision_id: str
    parent_geometry_sha256: str
    geometry_sha256: str
    source_point_cloud: PointCloudData
    normal_estimates: tuple[Point3 | None, ...]
    unresolved_point_indices: tuple[int, ...]
    ambiguous_orientation_edges: tuple[AmbiguousOrientationEdge, ...]
    neighborhood_counts: tuple[int, ...]
    policy: NormalEstimationPolicy
    scale_state: ScaleState
    scale_provenance_id: str | None
    physical_accuracy_validation_status: str
    mold_use_authorized: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "parent_revision_id": self.parent_revision_id,
            "child_revision_id": self.child_revision_id,
            "parent_geometry_sha256": self.parent_geometry_sha256,
            "geometry_sha256": self.geometry_sha256,
            "normal_estimates": self.normal_estimates,
            "unresolved_point_indices": self.unresolved_point_indices,
            "ambiguous_orientation_edges": [
                {
                    "point_index_a": edge.point_index_a,
                    "point_index_b": edge.point_index_b,
                    "reason": edge.reason,
                }
                for edge in self.ambiguous_orientation_edges
            ],
            "neighborhood_counts": self.neighborhood_counts,
            "policy": self.policy.as_dict(),
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
        }


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _safe_identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise NormalEstimationError(f"{field} must be a non-empty stable identifier")
    if any(ord(char) < 32 for char in value):
        raise NormalEstimationError(f"{field} must not contain control characters")
    return value


def _neighbors(
    cloud: PointCloudData, policy: NormalEstimationPolicy
) -> tuple[tuple[int, ...], ...]:
    points = cloud.points
    if len(points) > policy.maximum_points:
        raise NormalEstimationError("point count exceeds the configured resource bound")
    radius = policy.radius
    cells: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    point_cells: list[tuple[int, int, int]] = []
    for index, point in enumerate(points):
        cell: tuple[int, int, int] = (
            math.floor(point[0] / radius),
            math.floor(point[1] / radius),
            math.floor(point[2] / radius),
        )
        point_cells.append(cell)
        cells[cell].append(index)

    radius_squared = radius * radius
    result: list[tuple[int, ...]] = []
    candidate_work = 0
    for index, point in enumerate(points):
        cx, cy, cz = point_cells[index]
        candidates: list[tuple[float, int]] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for other in cells.get((cx + dx, cy + dy, cz + dz), ()):
                        if other == index:
                            continue
                        candidate_work += 1
                        if candidate_work > policy.maximum_neighbor_candidates:
                            raise NormalEstimationError(
                                "neighbor-search work exceeds configured bound"
                            )
                        delta = tuple(points[other][axis] - point[axis] for axis in range(3))
                        distance_squared = sum(component * component for component in delta)
                        if distance_squared <= radius_squared:
                            candidates.append((distance_squared, other))
        candidates.sort(key=lambda item: (item[0], item[1]))
        result.append(tuple(other for _, other in candidates[: policy.maximum_neighbors]))
    return tuple(result)


def _smallest_eigenvector(points: tuple[Point3, ...], indices: tuple[int, ...]) -> Point3 | None:
    sample = tuple(points[index] for index in indices)
    count = len(sample)
    mean = tuple(sum(point[axis] for point in sample) / count for axis in range(3))
    matrix = [[0.0] * 3 for _ in range(3)]
    for point in sample:
        delta = tuple(point[axis] - mean[axis] for axis in range(3))
        for row in range(3):
            for column in range(row, 3):
                matrix[row][column] += delta[row] * delta[column] / count
    for row in range(3):
        for column in range(row):
            matrix[row][column] = matrix[column][row]

    vectors = [[1.0 if row == column else 0.0 for column in range(3)] for row in range(3)]
    for _ in range(32):
        p, q = max(((0, 1), (0, 2), (1, 2)), key=lambda pair: abs(matrix[pair[0]][pair[1]]))
        off_diagonal = matrix[p][q]
        if abs(off_diagonal) <= 1e-15 * max(1.0, *(abs(matrix[i][i]) for i in range(3))):
            break
        tau = (matrix[q][q] - matrix[p][p]) / (2.0 * off_diagonal)
        tangent = math.copysign(1.0, tau) / (abs(tau) + math.sqrt(1.0 + tau * tau))
        cosine = 1.0 / math.sqrt(1.0 + tangent * tangent)
        sine = tangent * cosine
        app, aqq = matrix[p][p], matrix[q][q]
        matrix[p][p] = app - tangent * off_diagonal
        matrix[q][q] = aqq + tangent * off_diagonal
        matrix[p][q] = matrix[q][p] = 0.0
        for axis in range(3):
            if axis != p and axis != q:
                aip, aiq = matrix[axis][p], matrix[axis][q]
                matrix[axis][p] = matrix[p][axis] = cosine * aip - sine * aiq
                matrix[axis][q] = matrix[q][axis] = sine * aip + cosine * aiq
            vip, viq = vectors[axis][p], vectors[axis][q]
            vectors[axis][p] = cosine * vip - sine * viq
            vectors[axis][q] = sine * vip + cosine * viq

    order = sorted(range(3), key=lambda index: (matrix[index][index], index))
    smallest, middle, largest = (matrix[index][index] for index in order)
    tolerance = max(1e-18, abs(largest) * 1e-12)
    if middle <= tolerance or largest <= tolerance or smallest < -tolerance:
        return None
    vector = [vectors[axis][order[0]] for axis in range(3)]
    magnitude = math.sqrt(sum(component * component for component in vector))
    if magnitude <= 1e-15 or not math.isfinite(magnitude):
        return None
    vector = [component / magnitude for component in vector]
    pivot = max(range(3), key=lambda axis: (abs(vector[axis]), -axis))
    if vector[pivot] < 0:
        vector = [-component for component in vector]
    return (vector[0], vector[1], vector[2])


def _dot(a: Point3, b: Point3) -> float:
    return sum(a[index] * b[index] for index in range(3))


def _orient_consistently(
    estimates: list[Point3 | None],
    neighbors: tuple[tuple[int, ...], ...],
    ambiguity_cosine: float,
) -> tuple[tuple[Point3 | None, ...], tuple[AmbiguousOrientationEdge, ...]]:
    edges = sorted(
        {
            (min(index, other), max(index, other))
            for index, group in enumerate(neighbors)
            for other in group
        }
    )
    graph: dict[int, list[int]] = defaultdict(list)
    ambiguous: list[AmbiguousOrientationEdge] = []
    for first, second in edges:
        normal_a, normal_b = estimates[first], estimates[second]
        if normal_a is None or normal_b is None:
            continue
        similarity = _dot(normal_a, normal_b)
        if abs(similarity) <= ambiguity_cosine:
            ambiguous.append(AmbiguousOrientationEdge(first, second, "near-orthogonal-normal-pair"))
            continue
        graph[first].append(second)
        graph[second].append(first)

    signs: dict[int, int] = {}
    for seed, normal in enumerate(estimates):
        if normal is None or seed in signs:
            continue
        signs[seed] = 1
        queue = deque([seed])
        while queue:
            current = queue.popleft()
            current_normal = estimates[current]
            assert current_normal is not None
            for other in sorted(graph[current]):
                other_normal = estimates[other]
                assert other_normal is not None
                similarity = _dot(current_normal, other_normal)
                expected_sign = signs[current] * (1 if similarity > 0 else -1)
                if other not in signs:
                    signs[other] = expected_sign
                    queue.append(other)
                elif signs[other] != expected_sign:
                    edge = (min(current, other), max(current, other))
                    record = AmbiguousOrientationEdge(*edge, "orientation-cycle-conflict")
                    if record not in ambiguous:
                        ambiguous.append(record)

    oriented = tuple(
        None
        if normal is None
        else (
            signs.get(index, 1) * normal[0],
            signs.get(index, 1) * normal[1],
            signs.get(index, 1) * normal[2],
        )
        for index, normal in enumerate(estimates)
    )
    ambiguous.sort(key=lambda item: (item.point_index_a, item.point_index_b, item.reason))
    return oriented, tuple(ambiguous)


def estimate_point_cloud_normals(
    cloud: PointCloudData,
    *,
    parent_revision_id: str,
    scale_state: ScaleState,
    scale_provenance_id: str | None = None,
    policy: NormalEstimationPolicy = NormalEstimationPolicy(),
) -> NormalEstimationRevision:
    """Estimate local covariance normals and consistent signs as a child evidence revision."""

    parent_revision_id = _safe_identifier(parent_revision_id, "parent_revision_id")
    if not isinstance(scale_state, ScaleState) or scale_state is ScaleState.METRIC_VERIFIED:
        raise NormalEstimationError("scale_state must preserve relative or metric-unverified state")
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        scale_provenance_id = _safe_identifier(scale_provenance_id, "scale_provenance_id")
    elif scale_provenance_id is not None:
        scale_provenance_id = _safe_identifier(scale_provenance_id, "scale_provenance_id")
    neighborhoods: tuple[tuple[int, ...], ...]
    if len(cloud.points) < policy.minimum_neighbors + 1:
        neighborhoods = tuple(() for _ in cloud.points)
    else:
        neighborhoods = _neighbors(cloud, policy)

    estimates: list[Point3 | None] = []
    unresolved: list[int] = []
    counts: list[int] = []
    for index, nearby in enumerate(neighborhoods):
        counts.append(len(nearby))
        if len(nearby) < policy.minimum_neighbors:
            estimates.append(None)
            unresolved.append(index)
            continue
        estimate = _smallest_eigenvector(cloud.points, (index, *nearby))
        estimates.append(estimate)
        if estimate is None:
            unresolved.append(index)

    oriented, ambiguous = _orient_consistently(
        estimates, neighborhoods, policy.orientation_ambiguity_cosine
    )
    parent_payload = {
        "points": cloud.points,
        "colors": cloud.colors,
        "normals": cloud.normals,
    }
    parent_digest = _digest(parent_payload)
    output_digest = _digest(
        {
            "points": cloud.points,
            "colors": cloud.colors,
            "normal_estimates": oriented,
            "unresolved_point_indices": unresolved,
            "ambiguous_orientation_edges": [
                (edge.point_index_a, edge.point_index_b, edge.reason) for edge in ambiguous
            ],
        }
    )
    policy_record = policy.as_dict()
    revision_inputs = {
        "contract": NORMAL_ESTIMATION_CONTRACT,
        "parent_revision_id": parent_revision_id,
        "parent_geometry_sha256": parent_digest,
        "geometry_sha256": output_digest,
        "policy": policy_record,
        "scale_state": scale_state.value,
        "scale_provenance_id": scale_provenance_id,
        "physical_accuracy_validation_status": PHYSICAL_VALIDATION_DEFERRED,
        "mold_use_authorized": False,
    }
    child_revision_id = f"normal-estimation:{_digest(revision_inputs)}"
    return NormalEstimationRevision(
        contract=NORMAL_ESTIMATION_CONTRACT,
        parent_revision_id=parent_revision_id,
        child_revision_id=child_revision_id,
        parent_geometry_sha256=parent_digest,
        geometry_sha256=output_digest,
        source_point_cloud=cloud,
        normal_estimates=oriented,
        unresolved_point_indices=tuple(unresolved),
        ambiguous_orientation_edges=ambiguous,
        neighborhood_counts=tuple(counts),
        policy=policy,
        scale_state=scale_state,
        scale_provenance_id=scale_provenance_id,
        physical_accuracy_validation_status=PHYSICAL_VALIDATION_DEFERRED,
        mold_use_authorized=False,
    )


__all__ = [
    "NORMAL_ESTIMATION_CONTRACT",
    "PHYSICAL_VALIDATION_DEFERRED",
    "AmbiguousOrientationEdge",
    "NormalEstimationError",
    "NormalEstimationPolicy",
    "NormalEstimationRevision",
    "estimate_point_cloud_normals",
]
