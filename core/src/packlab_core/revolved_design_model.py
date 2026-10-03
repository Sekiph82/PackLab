"""Evidence-bound Design Model revolve graphs and disposable preview proxies."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_design_model_revision,
    stable_feature_id,
)
from .design_model_binding import DesignModelParentBindingRevision
from .design_operations import DesignOperation, create_revolve_operation
from .design_preview import DesignPreview, tessellate_design_preview
from .design_profile import DesignProfile
from .design_profile_fit import FIT_CONTRACT, DesignModelProfileFit, ProfileFitStatus
from .design_profile_zones import (
    ZONE_CONTRACT,
    DesignProfileZones,
    ProfileZoneStatus,
)
from .fitting_strategy import (
    STRATEGY_CONTRACT,
    FittingStrategy,
    FittingStrategyRecommendation,
    PrincipalAxis,
)


class RevolvedDesignModelError(ValueError):
    """Raised when accepted strategy, fit, or feature-zone evidence does not agree."""


@dataclass(frozen=True, slots=True)
class RevolvedDesignModel:
    model: DesignModelRevision
    profile: DesignProfile
    operation: DesignOperation
    preview: DesignPreview
    strategy_recommendation_id: str
    profile_fit_id: str
    feature_zone_revision_id: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.axisymmetric-revolved-design-model.v1",
            "authority_class": "DESIGN_MODEL_WITH_PREVIEW_PROXY",
            "model": self.model.as_dict(),
            "profile": self.profile.as_dict(),
            "operation": self.operation.as_dict(),
            "preview": self.preview.as_dict(),
            "fitting_evidence": {
                "strategy_recommendation_id": self.strategy_recommendation_id,
                "profile_fit_id": self.profile_fit_id,
                "feature_zone_revision_id": self.feature_zone_revision_id,
            },
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "cad_or_brep_generated": False,
            "scan_master_replaced": False,
        }


def build_axisymmetric_revolved_design_model(
    strategy: FittingStrategyRecommendation,
    profile_fit: DesignModelProfileFit,
    feature_zones: DesignProfileZones,
    *,
    expected_strategy_recommendation_id: str,
    expected_profile_fit_id: str,
    expected_feature_zone_revision_id: str,
    component_id: str,
    package_family: PackageFamily,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    chord_tolerance: float = 0.25,
    profile_samples: int = 64,
    maximum_angular_segments: int = 256,
) -> RevolvedDesignModel:
    """Create parametric revolve truth and tessellate only through Design Preview."""
    _validate_strategy(strategy, expected_strategy_recommendation_id)
    _validate_profile_fit(profile_fit, expected_profile_fit_id)
    _validate_feature_zones(
        feature_zones,
        profile_fit,
        expected_feature_zone_revision_id,
    )
    if strategy.principal_axis is not PrincipalAxis.Z:
        raise RevolvedDesignModelError("revolve_profile_axis_must_match_z_strategy")
    if (
        strategy.coordinate_unit != profile_fit.coordinate_unit
        or strategy.parent_binding.scale_state is not profile_fit.parent_binding.scale_state
        or strategy.scan_master_revision_id != profile_fit.scan_master_revision_id
        or strategy.scan_master_geometry_sha256 != profile_fit.scan_master_geometry_sha256
        or strategy.parent_binding.fitted_to_scan_master_revision_id
        != profile_fit.scan_master_revision_id
        or strategy.parent_binding.scan_master_geometry_sha256
        != profile_fit.scan_master_geometry_sha256
        or feature_zones.parent_binding_revision_id != profile_fit.parent_binding.revision_id
    ):
        raise RevolvedDesignModelError("revolve_evidence_parent_mismatch")
    if not isinstance(package_family, PackageFamily):
        raise RevolvedDesignModelError("package_family_invalid")
    _identifier(component_id, "component_id")

    profile = profile_fit.profile
    if profile is None:
        raise RevolvedDesignModelError("fitted_design_profile_required")
    if any(boundary.component_id != component_id for boundary in feature_zones.boundaries):
        raise RevolvedDesignModelError("profile_zone_component_mismatch")
    profile_feature = _feature(component_id, FeatureKind.BODY, "fitted-profile")
    axis_feature = _feature(component_id, FeatureKind.BODY, "principal-axis-z")
    zone_features = tuple(
        DesignModelFeatureReference(
            boundary.feature_id,
            boundary.component_id,
            _zone_feature_kind(boundary.zone_kind),
            boundary.semantic_key,
        )
        for boundary in feature_zones.boundaries
    )
    features = (profile_feature, axis_feature, *zone_features)
    parameters = (
        DesignModelParameter(
            "axisymmetric_strategy_evidence",
            {
                "recommendation_id": strategy.recommendation_id,
                "strategy": strategy.strategy.value,
                "principal_axis": strategy.principal_axis.value,
                "parent_binding_revision_id": strategy.parent_binding.revision_id,
                "uncertainty_codes": list(strategy.uncertainty_codes),
            },
            ParameterType.OBJECT,
        ),
        DesignModelParameter(
            "fitted_profile_evidence",
            {
                "fit_id": profile_fit.fit_id,
                "source_profile_id": profile_fit.source_profile_id,
                "profile_id": profile.profile_id,
                "regularization": {
                    "smoothing_strength": profile_fit.smoothing_strength,
                    "window_radius": profile_fit.window_radius,
                    "maximum_relative_adjustment": profile_fit.maximum_relative_adjustment,
                },
            },
            ParameterType.OBJECT,
        ),
        DesignModelParameter(
            "feature_zone_metadata",
            {
                "contract": ZONE_CONTRACT,
                "revision_id": feature_zones.revision_id,
                "boundaries": [item.as_dict() for item in feature_zones.boundaries],
            },
            ParameterType.OBJECT,
        ),
    )
    model = create_design_model_revision(
        profile_fit.parent_binding,
        package_family=package_family,
        parameters=parameters,
        features=features,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    operation = create_revolve_operation(
        model,
        profile,
        profile_feature_id=profile_feature.feature_id,
        axis_feature_id=axis_feature.feature_id,
        axis_origin=(0.0, 0.0, 0.0),
        axis_direction=(0.0, 0.0, 1.0),
        angle_degrees=360.0,
    )
    previews = tessellate_design_preview(
        model,
        profiles=(profile,),
        operations=(operation,),
        chord_tolerance=chord_tolerance,
        profile_samples=profile_samples,
        maximum_angular_segments=maximum_angular_segments,
    )
    if len(previews) != 1:
        raise RevolvedDesignModelError("revolve_preview_result_invalid")
    return RevolvedDesignModel(
        model,
        profile,
        operation,
        previews[0],
        strategy.recommendation_id,
        profile_fit.fit_id,
        feature_zones.revision_id,
    )


def _validate_strategy(strategy: FittingStrategyRecommendation, expected_id: str) -> None:
    if not isinstance(strategy, FittingStrategyRecommendation):
        raise RevolvedDesignModelError("fitting_strategy_recommendation_required")
    if strategy.recommendation_id != expected_id:
        raise RevolvedDesignModelError("fitting_strategy_recommendation_stale")
    if (
        not isinstance(strategy.parent_binding, DesignModelParentBindingRevision)
        or not isinstance(strategy.strategy, FittingStrategy)
        or not isinstance(strategy.principal_axis, PrincipalAxis)
        or strategy.strategy is not FittingStrategy.AXISYMMETRIC_REVOLVE
        or strategy.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or strategy.mold_use_authorized is not False
        or strategy.parent_binding.fitted_to_scan_master_revision_id
        != strategy.scan_master_revision_id
        or strategy.parent_binding.scan_master_geometry_sha256
        != strategy.scan_master_geometry_sha256
    ):
        raise RevolvedDesignModelError("fitting_strategy_not_accepted_for_revolve")
    axis_index = {PrincipalAxis.X: 0, PrincipalAxis.Y: 1, PrincipalAxis.Z: 2}[
        strategy.principal_axis
    ]
    body = {
        "contract": STRATEGY_CONTRACT,
        "strategy": strategy.strategy.value,
        "axis": axis_index,
        "elongation": strategy.axis_elongation_ratio,
        "sections": [item.as_dict() for item in strategy.section_evidence],
        "scan_master_revision_id": strategy.scan_master_revision_id,
        "scan_master_geometry_sha256": strategy.scan_master_geometry_sha256,
        "parent_binding": strategy.parent_binding.as_dict(),
        "geometry_statistics": strategy.geometry_statistics.as_dict(),
        "m09_vertical_profile_ids": list(strategy.m09_vertical_profile_ids),
        "m09_cross_section_measurement_ids": list(strategy.m09_cross_section_measurement_ids),
        "uncertainty_codes": list(strategy.uncertainty_codes),
        "policy": strategy.policy.as_dict(),
    }
    expected = (
        "fitting-strategy:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    if expected != strategy.recommendation_id:
        raise RevolvedDesignModelError("fitting_strategy_identity_invalid")


def _validate_profile_fit(profile_fit: DesignModelProfileFit, expected_id: str) -> None:
    if not isinstance(profile_fit, DesignModelProfileFit):
        raise RevolvedDesignModelError("design_profile_fit_required")
    if profile_fit.fit_id != expected_id:
        raise RevolvedDesignModelError("design_profile_fit_stale")
    if profile_fit.status is not ProfileFitStatus.FITTED or profile_fit.profile is None:
        raise RevolvedDesignModelError("design_profile_fit_not_accepted")
    if not isinstance(profile_fit.parent_binding, DesignModelParentBindingRevision):
        raise RevolvedDesignModelError("design_profile_fit_parent_or_authority_invalid")
    profile = profile_fit.profile
    body = {
        "contract": FIT_CONTRACT,
        "source_profile_id": profile_fit.source_profile_id,
        "scan_master_revision_id": profile_fit.scan_master_revision_id,
        "scan_master_geometry_sha256": profile_fit.scan_master_geometry_sha256,
        "profile": profile.as_dict(),
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
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    if expected != profile_fit.fit_id:
        raise RevolvedDesignModelError("design_profile_fit_identity_invalid")
    if (
        profile_fit.parent_binding.fitted_to_scan_master_revision_id
        != profile_fit.scan_master_revision_id
        or profile_fit.parent_binding.scan_master_geometry_sha256
        != profile_fit.scan_master_geometry_sha256
        or profile.scale_state is not profile_fit.parent_binding.scale_state
        or profile.coordinate_unit != profile_fit.coordinate_unit
        or profile_fit.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or profile_fit.mold_use_authorized is not False
    ):
        raise RevolvedDesignModelError("design_profile_fit_parent_or_authority_invalid")


def _validate_feature_zones(
    zones: DesignProfileZones,
    profile_fit: DesignModelProfileFit,
    expected_id: str,
) -> None:
    if not isinstance(zones, DesignProfileZones):
        raise RevolvedDesignModelError("design_profile_zones_required")
    if zones.revision_id != expected_id or zones.fit_id != profile_fit.fit_id:
        raise RevolvedDesignModelError("design_profile_zones_stale")
    profile = profile_fit.profile
    if profile is None:
        raise RevolvedDesignModelError("design_profile_fit_not_accepted")
    if (
        not isinstance(zones.status, ProfileZoneStatus)
        or zones.status is not ProfileZoneStatus.DETECTED
        or zones.review_required
        or zones.source_profile_id != profile_fit.source_profile_id
        or zones.parent_binding_revision_id != profile_fit.parent_binding.revision_id
        or zones.scan_master_revision_id != profile_fit.scan_master_revision_id
        or zones.scan_master_geometry_sha256 != profile_fit.scan_master_geometry_sha256
        or zones.coordinate_unit != profile_fit.coordinate_unit
    ):
        raise RevolvedDesignModelError("design_profile_zones_not_accepted_or_parent_mismatch")
    payload = {
        "contract": ZONE_CONTRACT,
        "status": zones.status.value,
        "fit_id": zones.fit_id,
        "source_profile_id": zones.source_profile_id,
        "scan_master_revision_id": zones.scan_master_revision_id,
        "scan_master_geometry_sha256": zones.scan_master_geometry_sha256,
        "parent_binding_revision_id": zones.parent_binding_revision_id,
        "boundaries": [item.as_dict() for item in zones.boundaries],
        "uncertainty_codes": list(zones.uncertainty_codes),
        "previous_revision_id": zones.previous_revision_id,
        "actor_id": zones.actor_id,
        "reason": zones.reason,
        "created_at_utc": zones.created_at_utc,
    }
    expected = (
        "design-profile-zones:"
        + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    if expected != zones.revision_id:
        raise RevolvedDesignModelError("design_profile_zones_identity_invalid")
    boundaries = zones.boundaries
    expected_kinds = ("base", "body", "shoulder", "neck")
    if (
        len(boundaries) != len(expected_kinds)
        or tuple(item.zone_kind for item in boundaries) != expected_kinds
        or boundaries[0].start_axial != profile.domain[0]
        or boundaries[-1].end_axial != profile.domain[1]
        or any(
            left.end_axial != right.start_axial for left, right in zip(boundaries, boundaries[1:])
        )
    ):
        raise RevolvedDesignModelError("design_profile_zones_partition_invalid")
    for boundary in boundaries:
        kind = _zone_feature_kind(boundary.zone_kind)
        semantic_key = f"profile-zone:{boundary.zone_kind}"
        if boundary.semantic_key != semantic_key or boundary.feature_id != stable_feature_id(
            boundary.component_id, kind, semantic_key
        ):
            raise RevolvedDesignModelError("design_profile_zone_feature_identity_invalid")


def _feature(
    component_id: str, kind: FeatureKind, semantic_key: str
) -> DesignModelFeatureReference:
    return DesignModelFeatureReference(
        stable_feature_id(component_id, kind, semantic_key), component_id, kind, semantic_key
    )


def _zone_feature_kind(value: str) -> FeatureKind:
    try:
        return {
            "base": FeatureKind.BASE,
            "body": FeatureKind.BODY,
            "shoulder": FeatureKind.SHOULDER,
            "neck": FeatureKind.NECK,
        }[value]
    except KeyError as error:
        raise RevolvedDesignModelError("profile_zone_feature_kind_invalid") from error


def _identifier(value: str, field: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or not value[0].isalpha()
        or not all(character.isalnum() or character in "_.:-" for character in value)
    ):
        raise RevolvedDesignModelError(f"{field}_invalid")


__all__ = [
    "RevolvedDesignModel",
    "RevolvedDesignModelError",
    "build_axisymmetric_revolved_design_model",
]
