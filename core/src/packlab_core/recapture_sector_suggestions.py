"""Deterministic, evidence-bound recapture-sector diagnostics."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Final, cast

from .object_geometry_coverage import (
    ObjectGeometryCoveragePolicy,
    ObjectGeometryCoverageReport,
    build_object_geometry_coverage_report,
)
from .object_mask_lifting import ObjectCaptureGeometry
from .registered_photo_ratio import RegisteredPhotoRatioReport

RECAPTURE_SECTOR_CONTRACT: Final = "packlab.recapture-sector-suggestions.v1"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_MAX_CAMERAS = 512
_MAX_SUGGESTIONS = 12


class RecaptureSectorError(ValueError):
    """Raised when the recapture suggestion policy is invalid."""


@dataclass(frozen=True, slots=True)
class RecaptureSectorPolicy:
    """Versioned bounded sector grid and inclusive QA thresholds."""

    profile_id: str = "recapture-sector-v1"
    azimuth_sector_count: int = 8
    elevation_band_count: int = 3
    maximum_suggestions: int = 6
    minimum_registration_ratio: float = 0.70
    minimum_selected_point_ratio: float = 0.20
    minimum_mean_support_ratio: float = 0.70
    minimum_projected_occupancy_ratio: float = 0.10

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", self.profile_id
        ):
            raise RecaptureSectorError("profile_id must be a safe identifier")
        for name, low, high in (
            ("azimuth_sector_count", 4, 24),
            ("elevation_band_count", 1, 6),
            ("maximum_suggestions", 1, _MAX_SUGGESTIONS),
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                raise RecaptureSectorError(f"{name} must be between {low} and {high}")
        for name in (
            "minimum_registration_ratio",
            "minimum_selected_point_ratio",
            "minimum_mean_support_ratio",
            "minimum_projected_occupancy_ratio",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or not 0 <= value <= 1
            ):
                raise RecaptureSectorError(f"{name} must be finite and within 0..1")
            object.__setattr__(self, name, float(value))

    def as_dict(self) -> dict[str, object]:
        return {
            "version": "packlab.recapture-sector-policy.v1",
            "profile_id": self.profile_id,
            "azimuth_sector_count": self.azimuth_sector_count,
            "elevation_band_count": self.elevation_band_count,
            "maximum_suggestions": self.maximum_suggestions,
            "minimum_registration_ratio": self.minimum_registration_ratio,
            "minimum_selected_point_ratio": self.minimum_selected_point_ratio,
            "minimum_mean_support_ratio": self.minimum_mean_support_ratio,
            "minimum_projected_occupancy_ratio": self.minimum_projected_occupancy_ratio,
            "threshold_boundaries_inclusive": True,
            "coordinate_frame": "normalized_world_xyz_relative_to_selected_point_centroid",
        }


@dataclass(frozen=True, slots=True)
class RecaptureSectorSuggestionReport:
    """Canonical diagnostic-only report; it cannot mutate capture or geometry."""

    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return json.loads(json.dumps(self.payload, sort_keys=True, allow_nan=False))

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


def _canonical_digest(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _unavailable(code: str, policy: RecaptureSectorPolicy) -> RecaptureSectorSuggestionReport:
    return RecaptureSectorSuggestionReport(
        {
            "contract": RECAPTURE_SECTOR_CONTRACT,
            "authority": "diagnostic_only_no_capture_mutation_or_acceptance",
            "decision": "unavailable",
            "fallback": None,
            "source_evidence": None,
            "qa_gaps": [],
            "suggestions": [],
            "diagnostics": [{"code": code}],
            "policy": policy.as_dict(),
        }
    )


def _finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _valid_registration(
    report: object, geometry: ObjectCaptureGeometry
) -> tuple[dict[str, object], dict[str, object]] | None:
    if not isinstance(report, RegisteredPhotoRatioReport):
        return None
    try:
        payload = report.as_dict()
        evidence = payload.get("source_evidence")
        statistics = payload.get("statistics")
        if (
            payload.get("contract") != "packlab.registered-photo-ratio.v1"
            or payload.get("observation_status") != "observed"
            or payload.get("acceptance_status") != "not_evaluated"
            or not isinstance(evidence, dict)
            or not isinstance(statistics, dict)
            or evidence.get("source_revision") != geometry.source_revision
            or evidence.get("source_sha256") != geometry.source_input_digest
        ):
            return None
        total = statistics.get("total_input_photos")
        registered = statistics.get("registered_photos")
        ratio = statistics.get("registration_ratio")
        input_count = evidence.get("ordered_input_photo_count")
        request_digest = evidence.get("request_sha256")
        photo_digest = evidence.get("ordered_input_photo_ids_sha256")
        if (
            isinstance(total, bool)
            or not isinstance(total, int)
            or total < 1
            or total != len(geometry.camera_evidence)
            or input_count != total
            or isinstance(registered, bool)
            or not isinstance(registered, int)
            or not 0 <= registered <= total
            or not _finite_number(ratio)
            or float(cast(float, ratio)) != registered / total
            or not isinstance(request_digest, str)
            or _SHA256.fullmatch(request_digest) is None
            or not isinstance(photo_digest, str)
            or _SHA256.fullmatch(photo_digest) is None
        ):
            return None
        return evidence, statistics
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def _valid_coverage(
    report: object, geometry: ObjectCaptureGeometry
) -> tuple[dict[str, object], dict[str, object]] | None:
    if not isinstance(report, ObjectGeometryCoverageReport):
        return None
    try:
        payload = report.as_dict()
        policy_payload = payload.get("policy")
        evidence = payload.get("source_evidence")
        statistics = payload.get("statistics")
        if (
            payload.get("contract") != "packlab.object-geometry-coverage.v1"
            or payload.get("authority") != "diagnostic_only_no_geometry_promotion"
            or payload.get("observation_status") not in {"observed", "empty"}
            or payload.get("acceptance_status") != "not_evaluated"
            or not isinstance(policy_payload, dict)
            or not isinstance(evidence, dict)
            or not isinstance(statistics, dict)
        ):
            return None
        policy = ObjectGeometryCoveragePolicy(
            profile_id=policy_payload["profile_id"],
            grid_resolution=policy_payload["grid_resolution"],
            minimum_selected_point_ratio=policy_payload["minimum_selected_point_ratio"],
            minimum_mean_support_ratio=policy_payload["minimum_mean_support_ratio"],
            minimum_projected_coverage_ratio=policy_payload["minimum_projected_coverage_ratio"],
        )
        rebuilt = build_object_geometry_coverage_report(geometry, policy=policy).as_dict()
        if payload != rebuilt:
            return None
        parents = evidence.get("parents")
        if (
            evidence.get("geometry_id") != geometry.geometry_id
            or not isinstance(parents, dict)
            or parents.get("source_revision") != geometry.source_revision
            or parents.get("source_input_digest") != geometry.source_input_digest
            or parents.get("reconstruction_revision") != geometry.reconstruction_revision
            or parents.get("camera_solution_revision") != geometry.camera_solution_revision
            or parents.get("mask_set_revision_id") != geometry.mask_set_revision_id
            or parents.get("mask_set_revision_digest") != geometry.mask_set_revision_digest
        ):
            return None
        return evidence, statistics
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return None


def _camera_center(matrix: tuple[float, ...]) -> tuple[float, float, float] | None:
    if len(matrix) != 16 or any(not _finite_number(value) for value in matrix):
        return None
    # The normalized parent contract is row-major world-to-camera, column vectors.
    if any(
        abs(float(matrix[index]) - expected) > 1e-6
        for index, expected in ((12, 0), (13, 0), (14, 0), (15, 1))
    ):
        return None
    rotation = (
        (float(matrix[0]), float(matrix[1]), float(matrix[2])),
        (float(matrix[4]), float(matrix[5]), float(matrix[6])),
        (float(matrix[8]), float(matrix[9]), float(matrix[10])),
    )
    for row in rotation:
        if abs(sum(value * value for value in row) - 1.0) > 1e-4:
            return None
    for left in range(3):
        for right in range(left + 1, 3):
            if abs(sum(rotation[left][axis] * rotation[right][axis] for axis in range(3))) > 1e-4:
                return None
    translation = (float(matrix[3]), float(matrix[7]), float(matrix[11]))
    center = (
        -sum(rotation[row][0] * translation[row] for row in range(3)),
        -sum(rotation[row][1] * translation[row] for row in range(3)),
        -sum(rotation[row][2] * translation[row] for row in range(3)),
    )
    return center if all(math.isfinite(value) for value in center) else None


def _sector_id(azimuth_index: int, elevation_index: int, policy: RecaptureSectorPolicy) -> str:
    return f"az{azimuth_index:02d}-el{elevation_index:02d}"


def _sector_for(
    direction: tuple[float, float, float], policy: RecaptureSectorPolicy
) -> tuple[int, int]:
    x, y, z = direction
    azimuth = math.degrees(math.atan2(y, x)) % 360.0
    elevation = math.degrees(math.asin(max(-1.0, min(1.0, z))))
    azimuth_index = min(
        policy.azimuth_sector_count - 1,
        int(azimuth / 360.0 * policy.azimuth_sector_count),
    )
    elevation_index = min(
        policy.elevation_band_count - 1,
        int((elevation + 90.0) / 180.0 * policy.elevation_band_count),
    )
    return azimuth_index, elevation_index


def _sector_center(
    azimuth_index: int, elevation_index: int, policy: RecaptureSectorPolicy
) -> tuple[float, float, float]:
    azimuth = math.radians((azimuth_index + 0.5) * 360.0 / policy.azimuth_sector_count)
    elevation = math.radians((elevation_index + 0.5) * 180.0 / policy.elevation_band_count - 90.0)
    return (
        math.cos(elevation) * math.cos(azimuth),
        math.cos(elevation) * math.sin(azimuth),
        math.sin(elevation),
    )


def suggest_recapture_sectors(
    geometry: object,
    registration_report: object,
    coverage_report: object,
    *,
    policy: RecaptureSectorPolicy = RecaptureSectorPolicy(),
) -> RecaptureSectorSuggestionReport:
    """Suggest missing relative-world sectors from validated registration and coverage evidence."""
    if not isinstance(policy, RecaptureSectorPolicy):
        raise RecaptureSectorError("an explicit RecaptureSectorPolicy is required")
    if not isinstance(geometry, ObjectCaptureGeometry):
        return _unavailable("object_geometry_missing_or_invalid", policy)
    registration = _valid_registration(registration_report, geometry)
    if registration is None:
        return _unavailable("registration_evidence_missing_or_unbound", policy)
    coverage = _valid_coverage(coverage_report, geometry)
    if coverage is None:
        return _unavailable("coverage_evidence_missing_or_unbound", policy)
    registration_evidence, registration_stats = registration
    coverage_evidence, coverage_stats = coverage
    registration_report = cast(RegisteredPhotoRatioReport, registration_report)
    coverage_report = cast(ObjectGeometryCoverageReport, coverage_report)
    coverage_values = coverage_stats.get("coverage")
    support_values = coverage_stats.get("multiview_support")
    if not isinstance(coverage_values, dict) or not isinstance(support_values, dict):
        return _unavailable("coverage_statistics_malformed", policy)
    raw_ratios = {
        "registration_ratio": registration_stats["registration_ratio"],
        "selected_point_ratio": coverage_stats.get("selected_point_ratio"),
        "mean_support_ratio": support_values.get("mean_support_ratio_per_selected_point"),
        "mean_projected_occupancy_ratio": coverage_values.get("mean_projected_occupancy_ratio"),
    }
    if any(
        not _finite_number(value) or not 0 <= float(cast(float, value)) <= 1
        for value in raw_ratios.values()
    ):
        return _unavailable("qa_metrics_malformed", policy)
    ratios = {key: float(cast(float, value)) for key, value in raw_ratios.items()}
    gaps = [
        code
        for code, value, minimum in (
            (
                "registration_below_threshold",
                ratios["registration_ratio"],
                policy.minimum_registration_ratio,
            ),
            (
                "selected_point_coverage_below_threshold",
                ratios["selected_point_ratio"],
                policy.minimum_selected_point_ratio,
            ),
            (
                "multiview_support_below_threshold",
                ratios["mean_support_ratio"],
                policy.minimum_mean_support_ratio,
            ),
            (
                "projected_occupancy_below_threshold",
                ratios["mean_projected_occupancy_ratio"],
                policy.minimum_projected_occupancy_ratio,
            ),
        )
        if value < minimum
    ]
    if not gaps:
        return RecaptureSectorSuggestionReport(
            {
                "contract": RECAPTURE_SECTOR_CONTRACT,
                "authority": "diagnostic_only_no_capture_mutation_or_acceptance",
                "decision": "no_recapture_indicated",
                "fallback": None,
                "source_evidence": {
                    "geometry_id": geometry.geometry_id,
                    "geometry_parents": geometry.as_dict()["parents"],
                    "registration_report_sha256": registration_report.digest(),
                    "coverage_report_sha256": coverage_report.digest(),
                },
                "qa_gaps": [],
                "qa_gap_localization": "none",
                "suggestions": [],
                "metrics": ratios,
                "policy": policy.as_dict(),
                "diagnostics": [],
            }
        )

    if len(geometry.camera_evidence) > _MAX_CAMERAS:
        return _unavailable("camera_evidence_exceeds_bound", policy)
    points = geometry.filtered_points
    center: tuple[float, float, float] | None = None
    if points:
        center = (
            sum(float(point[0]) for point in points) / len(points),
            sum(float(point[1]) for point in points) / len(points),
            sum(float(point[2]) for point in points) / len(points),
        )
    if center is None:
        return RecaptureSectorSuggestionReport(
            {
                "contract": RECAPTURE_SECTOR_CONTRACT,
                "authority": "diagnostic_only_no_capture_mutation_or_acceptance",
                "decision": "full_rescan",
                "fallback": {
                    "action": "full_rescan",
                    "reason_code": "qa_gap_without_selected_geometry_anchor",
                },
                "source_evidence": {
                    "geometry_id": geometry.geometry_id,
                    "geometry_parents": geometry.as_dict()["parents"],
                    "registration_report_sha256": registration_report.digest(),
                    "coverage_report_sha256": coverage_report.digest(),
                },
                "qa_gaps": gaps,
                "qa_gap_localization": "global_signals_are_not_attributed_to_individual_sectors",
                "suggestions": [],
                "metrics": ratios,
                "policy": policy.as_dict(),
                "diagnostics": [{"code": "targeted_recapture_not_localizable"}],
            }
        )

    occupied: set[tuple[int, int]] = set()
    camera_directions: list[tuple[float, float, float]] = []
    for camera in geometry.camera_evidence:
        camera_center = _camera_center(camera.normalized_world_to_camera)
        if camera_center is None:
            return _unavailable("camera_pose_invalid_for_sector_derivation", policy)
        vector = tuple(camera_center[axis] - center[axis] for axis in range(3))
        norm = math.sqrt(sum(value * value for value in vector))
        if norm <= 1e-9:
            continue
        direction = (vector[0] / norm, vector[1] / norm, vector[2] / norm)
        camera_directions.append(direction)
        occupied.add(_sector_for(direction, policy))
    if not camera_directions:
        return RecaptureSectorSuggestionReport(
            {
                "contract": RECAPTURE_SECTOR_CONTRACT,
                "authority": "diagnostic_only_no_capture_mutation_or_acceptance",
                "decision": "full_rescan",
                "fallback": {"action": "full_rescan", "reason_code": "no_usable_view_direction"},
                "source_evidence": {
                    "geometry_id": geometry.geometry_id,
                    "geometry_parents": geometry.as_dict()["parents"],
                    "registration_report_sha256": registration_report.digest(),
                    "coverage_report_sha256": coverage_report.digest(),
                },
                "qa_gaps": gaps,
                "qa_gap_localization": "global_signals_are_not_attributed_to_individual_sectors",
                "suggestions": [],
                "metrics": ratios,
                "policy": policy.as_dict(),
                "diagnostics": [{"code": "targeted_recapture_not_localizable"}],
            }
        )

    candidates: list[tuple[float, str, int, int]] = []
    for elevation_index in range(policy.elevation_band_count):
        for azimuth_index in range(policy.azimuth_sector_count):
            if (azimuth_index, elevation_index) in occupied:
                continue
            sector_vector = _sector_center(azimuth_index, elevation_index, policy)
            nearest_dot = max(
                sum(sector_vector[axis] * direction[axis] for axis in range(3))
                for direction in camera_directions
            )
            angular_gap = math.degrees(math.acos(max(-1.0, min(1.0, nearest_dot))))
            candidates.append(
                (
                    angular_gap,
                    _sector_id(azimuth_index, elevation_index, policy),
                    azimuth_index,
                    elevation_index,
                )
            )
    candidates.sort(key=lambda item: (-item[0], item[1]))
    suggestions = [
        {
            "sector_id": sector_id,
            "azimuth_index": azimuth_index,
            "elevation_band_index": elevation_index,
            "azimuth_degrees": {
                "start_inclusive": azimuth_index * 360.0 / policy.azimuth_sector_count,
                "end_exclusive": (azimuth_index + 1) * 360.0 / policy.azimuth_sector_count,
            },
            "elevation_degrees": {
                "start_inclusive": elevation_index * 180.0 / policy.elevation_band_count - 90.0,
                "end_inclusive": (elevation_index + 1) * 180.0 / policy.elevation_band_count - 90.0,
            },
            "nearest_observed_view_gap_degrees": round(angular_gap, 6),
            "reason_codes": ["unobserved_view_sector"],
            "associated_global_qa_gaps": gaps,
            "coordinate_frame": "normalized_world_xyz_relative_to_selected_point_centroid",
            "physical_orientation_claimed": False,
        }
        for angular_gap, sector_id, azimuth_index, elevation_index in candidates[
            : policy.maximum_suggestions
        ]
    ]
    decision = "targeted_recapture" if suggestions else "full_rescan"
    fallback = (
        None
        if suggestions
        else {
            "action": "full_rescan",
            "reason_code": "qa_gaps_remain_with_all_view_sectors_observed",
        }
    )
    return RecaptureSectorSuggestionReport(
        {
            "contract": RECAPTURE_SECTOR_CONTRACT,
            "authority": "diagnostic_only_no_capture_mutation_or_acceptance",
            "decision": decision,
            "fallback": fallback,
            "source_evidence": {
                "geometry_id": geometry.geometry_id,
                "geometry_parents": geometry.as_dict()["parents"],
                "camera_evidence_sha256": _canonical_digest(
                    [
                        camera.as_dict()
                        for camera in sorted(
                            geometry.camera_evidence, key=lambda item: item.camera_id
                        )
                    ]
                ),
                "registration_report_sha256": registration_report.digest(),
                "registration_source_evidence_sha256": _canonical_digest(registration_evidence),
                "coverage_report_sha256": coverage_report.digest(),
                "coverage_source_evidence_sha256": _canonical_digest(coverage_evidence),
            },
            "qa_gaps": gaps,
            "qa_gap_localization": "global_signals_are_not_attributed_to_individual_sectors",
            "metrics": ratios,
            "occupied_sector_count": len(occupied),
            "suggestions": suggestions,
            "policy": policy.as_dict(),
            "diagnostics": [],
        }
    )
