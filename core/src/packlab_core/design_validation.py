"""Versioned, deterministic validation for Design Model parameter graphs."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .cross_section import CrossSection
from .design_model import DesignModelRevision, ParameterType
from .design_operations import DesignOperation, OperationKind
from .design_profile import DesignProfile

VALIDATION_CONTRACT = "packlab.design-validation.v1"


class DesignValidationError(ValueError):
    """Raised when a validation policy itself is malformed."""


@dataclass(frozen=True, slots=True)
class NumericBound:
    parameter_id: str
    minimum: float
    maximum: float
    unit: str

    def __post_init__(self) -> None:
        if not isinstance(self.parameter_id, str) or not self.parameter_id:
            raise DesignValidationError("numeric_bound_parameter_id_invalid")
        if (
            isinstance(self.minimum, bool)
            or isinstance(self.maximum, bool)
            or not isinstance(self.minimum, (int, float))
            or not isinstance(self.maximum, (int, float))
        ):
            raise DesignValidationError("numeric_bound_must_be_numeric")
        if not isfinite(self.minimum) or not isfinite(self.maximum):
            raise DesignValidationError("numeric_bound_must_be_finite")
        if self.minimum > self.maximum:
            raise DesignValidationError("numeric_bound_range_invalid")
        if not isinstance(self.unit, str) or self.unit not in {
            "reconstruction_units",
            "mm_unverified",
        }:
            raise DesignValidationError("numeric_bound_unit_unauthorized")


@dataclass(frozen=True, slots=True)
class DesignValidationPolicy:
    version: str = VALIDATION_CONTRACT
    numeric_bounds: tuple[NumericBound, ...] = ()
    ordered_parameter_ids: tuple[str, ...] = ()
    available_scan_master_revision_ids: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.version != VALIDATION_CONTRACT:
            raise DesignValidationError("validation_policy_version_unsupported")
        if not isinstance(self.numeric_bounds, tuple) or any(
            not isinstance(item, NumericBound) for item in self.numeric_bounds
        ):
            raise DesignValidationError("numeric_bounds_must_be_immutable_tuple")
        bound_ids = tuple(item.parameter_id for item in self.numeric_bounds)
        if len(bound_ids) != len(set(bound_ids)):
            raise DesignValidationError("numeric_bound_parameter_duplicate")
        if not isinstance(self.ordered_parameter_ids, tuple) or any(
            not isinstance(item, str) or not item for item in self.ordered_parameter_ids
        ):
            raise DesignValidationError("ordered_parameter_ids_invalid")
        if len(self.ordered_parameter_ids) != len(set(self.ordered_parameter_ids)):
            raise DesignValidationError("ordered_parameter_id_duplicate")
        available = self.available_scan_master_revision_ids
        if available is not None:
            if not isinstance(available, tuple) or any(
                not isinstance(item, str) or not item for item in available
            ):
                raise DesignValidationError("available_scan_master_ids_invalid")
            if len(available) != len(set(available)):
                raise DesignValidationError("available_scan_master_id_duplicate")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


@dataclass(frozen=True, slots=True)
class DesignValidationReport:
    model_revision_id: str
    policy_version: str
    issues: tuple[ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": VALIDATION_CONTRACT,
            "model_revision_id": self.model_revision_id,
            "policy_version": self.policy_version,
            "status": "VALID" if self.valid else "INVALID",
            "issues": [item.as_dict() for item in self.issues],
            "mutated_or_clamped_parameters": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }


def validate_design_model(
    model: DesignModelRevision,
    *,
    policy: DesignValidationPolicy = DesignValidationPolicy(),
    profiles: tuple[DesignProfile, ...] = (),
    cross_sections: tuple[CrossSection, ...] = (),
    operations: tuple[DesignOperation, ...] = (),
) -> DesignValidationReport:
    """Return sorted diagnostics; validation never repairs or clamps source parameters."""
    if not isinstance(model, DesignModelRevision):
        raise DesignValidationError("design_model_revision_required")
    if not isinstance(policy, DesignValidationPolicy):
        raise DesignValidationError("design_validation_policy_required")
    issues: list[ValidationIssue] = []
    parameters = {item.parameter_id: item for item in model.parameters}
    for parameter in model.parameters:
        if parameter.value_type in {ParameterType.NUMBER, ParameterType.INTEGER}:
            if isinstance(parameter.value, bool) or not isinstance(parameter.value, (int, float)):
                issues.append(
                    ValidationIssue(
                        "parameter_numeric_value_invalid",
                        f"parameters.{parameter.parameter_id}",
                        "Numeric parameters must contain a finite numeric value.",
                    )
                )
            elif not isfinite(parameter.value):
                issues.append(
                    ValidationIssue(
                        "parameter_numeric_value_nonfinite",
                        f"parameters.{parameter.parameter_id}",
                        "Numeric parameters must be finite.",
                    )
                )
        if parameter.unit is not None and parameter.unit != model.coordinate_unit:
            issues.append(
                ValidationIssue(
                    "parameter_unit_mismatch",
                    f"parameters.{parameter.parameter_id}.unit",
                    "Parameter units must match the inherited Design Model coordinate unit.",
                )
            )

    for bound in policy.numeric_bounds:
        bounded_parameter = parameters.get(bound.parameter_id)
        path = f"parameters.{bound.parameter_id}"
        if bounded_parameter is None:
            issues.append(
                ValidationIssue("bounded_parameter_missing", path, "Bounded parameter is missing.")
            )
            continue
        if bounded_parameter.value_type not in {ParameterType.NUMBER, ParameterType.INTEGER}:
            issues.append(
                ValidationIssue(
                    "bounded_parameter_not_numeric", path, "Expected a numeric parameter."
                )
            )
            continue
        if bound.unit != model.coordinate_unit or bounded_parameter.unit != bound.unit:
            issues.append(
                ValidationIssue(
                    "bounded_parameter_unit_mismatch",
                    f"{path}.unit",
                    "Parameter and bound units must match the inherited model unit.",
                )
            )
            continue
        value = bounded_parameter.value
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            continue
        if not bound.minimum <= value <= bound.maximum:
            issues.append(
                ValidationIssue(
                    "parameter_out_of_bounds",
                    path,
                    f"Value must remain within [{bound.minimum}, {bound.maximum}] {bound.unit}.",
                )
            )

    if policy.ordered_parameter_ids:
        ordered_values: list[tuple[str, float]] = []
        for parameter_id in policy.ordered_parameter_ids:
            ordered_parameter = parameters.get(parameter_id)
            path = f"parameters.{parameter_id}"
            if ordered_parameter is None:
                issues.append(
                    ValidationIssue(
                        "ordered_parameter_missing", path, "Required ordering parameter is missing."
                    )
                )
                continue
            value = ordered_parameter.value
            if (
                ordered_parameter.value_type
                not in {
                    ParameterType.NUMBER,
                    ParameterType.INTEGER,
                }
                or isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
            ):
                issues.append(
                    ValidationIssue(
                        "ordered_parameter_not_numeric", path, "Ordering values must be numeric."
                    )
                )
                continue
            if ordered_parameter.unit != model.coordinate_unit:
                issues.append(
                    ValidationIssue(
                        "parameter_unit_mismatch",
                        f"{path}.unit",
                        "Ordering values must use the inherited Design Model coordinate unit.",
                    )
                )
                continue
            ordered_values.append((parameter_id, float(value)))
        if len(ordered_values) == len(policy.ordered_parameter_ids):
            for (left_id, left), (right_id, right) in zip(ordered_values, ordered_values[1:]):
                if left >= right:
                    issues.append(
                        ValidationIssue(
                            "parameter_order_contradiction",
                            f"parameters.{left_id}->{right_id}",
                            "Base/body/shoulder/neck height parameters must be strictly increasing.",
                        )
                    )

    available = policy.available_scan_master_revision_ids
    if available is not None and model.fitted_to_scan_master_revision_id not in available:
        issues.append(
            ValidationIssue(
                "scan_master_parent_stale",
                "parent.scan_master_revision_id",
                "The exact pinned Scan Master revision is not available; no retargeting was performed.",
            )
        )

    if not isinstance(profiles, tuple) or any(
        not isinstance(item, DesignProfile) for item in profiles
    ):
        raise DesignValidationError("profiles_must_be_immutable_tuple")
    if not isinstance(cross_sections, tuple) or any(
        not isinstance(item, CrossSection) for item in cross_sections
    ):
        raise DesignValidationError("cross_sections_must_be_immutable_tuple")
    if not isinstance(operations, tuple) or any(
        not isinstance(item, DesignOperation) for item in operations
    ):
        raise DesignValidationError("operations_must_be_immutable_tuple")
    profile_ids = tuple(item.profile_id for item in profiles)
    section_ids = tuple(item.section_id for item in cross_sections)
    if len(profile_ids) != len(set(profile_ids)):
        issues.append(
            ValidationIssue("profile_id_duplicate", "profiles", "Profile IDs must be unique.")
        )
    if len(section_ids) != len(set(section_ids)):
        issues.append(
            ValidationIssue(
                "cross_section_id_duplicate", "cross_sections", "Section IDs must be unique."
            )
        )
    for index, profile in enumerate(profiles):
        if (
            profile.coordinate_unit != model.coordinate_unit
            or profile.scale_state is not model.scale_state
        ):
            issues.append(
                ValidationIssue(
                    "profile_unit_mismatch",
                    f"profiles[{index}]",
                    "Profile unit state must match the Design Model.",
                )
            )
    for index, section in enumerate(cross_sections):
        if (
            section.coordinate_unit != model.coordinate_unit
            or section.scale_state is not model.scale_state
        ):
            issues.append(
                ValidationIssue(
                    "cross_section_unit_mismatch",
                    f"cross_sections[{index}]",
                    "Cross-section unit state must match the Design Model.",
                )
            )

    feature_ids = {feature.feature_id for feature in model.features}
    profile_id_set = set(profile_ids)
    section_id_set = set(section_ids)
    for index, operation in enumerate(operations):
        path = f"operations[{index}]"
        if operation.model_revision_id != model.revision_id:
            issues.append(
                ValidationIssue(
                    "operation_model_revision_stale",
                    path,
                    "Operation targets another model revision.",
                )
            )
        if any(feature_id not in feature_ids for feature_id in operation.parent_feature_ids):
            issues.append(
                ValidationIssue(
                    "operation_feature_reference_stale",
                    f"{path}.parent_feature_ids",
                    "Operation contains a missing or replaced feature ID.",
                )
            )
        if (
            operation.coordinate_unit != model.coordinate_unit
            or operation.scale_state is not model.scale_state
        ):
            issues.append(
                ValidationIssue(
                    "operation_unit_mismatch",
                    path,
                    "Operation unit state must match the Design Model.",
                )
            )
        expected_inputs = (
            profile_id_set if operation.kind is OperationKind.REVOLVE else section_id_set
        )
        if any(input_id not in expected_inputs for input_id in operation.input_ids):
            issues.append(
                ValidationIssue(
                    "operation_input_reference_stale",
                    f"{path}.input_ids",
                    "Operation refers to a profile or section missing from the validation set.",
                )
            )
        if operation.kind is OperationKind.REVOLVE:
            if (
                operation.axis_origin is None
                or operation.axis_direction is None
                or operation.angle_degrees is None
                or not 0 < operation.angle_degrees <= 360
                or abs(sum(value * value for value in operation.axis_direction) - 1.0) > 1e-9
            ):
                issues.append(
                    ValidationIssue(
                        "revolve_parameters_invalid", path, "Revolve axis/angle is invalid."
                    )
                )
        elif operation.kind is OperationKind.LOFT:
            positions = operation.section_positions
            if len(positions) != len(operation.input_ids) or any(
                right <= left for left, right in zip(positions, positions[1:])
            ):
                issues.append(
                    ValidationIssue(
                        "loft_order_invalid", path, "Loft sections are not strictly ordered."
                    )
                )

    ordered_issues = tuple(sorted(issues, key=lambda item: (item.code, item.path, item.message)))
    return DesignValidationReport(model.revision_id, policy.version, ordered_issues)


__all__ = [
    "VALIDATION_CONTRACT",
    "DesignValidationError",
    "DesignValidationPolicy",
    "DesignValidationReport",
    "NumericBound",
    "ValidationIssue",
    "validate_design_model",
]
