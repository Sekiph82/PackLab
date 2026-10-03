"""Revisioned direct profile and cross-section point edits with derived previews."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum

from .cross_section import (
    CrossSection,
    CrossSectionError,
    SectionPoint,
    edit_control_point,
)
from .design_history import (
    DesignEditCommand,
    DesignHistoryError,
    EditTargetKind,
    create_edit_command,
)
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
from .design_operations import (
    DesignOperation,
    DesignOperationError,
    LoftSectionInput,
    OperationKind,
    create_loft_operation,
    create_revolve_operation,
)
from .design_preview import DesignPreview, DesignPreviewError, tessellate_design_preview
from .design_profile import (
    DesignProfile,
    DesignProfileError,
    ProfilePoint,
    create_design_profile,
)
from .symmetric_section_loft import (
    SymmetricSectionLoft,
)

_PROFILE_PARAMETER_PREFIX = "profile_control_points_"
_SECTION_PARAMETER_PREFIX = "section_symmetry_"


class ControlPointEditError(ValueError):
    """Raised when a direct control-point edit is stale or geometrically invalid."""


class ControlPointAction(StrEnum):
    MOVE = "move"
    ADD = "add"
    REMOVE = "remove"


@dataclass(frozen=True, slots=True)
class ProfileControlPointRevision:
    model: DesignModelRevision
    profile: DesignProfile
    operation: DesignOperation
    preview: DesignPreview
    changed_indices: tuple[int, ...]
    history_command: DesignEditCommand


@dataclass(frozen=True, slots=True)
class SectionControlPointRevision:
    model: DesignModelRevision
    sections: tuple[CrossSection, ...]
    operation: DesignOperation
    preview: DesignPreview
    section_index: int
    changed_indices: tuple[int, ...]
    history_command: DesignEditCommand


def edit_design_profile_control_point(
    model: DesignModelRevision,
    profile: DesignProfile,
    operation: DesignOperation,
    *,
    expected_model_revision_id: str,
    expected_scan_master_revision_id: str,
    expected_scan_master_geometry_sha256: str,
    profile_feature_id: str,
    action: ControlPointAction,
    point_index: int,
    point: ProfilePoint | None,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    chord_tolerance: float = 0.25,
    profile_samples: int = 64,
    maximum_angular_segments: int = 128,
) -> ProfileControlPointRevision:
    """Move, add or remove one profile point, then rebuild its proxy preview."""
    _validate_model_revision(model, expected_model_revision_id)
    if not isinstance(profile, DesignProfile):
        raise ControlPointEditError("design_profile_required")
    if not isinstance(operation, DesignOperation) or operation.kind is not OperationKind.REVOLVE:
        raise ControlPointEditError("current_revolve_operation_required")
    if (
        operation.model_revision_id != model.revision_id
        or operation.input_ids != (profile.profile_id,)
        or model.fitted_to_scan_master_revision_id != expected_scan_master_revision_id
        or model.scan_master_geometry_sha256 != expected_scan_master_geometry_sha256
        or operation.scale_state is not model.scale_state
        or operation.coordinate_unit != model.coordinate_unit
    ):
        raise ControlPointEditError("profile_operation_or_scan_parent_stale")
    if (
        profile.scale_state is not model.scale_state
        or profile.coordinate_unit != model.coordinate_unit
    ):
        raise ControlPointEditError("profile_unit_binding_mismatch")
    if not isinstance(action, ControlPointAction):
        raise ControlPointEditError("control_point_action_invalid")
    _validate_index(point_index, len(profile.points), action)
    try:
        feature = resolve_design_model_feature(model, profile_feature_id)
    except DesignModelError as error:
        raise ControlPointEditError("profile_feature_stale_or_missing") from error
    if feature.feature_kind is not FeatureKind.BODY or feature.semantic_key != "fitted-profile":
        raise ControlPointEditError("profile_feature_reference_mismatch")
    if (
        len(operation.parent_feature_ids) != 2
        or profile_feature_id not in operation.parent_feature_ids
    ):
        raise ControlPointEditError("profile_operation_feature_binding_invalid")

    parameter_id = _profile_parameter_id(profile_feature_id)
    matches = tuple(item for item in model.parameters if item.parameter_id == parameter_id)
    if len(matches) > 1:
        raise ControlPointEditError("profile_parameter_ambiguous")
    before = matches[0] if matches else None
    if before is None:
        if _profile_evidence_id(model) != profile.profile_id:
            raise ControlPointEditError("profile_control_point_source_stale")
    else:
        _validate_profile_parameter(before, profile, profile_feature_id, model)

    try:
        changed = _edit_profile_points(profile, action, point_index, point)
        updated_profile = create_design_profile(changed, model.scale_state)
        after = DesignModelParameter(
            parameter_id,
            {
                "contract": "packlab.design-profile-control-points.v1",
                "feature_id": profile_feature_id,
                "profile_id": updated_profile.profile_id,
                "profile": updated_profile.as_dict(),
                "scan_master_revision_id": model.fitted_to_scan_master_revision_id,
                "scan_master_geometry_sha256": model.scan_master_geometry_sha256,
                "authority_class": "DESIGN_MODEL_PARAMETRIC_PROFILE",
                "physical_accuracy_validation_status": model.physical_accuracy_validation_status,
                "mold_use_authorized": False,
            },
            ParameterType.OBJECT,
        )
        try:
            command = create_edit_command(
                model.revision_id,
                EditTargetKind.PARAMETER,
                parameter_id,
                before,
                after,
            )
        except DesignHistoryError as error:
            raise ControlPointEditError(
                f"profile_control_point_history_rejected:{error}"
            ) from error
        revised = _revise_model(model, parameter_id, after, actor_id, reason, created_at_utc)
        axis_feature_id = next(
            item for item in operation.parent_feature_ids if item != profile_feature_id
        )
        if operation.axis_origin is None or operation.axis_direction is None:
            raise ControlPointEditError("revolve_operation_axis_missing")
        updated_operation = create_revolve_operation(
            revised,
            updated_profile,
            profile_feature_id=profile_feature_id,
            axis_feature_id=axis_feature_id,
            axis_origin=operation.axis_origin,
            axis_direction=operation.axis_direction,
            angle_degrees=operation.angle_degrees or 360.0,
        )
        previews = tessellate_design_preview(
            revised,
            profiles=(updated_profile,),
            operations=(updated_operation,),
            chord_tolerance=chord_tolerance,
            profile_samples=profile_samples,
            maximum_angular_segments=maximum_angular_segments,
        )
    except (
        DesignProfileError,
        DesignModelError,
        DesignOperationError,
        DesignPreviewError,
    ) as error:
        raise ControlPointEditError(f"profile_control_point_edit_rejected:{error}") from error
    if len(previews) != 1:
        raise ControlPointEditError("profile_preview_result_invalid")
    return ProfileControlPointRevision(
        revised,
        updated_profile,
        updated_operation,
        previews[0],
        _changed_indices(action, point_index, len(profile.points)),
        command,
    )


def edit_design_section_control_point(
    model: DesignModelRevision,
    loft: SymmetricSectionLoft,
    sections: tuple[CrossSection, ...],
    *,
    expected_model_revision_id: str,
    expected_scan_master_revision_id: str,
    expected_scan_master_geometry_sha256: str,
    section_index: int,
    action: ControlPointAction,
    point_index: int,
    point: SectionPoint | None,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    chord_tolerance: float = 0.25,
    maximum_angular_segments: int = 128,
) -> SectionControlPointRevision:
    """Move a section point through its symmetry constraint and rebuild the loft proxy."""
    _validate_model_revision(model, expected_model_revision_id)
    if not isinstance(loft, SymmetricSectionLoft):
        raise ControlPointEditError("symmetric_section_loft_required")
    if (
        not isinstance(sections, tuple)
        or any(not isinstance(item, CrossSection) for item in sections)
        or loft.operation.kind is not OperationKind.LOFT
    ):
        raise ControlPointEditError("section_preview_inputs_invalid")
    if (
        model.parent_binding_revision_id != loft.parent_binding_revision_id
        or model.fitted_to_scan_master_revision_id != expected_scan_master_revision_id
        or model.scan_master_geometry_sha256 != expected_scan_master_geometry_sha256
        or loft.scan_master_revision_id != expected_scan_master_revision_id
        or loft.scan_master_geometry_sha256 != expected_scan_master_geometry_sha256
        or len(sections) != len(loft.sections)
        or len(sections) != len(loft.section_heights)
        or len(sections) != len(loft.symmetry_evidence)
    ):
        raise ControlPointEditError("section_model_or_scan_parent_stale")
    if (
        isinstance(section_index, bool)
        or not isinstance(section_index, int)
        or not 0 <= section_index < len(sections)
    ):
        raise ControlPointEditError("section_index_invalid")
    if not isinstance(action, ControlPointAction):
        raise ControlPointEditError("control_point_action_invalid")
    if action is not ControlPointAction.MOVE:
        raise ControlPointEditError("cross_section_add_remove_not_supported")
    if not isinstance(point, SectionPoint):
        raise ControlPointEditError("section_control_point_required")
    feature_ids: list[str] = []
    existing_parameters: dict[str, DesignModelParameter | None] = {}
    for index, section in enumerate(sections):
        feature_id = stable_feature_id(
            section.component_id,
            FeatureKind.BODY,
            f"loft-section:{index:04d}",
        )
        try:
            feature = resolve_design_model_feature(model, feature_id)
        except DesignModelError as error:
            raise ControlPointEditError("section_feature_stale_or_missing") from error
        source_feature = next(
            (item for item in loft.model.features if item.feature_id == feature_id), None
        )
        if not isinstance(feature, DesignModelFeatureReference) or feature != source_feature:
            raise ControlPointEditError("section_feature_binding_mismatch")
        original = loft.sections[index]
        evidence = loft.symmetry_evidence[index]
        if (
            section.component_id != original.component_id
            or section.scale_state is not model.scale_state
            or section.coordinate_unit != model.coordinate_unit
            or section.center_x != evidence.center_x
            or section.center_y != evidence.center_y
        ):
            raise ControlPointEditError("section_axis_or_scale_binding_mismatch")
        parameter_id = _section_parameter_id(feature_id)
        matches = tuple(item for item in model.parameters if item.parameter_id == parameter_id)
        if len(matches) > 1:
            raise ControlPointEditError("section_parameter_ambiguous")
        parameter = matches[0] if matches else None
        if parameter is None:
            if section != original:
                raise ControlPointEditError("section_control_point_source_stale")
        else:
            _validate_section_parameter(parameter, section, feature_id, model)
        feature_ids.append(feature_id)
        existing_parameters[feature_id] = parameter

    target = sections[section_index]
    try:
        updated_target = edit_control_point(target, point_index, point)
    except CrossSectionError as error:
        raise ControlPointEditError(f"section_control_point_edit_rejected:{error}") from error
    updated_sections = tuple(
        updated_target if index == section_index else section
        for index, section in enumerate(sections)
    )
    feature_id = feature_ids[section_index]
    parameter_id = _section_parameter_id(feature_id)
    before = existing_parameters[feature_id]
    evidence = loft.symmetry_evidence[section_index]
    if before is None:
        parameter_value = {
            "contract": "packlab.design-section-symmetry-parameter.v1",
            "feature_id": feature_id,
            "section_id": updated_target.section_id,
            "section": updated_target.as_dict(),
            "section_height": loft.section_heights[section_index],
            "scan_evidence": {
                "scan_master_revision_id": loft.scan_master_revision_id,
                "scan_master_geometry_sha256": loft.scan_master_geometry_sha256,
                "left_right_reflection_error_ratio": evidence.left_right_reflection_error_ratio,
                "front_back_reflection_error_ratio": evidence.front_back_reflection_error_ratio,
                "disagreement_tolerance": 0.08,
                "disagreement_axes": [],
                "disposition": evidence.disposition,
            },
            "constraint_intent": updated_target.symmetry.value,
            "authority_class": "DESIGN_MODEL_PARAMETRIC_CONSTRAINT",
            "physical_accuracy_validation_status": model.physical_accuracy_validation_status,
            "mold_use_authorized": False,
        }
    else:
        raw_parameter_value = before.as_dict()["value"]
        if not isinstance(raw_parameter_value, dict):
            raise ControlPointEditError("section_parameter_invalid")
        parameter_value = {
            **raw_parameter_value,
            "section_id": updated_target.section_id,
            "section": updated_target.as_dict(),
        }
    after = DesignModelParameter(parameter_id, parameter_value, ParameterType.OBJECT)
    try:
        command = create_edit_command(
            model.revision_id,
            EditTargetKind.PARAMETER,
            parameter_id,
            before,
            after,
        )
    except DesignHistoryError as error:
        raise ControlPointEditError(f"section_control_point_history_rejected:{error}") from error
    try:
        revised = _revise_model(model, parameter_id, after, actor_id, reason, created_at_utc)
        inputs = tuple(
            LoftSectionInput(feature_ids[index], section, loft.section_heights[index])
            for index, section in enumerate(updated_sections)
        )
        operation = create_loft_operation(revised, inputs)
        previews = tessellate_design_preview(
            revised,
            cross_sections=updated_sections,
            operations=(operation,),
            chord_tolerance=chord_tolerance,
            maximum_angular_segments=maximum_angular_segments,
        )
    except (DesignModelError, DesignOperationError, DesignPreviewError) as error:
        raise ControlPointEditError(f"section_control_point_edit_rejected:{error}") from error
    if len(previews) != 1:
        raise ControlPointEditError("section_preview_result_invalid")
    return SectionControlPointRevision(
        revised,
        updated_sections,
        operation,
        previews[0],
        section_index,
        _changed_indices(ControlPointAction.MOVE, point_index, len(target.points)),
        command,
    )


def _validate_model_revision(model: DesignModelRevision, expected: str) -> None:
    if not isinstance(model, DesignModelRevision):
        raise ControlPointEditError("design_model_revision_required")
    if model.revision_id != expected:
        raise ControlPointEditError("design_model_revision_stale")


def _validate_index(index: int, point_count: int, action: ControlPointAction) -> None:
    maximum = point_count if action is ControlPointAction.ADD else point_count - 1
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index <= maximum:
        raise ControlPointEditError("control_point_index_invalid")


def _edit_profile_points(
    profile: DesignProfile,
    action: ControlPointAction,
    point_index: int,
    point: ProfilePoint | None,
) -> tuple[ProfilePoint, ...]:
    points = list(profile.points)
    if action is ControlPointAction.REMOVE:
        if point is not None:
            raise ControlPointEditError("remove_point_must_be_omitted")
        if len(points) <= 2:
            raise ControlPointEditError("profile_minimum_control_points_would_be_violated")
        points.pop(point_index)
    else:
        if not isinstance(point, ProfilePoint):
            raise ControlPointEditError("profile_control_point_required")
        if action is ControlPointAction.MOVE:
            points[point_index] = point
        elif action is ControlPointAction.ADD:
            points.insert(point_index, point)
        else:
            raise ControlPointEditError("control_point_action_invalid")
    return tuple(points)


def _profile_evidence_id(model: DesignModelRevision) -> str | None:
    matches = tuple(
        item for item in model.parameters if item.parameter_id == "fitted_profile_evidence"
    )
    if len(matches) != 1:
        return None
    value = matches[0].as_dict()["value"]
    return value.get("profile_id") if isinstance(value, dict) else None


def _validate_profile_parameter(
    parameter: DesignModelParameter,
    profile: DesignProfile,
    feature_id: str,
    model: DesignModelRevision,
) -> None:
    value = parameter.as_dict()["value"]
    if (
        parameter.value_type is not ParameterType.OBJECT
        or not isinstance(value, dict)
        or value.get("contract") != "packlab.design-profile-control-points.v1"
        or value.get("feature_id") != feature_id
        or value.get("profile_id") != profile.profile_id
        or value.get("profile") != profile.as_dict()
        or value.get("scan_master_revision_id") != model.fitted_to_scan_master_revision_id
        or value.get("scan_master_geometry_sha256") != model.scan_master_geometry_sha256
    ):
        raise ControlPointEditError("profile_control_point_parameter_stale_or_invalid")


def _validate_section_parameter(
    parameter: DesignModelParameter,
    section: CrossSection,
    feature_id: str,
    model: DesignModelRevision,
) -> None:
    value = parameter.as_dict()["value"]
    if (
        parameter.value_type is not ParameterType.OBJECT
        or not isinstance(value, dict)
        or value.get("contract") != "packlab.design-section-symmetry-parameter.v1"
        or value.get("feature_id") != feature_id
        or value.get("section_id") != section.section_id
        or value.get("section") != section.as_dict()
        or not isinstance(value.get("scan_evidence"), dict)
        or value["scan_evidence"].get("scan_master_revision_id")
        != model.fitted_to_scan_master_revision_id
        or value["scan_evidence"].get("scan_master_geometry_sha256")
        != model.scan_master_geometry_sha256
    ):
        raise ControlPointEditError("section_control_point_parameter_stale_or_invalid")


def _revise_model(
    model: DesignModelRevision,
    parameter_id: str,
    parameter: DesignModelParameter,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignModelRevision:
    parameters = tuple(item for item in model.parameters if item.parameter_id != parameter_id)
    try:
        return revise_design_model_revision(
            model,
            parameters=(*parameters, parameter),
            features=model.features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise ControlPointEditError("design_model_edit_revision_invalid") from error


def _profile_parameter_id(feature_id: str) -> str:
    return _PROFILE_PARAMETER_PREFIX + hashlib.sha256(feature_id.encode("utf-8")).hexdigest()


def _section_parameter_id(feature_id: str) -> str:
    return _SECTION_PARAMETER_PREFIX + hashlib.sha256(feature_id.encode("utf-8")).hexdigest()


def _changed_indices(
    action: ControlPointAction, index: int, original_count: int
) -> tuple[int, ...]:
    if action is ControlPointAction.ADD:
        return (index,)
    if action is ControlPointAction.REMOVE:
        return tuple(range(index, original_count))
    return (index,)


__all__ = [
    "ControlPointAction",
    "ControlPointEditError",
    "ProfileControlPointRevision",
    "SectionControlPointRevision",
    "edit_design_profile_control_point",
    "edit_design_section_control_point",
]
