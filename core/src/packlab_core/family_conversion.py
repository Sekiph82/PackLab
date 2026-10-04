"""Explicit immutable Design Model package-family conversions."""

from __future__ import annotations

from dataclasses import dataclass

from .design_model import (
    DesignModelError,
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelParentKind,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    convert_design_model_family_revision,
    stable_feature_id,
)


class FamilyConversionError(ValueError):
    """Raised when a family conversion has ambiguous mapping or authority."""


@dataclass(frozen=True, slots=True)
class FeatureSemanticMapping:
    source_feature_id: str
    target_component_id: str
    target_feature_kind: FeatureKind
    target_semantic_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_feature_id, str) or not self.source_feature_id.startswith(
            "packlab-feature:"
        ):
            raise FamilyConversionError("family_conversion_source_feature_invalid")
        if not isinstance(self.target_feature_kind, FeatureKind):
            raise FamilyConversionError("family_conversion_target_feature_kind_invalid")
        try:
            stable_feature_id(
                self.target_component_id,
                self.target_feature_kind,
                self.target_semantic_key,
            )
        except DesignModelError as error:
            raise FamilyConversionError("family_conversion_target_semantics_invalid") from error

    def as_dict(self) -> dict[str, str]:
        return {
            "source_feature_id": self.source_feature_id,
            "target_feature_id": stable_feature_id(
                self.target_component_id,
                self.target_feature_kind,
                self.target_semantic_key,
            ),
            "target_component_id": self.target_component_id,
            "target_feature_kind": self.target_feature_kind.value,
            "target_semantic_key": self.target_semantic_key,
        }


@dataclass(frozen=True, slots=True)
class ParameterSemanticMapping:
    source_parameter_id: str
    target_parameter_id: str

    def __post_init__(self) -> None:
        _parameter_id(self.source_parameter_id)
        _parameter_id(self.target_parameter_id)

    def as_dict(self) -> dict[str, str]:
        return {
            "source_parameter_id": self.source_parameter_id,
            "target_parameter_id": self.target_parameter_id,
        }


@dataclass(frozen=True, slots=True)
class FamilyConversionResult:
    source_revision_id: str
    source_family: PackageFamily
    target_family: PackageFamily
    converted_model: DesignModelRevision
    feature_mappings: tuple[FeatureSemanticMapping, ...]
    parameter_mappings: tuple[ParameterSemanticMapping, ...]
    unsupported_feature_ids: tuple[str, ...]
    unsupported_parameter_ids: tuple[str, ...]
    no_op: bool

    @property
    def conversion_revision_id(self) -> str:
        return self.converted_model.revision_id

    def as_dict(self) -> dict[str, object]:
        model = self.converted_model
        if model.standalone_root is not None:
            parent_authority = model.standalone_root.as_dict()
        else:
            parent_authority = {
                "kind": DesignModelParentKind.CAPTURED_SCAN_MASTER.value,
                "parent_binding_revision_id": model.parent_binding_revision_id,
                "scan_master_revision_id": model.fitted_to_scan_master_revision_id,
                "scan_master_geometry_sha256": model.scan_master_geometry_sha256,
                "scale_provenance_id": model.scale_provenance_id,
            }
        return {
            "contract": "packlab.design-model-family-conversion.v1",
            "source_revision_id": self.source_revision_id,
            "conversion_revision_id": self.conversion_revision_id,
            "source_family": self.source_family.value,
            "target_family": self.target_family.value,
            "parent_authority_kind": self.converted_model.parent_kind.value,
            "parent_authority": parent_authority,
            "parent_authority_preserved": True,
            "no_op": self.no_op,
            "feature_mappings": [item.as_dict() for item in self.feature_mappings],
            "parameter_mappings": [item.as_dict() for item in self.parameter_mappings],
            "unsupported_feature_ids": list(self.unsupported_feature_ids),
            "unsupported_parameter_ids": list(self.unsupported_parameter_ids),
            "unsupported_items_dropped_explicitly": bool(
                self.unsupported_feature_ids or self.unsupported_parameter_ids
            ),
            "original_revision_preserved": True,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }


def convert_package_family(
    source: DesignModelRevision,
    target_family: PackageFamily,
    *,
    feature_mappings: tuple[FeatureSemanticMapping, ...] = (),
    parameter_mappings: tuple[ParameterSemanticMapping, ...] = (),
    unsupported_feature_ids: tuple[str, ...] = (),
    unsupported_parameter_ids: tuple[str, ...] = (),
    target_parent_kind: DesignModelParentKind | None = None,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> FamilyConversionResult:
    """Convert by an explicit complete semantic map, retaining the source parent exactly.

    Every source feature and parameter must be mapped or named as unsupported. Unsupported
    source entries are omitted from the new revision only when explicitly listed in the result.
    Parent rebinding is not supported by this API.
    """
    if not isinstance(source, DesignModelRevision):
        raise FamilyConversionError("family_conversion_source_model_required")
    if not isinstance(target_family, PackageFamily):
        raise FamilyConversionError("family_conversion_target_family_invalid")
    if target_parent_kind is not None and target_parent_kind is not source.parent_kind:
        raise FamilyConversionError("family_conversion_cross_authority_rebind_forbidden")
    if target_family is source.package_family:
        if any(
            (
                feature_mappings,
                parameter_mappings,
                unsupported_feature_ids,
                unsupported_parameter_ids,
            )
        ):
            raise FamilyConversionError("family_conversion_same_family_mapping_not_allowed")
        return FamilyConversionResult(
            source.revision_id,
            source.package_family,
            target_family,
            source,
            (),
            (),
            (),
            (),
            True,
        )
    _tuple_of(feature_mappings, FeatureSemanticMapping, "feature_mappings")
    _tuple_of(parameter_mappings, ParameterSemanticMapping, "parameter_mappings")
    _unique_ids(unsupported_feature_ids, "unsupported_feature_ids")
    _unique_ids(unsupported_parameter_ids, "unsupported_parameter_ids")
    feature_map_by_id = {item.source_feature_id: item for item in feature_mappings}
    parameter_map_by_id = {item.source_parameter_id: item for item in parameter_mappings}
    if len(feature_map_by_id) != len(feature_mappings):
        raise FamilyConversionError("family_conversion_feature_mapping_duplicate")
    if len(parameter_map_by_id) != len(parameter_mappings):
        raise FamilyConversionError("family_conversion_parameter_mapping_duplicate")
    source_feature_ids = {item.feature_id for item in source.features}
    source_parameter_ids = {item.parameter_id for item in source.parameters}
    _validate_coverage(
        source_feature_ids,
        set(feature_map_by_id),
        set(unsupported_feature_ids),
        "feature",
    )
    _validate_coverage(
        source_parameter_ids,
        set(parameter_map_by_id),
        set(unsupported_parameter_ids),
        "parameter",
    )
    converted_features = tuple(
        DesignModelFeatureReference(
            stable_feature_id(
                mapping.target_component_id,
                mapping.target_feature_kind,
                mapping.target_semantic_key,
            ),
            mapping.target_component_id,
            mapping.target_feature_kind,
            mapping.target_semantic_key,
        )
        for mapping in sorted(feature_mappings, key=lambda item: item.source_feature_id)
    )
    source_parameters = {item.parameter_id: item for item in source.parameters}
    converted_parameters = tuple(
        DesignModelParameter(
            mapping.target_parameter_id,
            source_parameters[mapping.source_parameter_id].as_dict()["value"],
            source_parameters[mapping.source_parameter_id].value_type,
            source_parameters[mapping.source_parameter_id].unit,
        )
        for mapping in sorted(parameter_mappings, key=lambda item: item.source_parameter_id)
    )
    try:
        converted = convert_design_model_family_revision(
            source,
            package_family=target_family,
            parameters=converted_parameters,
            features=converted_features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise FamilyConversionError("family_conversion_design_model_invalid") from error
    if (
        converted.previous_revision_id != source.revision_id
        or converted.parent_kind is not source.parent_kind
        or converted.standalone_root != source.standalone_root
        or converted.parent_binding_revision_id != source.parent_binding_revision_id
        or converted.fitted_to_scan_master_revision_id != source.fitted_to_scan_master_revision_id
        or converted.scan_master_geometry_sha256 != source.scan_master_geometry_sha256
        or converted.scale_provenance_id != source.scale_provenance_id
    ):
        raise FamilyConversionError("family_conversion_parent_authority_changed")
    return FamilyConversionResult(
        source.revision_id,
        source.package_family,
        target_family,
        converted,
        tuple(sorted(feature_mappings, key=lambda item: item.source_feature_id)),
        tuple(sorted(parameter_mappings, key=lambda item: item.source_parameter_id)),
        tuple(sorted(unsupported_feature_ids)),
        tuple(sorted(unsupported_parameter_ids)),
        False,
    )


def _validate_coverage(
    source_ids: set[str], mapped_ids: set[str], unsupported_ids: set[str], kind: str
) -> None:
    if mapped_ids & unsupported_ids:
        raise FamilyConversionError(f"family_conversion_{kind}_mapped_and_unsupported")
    if mapped_ids | unsupported_ids != source_ids:
        raise FamilyConversionError(f"family_conversion_{kind}_coverage_incomplete")


def _tuple_of(value: object, item_type: type, field: str) -> None:
    if not isinstance(value, tuple) or any(not isinstance(item, item_type) for item in value):
        raise FamilyConversionError(f"family_conversion_{field}_must_be_tuple")


def _unique_ids(value: object, field: str) -> None:
    if not isinstance(value, tuple) or any(not isinstance(item, str) or not item for item in value):
        raise FamilyConversionError(f"family_conversion_{field}_invalid")
    if len(value) != len(set(value)):
        raise FamilyConversionError(f"family_conversion_{field}_duplicate")


def _parameter_id(value: str) -> None:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise FamilyConversionError("family_conversion_parameter_id_invalid")


__all__ = [
    "FamilyConversionError",
    "FamilyConversionResult",
    "FeatureSemanticMapping",
    "ParameterSemanticMapping",
    "convert_package_family",
]
