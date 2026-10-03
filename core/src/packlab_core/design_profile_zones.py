"""Deterministic, evidence-bound body-zone candidates for fitted profiles."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .design_model import FeatureKind, stable_feature_id
from .design_model_binding import DesignModelParentBindingRevision
from .design_profile import ProfilePoint
from .design_profile_fit import FIT_CONTRACT, DesignModelProfileFit, ProfileFitStatus

ZONE_CONTRACT = "packlab.design-profile-zones.v1"
_ZONE_ORDER = ("base", "body", "shoulder", "neck")
_FEATURE_KIND = {
    "base": FeatureKind.BASE,
    "body": FeatureKind.BODY,
    "shoulder": FeatureKind.SHOULDER,
    "neck": FeatureKind.NECK,
}


class ProfileZoneError(ValueError):
    """Raised when zone evidence, boundaries, or override lineage is invalid."""


class ProfileZoneStatus(StrEnum):
    DETECTED = "DETECTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


@dataclass(frozen=True, slots=True)
class ProfileZoneBoundary:
    feature_id: str
    component_id: str
    zone_kind: str
    semantic_key: str
    start_axial: float
    end_axial: float
    confidence: float
    evidence_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "feature_id": self.feature_id,
            "component_id": self.component_id,
            "feature_kind": self.zone_kind,
            "semantic_key": self.semantic_key,
            "start_axial": self.start_axial,
            "end_axial": self.end_axial,
            "confidence": self.confidence,
            "evidence_codes": list(self.evidence_codes),
        }


@dataclass(frozen=True, slots=True)
class DesignProfileZones:
    revision_id: str
    status: ProfileZoneStatus
    review_required: bool
    fit_id: str
    source_profile_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    parent_binding_revision_id: str
    coordinate_unit: str
    boundaries: tuple[ProfileZoneBoundary, ...]
    uncertainty_codes: tuple[str, ...]
    previous_revision_id: str | None = None
    actor_id: str | None = None
    reason: str | None = None
    created_at_utc: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": ZONE_CONTRACT,
            "revision_id": self.revision_id,
            "status": self.status.value,
            "review_required": self.review_required,
            "authority_class": "DESIGN_MODEL_FEATURE_METADATA",
            "fit_id": self.fit_id,
            "source_profile_id": self.source_profile_id,
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "parent_binding_revision_id": self.parent_binding_revision_id,
            },
            "coordinate_unit": self.coordinate_unit,
            "boundaries": [item.as_dict() for item in self.boundaries],
            "uncertainty_codes": list(self.uncertainty_codes),
            "override": {
                "previous_revision_id": self.previous_revision_id,
                "actor_id": self.actor_id,
                "reason": self.reason,
                "created_at_utc": self.created_at_utc,
            },
            "thread_or_finish_classified": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "scan_master_replaced": False,
        }


def detect_design_profile_zones(
    profile_fit: DesignModelProfileFit,
    *,
    expected_fit_id: str,
    component_id: str,
) -> DesignProfileZones:
    """Detect candidate zone boundaries with fixed radius-ratio rules."""
    points = _validated_fit(profile_fit, expected_fit_id)
    _validate_component_id(component_id)
    radii = tuple(point.radius for point in points)
    peak_index = max(range(len(points)), key=lambda index: (radii[index], -index))
    peak = radii[peak_index]
    if peak <= 0:
        raise ProfileZoneError("profile_radii_invalid")

    base_candidates = tuple(
        index
        for index in range(1, max(2, len(points) // 3))
        if radii[index] >= max(radii[0] * 1.2, peak * 0.5)
    )
    shoulder_candidates = tuple(
        index for index in range(peak_index + 1, len(points) - 1) if radii[index] <= peak * 0.9
    )
    neck_candidates = tuple(
        index
        for index in range(
            (shoulder_candidates[0] + 1) if shoulder_candidates else peak_index + 1, len(points) - 1
        )
        if radii[index] <= peak * 0.75
    )
    ambiguous: list[str] = []
    if not base_candidates:
        ambiguous.append("base_transition_ambiguous")
    if not shoulder_candidates:
        ambiguous.append("shoulder_transition_ambiguous")
    if not neck_candidates:
        ambiguous.append("shoulder_neck_boundary_ambiguous")

    cuts = [0]
    if base_candidates:
        cuts.append(base_candidates[0])
    else:
        cuts.append(max(1, len(points) // 8))
    if shoulder_candidates:
        cuts.append(shoulder_candidates[0])
    else:
        cuts.append(max(cuts[-1] + 1, (3 * len(points)) // 4))
    if neck_candidates:
        cuts.append(neck_candidates[0])
    else:
        cuts.append(max(cuts[-1] + 1, len(points) - 2))
    cuts.append(len(points) - 1)
    if any(right <= left for left, right in zip(cuts, cuts[1:])):
        ambiguous.append("zone_boundary_order_ambiguous")
        cuts = [0, 1, max(2, len(points) // 3), max(3, (2 * len(points)) // 3), len(points) - 1]
    if cuts[-1] >= len(points) or any(right <= left for left, right in zip(cuts, cuts[1:])):
        raise ProfileZoneError("profile_too_short_for_zone_partition")

    confidence = 0.35 if ambiguous else 0.9
    boundaries = tuple(
        _boundary(
            component_id,
            kind,
            points[cuts[index]].axial,
            points[cuts[index + 1]].axial,
            confidence,
            tuple(ambiguous) or ("radius_ratio_transition",),
        )
        for index, kind in enumerate(_ZONE_ORDER)
    )
    return _make_zone_set(
        profile_fit,
        boundaries,
        ProfileZoneStatus.REVIEW_REQUIRED if ambiguous else ProfileZoneStatus.DETECTED,
        tuple(ambiguous),
    )


def override_design_profile_zones(
    current: DesignProfileZones,
    profile_fit: DesignModelProfileFit,
    *,
    expected_zone_revision_id: str,
    expected_fit_id: str,
    boundaries: tuple[ProfileZoneBoundary, ...],
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignProfileZones:
    """Create an immutable, stale-checked manual boundary revision."""
    points = _validated_fit(profile_fit, expected_fit_id)
    if not isinstance(current, DesignProfileZones):
        raise ProfileZoneError("current_profile_zones_required")
    if current.revision_id != expected_zone_revision_id or current.fit_id != profile_fit.fit_id:
        raise ProfileZoneError("profile_zones_or_fit_stale")
    reconstructed = _make_zone_set(
        profile_fit,
        current.boundaries,
        current.status,
        current.uncertainty_codes,
        previous_revision_id=current.previous_revision_id,
        actor_id=current.actor_id,
        reason=current.reason,
        created_at_utc=current.created_at_utc,
    )
    if reconstructed.revision_id != current.revision_id:
        raise ProfileZoneError("profile_zones_identity_invalid")
    _validate_partition(current.boundaries, points[0].axial, points[-1].axial)
    if not isinstance(boundaries, tuple) or len(boundaries) != len(_ZONE_ORDER):
        raise ProfileZoneError("zone_boundaries_must_be_complete_tuple")
    if any(not isinstance(item, ProfileZoneBoundary) for item in boundaries):
        raise ProfileZoneError("zone_boundary_invalid")
    if tuple(item.zone_kind for item in boundaries) != _ZONE_ORDER:
        raise ProfileZoneError("zone_boundary_order_invalid")
    if any(
        (item.feature_id, item.component_id, item.zone_kind, item.semantic_key)
        != (prior.feature_id, prior.component_id, prior.zone_kind, prior.semantic_key)
        for item, prior in zip(boundaries, current.boundaries, strict=True)
    ):
        raise ProfileZoneError("zone_feature_identity_changed")
    _validate_partition(boundaries, points[0].axial, points[-1].axial)
    actor = _text(actor_id, "actor_id")
    why = _text(reason, "override_reason")
    timestamp = _utc_timestamp(created_at_utc)
    result = _make_zone_set(
        profile_fit,
        boundaries,
        ProfileZoneStatus.MANUAL_OVERRIDE,
        current.uncertainty_codes,
        previous_revision_id=current.revision_id,
        actor_id=actor,
        reason=why,
        created_at_utc=timestamp,
    )
    return result


def _validated_fit(
    profile_fit: DesignModelProfileFit, expected_fit_id: str
) -> tuple[ProfilePoint, ...]:
    if not isinstance(profile_fit, DesignModelProfileFit):
        raise ProfileZoneError("design_profile_fit_required")
    if profile_fit.fit_id != expected_fit_id:
        raise ProfileZoneError("design_profile_fit_stale")
    if (
        profile_fit.status is not ProfileFitStatus.FITTED
        or profile_fit.profile is None
        or not isinstance(profile_fit.parent_binding, DesignModelParentBindingRevision)
        or profile_fit.profile.scale_state is not profile_fit.parent_binding.scale_state
        or profile_fit.profile.coordinate_unit != profile_fit.coordinate_unit
        or profile_fit.parent_binding.fitted_to_scan_master_revision_id
        != profile_fit.scan_master_revision_id
        or profile_fit.parent_binding.scan_master_geometry_sha256
        != profile_fit.scan_master_geometry_sha256
        or profile_fit.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or profile_fit.mold_use_authorized is not False
    ):
        raise ProfileZoneError("design_profile_fit_authority_or_parent_invalid")
    identity = {
        "contract": FIT_CONTRACT,
        "source_profile_id": profile_fit.source_profile_id,
        "scan_master_revision_id": profile_fit.scan_master_revision_id,
        "scan_master_geometry_sha256": profile_fit.scan_master_geometry_sha256,
        "profile": profile_fit.profile.as_dict(),
        "smoothing_strength": profile_fit.smoothing_strength,
        "window_radius": profile_fit.window_radius,
        "maximum_relative_adjustment": profile_fit.maximum_relative_adjustment,
        "transition_anchors": [item.as_dict() for item in profile_fit.transition_anchors],
        "residuals": [item.as_dict() for item in profile_fit.residuals],
        "rejected_source_vertex_indices": list(profile_fit.rejected_source_vertex_indices),
    }
    expected = (
        "design-profile-fit:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    if profile_fit.fit_id != expected:
        raise ProfileZoneError("design_profile_fit_identity_invalid")
    if len(profile_fit.profile.points) < 5:
        raise ProfileZoneError("profile_too_short_for_zone_partition")
    return profile_fit.profile.points


def _boundary(
    component_id: str,
    kind: str,
    start: float,
    end: float,
    confidence: float,
    evidence: tuple[str, ...],
) -> ProfileZoneBoundary:
    semantic_key = f"profile-zone:{kind}"
    return ProfileZoneBoundary(
        stable_feature_id(component_id, _FEATURE_KIND[kind], semantic_key),
        component_id,
        kind,
        semantic_key,
        start,
        end,
        confidence,
        evidence,
    )


def _make_zone_set(
    profile_fit: DesignModelProfileFit,
    boundaries: tuple[ProfileZoneBoundary, ...],
    status: ProfileZoneStatus,
    uncertainty: tuple[str, ...],
    *,
    previous_revision_id: str | None = None,
    actor_id: str | None = None,
    reason: str | None = None,
    created_at_utc: str | None = None,
) -> DesignProfileZones:
    payload = {
        "contract": ZONE_CONTRACT,
        "status": status.value,
        "fit_id": profile_fit.fit_id,
        "source_profile_id": profile_fit.source_profile_id,
        "scan_master_revision_id": profile_fit.scan_master_revision_id,
        "scan_master_geometry_sha256": profile_fit.scan_master_geometry_sha256,
        "parent_binding_revision_id": profile_fit.parent_binding.revision_id,
        "boundaries": [item.as_dict() for item in boundaries],
        "uncertainty_codes": list(uncertainty),
        "previous_revision_id": previous_revision_id,
        "actor_id": actor_id,
        "reason": reason,
        "created_at_utc": created_at_utc,
    }
    revision_id = (
        "design-profile-zones:"
        + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    return DesignProfileZones(
        revision_id,
        status,
        status is not ProfileZoneStatus.DETECTED,
        profile_fit.fit_id,
        profile_fit.source_profile_id,
        profile_fit.scan_master_revision_id,
        profile_fit.scan_master_geometry_sha256,
        profile_fit.parent_binding.revision_id,
        profile_fit.coordinate_unit,
        boundaries,
        uncertainty,
        previous_revision_id,
        actor_id,
        reason,
        created_at_utc,
    )


def _validate_partition(
    boundaries: tuple[ProfileZoneBoundary, ...], start: float, end: float
) -> None:
    if (
        any(
            not math.isfinite(item.start_axial)
            or not math.isfinite(item.end_axial)
            or not math.isfinite(item.confidence)
            or not 0.0 <= item.confidence <= 1.0
            or item.end_axial <= item.start_axial
            or not item.evidence_codes
            for item in boundaries
        )
        or boundaries[0].start_axial != start
        or boundaries[-1].end_axial != end
        or any(
            left.end_axial != right.start_axial for left, right in zip(boundaries, boundaries[1:])
        )
    ):
        raise ProfileZoneError("zone_partition_invalid")


def _validate_component_id(value: str) -> None:
    try:
        stable_feature_id(value, FeatureKind.BODY, "validation")
    except ValueError as error:
        raise ProfileZoneError("component_id_invalid") from error


def _text(value: str, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > 1000
    ):
        raise ProfileZoneError(f"{field}_invalid")
    return value


def _utc_timestamp(value: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ProfileZoneError("created_at_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ProfileZoneError("created_at_invalid") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ProfileZoneError("created_at_must_be_utc_z")
    return value


__all__ = [
    "DesignProfileZones",
    "ProfileZoneBoundary",
    "ProfileZoneError",
    "ProfileZoneStatus",
    "detect_design_profile_zones",
    "override_design_profile_zones",
]
