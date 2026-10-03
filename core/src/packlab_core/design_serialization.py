"""Canonical, integrity-checked Design Model document serialization."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from .cross_section import CrossSection, CrossSectionSymmetry, SectionPoint
from .design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    ParameterType,
)
from .design_operations import DesignOperation, OperationKind
from .design_profile import DesignProfile, ProfilePoint, create_design_profile
from .reconstruction import ScaleState

DOCUMENT_CONTRACT = "packlab.design-model-document.v1"
MAX_DOCUMENT_BYTES = 16 * 1024 * 1024


class DesignSerializationError(ValueError):
    """Raised when a Design Model document is malformed, stale or tampered."""


@dataclass(frozen=True, slots=True)
class DesignModelDocument:
    model: DesignModelRevision
    profiles: tuple[DesignProfile, ...]
    cross_sections: tuple[CrossSection, ...]
    operations: tuple[DesignOperation, ...]


def serialize_design_model(
    model: DesignModelRevision,
    *,
    profiles: tuple[DesignProfile, ...] = (),
    cross_sections: tuple[CrossSection, ...] = (),
    operations: tuple[DesignOperation, ...] = (),
) -> bytes:
    """Encode canonical UTF-8 JSON with a SHA-256 digest over the complete document body."""
    document = DesignModelDocument(model, profiles, cross_sections, operations)
    _validate_document_references(document)
    body = {
        "contract": DOCUMENT_CONTRACT,
        "model": model.as_dict(),
        "profiles": [item.as_dict() for item in sorted(profiles, key=lambda item: item.profile_id)],
        "cross_sections": [
            item.as_dict() for item in sorted(cross_sections, key=lambda item: item.section_id)
        ],
        "operations": [
            item.as_dict() for item in sorted(operations, key=lambda item: item.operation_id)
        ],
    }
    digest = hashlib.sha256(_canonical_json(body)).hexdigest()
    encoded = _canonical_json({"body": body, "content_sha256": digest})
    if len(encoded) > MAX_DOCUMENT_BYTES:
        raise DesignSerializationError("document_size_limit_exceeded")
    return encoded


def deserialize_design_model(
    data: bytes | str,
    *,
    expected_scan_master_revision_id: str | None = None,
    expected_scan_master_geometry_sha256: str | None = None,
    expected_parent_binding_revision_id: str | None = None,
) -> DesignModelDocument:
    """Strictly parse one supported version without duplicate keys or inferred defaults."""
    if isinstance(data, bytes):
        raw = data
    elif isinstance(data, str):
        raw = data.encode("utf-8")
    else:
        raise DesignSerializationError("document_data_type_invalid")
    if not raw or len(raw) > MAX_DOCUMENT_BYTES:
        raise DesignSerializationError("document_size_invalid")
    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                DesignSerializationError(f"nonfinite_json_constant:{value}")
            ),
        )
    except DesignSerializationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DesignSerializationError("document_json_invalid") from error
    if not isinstance(decoded, dict) or set(decoded) != {"body", "content_sha256"}:
        raise DesignSerializationError("document_envelope_invalid")
    body = decoded["body"]
    if not isinstance(body, dict) or set(body) != {
        "contract",
        "model",
        "profiles",
        "cross_sections",
        "operations",
    }:
        raise DesignSerializationError("document_body_invalid")
    if body["contract"] != DOCUMENT_CONTRACT:
        raise DesignSerializationError("document_version_unsupported")
    digest = decoded["content_sha256"]
    if not isinstance(digest, str) or len(digest) != 64:
        raise DesignSerializationError("document_digest_invalid")
    if hashlib.sha256(_canonical_json(body)).hexdigest() != digest:
        raise DesignSerializationError("document_digest_mismatch")
    model = _deserialize_model(body["model"])
    profiles = _deserialize_profiles(body["profiles"])
    sections = _deserialize_sections(body["cross_sections"])
    operations = _deserialize_operations(body["operations"])
    document = DesignModelDocument(model, profiles, sections, operations)
    _validate_document_references(document)
    if (
        expected_scan_master_revision_id is not None
        and model.fitted_to_scan_master_revision_id != expected_scan_master_revision_id
    ):
        raise DesignSerializationError("scan_master_parent_revision_stale")
    if (
        expected_scan_master_geometry_sha256 is not None
        and model.scan_master_geometry_sha256 != expected_scan_master_geometry_sha256
    ):
        raise DesignSerializationError("scan_master_parent_digest_stale")
    if (
        expected_parent_binding_revision_id is not None
        and model.parent_binding_revision_id != expected_parent_binding_revision_id
    ):
        raise DesignSerializationError("parent_binding_revision_stale")
    return document


def _deserialize_model(value: object) -> DesignModelRevision:
    model = _mapping(
        value,
        {
            "contract",
            "revision_id",
            "project_id",
            "package_family",
            "parameters",
            "features",
            "parent",
            "scale_state",
            "scale_provenance_id",
            "coordinate_unit",
            "physical_accuracy_validation_status",
            "mold_use_authorized",
            "previous_revision_id",
            "actor_id",
            "reason",
            "created_at_utc",
        },
        "model",
    )
    if model["contract"] != "packlab.design-model.v1":
        raise DesignSerializationError("design_model_version_unsupported")
    parent = _mapping(
        model["parent"],
        {"binding_revision_id", "scan_master_revision_id", "scan_master_geometry_sha256"},
        "model.parent",
    )
    parameters = tuple(
        _deserialize_parameter(item) for item in _array(model["parameters"], "model.parameters")
    )
    features = tuple(
        _deserialize_feature(item) for item in _array(model["features"], "model.features")
    )
    return DesignModelRevision(
        revision_id=_string(model["revision_id"], "model.revision_id"),
        project_id=_string(model["project_id"], "model.project_id"),
        package_family=_enum(PackageFamily, model["package_family"], "model.package_family"),
        parameters=parameters,
        features=features,
        parent_binding_revision_id=_string(
            parent["binding_revision_id"], "model.parent.binding_revision_id"
        ),
        fitted_to_scan_master_revision_id=_string(
            parent["scan_master_revision_id"], "model.parent.scan_master_revision_id"
        ),
        scan_master_geometry_sha256=_string(
            parent["scan_master_geometry_sha256"], "model.parent.scan_master_geometry_sha256"
        ),
        scale_state=_enum(ScaleState, model["scale_state"], "model.scale_state"),
        scale_provenance_id=_string(model["scale_provenance_id"], "model.scale_provenance_id"),
        coordinate_unit=_string(model["coordinate_unit"], "model.coordinate_unit"),
        physical_accuracy_validation_status=_string(
            model["physical_accuracy_validation_status"],
            "model.physical_accuracy_validation_status",
        ),
        mold_use_authorized=_boolean(model["mold_use_authorized"], "model.mold_use_authorized"),
        previous_revision_id=_optional_string(
            model["previous_revision_id"], "model.previous_revision_id"
        ),
        actor_id=_string(model["actor_id"], "model.actor_id"),
        reason=_string(model["reason"], "model.reason"),
        created_at_utc=_string(model["created_at_utc"], "model.created_at_utc"),
    )


def _deserialize_parameter(value: object) -> DesignModelParameter:
    item = _mapping(value, {"parameter_id", "value", "value_type", "unit"}, "parameter")
    return DesignModelParameter(
        _string(item["parameter_id"], "parameter.parameter_id"),
        item["value"],
        _enum(ParameterType, item["value_type"], "parameter.value_type"),
        _optional_string(item["unit"], "parameter.unit"),
    )


def _deserialize_feature(value: object) -> DesignModelFeatureReference:
    item = _mapping(
        value,
        {"feature_id", "component_id", "feature_kind", "semantic_key"},
        "feature",
    )
    return DesignModelFeatureReference(
        _string(item["feature_id"], "feature.feature_id"),
        _string(item["component_id"], "feature.component_id"),
        _enum(FeatureKind, item["feature_kind"], "feature.feature_kind"),
        _string(item["semantic_key"], "feature.semantic_key"),
    )


def _deserialize_profiles(value: object) -> tuple[DesignProfile, ...]:
    result: list[DesignProfile] = []
    for raw in _array(value, "profiles"):
        item = _mapping(
            raw,
            {
                "contract",
                "profile_id",
                "interpolation",
                "point_order",
                "endpoint_policy",
                "tangent_policy",
                "scale_state",
                "coordinate_unit",
                "physical_accuracy_validation_status",
                "mold_use_authorized",
                "control_points",
            },
            "profile",
        )
        if (
            item["contract"] != "packlab.design-profile.v1"
            or item["interpolation"] != "piecewise-cubic-hermite-v1"
            or item["point_order"] != "strictly-increasing-axial-coordinate"
            or item["endpoint_policy"] != "exact-control-point-value; no-extrapolation"
            or item["tangent_policy"] != "explicit-drdz-or-one-sided/centered-secant"
            or item["physical_accuracy_validation_status"] != "DEFERRED_OWNER_VALIDATION"
            or item["mold_use_authorized"] is not False
        ):
            raise DesignSerializationError("profile_contract_invalid")
        points = tuple(
            ProfilePoint(
                _number(point["axial"], "profile.control_points.axial"),
                _number(point["radius"], "profile.control_points.radius"),
                _optional_number(point["tangent"], "profile.control_points.tangent"),
            )
            for point in (
                _mapping(raw_point, {"axial", "radius", "tangent"}, "profile.control_point")
                for raw_point in _array(item["control_points"], "profile.control_points")
            )
        )
        profile = create_design_profile(
            points, _enum(ScaleState, item["scale_state"], "profile.scale_state")
        )
        if (
            profile.profile_id != item["profile_id"]
            or profile.coordinate_unit != item["coordinate_unit"]
        ):
            raise DesignSerializationError("profile_identity_or_unit_mismatch")
        result.append(profile)
    _unique_ids(tuple(item.profile_id for item in result), "profile_id_duplicate")
    return tuple(result)


def _deserialize_sections(value: object) -> tuple[CrossSection, ...]:
    result: list[CrossSection] = []
    for raw in _array(value, "cross_sections"):
        item = _mapping(
            raw,
            {
                "contract",
                "section_id",
                "component_id",
                "points",
                "symmetry",
                "symmetry_axes",
                "scale_state",
                "coordinate_unit",
                "physical_accuracy_validation_status",
                "mold_use_authorized",
                "previous_section_id",
            },
            "cross_section",
        )
        if (
            item["contract"] != "packlab.cross-section.v1"
            or item["physical_accuracy_validation_status"] != "DEFERRED_OWNER_VALIDATION"
            or item["mold_use_authorized"] is not False
        ):
            raise DesignSerializationError("cross_section_contract_invalid")
        axes = _mapping(
            item["symmetry_axes"],
            {"left_right_axis_x", "front_back_axis_y"},
            "cross_section.symmetry_axes",
        )
        points = tuple(
            SectionPoint(
                _number(point["x"], "cross_section.points.x"),
                _number(point["y"], "cross_section.points.y"),
            )
            for point in (
                _mapping(raw_point, {"x", "y"}, "cross_section.point")
                for raw_point in _array(item["points"], "cross_section.points")
            )
        )
        try:
            section = CrossSection(
                _string(item["section_id"], "cross_section.section_id"),
                _string(item["component_id"], "cross_section.component_id"),
                points,
                _enum(CrossSectionSymmetry, item["symmetry"], "cross_section.symmetry"),
                _number(axes["left_right_axis_x"], "cross_section.axis_x"),
                _number(axes["front_back_axis_y"], "cross_section.axis_y"),
                _enum(ScaleState, item["scale_state"], "cross_section.scale_state"),
                _string(item["coordinate_unit"], "cross_section.coordinate_unit"),
                _optional_string(item["previous_section_id"], "cross_section.previous_section_id"),
            )
        except ValueError as error:
            raise DesignSerializationError("cross_section_invalid") from error
        result.append(section)
    _unique_ids(tuple(item.section_id for item in result), "cross_section_id_duplicate")
    return tuple(result)


def _deserialize_operations(value: object) -> tuple[DesignOperation, ...]:
    result: list[DesignOperation] = []
    for raw in _array(value, "operations"):
        item = _mapping(
            raw,
            {
                "contract",
                "authority_class",
                "operation_id",
                "kind",
                "model_revision_id",
                "parent_feature_ids",
                "input_ids",
                "axis_origin",
                "axis_direction",
                "angle_degrees",
                "section_positions",
                "coordinate_unit",
                "scale_state",
                "physical_accuracy_validation_status",
                "mold_use_authorized",
                "output_geometry",
            },
            "operation",
        )
        if (
            item["contract"] != "packlab.design-operation.v1"
            or item["authority_class"] != "DESIGN_MODEL_OPERATION"
            or item["physical_accuracy_validation_status"] != "DEFERRED_OWNER_VALIDATION"
            or item["mold_use_authorized"] is not False
            or item["output_geometry"] is not None
        ):
            raise DesignSerializationError("operation_contract_invalid")
        origin = _optional_vector3(item["axis_origin"], "operation.axis_origin")
        direction = _optional_vector3(item["axis_direction"], "operation.axis_direction")
        angle = _optional_number(item["angle_degrees"], "operation.angle_degrees")
        operation = DesignOperation(
            operation_id=_string(item["operation_id"], "operation.operation_id"),
            kind=_enum(OperationKind, item["kind"], "operation.kind"),
            model_revision_id=_string(item["model_revision_id"], "operation.model_revision_id"),
            parent_feature_ids=tuple(
                _string(entry, "operation.parent_feature_id")
                for entry in _array(item["parent_feature_ids"], "operation.parent_feature_ids")
            ),
            input_ids=tuple(
                _string(entry, "operation.input_id")
                for entry in _array(item["input_ids"], "operation.input_ids")
            ),
            axis_origin=origin,
            axis_direction=direction,
            angle_degrees=angle,
            section_positions=tuple(
                _number(entry, "operation.section_position")
                for entry in _array(item["section_positions"], "operation.section_positions")
            ),
            coordinate_unit=_string(item["coordinate_unit"], "operation.coordinate_unit"),
            scale_state=_enum(ScaleState, item["scale_state"], "operation.scale_state"),
            physical_accuracy_validation_status=_string(
                item["physical_accuracy_validation_status"],
                "operation.physical_accuracy_validation_status",
            ),
            mold_use_authorized=_boolean(
                item["mold_use_authorized"], "operation.mold_use_authorized"
            ),
        )
        result.append(operation)
    _unique_ids(tuple(item.operation_id for item in result), "operation_id_duplicate")
    return tuple(result)


def _validate_document_references(document: DesignModelDocument) -> None:
    model = document.model
    if not isinstance(model, DesignModelRevision):
        raise DesignSerializationError("design_model_revision_required")
    if any(
        profile.coordinate_unit != model.coordinate_unit
        or profile.scale_state is not model.scale_state
        for profile in document.profiles
    ):
        raise DesignSerializationError("profile_model_unit_mismatch")
    if any(
        section.coordinate_unit != model.coordinate_unit
        or section.scale_state is not model.scale_state
        for section in document.cross_sections
    ):
        raise DesignSerializationError("cross_section_model_unit_mismatch")
    feature_ids = {feature.feature_id for feature in model.features}
    profile_ids = {profile.profile_id for profile in document.profiles}
    section_ids = {section.section_id for section in document.cross_sections}
    for operation in document.operations:
        if operation.model_revision_id != model.revision_id:
            raise DesignSerializationError("operation_model_revision_stale")
        if any(feature_id not in feature_ids for feature_id in operation.parent_feature_ids):
            raise DesignSerializationError("operation_feature_reference_stale")
        input_ids = profile_ids if operation.kind is OperationKind.REVOLVE else section_ids
        if any(input_id not in input_ids for input_id in operation.input_ids):
            raise DesignSerializationError("operation_input_reference_stale")


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DesignSerializationError("duplicate_json_key")
        result[key] = value
    return result


def _mapping(value: object, expected: set[str], field: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise DesignSerializationError(f"{field}_fields_invalid")
    return value


def _array(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise DesignSerializationError(f"{field}_must_be_array")
    return value


def _string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise DesignSerializationError(f"{field}_must_be_string")
    return value


def _optional_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field)


def _boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise DesignSerializationError(f"{field}_must_be_boolean")
    return value


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DesignSerializationError(f"{field}_must_be_number")
    return float(value)


def _optional_number(value: object, field: str) -> float | None:
    if value is None:
        return None
    return _number(value, field)


def _optional_vector3(value: object, field: str) -> tuple[float, float, float] | None:
    if value is None:
        return None
    entries = _array(value, field)
    if len(entries) != 3:
        raise DesignSerializationError(f"{field}_length_invalid")
    return tuple(_number(entry, field) for entry in entries)  # type: ignore[return-value]


def _enum(enum_type: type[StrEnum], value: object, field: str):
    if not isinstance(value, str):
        raise DesignSerializationError(f"{field}_must_be_string")
    try:
        return enum_type(value)
    except ValueError as error:
        raise DesignSerializationError(f"{field}_unsupported") from error


def _unique_ids(ids: tuple[str, ...], error_code: str) -> None:
    if len(ids) != len(set(ids)):
        raise DesignSerializationError(error_code)


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise DesignSerializationError("document_value_not_canonical_json") from error


__all__ = [
    "DOCUMENT_CONTRACT",
    "MAX_DOCUMENT_BYTES",
    "DesignModelDocument",
    "DesignSerializationError",
    "deserialize_design_model",
    "serialize_design_model",
]
