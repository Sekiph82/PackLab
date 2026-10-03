"""Revisioned front/back and left/right constraints for fitted Design Model sections."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass

from .cross_section import (
    CrossSection,
    CrossSectionError,
    CrossSectionSymmetry,
    SectionPoint,
    edit_control_point,
    set_symmetry,
)
from .design_history import DesignEditCommand, EditTargetKind, create_edit_command
from .design_model import (
    DesignModelError,
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    ParameterType,
    resolve_design_model_feature,
    revise_design_model_revision,
    stable_feature_id,
)
from .symmetric_section_loft import SectionSymmetryEvidence, SymmetricSectionLoft

_PARAMETER_PREFIX = "section_symmetry_"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_TOLERANCE = 1.0


class DesignSymmetryError(ValueError):
    """Raised for stale bindings, invalid section edits, or impossible constraints."""


@dataclass(frozen=True, slots=True)
class DesignSectionSymmetryRevision:
    model: DesignModelRevision
    section: CrossSection
    parameter: DesignModelParameter
    evidence_disagreement: bool
    disagreement_axes: tuple[str, ...]
    history_command: DesignEditCommand

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.design-section-symmetry-revision.v1",
            "model_revision_id": self.model.revision_id,
            "previous_model_revision_id": self.model.previous_revision_id,
            "section": self.section.as_dict(),
            "parameter": self.parameter.as_dict(),
            "evidence_disagreement": self.evidence_disagreement,
            "disagreement_axes": list(self.disagreement_axes),
            "history_command_id": self.history_command.command_id,
            "authority_class": "DESIGN_MODEL_PARAMETRIC_REVISION",
            "physical_accuracy_validation_status": self.model.physical_accuracy_validation_status,
            "mold_use_authorized": self.model.mold_use_authorized,
            "scan_master_changed": False,
            "preview_or_manufacturing_authority_created": False,
        }


def revise_section_symmetry(
    model: DesignModelRevision,
    loft: SymmetricSectionLoft,
    *,
    section: CrossSection,
    section_index: int,
    expected_model_revision_id: str,
    expected_scan_master_revision_id: str,
    expected_scan_master_geometry_sha256: str,
    target_symmetry: CrossSectionSymmetry,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    edited_point_index: int | None = None,
    edited_point: SectionPoint | None = None,
    evidence_disagreement_tolerance: float = 0.08,
) -> DesignSectionSymmetryRevision:
    """Toggle a fitted section constraint and persist the edit as one model revision.

    A control-point edit, when supplied, occurs after applying the requested
    constraint so the existing cross-section orbit propagation remains the
    sole authority for mirrored parameter values.
    """
    if not isinstance(model, DesignModelRevision) or not isinstance(loft, SymmetricSectionLoft):
        raise DesignSymmetryError("design_model_and_section_loft_required")
    if model.revision_id != expected_model_revision_id:
        raise DesignSymmetryError("design_model_revision_stale")
    if (
        model.parent_binding_revision_id != loft.parent_binding_revision_id
        or model.fitted_to_scan_master_revision_id != expected_scan_master_revision_id
        or model.scan_master_geometry_sha256 != expected_scan_master_geometry_sha256
        or loft.scan_master_revision_id != expected_scan_master_revision_id
        or loft.scan_master_geometry_sha256 != expected_scan_master_geometry_sha256
        or not isinstance(expected_scan_master_geometry_sha256, str)
        or not _SHA256.fullmatch(expected_scan_master_geometry_sha256)
    ):
        raise DesignSymmetryError("scan_master_parent_binding_mismatch")
    if (
        isinstance(section_index, bool)
        or not isinstance(section_index, int)
        or not 0 <= section_index < len(loft.sections)
        or len(loft.sections) != len(loft.symmetry_evidence)
        or len(loft.sections) != len(loft.section_heights)
    ):
        raise DesignSymmetryError("section_index_invalid")
    if not isinstance(target_symmetry, CrossSectionSymmetry):
        raise DesignSymmetryError("section_symmetry_invalid")
    if (
        isinstance(evidence_disagreement_tolerance, bool)
        or not isinstance(evidence_disagreement_tolerance, (int, float))
        or not math.isfinite(evidence_disagreement_tolerance)
        or not 0.0 <= evidence_disagreement_tolerance <= _MAX_TOLERANCE
    ):
        raise DesignSymmetryError("evidence_disagreement_tolerance_invalid")
    if not isinstance(edited_point_index, (int, type(None))) or isinstance(
        edited_point_index, bool
    ):
        raise DesignSymmetryError("edited_point_index_invalid")
    if (edited_point_index is None) != (edited_point is None):
        raise DesignSymmetryError("edited_point_pair_required")

    original = loft.sections[section_index]
    if not isinstance(section, CrossSection):
        raise DesignSymmetryError("section_required")
    semantic_key = f"loft-section:{section_index:04d}"
    feature_id = stable_feature_id(original.component_id, FeatureKind.BODY, semantic_key)
    try:
        feature = resolve_design_model_feature(model, feature_id)
    except DesignModelError as error:
        raise DesignSymmetryError("section_feature_stale_or_missing") from error
    source_feature = next(
        (item for item in loft.model.features if item.feature_id == feature_id), None
    )
    if not isinstance(feature, DesignModelFeatureReference) or feature != source_feature:
        raise DesignSymmetryError("section_feature_binding_mismatch")
    if (
        section.component_id != original.component_id
        or section.scale_state is not model.scale_state
        or section.coordinate_unit != model.coordinate_unit
        or section.center_x != loft.symmetry_evidence[section_index].center_x
        or section.center_y != loft.symmetry_evidence[section_index].center_y
    ):
        raise DesignSymmetryError("section_axes_or_scale_binding_mismatch")

    parameter_id = _parameter_id(feature_id)
    existing = tuple(item for item in model.parameters if item.parameter_id == parameter_id)
    if len(existing) > 1:
        raise DesignSymmetryError("section_symmetry_parameter_ambiguous")
    before = existing[0] if existing else None
    if before is None:
        if model.revision_id != loft.model.revision_id or original.previous_section_id is not None:
            raise DesignSymmetryError("section_symmetry_parameter_missing_for_revision")
        if section != original:
            raise DesignSymmetryError("section_symmetry_parameter_missing_for_revision")
        source_section = section
    else:
        value = before.as_dict()["value"]
        if not isinstance(value, dict):
            raise DesignSymmetryError("section_symmetry_parameter_invalid")
        if (
            value.get("section_id") != section.section_id
            or value.get("section") != section.as_dict()
        ):
            raise DesignSymmetryError("section_symmetry_parameter_stale")
        source_section = section

    try:
        updated_section = set_symmetry(source_section, target_symmetry)
        if edited_point_index is not None and edited_point is not None:
            updated_section = edit_control_point(updated_section, edited_point_index, edited_point)
    except CrossSectionError as error:
        raise DesignSymmetryError(f"section_constraint_rejected:{error}") from error

    evidence = loft.symmetry_evidence[section_index]
    if not isinstance(evidence, SectionSymmetryEvidence):
        raise DesignSymmetryError("section_symmetry_evidence_invalid")
    axes = _constrained_axes(target_symmetry)
    errors = {
        "left_right": evidence.left_right_reflection_error_ratio,
        "front_back": evidence.front_back_reflection_error_ratio,
    }
    for name in ("left_right", "front_back"):
        value = errors[name]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise DesignSymmetryError("section_symmetry_evidence_invalid")
    disagreement_axes = tuple(
        name for name in axes if errors[name] > evidence_disagreement_tolerance
    )
    payload = {
        "contract": "packlab.design-section-symmetry-parameter.v1",
        "feature_id": feature_id,
        "section_id": updated_section.section_id,
        "section": updated_section.as_dict(),
        "section_height": loft.section_heights[section_index],
        "scan_evidence": {
            "scan_master_revision_id": loft.scan_master_revision_id,
            "scan_master_geometry_sha256": loft.scan_master_geometry_sha256,
            "left_right_reflection_error_ratio": evidence.left_right_reflection_error_ratio,
            "front_back_reflection_error_ratio": evidence.front_back_reflection_error_ratio,
            "disagreement_tolerance": evidence_disagreement_tolerance,
            "disagreement_axes": list(disagreement_axes),
            "disposition": evidence.disposition,
        },
        "constraint_intent": target_symmetry.value,
        "authority_class": "DESIGN_MODEL_PARAMETRIC_CONSTRAINT",
        "physical_accuracy_validation_status": model.physical_accuracy_validation_status,
        "mold_use_authorized": False,
    }
    after = DesignModelParameter(parameter_id, payload, ParameterType.OBJECT)
    command = create_edit_command(
        model.revision_id,
        EditTargetKind.PARAMETER,
        parameter_id,
        before,
        after,
    )
    parameters = tuple(item for item in model.parameters if item.parameter_id != parameter_id)
    parameters = (*parameters, after)
    try:
        revised = revise_design_model_revision(
            model,
            parameters=parameters,
            features=model.features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise DesignSymmetryError("section_symmetry_revision_invalid") from error
    return DesignSectionSymmetryRevision(
        revised,
        updated_section,
        after,
        bool(disagreement_axes),
        disagreement_axes,
        command,
    )


def _parameter_id(feature_id: str) -> str:
    return _PARAMETER_PREFIX + hashlib.sha256(feature_id.encode("utf-8")).hexdigest()


def _constrained_axes(symmetry: CrossSectionSymmetry) -> tuple[str, ...]:
    if symmetry is CrossSectionSymmetry.LEFT_RIGHT:
        return ("left_right",)
    if symmetry is CrossSectionSymmetry.FRONT_BACK:
        return ("front_back",)
    if symmetry is CrossSectionSymmetry.BOTH:
        return ("left_right", "front_back")
    return ()


__all__ = [
    "DesignSectionSymmetryRevision",
    "DesignSymmetryError",
    "revise_section_symmetry",
]
