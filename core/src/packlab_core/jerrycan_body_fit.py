"""Evidence-bound stacked-section fitting for jerrycan Design Model bodies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .cross_section import (
    CrossSection,
    CrossSectionError,
    CrossSectionSymmetry,
    create_cross_section,
)
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
from .design_operations import DesignOperation, LoftSectionInput, create_loft_operation
from .design_preview import DesignPreview, tessellate_design_preview
from .fitting_strategy import FittingStrategyRecommendation
from .scan_master import ScanMasterRevision
from .symmetric_section_loft import (
    SectionLoftError,
    SectionLoftStatus,
    fit_symmetric_section_loft,
)


class JerrycanFrontDirection(StrEnum):
    POSITIVE_Y = "+y"
    NEGATIVE_Y = "-y"


@dataclass(frozen=True, slots=True)
class JerrycanBodyFit:
    """Parametric section graph plus a diagnostic preview, pinned to one Scan Master."""

    status: SectionLoftStatus
    review_required: bool
    model_revision_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    parent_binding_revision_id: str
    strategy_recommendation_id: str
    sections: tuple[CrossSection, ...]
    section_heights: tuple[float, ...]
    model: DesignModelRevision
    operation: DesignOperation
    preview: DesignPreview
    front_direction: JerrycanFrontDirection

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.jerrycan-body-fit.v1",
            "status": self.status.value,
            "review_required": self.review_required,
            "authority_class": "DESIGN_MODEL_OPERATION_WITH_PREVIEW_PROXY",
            "model_revision_id": self.model_revision_id,
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "parent_binding_revision_id": self.parent_binding_revision_id,
            },
            "strategy_recommendation_id": self.strategy_recommendation_id,
            "sections": [section.as_dict() for section in self.sections],
            "section_heights": list(self.section_heights),
            "section_frame": {
                "vertical_axis": "+z",
                "side_axis": "x (left/right)",
                "front_back_axis": "y",
                "front_direction": self.front_direction.value,
            },
            "operation": self.operation.as_dict(),
            "preview": self.preview.as_dict(),
            "coordinate_unit": self.model.coordinate_unit,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "scan_master_replaced": False,
            "preview_is_parametric_truth": False,
            "handles_or_voids_modeled": False,
            "cad_or_brep_generated": False,
        }


def fit_jerrycan_body(
    scan_master: ScanMasterRevision,
    strategy: FittingStrategyRecommendation,
    *,
    expected_scan_master_revision_id: str,
    expected_strategy_recommendation_id: str,
    section_heights: tuple[float, ...],
    component_id: str,
    symmetry: CrossSectionSymmetry,
    front_direction: JerrycanFrontDirection,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    chord_tolerance: float = 0.25,
    maximum_preview_angular_segments: int = 256,
) -> JerrycanBodyFit:
    """Fit ordered Z sections without altering observed contours or captured authority."""
    if not isinstance(symmetry, CrossSectionSymmetry):
        raise SectionLoftError("jerrycan_symmetry_constraint_invalid")
    if not isinstance(front_direction, JerrycanFrontDirection):
        raise SectionLoftError("jerrycan_front_direction_required")

    # The M11 kernel validates the selected Scan Master, strategy identity/binding,
    # ordered section support, bounded work and the full-bilateral case.
    bilateral = symmetry is CrossSectionSymmetry.BOTH
    base = fit_symmetric_section_loft(
        scan_master,
        strategy,
        expected_scan_master_revision_id=expected_scan_master_revision_id,
        expected_strategy_recommendation_id=expected_strategy_recommendation_id,
        section_heights=section_heights,
        component_id=component_id,
        symmetry_constraints_enabled=bilateral,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
        package_family=PackageFamily.JERRYCAN,
        chord_tolerance=chord_tolerance,
        maximum_preview_angular_segments=maximum_preview_angular_segments,
    )

    if len(base.sections) != len(section_heights):
        raise SectionLoftError("jerrycan_section_capture_incomplete")
    sections: list[CrossSection] = []
    for section in base.sections:
        try:
            sections.append(
                section
                if section.symmetry is symmetry
                else create_cross_section(
                    component_id,
                    section.points,
                    symmetry=symmetry,
                    center_x=section.center_x,
                    center_y=section.center_y,
                    scale_state=section.scale_state,
                )
            )
        except CrossSectionError as error:
            # A requested plane constraint must be supported by the observed points;
            # this fitter never reflects, averages, or otherwise invents scan geometry.
            raise SectionLoftError(
                "jerrycan_section_constraint_not_supported_by_evidence"
            ) from error

    binding = strategy.parent_binding
    features = tuple(
        DesignModelFeatureReference(
            stable_feature_id(component_id, FeatureKind.BODY, f"jerrycan-body-section:{index:04d}"),
            component_id,
            FeatureKind.BODY,
            f"jerrycan-body-section:{index:04d}",
        )
        for index in range(len(sections))
    )
    raw_base_parameters = base.model.as_dict()["parameters"]
    if not isinstance(raw_base_parameters, list) or any(
        not isinstance(parameter, dict) for parameter in raw_base_parameters
    ):
        raise SectionLoftError("jerrycan_strategy_parameters_invalid")
    base_parameters = {
        str(parameter["parameter_id"]): parameter["value"] for parameter in raw_base_parameters
    }
    base_policy = base_parameters["stacked_section_policy"]
    if not isinstance(base_policy, dict):
        raise SectionLoftError("jerrycan_strategy_policy_invalid")
    parameters = tuple(
        parameter
        for parameter in base.model.parameters
        if parameter.parameter_id
        not in {"stacked_section_policy", "stacked_section_symmetry_evidence"}
    ) + (
        DesignModelParameter(
            "stacked_section_policy",
            {
                **base_policy,
                "symmetry_constraint": symmetry.value,
            },
            ParameterType.OBJECT,
        ),
        DesignModelParameter(
            "stacked_section_symmetry_evidence",
            [
                {
                    **evidence.as_dict(),
                    "symmetry_constraint": symmetry.value,
                    "symmetry_constraint_enabled": symmetry is not CrossSectionSymmetry.NONE,
                    "disposition": (
                        "OBSERVED_POINTS_PRESERVED_CONSTRAINT_SUPPORTED"
                        if symmetry is not CrossSectionSymmetry.NONE
                        else evidence.disposition
                    ),
                }
                for evidence in base.symmetry_evidence
            ],
            ParameterType.ARRAY,
        ),
        DesignModelParameter(
            "jerrycan_section_frame",
            {
                "vertical_axis": "+z",
                "side_axis": "x (left/right)",
                "front_back_axis": "y",
                "front_direction": front_direction.value,
                "symmetry_constraint": symmetry.value,
            },
            ParameterType.OBJECT,
        ),
    )
    model = create_design_model_revision(
        binding,
        package_family=PackageFamily.JERRYCAN,
        parameters=parameters,
        features=features,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    loft_inputs = tuple(
        LoftSectionInput(feature.feature_id, section, height)
        for feature, section, height in zip(features, sections, section_heights, strict=True)
    )
    operation = create_loft_operation(model, loft_inputs)
    previews = tessellate_design_preview(
        model,
        cross_sections=tuple(sections),
        operations=(operation,),
        chord_tolerance=chord_tolerance,
        maximum_angular_segments=maximum_preview_angular_segments,
    )
    if len(previews) != 1:
        raise SectionLoftError("jerrycan_preview_result_invalid")
    return JerrycanBodyFit(
        base.status,
        base.review_required,
        model.revision_id,
        scan_master.revision_id,
        base.scan_master_geometry_sha256,
        binding.revision_id,
        strategy.recommendation_id,
        tuple(sections),
        section_heights,
        model,
        operation,
        previews[0],
        front_direction,
    )


__all__ = ["JerrycanBodyFit", "JerrycanFrontDirection", "fit_jerrycan_body"]
