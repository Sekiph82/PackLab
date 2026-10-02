"""Estimate reconstruction units to millimetres from bound 3D marker geometry."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from statistics import median

from .marker_association import AssociatedMarkerObservation

SCALE_MATH_VERSION = "camera_bound_marker_3d_scale_v1"
OUTLIER_POLICY_VERSION = "median_relative_residual_5pct_v1"
MIN_SCALE_OBSERVATIONS = 2
MAX_RELATIVE_RESIDUAL = 0.05
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
Point3 = tuple[float, float, float]


class ReconstructionScaleError(ValueError):
    """Raised when reconstruction-scale inputs are structurally unsafe."""


@dataclass(frozen=True, slots=True)
class PhysicalMarkerReference:
    """Versioned known marker geometry, explicitly physical or test-only."""

    marker_id: int
    reference_id: str
    reference_digest: str
    side_length: float
    unit: str
    uncertainty_mm: float
    evidence_class: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.marker_id, int)
            or isinstance(self.marker_id, bool)
            or self.marker_id < 0
        ):
            raise ReconstructionScaleError("marker_id_invalid")
        if not isinstance(self.reference_id, str) or not self.reference_id.strip():
            raise ReconstructionScaleError("physical_reference_id_required")
        if not isinstance(self.reference_digest, str) or not _SHA256.fullmatch(
            self.reference_digest
        ):
            raise ReconstructionScaleError("physical_reference_digest_invalid")
        if self.unit != "mm":
            raise ReconstructionScaleError("physical_reference_unit_must_be_mm")
        if not _positive_finite(self.side_length):
            raise ReconstructionScaleError("physical_marker_side_must_be_positive_finite")
        if not _positive_finite(self.uncertainty_mm):
            raise ReconstructionScaleError("physical_reference_uncertainty_must_be_positive_finite")
        if self.evidence_class not in {"accepted_owner_physical", "synthetic_test_fixture"}:
            raise ReconstructionScaleError("physical_reference_evidence_class_invalid")


@dataclass(frozen=True, slots=True)
class ReconstructedMarkerGeometry:
    """Four reconstructed 3D corners tied to the PL-0202 image observation."""

    observation: AssociatedMarkerObservation
    reconstruction_revision: str
    coordinate_unit: str
    corners_reconstruction_units: tuple[Point3, Point3, Point3, Point3]
    corner_uncertainty_units: float

    def __post_init__(self) -> None:
        if not isinstance(self.reconstruction_revision, str) or not self.reconstruction_revision:
            raise ReconstructionScaleError("reconstruction_revision_required")
        if self.coordinate_unit != "reconstruction_units":
            raise ReconstructionScaleError("reconstructed_marker_unit_mismatch")
        if len(self.corners_reconstruction_units) != 4 or any(
            len(point) != 3 or not all(_finite(value) for value in point)
            for point in self.corners_reconstruction_units
        ):
            raise ReconstructionScaleError("reconstructed_marker_corners_invalid")
        if not _positive_finite(self.corner_uncertainty_units):
            raise ReconstructionScaleError("reconstructed_corner_uncertainty_invalid")


@dataclass(frozen=True, slots=True)
class ReconstructionScaleObservation:
    physical_reference: PhysicalMarkerReference
    reconstructed_geometry: ReconstructedMarkerGeometry


@dataclass(frozen=True, slots=True)
class ReconstructionScaleEstimate:
    status: str
    reconstruction_units_to_mm: float | None
    uncertainty_mm_per_reconstruction_unit: float | None
    metric_state: str
    observations_used: tuple[str, ...]
    observations_rejected: tuple[str, ...]
    residuals: tuple[dict[str, float | str | bool], ...]
    provenance: dict[str, str]
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.reconstruction-scale-estimate.v1",
            "status": self.status,
            "reconstruction_units_to_mm": self.reconstruction_units_to_mm,
            "uncertainty_mm_per_reconstruction_unit": self.uncertainty_mm_per_reconstruction_unit,
            "metric_state": self.metric_state,
            "observations_used": list(self.observations_used),
            "observations_rejected": list(self.observations_rejected),
            "residuals": [dict(item) for item in self.residuals],
            "provenance": dict(self.provenance),
            "errors": list(self.errors),
        }


def estimate_reconstruction_scale(
    observations: tuple[ReconstructionScaleObservation, ...],
    *,
    reconstruction_revision: str,
    camera_solution_revision: str,
) -> ReconstructionScaleEstimate:
    """Estimate one global factor without promoting metric authority.

    Each physical side length is compared with its corresponding edge length
    in reconstruction coordinates. The existing image-space mm/pixel
    estimator is deliberately not used. All observations must bind to the
    requested reconstruction and camera-solution revisions.
    """

    if not reconstruction_revision or not camera_solution_revision:
        raise ReconstructionScaleError("scale_parent_revision_required")
    ordered = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.reconstructed_geometry.observation.marker_id,
                item.reconstructed_geometry.observation.camera_id,
                item.reconstructed_geometry.observation.source_image_asset_id,
            ),
        )
    )
    candidates: list[tuple[str, float, float, str]] = []
    rejected: list[str] = []
    seen: set[str] = set()
    for item in ordered:
        geometry = item.reconstructed_geometry
        association = geometry.observation
        observation_id = _observation_id(association)
        if observation_id in seen:
            rejected.append(f"{observation_id}:duplicate_observation")
            continue
        seen.add(observation_id)
        reason = _mismatch_reason(
            item,
            reconstruction_revision=reconstruction_revision,
            camera_solution_revision=camera_solution_revision,
        )
        if reason is not None:
            rejected.append(f"{observation_id}:{reason}")
            continue
        edge_lengths = _edge_lengths(geometry.corners_reconstruction_units)
        mean_edge = sum(edge_lengths) / 4.0
        if any(not _positive_finite(edge) for edge in edge_lengths):
            rejected.append(f"{observation_id}:reconstructed_marker_edges_degenerate")
            continue
        spread = (max(edge_lengths) - min(edge_lengths)) / mean_edge
        reference = item.physical_reference
        factor = reference.side_length / mean_edge
        relative_uncertainty = math.sqrt(
            (reference.uncertainty_mm / reference.side_length) ** 2
            + (geometry.corner_uncertainty_units / mean_edge) ** 2
            + spread**2
        )
        sigma = max(factor * relative_uncertainty, 1e-12)
        candidates.append((observation_id, factor, sigma, reference.evidence_class))

    if len(candidates) < MIN_SCALE_OBSERVATIONS:
        rejected.extend(f"{item[0]}:insufficient_consensus" for item in candidates)
        return _rejected(
            rejected,
            (),
            "insufficient_camera_bound_scale_observations",
        )

    robust_center = median(item[1] for item in candidates)
    inliers = [
        item
        for item in candidates
        if abs(item[1] - robust_center) / robust_center <= MAX_RELATIVE_RESIDUAL
    ]
    for observation_id, factor, _sigma, _evidence_class in candidates:
        if abs(factor - robust_center) / robust_center > MAX_RELATIVE_RESIDUAL:
            rejected.append(f"{observation_id}:outlier_relative_residual")
    if len(inliers) < MIN_SCALE_OBSERVATIONS:
        rejected.extend(f"{item[0]}:insufficient_consensus" for item in inliers)
        return _rejected(
            rejected,
            (),
            "insufficient_consistent_scale_observations",
        )

    weights = [1.0 / (item[2] * item[2]) for item in inliers]
    weight_sum = sum(weights)
    estimate = (
        sum(weight * item[1] for weight, item in zip(weights, inliers, strict=True)) / weight_sum
    )
    residuals: tuple[dict[str, float | str | bool], ...] = tuple(
        {
            "observation_id": observation_id,
            "scale_factor_mm_per_unit": factor,
            "relative_residual": abs(factor - estimate) / estimate,
            "used": observation_id in {item[0] for item in inliers},
        }
        for observation_id, factor, _sigma, _evidence_class in candidates
    )
    if any(
        residual["used"] is True
        and isinstance(residual["relative_residual"], (int, float))
        and residual["relative_residual"] > MAX_RELATIVE_RESIDUAL
        for residual in residuals
    ):
        return _rejected(
            (*rejected, "inliers:inconsistent_after_weighted_fit"),
            tuple(item[0] for item in inliers),
            "inconsistent_camera_bound_scale_observations",
            residuals,
        )
    variance = (
        sum(
            weight * (item[1] - estimate) ** 2
            for weight, item in zip(weights, inliers, strict=True)
        )
        / weight_sum
    )
    uncertainty = math.sqrt(variance + 1.0 / weight_sum)
    provenance = _provenance(inliers, reconstruction_revision, camera_solution_revision)
    return ReconstructionScaleEstimate(
        "estimated",
        estimate,
        uncertainty,
        "METRIC_UNVERIFIED",
        tuple(item[0] for item in inliers),
        tuple(sorted(rejected)),
        residuals,
        provenance,
        (),
    )


def _mismatch_reason(
    item: ReconstructionScaleObservation,
    *,
    reconstruction_revision: str,
    camera_solution_revision: str,
) -> str | None:
    reference = item.physical_reference
    geometry = item.reconstructed_geometry
    association = geometry.observation
    if reference.marker_id != association.marker_id:
        return "marker_identity_mismatch"
    if geometry.reconstruction_revision != reconstruction_revision:
        return "reconstruction_revision_mismatch"
    if association.camera_solution_revision != camera_solution_revision:
        return "camera_solution_revision_mismatch"
    if association.image_width <= 0 or association.image_height <= 0:
        return "source_image_dimensions_invalid"
    if not _SHA256.fullmatch(association.source_digest):
        return "source_image_digest_invalid"
    return None


def _edge_lengths(corners: tuple[Point3, Point3, Point3, Point3]) -> tuple[float, ...]:
    return tuple(
        math.sqrt(
            sum((corners[(index + 1) % 4][axis] - corners[index][axis]) ** 2 for axis in range(3))
        )
        for index in range(4)
    )


def _observation_id(observation: AssociatedMarkerObservation) -> str:
    payload = {
        "marker_id": observation.marker_id,
        "source_image_asset_id": observation.source_image_asset_id,
        "source_digest": observation.source_digest,
        "camera_id": observation.camera_id,
        "camera_solution_revision": observation.camera_solution_revision,
        "corners_px": [list(point) for point in observation.corners_px],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _provenance(
    inliers: list[tuple[str, float, float, str]],
    reconstruction_revision: str,
    camera_solution_revision: str,
) -> dict[str, str]:
    evidence_classes = ",".join(sorted({item[3] for item in inliers}))
    return {
        "math_version": SCALE_MATH_VERSION,
        "outlier_policy_version": OUTLIER_POLICY_VERSION,
        "input_geometry_unit": "reconstruction_units",
        "output_unit": "mm_per_reconstruction_unit",
        "reconstruction_revision": reconstruction_revision,
        "camera_solution_revision": camera_solution_revision,
        "evidence_classes": evidence_classes,
        "metric_state": "METRIC_UNVERIFIED",
    }


def _rejected(
    rejected: list[str] | tuple[str, ...],
    used: tuple[str, ...],
    error: str,
    residuals: tuple[dict[str, float | str | bool], ...] = (),
) -> ReconstructionScaleEstimate:
    return ReconstructionScaleEstimate(
        "rejected",
        None,
        None,
        "METRIC_UNVERIFIED",
        used,
        tuple(sorted(rejected)),
        residuals,
        {
            "math_version": SCALE_MATH_VERSION,
            "outlier_policy_version": OUTLIER_POLICY_VERSION,
            "metric_state": "METRIC_UNVERIFIED",
        },
        (error,),
    )


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0.0
    )
