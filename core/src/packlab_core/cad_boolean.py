"""Deterministic cuts for existing parametric jerrycan Design Model features."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .cad_adapter import (
    CadAdapterError,
    build_polygon_prism_cut,
    cad_shape_bounds,
)
from .cad_brep import (
    CadBrepRepresentationRevision,
    _representation_from_lineage,
)
from .design_model import (
    DesignModelRevision,
    FeatureKind,
)
from .jerrycan_grip_indent import (
    GripIndentSide,
)
from .jerrycan_grip_indent import (
    _resolve_feature as _resolve_grip_indent,
)
from .jerrycan_handle_opening import (
    resolve_jerrycan_handle_opening,
)


class CadBooleanError(ValueError):
    """Raised when the requested BREP or Design Model authority is invalid."""


@dataclass(frozen=True, slots=True)
class CadBooleanFeatureResult:
    operation_id: str
    operation_type: str
    status: str
    tool_feature_id: str
    body_feature_ids: tuple[str, ...]
    source_design_model_revision_id: str
    source_brep_revision_id: str
    adapter_result: str
    kernel_result: str
    topology_status: str
    cut_extent_policy: str
    feature_hidden_extent_inferred: bool
    failure_diagnostics: tuple[str, ...]
    representation: CadBrepRepresentationRevision | None
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.cad-boolean-feature-result.v1",
            "authority_class": "DERIVED_CAD_BREP_OPERATION",
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "status": self.status,
            "tool_feature_id": self.tool_feature_id,
            "body_feature_ids": list(self.body_feature_ids),
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "adapter_result": self.adapter_result,
            "kernel_result": self.kernel_result,
            "topology_status": self.topology_status,
            "cut_extent_policy": self.cut_extent_policy,
            "feature_hidden_extent_inferred": self.feature_hidden_extent_inferred,
            "failure_diagnostics": list(self.failure_diagnostics),
            "representation_revision_id": (
                self.representation.revision_id if self.representation else None
            ),
            "scan_master_promoted": False,
            "design_model_replaced": False,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
        }


def cut_design_model_feature(
    model: DesignModelRevision,
    parent_brep: CadBrepRepresentationRevision,
    feature_id: str,
) -> CadBooleanFeatureResult:
    """Cut one explicit handle-opening or grip-indent feature from its parent BREP."""
    if not isinstance(model, DesignModelRevision):
        raise CadBooleanError("design_model_revision_required")
    if not isinstance(parent_brep, CadBrepRepresentationRevision):
        raise CadBooleanError("cad_brep_representation_required")
    if (
        parent_brep.source_design_model_revision_id
        not in {
            model.revision_id,
            model.previous_revision_id,
        }
        or parent_brep.parent_kind is not model.parent_kind
        or parent_brep.parent_authority_revision_id
        != (
            model.standalone_root.revision_id
            if model.standalone_root
            else model.parent_binding_revision_id
        )
        or parent_brep.scale_state is not model.scale_state
        or parent_brep.coordinate_unit != model.coordinate_unit
        or parent_brep.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or parent_brep.mold_use_authorized
    ):
        raise CadBooleanError("cad_brep_model_or_authority_mismatch")
    feature = next((item for item in model.features if item.feature_id == feature_id), None)
    if feature is None:
        raise CadBooleanError("cad_boolean_feature_missing_or_stale")
    if feature.feature_kind is FeatureKind.HANDLE_OPENING:
        operation_type = "CUT_HANDLE_OPENING_THROUGH_BODY"
        opening = resolve_jerrycan_handle_opening(model, feature_id)
        bodies = opening.parent_body_feature_ids
        profile, extrusion = _opening_tool(opening, parent_brep)
        provenance_values: object = {
            "profile": opening.profile,
            "plane_axis": opening.plane_axis,
            "plane_position": opening.plane_position,
            "source_candidate_id": opening.candidate_id,
            "hidden_extent_inferred": False,
            "cut_extent": "through_body_brep_bounds",
        }
        extent_policy = "through_body_brep_bounds"
    elif feature.feature_kind is FeatureKind.GRIP_INDENT:
        operation_type = "CUT_GRIP_INDENT"
        definition, prefix = _resolve_grip_indent(model, feature_id)
        bodies_value = definition.get("body_feature_id")
        if not isinstance(bodies_value, str) or not bodies_value:
            raise CadBooleanError("grip_indent_body_reference_invalid")
        bodies = (bodies_value,)
        profile_value = _parameter_value(model, f"{prefix}:profile")
        depth_value = _parameter_value(model, f"{prefix}:depth")
        side_value = definition.get("side")
        if (
            not isinstance(profile_value, list)
            or any(not isinstance(point, list) or len(point) != 2 for point in profile_value)
            or not isinstance(depth_value, (int, float))
            or isinstance(depth_value, bool)
            or not math.isfinite(float(depth_value))
            or side_value not in {GripIndentSide.FRONT.value, GripIndentSide.BACK.value}
        ):
            raise CadBooleanError("grip_indent_tool_parameters_invalid")
        profile, extrusion = _indent_tool(
            tuple((float(point[0]), float(point[1])) for point in profile_value),
            float(depth_value),
            side_value,
            model,
            parent_brep,
        )
        provenance_values = {
            "profile_xz": profile_value,
            "depth": float(depth_value),
            "side": side_value,
            "evidence_sha256": definition.get("evidence_sha256"),
        }
        extent_policy = "explicit_depth_from_brep_surface"
    else:
        raise CadBooleanError("cad_boolean_feature_kind_unsupported")

    input_ids = (parent_brep.revision_id, feature_id, *bodies)
    operation_id = _operation_id(
        model.revision_id,
        parent_brep.revision_id,
        operation_type,
        input_ids,
        provenance_values,
    )
    try:
        build = build_polygon_prism_cut(
            model,
            parent_brep.shape_handle,
            operation_id=operation_id,
            input_ids=input_ids,
            profile=profile,
            extrusion=extrusion,
        )
    except CadAdapterError as error:
        diagnostic = str(error)
        return CadBooleanFeatureResult(
            operation_id,
            operation_type,
            "FAILED",
            feature_id,
            bodies,
            model.revision_id,
            parent_brep.revision_id,
            "FAILED",
            "FAILED",
            "INVALID_OR_UNAVAILABLE",
            extent_policy,
            False,
            (diagnostic,),
            None,
        )
    representation = _representation_from_lineage(model, operation_id, input_ids, build.shape_build)
    return CadBooleanFeatureResult(
        operation_id,
        operation_type,
        "SUCCEEDED",
        feature_id,
        bodies,
        model.revision_id,
        parent_brep.revision_id,
        "SUCCEEDED",
        "DONE",
        "VALID_SINGLE_SOLID",
        extent_policy,
        False,
        (),
        representation,
    )


def _opening_tool(
    opening: object, parent_brep: CadBrepRepresentationRevision
) -> tuple[tuple[tuple[float, float, float], ...], tuple[float, float, float]]:
    axis = getattr(opening, "plane_axis")
    bounds = cad_shape_bounds(parent_brep.shape_handle)
    lows = (bounds[0], bounds[2], bounds[4])
    highs = (bounds[1], bounds[3], bounds[5])
    directions = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0)}
    if axis not in directions:
        raise CadBooleanError("handle_opening_plane_axis_invalid")
    normal = directions[axis]
    axis_index = "xyz".index(axis)
    axis_span = highs[axis_index] - lows[axis_index]
    margin = max(axis_span * 0.1, 1e-3)
    start = [0.0, 0.0, 0.0]
    start[axis_index] = lows[axis_index] - margin
    plane_axes = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}[axis]
    vertices: list[tuple[float, float, float]] = []
    for point in getattr(opening, "profile"):
        coordinate = list(start)
        coordinate[plane_axes[0]] = float(point[0])
        coordinate[plane_axes[1]] = float(point[1])
        vertices.append((coordinate[0], coordinate[1], coordinate[2]))
    return tuple(vertices), (
        (axis_span + 2.0 * margin) * normal[0],
        (axis_span + 2.0 * margin) * normal[1],
        (axis_span + 2.0 * margin) * normal[2],
    )


def _indent_tool(
    profile: tuple[tuple[float, float], ...],
    depth: float,
    side: str,
    model: DesignModelRevision,
    parent_brep: CadBrepRepresentationRevision,
) -> tuple[tuple[tuple[float, float, float], ...], tuple[float, float, float]]:
    bounds = cad_shape_bounds(parent_brep.shape_handle)
    front_parameter = next(
        (item for item in model.parameters if item.parameter_id == "jerrycan_section_frame"),
        None,
    )
    front = front_parameter.as_dict()["value"] if front_parameter is not None else None
    if not isinstance(front, dict) or front.get("front_direction") not in {"+y", "-y"}:
        raise CadBooleanError("jerrycan_front_direction_missing_or_invalid")
    front_sign = 1 if front["front_direction"] == "+y" else -1
    sign = front_sign if side == GripIndentSide.FRONT.value else -front_sign
    surface = bounds[4] if sign > 0 else bounds[1]
    points = tuple((x, surface, z) for x, z in profile)
    return points, (0.0, -depth * sign, 0.0)


def _parameter_value(model: DesignModelRevision, parameter_id: str) -> object:
    matches = tuple(item for item in model.parameters if item.parameter_id == parameter_id)
    if len(matches) != 1:
        raise CadBooleanError("cad_boolean_feature_parameter_missing_or_ambiguous")
    return matches[0].as_dict()["value"]


def _operation_id(
    model_revision_id: str,
    parent_revision_id: str,
    operation_type: str,
    input_ids: tuple[str, ...],
    parameters: object,
) -> str:
    payload = {
        "contract": "packlab.cad-boolean-operation.v1",
        "model_revision_id": model_revision_id,
        "parent_brep_revision_id": parent_revision_id,
        "operation_type": operation_type,
        "input_ids": list(input_ids),
        "parameters": parameters,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return f"cad-cut:{digest}"


__all__ = ["CadBooleanError", "CadBooleanFeatureResult", "cut_design_model_feature"]
