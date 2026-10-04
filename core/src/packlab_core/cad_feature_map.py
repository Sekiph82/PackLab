"""Conservative, lineage-bound named references for regenerated CAD solids."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .cad_brep import CadBrepRepresentationRevision
from .design_model import DesignModelRevision, FeatureKind


class CadFeatureMappingError(ValueError):
    """Raised when feature mapping inputs do not share exact model/BREP provenance."""


@dataclass(frozen=True, slots=True)
class CadNamedFeatureReference:
    feature_id: str
    feature_kind: str
    semantic_key: str
    status: str
    named_reference_id: str
    target_subshape_type: str | None
    target_selector: str | None
    reference_scope: str
    evidence_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "feature_id": self.feature_id,
            "feature_kind": self.feature_kind,
            "semantic_key": self.semantic_key,
            "status": self.status,
            "named_reference_id": self.named_reference_id,
            "target_subshape_type": self.target_subshape_type,
            "target_selector": self.target_selector,
            "reference_scope": self.reference_scope,
            "evidence_codes": list(self.evidence_codes),
        }


@dataclass(frozen=True, slots=True)
class CadFeatureMappingRevision:
    revision_id: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_operation_id: str
    source_feature_ids: tuple[str, ...]
    references: tuple[CadNamedFeatureReference, ...]
    parent_kind: str
    parent_authority_revision_id: str
    scale_state: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.cad-feature-mapping.v1",
            "authority_class": "CAD_FEATURE_REFERENCE_DIAGNOSTIC",
            "revision_id": self.revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_operation_id": self.source_operation_id,
            "source_feature_ids": list(self.source_feature_ids),
            "references": [item.as_dict() for item in self.references],
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "preview_indices_used": False,
            "native_topology_hashes_used_as_authority": False,
            "universal_topological_identity_claimed": False,
        }


def map_design_model_features_to_brep(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
) -> CadFeatureMappingRevision:
    """Resolve only feature references supported by exact operation lineage.

    Whole-solid targets are deliberately coarse. Multiple same-output contributors
    remain ambiguous, and modifier features are never promoted to face identity.
    """
    if not isinstance(model, DesignModelRevision):
        raise CadFeatureMappingError("design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise CadFeatureMappingError("cad_brep_representation_required")
    if (
        representation.source_design_model_revision_id != model.revision_id
        or representation.parent_kind is not model.parent_kind
        or representation.parent_authority_revision_id
        != (
            model.standalone_root.revision_id
            if model.standalone_root
            else model.parent_binding_revision_id
        )
        or representation.scale_state is not model.scale_state
        or representation.coordinate_unit != model.coordinate_unit
        or representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or representation.mold_use_authorized
    ):
        raise CadFeatureMappingError("cad_feature_mapping_model_or_authority_mismatch")
    features = {item.feature_id: item for item in model.features}
    if any(feature_id not in features for feature_id in representation.source_feature_ids):
        raise CadFeatureMappingError("cad_feature_mapping_lineage_feature_stale")

    participating = tuple(
        features[feature_id]
        for feature_id in representation.source_feature_ids
        if feature_id in features
    )
    whole_solid_contributors = tuple(
        item
        for item in participating
        if item.feature_kind in {FeatureKind.BODY, FeatureKind.NECK, FeatureKind.CAP}
    )
    modifier_features = tuple(
        item
        for item in participating
        if item.feature_kind in {FeatureKind.HANDLE_OPENING, FeatureKind.GRIP_INDENT}
    )
    references: list[CadNamedFeatureReference] = []
    for feature in model.features:
        if feature.feature_id not in representation.source_feature_ids:
            references.append(
                _reference(
                    feature.feature_id,
                    feature.feature_kind.value,
                    feature.semantic_key,
                    "UNRESOLVED",
                    None,
                    None,
                    "none",
                    ("feature_not_in_source_operation_lineage",),
                )
            )
            continue
        if feature.feature_kind in {FeatureKind.BODY, FeatureKind.NECK, FeatureKind.CAP}:
            if representation.solid_count != 1:
                references.append(
                    _reference(
                        feature.feature_id,
                        feature.feature_kind.value,
                        feature.semantic_key,
                        "UNRESOLVED",
                        None,
                        None,
                        "none",
                        ("single_output_solid_not_available",),
                    )
                )
            elif len(whole_solid_contributors) == 1:
                references.append(
                    _reference(
                        feature.feature_id,
                        feature.feature_kind.value,
                        feature.semantic_key,
                        "MAPPED",
                        "SOLID",
                        "whole_output_solid",
                        "whole_component_solid",
                        ("exact_operation_feature_lineage", "single_output_solid"),
                    )
                )
            else:
                references.append(
                    _reference(
                        feature.feature_id,
                        feature.feature_kind.value,
                        feature.semantic_key,
                        "AMBIGUOUS",
                        None,
                        None,
                        "none",
                        ("multiple_features_share_one_output_solid",),
                    )
                )
        elif feature.feature_kind in {FeatureKind.HANDLE_OPENING, FeatureKind.GRIP_INDENT}:
            if (
                representation.source_operation_id.startswith("cad-cut:")
                and len(modifier_features) == 1
                and representation.solid_count == 1
            ):
                references.append(
                    _reference(
                        feature.feature_id,
                        feature.feature_kind.value,
                        feature.semantic_key,
                        "MAPPED_COARSE",
                        "SOLID",
                        "boolean_result_solid",
                        "modifier_operation_result",
                        ("exact_boolean_tool_feature_lineage", "result_solid_only"),
                    )
                )
            else:
                references.append(
                    _reference(
                        feature.feature_id,
                        feature.feature_kind.value,
                        feature.semantic_key,
                        "AMBIGUOUS" if len(modifier_features) > 1 else "UNRESOLVED",
                        None,
                        None,
                        "none",
                        (
                            "multiple_modifiers_share_boolean_result"
                            if len(modifier_features) > 1
                            else "feature_has_no_supported_subshape_selector",
                        ),
                    )
                )
        else:
            references.append(
                _reference(
                    feature.feature_id,
                    feature.feature_kind.value,
                    feature.semantic_key,
                    "UNRESOLVED",
                    None,
                    None,
                    "none",
                    ("feature_kind_has_no_supported_subshape_selector",),
                )
            )

    reference_tuple = tuple(references)
    payload = {
        "contract": "packlab.cad-feature-mapping.v1",
        "model_revision_id": model.revision_id,
        "brep_revision_id": representation.revision_id,
        "operation_id": representation.source_operation_id,
        "source_feature_ids": list(representation.source_feature_ids),
        "references": [item.as_dict() for item in reference_tuple],
    }
    revision_id = (
        "cad-feature-mapping:"
        + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
    )
    return CadFeatureMappingRevision(
        revision_id,
        model.revision_id,
        representation.revision_id,
        representation.source_operation_id,
        representation.source_feature_ids,
        reference_tuple,
        model.parent_kind.value,
        representation.parent_authority_revision_id,
        model.scale_state.value,
        model.coordinate_unit,
        model.physical_accuracy_validation_status,
        model.mold_use_authorized,
    )


def _reference(
    feature_id: str,
    feature_kind: str,
    semantic_key: str,
    status: str,
    target_subshape_type: str | None,
    target_selector: str | None,
    reference_scope: str,
    evidence_codes: tuple[str, ...],
) -> CadNamedFeatureReference:
    return CadNamedFeatureReference(
        feature_id,
        feature_kind,
        semantic_key,
        status,
        f"cad-feature-ref:{feature_id}",
        target_subshape_type,
        target_selector,
        reference_scope,
        evidence_codes,
    )


__all__ = [
    "CadFeatureMappingError",
    "CadFeatureMappingRevision",
    "CadNamedFeatureReference",
    "map_design_model_features_to_brep",
]
