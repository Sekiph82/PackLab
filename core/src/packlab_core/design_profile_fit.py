"""Constrained smoothing of complete Scan Master profile evidence into Design Model data."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import StrEnum

from .design_model_binding import DesignModelParentBindingRevision
from .design_profile import DesignProfile, ProfilePoint, create_design_profile
from .reconstruction import ScaleState
from .scan_master_profile import ScanMasterVerticalProfile

FIT_CONTRACT = "packlab.design-model-profile-fit.v1"
MAX_FIT_BANDS = 512


class DesignProfileFitError(ValueError):
    """Raised when fit controls or source profile evidence are invalid."""


class ProfileTransitionKind(StrEnum):
    BASE = "base_transition"
    SHOULDER = "shoulder_transition"


class ProfileFitStatus(StrEnum):
    FITTED = "FITTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class ProfileTransitionAnchor:
    kind: ProfileTransitionKind
    band_index: int

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProfileTransitionKind):
            raise DesignProfileFitError("transition_kind_invalid")
        if isinstance(self.band_index, bool) or not isinstance(self.band_index, int):
            raise DesignProfileFitError("transition_band_index_invalid")

    def as_dict(self) -> dict[str, object]:
        return {"kind": self.kind.value, "band_index": self.band_index}


@dataclass(frozen=True, slots=True)
class ProfileFitResidual:
    band_index: int
    axis_position: float
    observed_radius: float
    fitted_radius: float
    residual: float
    source_vertex_indices: tuple[int, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "band_index": self.band_index,
            "axis_position": self.axis_position,
            "observed_radius": self.observed_radius,
            "fitted_radius": self.fitted_radius,
            "residual": self.residual,
            "source_vertex_indices": list(self.source_vertex_indices),
        }


@dataclass(frozen=True, slots=True)
class DesignModelProfileFit:
    fit_id: str
    status: ProfileFitStatus
    profile: DesignProfile | None
    source_profile_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    parent_binding: DesignModelParentBindingRevision
    smoothing_strength: float
    window_radius: int
    maximum_relative_adjustment: float
    transition_anchors: tuple[ProfileTransitionAnchor, ...]
    residuals: tuple[ProfileFitResidual, ...]
    rejected_source_vertex_indices: tuple[int, ...]
    uncertainty_codes: tuple[str, ...]
    coordinate_unit: str
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": FIT_CONTRACT,
            "fit_id": self.fit_id,
            "status": self.status.value,
            "authority_class": "DESIGN_MODEL_PROFILE_DATA",
            "source_profile_id": self.source_profile_id,
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "design_model_parent_binding": self.parent_binding.as_dict(),
            },
            "profile": self.profile.as_dict() if self.profile is not None else None,
            "regularization": {
                "method": "bounded_segment_local_moving_mean_blend_v1",
                "smoothing_strength": self.smoothing_strength,
                "window_radius": self.window_radius,
                "maximum_relative_adjustment": self.maximum_relative_adjustment,
                "protected_transition_anchors": [
                    item.as_dict() for item in self.transition_anchors
                ],
                "transition_neighborhood_radius": 1,
            },
            "residuals": [item.as_dict() for item in self.residuals],
            "rejected_evidence": {
                "source_vertex_indices": list(self.rejected_source_vertex_indices),
                "source_profile_outliers_retained_as_rejections": True,
            },
            "uncertainty_codes": list(self.uncertainty_codes),
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "scan_master_replaced": False,
            "missing_gaps_interpolated": False,
        }


def fit_design_profile(
    evidence: ScanMasterVerticalProfile,
    *,
    transition_anchors: tuple[ProfileTransitionAnchor, ...],
    smoothing_strength: float,
    window_radius: int,
    maximum_relative_adjustment: float = 0.10,
) -> DesignModelProfileFit:
    """Fit a Design Profile without crossing or smoothing declared transitions."""
    if not isinstance(evidence, ScanMasterVerticalProfile):
        raise DesignProfileFitError("scan_master_profile_evidence_required")
    _validate_source_authority(evidence)
    _finite_range(smoothing_strength, 0.0, 0.5, "smoothing_strength_out_of_range")
    _finite_range(
        maximum_relative_adjustment, 0.0, 0.25, "maximum_relative_adjustment_out_of_range"
    )
    if (
        isinstance(window_radius, bool)
        or not isinstance(window_radius, int)
        or not 1 <= window_radius <= 8
    ):
        raise DesignProfileFitError("window_radius_out_of_range")
    if not isinstance(transition_anchors, tuple) or any(
        not isinstance(item, ProfileTransitionAnchor) for item in transition_anchors
    ):
        raise DesignProfileFitError("transition_anchors_must_be_typed_tuple")
    if len(transition_anchors) != 2 or {item.kind for item in transition_anchors} != {
        ProfileTransitionKind.BASE,
        ProfileTransitionKind.SHOULDER,
    }:
        raise DesignProfileFitError("base_and_shoulder_anchors_required")
    bands = tuple(sorted(evidence.bands, key=lambda item: item.band_index))
    anchors = tuple(sorted(transition_anchors, key=lambda item: item.band_index))
    if len(bands) > MAX_FIT_BANDS:
        raise DesignProfileFitError("profile_band_limit_exceeded")
    if len({item.band_index for item in anchors}) != len(anchors):
        raise DesignProfileFitError("transition_anchor_duplicate")
    if len({item.band_index for item in bands}) != len(bands):
        raise DesignProfileFitError("source_profile_band_duplicate")
    band_indices = tuple(item.band_index for item in bands)
    if any(anchor.band_index not in band_indices for anchor in anchors):
        raise DesignProfileFitError("transition_anchor_not_observed")
    rejected_ids = tuple(sorted({item.source_vertex_index for item in evidence.outliers}))
    if evidence.coverage_gaps:
        return _review_result(
            evidence,
            anchors,
            smoothing_strength,
            window_radius,
            maximum_relative_adjustment,
            rejected_ids,
            ("source_profile_has_coverage_gaps",),
        )
    if len(bands) < 3 or any(
        right.band_index != left.band_index + 1 for left, right in zip(bands, bands[1:])
    ):
        return _review_result(
            evidence,
            anchors,
            smoothing_strength,
            window_radius,
            maximum_relative_adjustment,
            rejected_ids,
            ("source_profile_band_sequence_incomplete",),
        )
    axis_values: list[float] = []
    observed_radii: list[float] = []
    for item in bands:
        if (
            item.observed_axis_minimum is None
            or item.observed_axis_maximum is None
            or item.horizontal_minimum is None
            or item.horizontal_maximum is None
            or not item.source_vertex_indices
        ):
            raise DesignProfileFitError("source_profile_band_incomplete")
        axis_values.append((item.observed_axis_minimum + item.observed_axis_maximum) / 2.0)
        observed_radii.append(max(abs(item.horizontal_minimum), abs(item.horizontal_maximum)))
    axis = tuple(axis_values)
    observed = tuple(observed_radii)
    if any(not math.isfinite(value) or value <= 0 for value in (*axis, *observed)):
        raise DesignProfileFitError("source_profile_sample_invalid")
    anchor_positions = {item.band_index for item in anchors}
    protected = {
        index
        for anchor_index in anchor_positions
        for index in range(max(0, anchor_index - 1), min(len(bands), anchor_index + 2))
    }
    fitted = _regularize(observed, anchor_positions, protected, smoothing_strength, window_radius)
    relative_adjustments = tuple(
        abs(new - old) / old for old, new in zip(observed, fitted, strict=True)
    )
    if max(relative_adjustments, default=0.0) > maximum_relative_adjustment:
        return _review_result(
            evidence,
            anchors,
            smoothing_strength,
            window_radius,
            maximum_relative_adjustment,
            rejected_ids,
            ("smoothing_adjustment_exceeds_policy",),
        )
    control_points = tuple(
        ProfilePoint(axis_value, radius) for axis_value, radius in zip(axis, fitted, strict=True)
    )
    if any(right.axial <= left.axial for left, right in zip(control_points, control_points[1:])):
        return _review_result(
            evidence,
            anchors,
            smoothing_strength,
            window_radius,
            maximum_relative_adjustment,
            rejected_ids,
            ("source_profile_axis_not_strictly_increasing",),
        )
    profile = create_design_profile(control_points, evidence.scale_state)
    residuals = tuple(
        ProfileFitResidual(
            band.band_index,
            axis_value,
            observed_radius,
            fitted_radius,
            fitted_radius - observed_radius,
            band.source_vertex_indices,
        )
        for band, axis_value, observed_radius, fitted_radius in zip(
            bands, axis, observed, fitted, strict=True
        )
    )
    body = {
        "contract": FIT_CONTRACT,
        "source_profile_id": evidence.profile_id,
        "scan_master_revision_id": evidence.scan_master_revision_id,
        "scan_master_geometry_sha256": evidence.scan_master_geometry_sha256,
        "profile": profile.as_dict(),
        "smoothing_strength": smoothing_strength,
        "window_radius": window_radius,
        "maximum_relative_adjustment": maximum_relative_adjustment,
        "transition_anchors": [item.as_dict() for item in anchors],
        "residuals": [item.as_dict() for item in residuals],
        "rejected_source_vertex_indices": list(rejected_ids),
    }
    fit_id = (
        "design-profile-fit:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return DesignModelProfileFit(
        fit_id,
        ProfileFitStatus.FITTED,
        profile,
        evidence.profile_id,
        evidence.scan_master_revision_id,
        evidence.scan_master_geometry_sha256,
        evidence.parent_binding,
        smoothing_strength,
        window_radius,
        maximum_relative_adjustment,
        anchors,
        residuals,
        rejected_ids,
        (),
        evidence.coordinate_unit,
    )


def _review_result(
    evidence: ScanMasterVerticalProfile,
    anchors: tuple[ProfileTransitionAnchor, ...],
    smoothing_strength: float,
    window_radius: int,
    maximum_relative_adjustment: float,
    rejected_ids: tuple[int, ...],
    uncertainty: tuple[str, ...],
) -> DesignModelProfileFit:
    body = {
        "contract": FIT_CONTRACT,
        "status": ProfileFitStatus.REVIEW_REQUIRED.value,
        "source_profile_id": evidence.profile_id,
        "scan_master_revision_id": evidence.scan_master_revision_id,
        "scan_master_geometry_sha256": evidence.scan_master_geometry_sha256,
        "transition_anchors": [item.as_dict() for item in anchors],
        "smoothing_strength": smoothing_strength,
        "window_radius": window_radius,
        "maximum_relative_adjustment": maximum_relative_adjustment,
        "rejected_source_vertex_indices": list(rejected_ids),
        "uncertainty_codes": list(uncertainty),
    }
    fit_id = (
        "design-profile-fit:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return DesignModelProfileFit(
        fit_id,
        ProfileFitStatus.REVIEW_REQUIRED,
        None,
        evidence.profile_id,
        evidence.scan_master_revision_id,
        evidence.scan_master_geometry_sha256,
        evidence.parent_binding,
        smoothing_strength,
        window_radius,
        maximum_relative_adjustment,
        anchors,
        (),
        rejected_ids,
        uncertainty,
        evidence.coordinate_unit,
    )


def _regularize(
    values: tuple[float, ...],
    anchors: set[int],
    protected: set[int],
    strength: float,
    window: int,
) -> tuple[float, ...]:
    output: list[float] = []
    for index, value in enumerate(values):
        if index in protected or strength == 0.0:
            output.append(value)
            continue
        left_anchor = max((item for item in anchors if item < index), default=-1)
        right_anchor = min((item for item in anchors if item > index), default=len(values))
        neighbors = tuple(
            values[neighbor]
            for neighbor in range(
                max(left_anchor + 1, index - window), min(right_anchor, index + window + 1)
            )
            if neighbor != index
        )
        if not neighbors:
            output.append(value)
            continue
        local_mean = math.fsum(neighbors) / len(neighbors)
        output.append(value * (1.0 - strength) + local_mean * strength)
    return tuple(output)


def _finite_range(value: float, minimum: float, maximum: float, error: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not minimum <= value <= maximum
    ):
        raise DesignProfileFitError(error)


def _validate_source_authority(evidence: ScanMasterVerticalProfile) -> None:
    binding = evidence.parent_binding
    if not isinstance(binding, DesignModelParentBindingRevision):
        raise DesignProfileFitError("source_profile_parent_binding_invalid")
    expected_unit = (
        "reconstruction_units"
        if evidence.scale_state is ScaleState.RELATIVE
        else "mm_unverified"
        if evidence.scale_state is ScaleState.METRIC_UNVERIFIED
        else None
    )
    if (
        not evidence.profile_id
        or not evidence.scan_master_revision_id
        or binding.fitted_to_scan_master_revision_id != evidence.scan_master_revision_id
        or binding.scan_master_geometry_sha256 != evidence.scan_master_geometry_sha256
        or binding.scale_state is not evidence.scale_state
        or evidence.coordinate_unit != expected_unit
        or evidence.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or evidence.mold_use_authorized is not False
        or evidence.closure_invented is not False
        or evidence.smoothing_applied is not False
    ):
        raise DesignProfileFitError("source_profile_authority_or_parent_invalid")


__all__ = [
    "FIT_CONTRACT",
    "DesignModelProfileFit",
    "DesignProfileFitError",
    "ProfileFitResidual",
    "ProfileFitStatus",
    "ProfileTransitionAnchor",
    "ProfileTransitionKind",
    "fit_design_profile",
]
