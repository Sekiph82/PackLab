"""Conservative spatial-component diagnostics for reconstruction observations."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, cast

from .object_mask_lifting import MAX_LIFT_POINTS, ObjectCaptureGeometry
from .reconstruction import ReconstructionOutputManifest, ScaleState

RECONSTRUCTION_ARTIFACT_CONTRACT: Final = "packlab.reconstruction-artifact-diagnostics.v1"
RECONSTRUCTION_ARTIFACT_POLICY_VERSION: Final = "packlab.reconstruction-artifact-policy.v1"
MAX_COMPONENT_PAIR_CHECKS: Final = 1_000_000
MAX_REPORTED_COMPONENTS: Final = 32
_SHA256 = re.compile(r"[0-9a-f]{64}")


class ReconstructionArtifactError(ValueError):
    """Raised when artifact-diagnostic policy configuration is invalid."""


@dataclass(frozen=True, slots=True)
class ReconstructionArtifactPolicy:
    """Explicit scale-relative thresholds for identifying review-only outlier groups."""

    profile_id: str = "floating-components-v1"
    neighbor_radius_ratio: float = 0.025
    maximum_candidate_component_ratio: float = 0.02
    minimum_component_centroid_gap_ratio: float = 0.10
    max_pair_checks: int = MAX_COMPONENT_PAIR_CHECKS

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not re.fullmatch(
            r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}", self.profile_id
        ):
            raise ReconstructionArtifactError("profile_id must be a safe identifier")
        if (
            isinstance(self.max_pair_checks, bool)
            or not isinstance(self.max_pair_checks, int)
            or not 1 <= self.max_pair_checks <= MAX_COMPONENT_PAIR_CHECKS
        ):
            raise ReconstructionArtifactError("max_pair_checks must be between 1 and 1000000")
        for name in (
            "neighbor_radius_ratio",
            "maximum_candidate_component_ratio",
            "minimum_component_centroid_gap_ratio",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or not 0 <= value <= 1
                or (name == "neighbor_radius_ratio" and not 1e-6 <= value <= 0.5)
            ):
                raise ReconstructionArtifactError(
                    f"{name} must be finite and within its supported range"
                )
            object.__setattr__(self, name, float(value))

    def as_dict(self) -> dict[str, object]:
        return {
            "version": RECONSTRUCTION_ARTIFACT_POLICY_VERSION,
            "profile_id": self.profile_id,
            "neighbor_radius_ratio": self.neighbor_radius_ratio,
            "maximum_candidate_component_ratio": self.maximum_candidate_component_ratio,
            "minimum_component_centroid_gap_ratio": self.minimum_component_centroid_gap_ratio,
            "boundaries_inclusive": True,
            "automatic_removal": False,
        }


@dataclass(frozen=True, slots=True)
class ReconstructionArtifactReport:
    """Canonical diagnostic output with no authority to mutate or promote source geometry."""

    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return json.loads(json.dumps(self.payload, sort_keys=True, allow_nan=False))

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _unavailable(code: str, policy: ReconstructionArtifactPolicy) -> ReconstructionArtifactReport:
    return ReconstructionArtifactReport(
        {
            "contract": RECONSTRUCTION_ARTIFACT_CONTRACT,
            "authority": "diagnostic_only_no_geometry_mutation_or_promotion",
            "observation_status": "unavailable",
            "candidate_status": "not_evaluated",
            "acceptance_status": "not_evaluated",
            "source_evidence": None,
            "statistics": None,
            "candidates": [],
            "policy": policy.as_dict(),
            "diagnostics": [{"code": code}],
        }
    )


def _valid_inputs(
    manifest: ReconstructionOutputManifest,
    geometry: ObjectCaptureGeometry,
) -> bool:
    if (
        manifest.authority_class != "RECONSTRUCTION_OBSERVATION"
        or manifest.scale_state is ScaleState.METRIC_VERIFIED
        or geometry.generated is not False
        or geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY"
        or geometry.scale_state is ScaleState.METRIC_VERIFIED
        or not isinstance(geometry.geometry_id, str)
        or re.fullmatch(r"object-geometry:[0-9a-f]{64}", geometry.geometry_id) is None
        or manifest.project_id != geometry.project_id
        or manifest.reconstruction_revision != geometry.reconstruction_revision
        or manifest.source_input_digest != geometry.source_input_digest
        or not _SHA256.fullmatch(manifest.source_input_digest)
        or isinstance(manifest.point_count, bool)
        or not isinstance(manifest.point_count, int)
        or isinstance(geometry.candidate_count, bool)
        or not isinstance(geometry.candidate_count, int)
        or not 0 <= geometry.candidate_count <= manifest.point_count
        or geometry.candidate_count > MAX_LIFT_POINTS
        or geometry.point_count != len(geometry.filtered_points)
        or geometry.point_count != len(geometry.unfiltered_points)
        or geometry.filtered_points != geometry.unfiltered_points
        or len(geometry.point_votes) != geometry.candidate_count
        or geometry.point_count != sum(1 for vote in geometry.point_votes if vote.selected)
        or not _SHA256.fullmatch(geometry.mask_set_revision_digest)
    ):
        return False
    point_ids: set[str] = set()
    for vote in geometry.point_votes:
        if not vote.point_id or vote.point_id in point_ids or not isinstance(vote.selected, bool):
            return False
        point_ids.add(vote.point_id)
    for point in geometry.filtered_points:
        if (
            not isinstance(point, Sequence)
            or len(point) != 3
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or abs(float(value)) > 1e12
                for value in point
            )
        ):
            return False
    return True


def _components(
    points: tuple[tuple[float, float, float], ...],
    radius: float,
    pair_limit: int,
) -> tuple[tuple[tuple[int, ...], ...] | None, int]:
    parent = list(range(len(points)))
    size = [1] * len(points)

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            return
        if size[root_left] < size[root_right] or (
            size[root_left] == size[root_right] and root_left > root_right
        ):
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left
        size[root_left] += size[root_right]

    buckets: dict[tuple[int, int, int], list[int]] = {}
    pair_checks = 0
    radius_squared = radius * radius
    for index, point in enumerate(points):
        cell = (
            math.floor(point[0] / radius),
            math.floor(point[1] / radius),
            math.floor(point[2] / radius),
        )
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    neighbor_cell = (cell[0] + dx, cell[1] + dy, cell[2] + dz)
                    for neighbor in buckets.get(neighbor_cell, ()):
                        pair_checks += 1
                        if pair_checks > pair_limit:
                            return None, pair_checks
                        distance_squared = sum(
                            (point[axis] - points[neighbor][axis]) ** 2 for axis in range(3)
                        )
                        if distance_squared <= radius_squared:
                            union(index, neighbor)
        buckets.setdefault(cell, []).append(index)

    groups: dict[int, list[int]] = {}
    for index in range(len(points)):
        groups.setdefault(find(index), []).append(index)
    components = tuple(
        sorted(
            (tuple(indices) for indices in groups.values()),
            key=lambda indices: (-len(indices), indices[0]),
        )
    )
    return components, pair_checks


def build_reconstruction_artifact_report(
    manifest: object,
    geometry: object,
    *,
    policy: ReconstructionArtifactPolicy,
) -> ReconstructionArtifactReport:
    """Find spatially separated small components as review candidates only."""
    if not isinstance(policy, ReconstructionArtifactPolicy):
        raise ReconstructionArtifactError("an explicit ReconstructionArtifactPolicy is required")
    if not isinstance(manifest, ReconstructionOutputManifest) or not isinstance(
        geometry, ObjectCaptureGeometry
    ):
        return _unavailable("reconstruction_parent_invalid", policy)
    try:
        valid = _valid_inputs(manifest, geometry)
    except (AttributeError, TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        return _unavailable("reconstruction_parent_invalid", policy)
    if not geometry.filtered_points:
        return _unavailable("object_geometry_empty", policy)
    points: tuple[tuple[float, float, float], ...] = tuple(
        sorted(
            (float(point[0]), float(point[1]), float(point[2]))
            for point in geometry.filtered_points
        )
    )
    minima = tuple(min(point[axis] for point in points) for axis in range(3))
    maxima = tuple(max(point[axis] for point in points) for axis in range(3))
    diagonal = math.sqrt(sum((maxima[axis] - minima[axis]) ** 2 for axis in range(3)))
    if not math.isfinite(diagonal) or diagonal == 0:
        return _unavailable("object_geometry_degenerate", policy)
    radius = diagonal * policy.neighbor_radius_ratio
    components, pair_checks = _components(points, radius, policy.max_pair_checks)
    if components is None:
        return _unavailable("component_pair_check_limit_exceeded", policy)
    largest = components[0]
    largest_center = tuple(
        sum(points[index][axis] for index in largest) / len(largest) for axis in range(3)
    )
    candidates: list[dict[str, object]] = []
    for ordinal, component in enumerate(components[1:], start=1):
        ratio = len(component) / len(points)
        center = tuple(
            sum(points[index][axis] for index in component) / len(component) for axis in range(3)
        )
        gap_ratio = math.dist(center, largest_center) / diagonal
        if (
            ratio <= policy.maximum_candidate_component_ratio
            and gap_ratio >= policy.minimum_component_centroid_gap_ratio
        ):
            candidates.append(
                {
                    "candidate_id": f"component-{ordinal:04d}",
                    "classification": "small_spatially_separated_component_review_candidate",
                    "point_count": len(component),
                    "point_ratio": ratio,
                    "centroid_gap_ratio_to_largest_component": gap_ratio,
                    "automatic_removal": False,
                }
            )
    parent_geometry = geometry.as_dict()
    parent_geometry["point_votes"] = [
        vote.as_dict() for vote in sorted(geometry.point_votes, key=lambda item: item.point_id)
    ]
    parent_geometry["points"] = [list(point) for point in points]
    parent_geometry["unfiltered_points"] = [list(point) for point in points]
    camera_evidence = cast(list[dict[str, object]], parent_geometry["camera_projection_evidence"])
    parent_geometry["camera_projection_evidence"] = sorted(
        camera_evidence, key=lambda item: str(item["camera_id"])
    )
    evidence = {
        "project_id": manifest.project_id,
        "reconstruction_revision": manifest.reconstruction_revision,
        "source_input_digest": manifest.source_input_digest,
        "manifest_digest": _digest(manifest.as_dict()),
        "geometry_id": geometry.geometry_id,
        "geometry_digest": _digest(parent_geometry),
        "mask_set_revision_id": geometry.mask_set_revision_id,
        "mask_set_revision_digest": geometry.mask_set_revision_digest,
    }
    return ReconstructionArtifactReport(
        {
            "contract": RECONSTRUCTION_ARTIFACT_CONTRACT,
            "authority": "diagnostic_only_no_geometry_mutation_or_promotion",
            "observation_status": "observed",
            "candidate_status": "candidates_detected" if candidates else "no_candidates_detected",
            "acceptance_status": "not_evaluated",
            "source_evidence": evidence,
            "statistics": {
                "object_point_count": len(points),
                "reconstruction_observation_point_count": manifest.point_count,
                "reconstruction_observation_triangle_count": manifest.triangle_count,
                "component_count": len(components),
                "largest_component_point_count": len(largest),
                "largest_component_point_ratio": len(largest) / len(points),
                "isolated_component_count": sum(
                    1 for component in components if len(component) == 1
                ),
                "neighbor_radius_ratio_of_bounding_box_diagonal": policy.neighbor_radius_ratio,
                "neighbor_radius": radius,
                "point_pair_checks": pair_checks,
                "component_summaries": [
                    {"component_id": f"component-{index:04d}", "point_count": len(component)}
                    for index, component in enumerate(components[:MAX_REPORTED_COMPONENTS])
                ],
                "component_summaries_truncated": len(components) > MAX_REPORTED_COMPONENTS,
                "candidate_count": len(candidates),
                "candidates_truncated": len(candidates) > MAX_REPORTED_COMPONENTS,
            },
            "candidates": candidates[:MAX_REPORTED_COMPONENTS],
            "policy": policy.as_dict(),
            "diagnostics": [],
        }
    )
