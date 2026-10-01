"""Deterministic density and projected-coverage diagnostics for captured object geometry."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, cast

from .object_mask_lifting import (
    MAX_LIFT_POINTS,
    LiftThresholdProfile,
    LiftVisibilityPolicy,
    ObjectCaptureGeometry,
    PointVoteAggregate,
)
from .reconstruction import ScaleState

OBJECT_GEOMETRY_COVERAGE_CONTRACT: Final = "packlab.object-geometry-coverage.v1"
OBJECT_GEOMETRY_COVERAGE_POLICY_VERSION: Final = "packlab.object-geometry-coverage-policy.v1"
MAX_COVERAGE_GRID_RESOLUTION: Final = 64
_SHA256 = re.compile(r"[0-9a-f]{64}")


class ObjectGeometryCoverageError(ValueError):
    """Raised when an explicit coverage threshold profile is invalid."""


@dataclass(frozen=True, slots=True)
class ObjectGeometryCoveragePolicy:
    """Versioned inclusive thresholds for unitless cloud-occupancy diagnostics."""

    profile_id: str = "object-coverage-v1"
    grid_resolution: int = 8
    minimum_selected_point_ratio: float = 0.20
    minimum_mean_support_ratio: float = 0.70
    minimum_projected_coverage_ratio: float = 0.10

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not re.fullmatch(
            r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}", self.profile_id
        ):
            raise ObjectGeometryCoverageError("profile_id must be a safe identifier")
        if (
            isinstance(self.grid_resolution, bool)
            or not isinstance(self.grid_resolution, int)
            or not 2 <= self.grid_resolution <= MAX_COVERAGE_GRID_RESOLUTION
        ):
            raise ObjectGeometryCoverageError("grid_resolution must be between 2 and 64")
        for name in (
            "minimum_selected_point_ratio",
            "minimum_mean_support_ratio",
            "minimum_projected_coverage_ratio",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or not 0 <= value <= 1
            ):
                raise ObjectGeometryCoverageError(f"{name} must be finite and within 0..1")
            object.__setattr__(self, name, float(value))

    def as_dict(self) -> dict[str, object]:
        return {
            "version": OBJECT_GEOMETRY_COVERAGE_POLICY_VERSION,
            "profile_id": self.profile_id,
            "grid_resolution": self.grid_resolution,
            "minimum_selected_point_ratio": self.minimum_selected_point_ratio,
            "minimum_mean_support_ratio": self.minimum_mean_support_ratio,
            "minimum_projected_coverage_ratio": self.minimum_projected_coverage_ratio,
            "boundaries_inclusive": True,
        }


@dataclass(frozen=True, slots=True)
class ObjectGeometryCoverageReport:
    """Canonical diagnostic report that cannot promote captured geometry authority."""

    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return json.loads(json.dumps(self.payload, sort_keys=True, allow_nan=False))

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _invalid_report(
    code: str, policy: ObjectGeometryCoveragePolicy
) -> ObjectGeometryCoverageReport:
    return ObjectGeometryCoverageReport(
        {
            "contract": OBJECT_GEOMETRY_COVERAGE_CONTRACT,
            "authority": "diagnostic_only_no_geometry_promotion",
            "observation_status": "invalid",
            "threshold_status": "not_evaluated",
            "acceptance_status": "not_evaluated",
            "source_evidence": None,
            "statistics": None,
            "policy": policy.as_dict(),
            "diagnostics": [{"code": code}],
        }
    )


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _valid_geometry(geometry: ObjectCaptureGeometry) -> bool:
    if (
        geometry.generated is not False
        or geometry.authority_class != "OBJECT_CAPTURE_GEOMETRY"
        or geometry.scale_state is ScaleState.METRIC_VERIFIED
        or not isinstance(geometry.geometry_id, str)
        or re.fullmatch(r"object-geometry:[0-9a-f]{64}", geometry.geometry_id) is None
        or not all(
            isinstance(value, str) and value.strip()
            for value in (
                geometry.project_id,
                geometry.source_revision,
                geometry.reconstruction_revision,
                geometry.camera_solution_revision,
                geometry.mask_set_revision_id,
                geometry.projection_convention,
                geometry.projection_version,
            )
        )
        or not _is_digest(geometry.source_input_digest)
        or not _is_digest(geometry.mask_set_revision_digest)
        or not isinstance(geometry.threshold_profile, LiftThresholdProfile)
        or not isinstance(geometry.visibility_policy, LiftVisibilityPolicy)
        or isinstance(geometry.candidate_count, bool)
        or not isinstance(geometry.candidate_count, int)
        or not 1 <= geometry.candidate_count <= MAX_LIFT_POINTS
        or isinstance(geometry.point_count, bool)
        or not isinstance(geometry.point_count, int)
        or geometry.point_count != len(geometry.filtered_points)
        or geometry.point_count != len(geometry.unfiltered_points)
        or geometry.filtered_points != geometry.unfiltered_points
    ):
        return False
    if not geometry.camera_evidence or len(geometry.camera_evidence) > 512:
        return False
    camera_ids: set[str] = set()
    source_pairs: set[tuple[str, str]] = set()
    mask_pairs: set[tuple[str, str]] = set()
    for item in geometry.camera_evidence:
        if (
            not item.camera_id
            or item.camera_id in camera_ids
            or not item.source_image_asset_id
            or not _is_digest(item.source_digest)
            or not item.mask_artifact_id
            or not _is_digest(item.mask_digest)
        ):
            return False
        camera_ids.add(item.camera_id)
        source_pairs.add((item.source_image_asset_id, item.source_digest))
        mask_pairs.add((item.mask_artifact_id, item.mask_digest))
        if (
            len(item.image_dimensions) != 2
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in item.image_dimensions
            )
            or len(item.intrinsics) != 4
            or any(not math.isfinite(float(value)) for value in item.intrinsics)
            or len(item.normalized_world_to_camera) != 16
            or any(not math.isfinite(float(value)) for value in item.normalized_world_to_camera)
        ):
            return False
    if tuple(sorted(source_pairs)) != geometry.source_images:
        return False
    if tuple(sorted(mask_pairs)) != geometry.source_mask_artifacts:
        return False
    expected_conventions = tuple(
        sorted(
            (
                item.camera_id,
                item.pose_convention,
                item.camera_axis_convention,
            )
            for item in geometry.camera_evidence
        )
    )
    if expected_conventions != geometry.camera_conventions:
        return False
    if len(geometry.point_votes) != geometry.candidate_count:
        return False
    point_ids: set[str] = set()
    selected_count = 0
    for vote in geometry.point_votes:
        if (
            not isinstance(vote, PointVoteAggregate)
            or not vote.point_id
            or vote.point_id in point_ids
        ):
            return False
        point_ids.add(vote.point_id)
        counts = (
            vote.observed_views,
            vote.support_views,
            vote.reject_views,
            vote.not_observed_views,
            vote.behind_camera_views,
            vote.out_of_frame_views,
            vote.occluded_views,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts
        ):
            return False
        if (
            vote.observed_views != vote.support_views + vote.reject_views
            or vote.observed_views + vote.not_observed_views > len(geometry.camera_evidence)
            or vote.behind_camera_views + vote.out_of_frame_views + vote.occluded_views
            > vote.not_observed_views
            or not isinstance(vote.support_ratio, (int, float))
            or isinstance(vote.support_ratio, bool)
            or not math.isfinite(float(vote.support_ratio))
            or vote.support_ratio
            != (vote.support_views / vote.observed_views if vote.observed_views else 0.0)
            or not isinstance(vote.selected, bool)
        ):
            return False
        expected_selected = (
            vote.observed_views >= geometry.threshold_profile.minimum_observed_views
            and vote.support_views >= geometry.threshold_profile.minimum_support_views
            and vote.support_ratio >= geometry.threshold_profile.minimum_support_ratio
        )
        if vote.selected is not expected_selected:
            return False
        selected_count += int(vote.selected)
    if selected_count != geometry.point_count:
        return False
    for point in geometry.filtered_points:
        if (
            not isinstance(point, Sequence)
            or len(point) != 3
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in point
            )
        ):
            return False
    return True


def _bin(value: float, minimum: float, maximum: float, resolution: int) -> int:
    if maximum == minimum:
        return 0
    return min(resolution - 1, max(0, int((value - minimum) / (maximum - minimum) * resolution)))


def _coverage(
    points: tuple[tuple[float, float, float], ...],
    minima: tuple[float, float, float],
    maxima: tuple[float, float, float],
    axes: tuple[int, int],
    resolution: int,
) -> float:
    occupied = {
        (
            _bin(point[axes[0]], minima[axes[0]], maxima[axes[0]], resolution),
            _bin(point[axes[1]], minima[axes[1]], maxima[axes[1]], resolution),
        )
        for point in points
    }
    return len(occupied) / (resolution * resolution)


def build_object_geometry_coverage_report(
    geometry: object,
    *,
    policy: ObjectGeometryCoveragePolicy,
) -> ObjectGeometryCoverageReport:
    """Report unitless voxel density, projected occupancy, and multiview vote support."""
    if not isinstance(policy, ObjectGeometryCoveragePolicy):
        raise ObjectGeometryCoverageError("an explicit ObjectGeometryCoveragePolicy is required")
    if not isinstance(geometry, ObjectCaptureGeometry):
        return _invalid_report("object_geometry_provenance_invalid", policy)
    try:
        valid_geometry = _valid_geometry(geometry)
    except (AttributeError, TypeError, ValueError, OverflowError):
        valid_geometry = False
    if not valid_geometry:
        return _invalid_report("object_geometry_provenance_invalid", policy)
    points: tuple[tuple[float, float, float], ...] = tuple(
        sorted(
            (float(point[0]), float(point[1]), float(point[2]))
            for point in geometry.filtered_points
        )
    )
    votes = tuple(sorted(geometry.point_votes, key=lambda vote: vote.point_id))
    selected_votes = tuple(vote for vote in votes if vote.selected)
    selected_ratio = len(selected_votes) / geometry.candidate_count
    camera_count = len(geometry.camera_evidence)
    support_total = sum(vote.support_views for vote in selected_votes)
    observed_total = sum(vote.observed_views for vote in selected_votes)
    mean_support_ratio = (
        sum(vote.support_ratio for vote in selected_votes) / len(selected_votes)
        if selected_votes
        else 0.0
    )
    support_per_candidate = support_total / geometry.candidate_count
    minima: tuple[float, float, float] = (
        (
            min(point[0] for point in points),
            min(point[1] for point in points),
            min(point[2] for point in points),
        )
        if points
        else (0.0, 0.0, 0.0)
    )
    maxima: tuple[float, float, float] = (
        (
            max(point[0] for point in points),
            max(point[1] for point in points),
            max(point[2] for point in points),
        )
        if points
        else (0.0, 0.0, 0.0)
    )
    resolution = policy.grid_resolution
    occupied_voxels = {
        tuple(_bin(point[axis], minima[axis], maxima[axis], resolution) for axis in range(3))
        for point in points
    }
    voxel_count = resolution**3
    voxel_occupancy = len(occupied_voxels) / voxel_count if points else 0.0
    points_per_occupied_voxel = len(points) / len(occupied_voxels) if occupied_voxels else 0.0
    projection_coverage = {
        "xy": _coverage(points, minima, maxima, (0, 1), resolution) if points else 0.0,
        "xz": _coverage(points, minima, maxima, (0, 2), resolution) if points else 0.0,
        "yz": _coverage(points, minima, maxima, (1, 2), resolution) if points else 0.0,
    }
    mean_projection_coverage = sum(projection_coverage.values()) / 3
    threshold_status = (
        "not_evaluated"
        if not points
        else "pass"
        if (
            selected_ratio >= policy.minimum_selected_point_ratio
            and mean_support_ratio >= policy.minimum_mean_support_ratio
            and mean_projection_coverage >= policy.minimum_projected_coverage_ratio
        )
        else "below_threshold"
    )
    parent_payload = geometry.as_dict()
    source_images = cast(list[dict[str, object]], parent_payload["source_images"])
    source_masks = cast(list[dict[str, object]], parent_payload["source_mask_artifacts"])
    camera_conventions = cast(list[dict[str, object]], parent_payload["camera_conventions"])
    camera_projection_evidence = cast(
        list[dict[str, object]], parent_payload["camera_projection_evidence"]
    )
    parent_payload["source_images"] = sorted(
        source_images, key=lambda item: (str(item["asset_id"]), str(item["sha256"]))
    )
    parent_payload["source_mask_artifacts"] = sorted(
        source_masks, key=lambda item: (str(item["artifact_id"]), str(item["sha256"]))
    )
    parent_payload["camera_conventions"] = sorted(
        camera_conventions, key=lambda item: str(item["camera_id"])
    )
    parent_payload["camera_projection_evidence"] = sorted(
        camera_projection_evidence, key=lambda item: str(item["camera_id"])
    )
    parent_payload["point_votes"] = [vote.as_dict() for vote in votes]
    parent_payload["points"] = [list(point) for point in points]
    parent_payload["unfiltered_points"] = [list(point) for point in points]
    evidence = {
        "geometry_id": geometry.geometry_id,
        "parents": {
            "project_id": geometry.project_id,
            "source_revision": geometry.source_revision,
            "source_input_digest": geometry.source_input_digest,
            "reconstruction_revision": geometry.reconstruction_revision,
            "camera_solution_revision": geometry.camera_solution_revision,
            "mask_set_revision_id": geometry.mask_set_revision_id,
            "mask_set_revision_digest": geometry.mask_set_revision_digest,
        },
        "camera_evidence_digest": _canonical_digest(
            [
                item.as_dict()
                for item in sorted(geometry.camera_evidence, key=lambda item: item.camera_id)
            ]
        ),
        "vote_digest": _canonical_digest([item.as_dict() for item in votes]),
        "parent_geometry_digest": _canonical_digest(parent_payload),
        "lift_threshold_profile_digest": _canonical_digest(geometry.threshold_profile.as_dict()),
        "visibility_policy_digest": _canonical_digest(geometry.visibility_policy.as_dict()),
    }
    return ObjectGeometryCoverageReport(
        {
            "contract": OBJECT_GEOMETRY_COVERAGE_CONTRACT,
            "authority": "diagnostic_only_no_geometry_promotion",
            "observation_status": "observed" if points else "empty",
            "threshold_status": threshold_status,
            "acceptance_status": "not_evaluated",
            "source_evidence": evidence,
            "statistics": {
                "candidate_point_count": geometry.candidate_count,
                "selected_point_count": len(points),
                "selected_point_ratio": selected_ratio,
                "density": {
                    "kind": "normalized_aabb_voxel_occupancy_proxy",
                    "grid_resolution": resolution,
                    "grid_cell_count": voxel_count,
                    "occupied_voxel_count": len(occupied_voxels),
                    "occupied_voxel_ratio": voxel_occupancy,
                    "points_per_occupied_voxel": points_per_occupied_voxel,
                    "physical_units": False,
                },
                "coverage": {
                    "kind": "orthographic_projected_grid_occupancy_proxy",
                    "grid_resolution": resolution,
                    "xy_occupancy_ratio": projection_coverage["xy"],
                    "xz_occupancy_ratio": projection_coverage["xz"],
                    "yz_occupancy_ratio": projection_coverage["yz"],
                    "mean_projected_occupancy_ratio": mean_projection_coverage,
                    "surface_area_claimed": False,
                },
                "multiview_support": {
                    "camera_count": camera_count,
                    "selected_point_count": len(selected_votes),
                    "support_view_votes": support_total,
                    "observed_view_votes": observed_total,
                    "mean_support_ratio_per_selected_point": mean_support_ratio,
                    "support_views_per_candidate_point": support_per_candidate,
                    "minimum_selected_support_ratio": min(
                        (vote.support_ratio for vote in selected_votes), default=0.0
                    ),
                },
            },
            "policy": policy.as_dict(),
            "diagnostics": [],
        }
    )
