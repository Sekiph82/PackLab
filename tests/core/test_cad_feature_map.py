from __future__ import annotations

import importlib

from tests.core.test_jerrycan_handle_opening import _opening

from packlab_core.cad_adapter import _registered_shape_build
from packlab_core.cad_boolean import cut_design_model_feature
from packlab_core.cad_brep import _representation_from_lineage
from packlab_core.cad_feature_map import map_design_model_features_to_brep
from packlab_core.design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_standalone_design_model_revision,
    revise_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    create_standalone_design_geometry_root,
)
from packlab_core.reconstruction import ScaleState

PROJECT_ID = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
NOW = "2026-10-04T12:00:00Z"


def _model(kinds: tuple[tuple[FeatureKind, str], ...]):
    features = tuple(
        DesignModelFeatureReference(
            stable_feature_id("package", kind, semantic),
            "package",
            kind,
            semantic,
        )
        for kind, semantic in kinds
    )
    root = create_standalone_design_geometry_root(
        project_id=PROJECT_ID,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="nominal-input:cad-feature-map-fixture",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="unit-choice:mm_unverified",
        actor_id="operator-1",
        reason="Create a named CAD feature mapping fixture.",
        created_at_utc=NOW,
    )
    return create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.JERRYCAN,
        parameters=(
            DesignModelParameter(
                "nominal_extent",
                2.0,
                ParameterType.NUMBER,
                "mm_unverified",
            ),
        ),
        features=features,
        actor_id="operator-1",
        reason="Create a named CAD feature mapping fixture.",
        created_at_utc=NOW,
    )


def _representation(model, feature_ids: tuple[str, ...], operation_id: str, size: float = 2.0):
    primitive = importlib.import_module("OCP.BRepPrimAPI")
    shape = primitive.BRepPrimAPI_MakeBox(size, size, size).Shape()
    shape_build = _registered_shape_build(
        model,
        operation_id,
        feature_ids,
        shape,
        1,
    )
    return _representation_from_lineage(
        model,
        operation_id,
        feature_ids,
        shape_build,
        source_feature_ids=feature_ids,
    )


def _by_kind(mapping, kind: FeatureKind):
    return next(item for item in mapping.references if item.feature_kind == kind.value)


def test_body_neck_cap_and_handle_mappings_are_bounded_by_exact_lineage() -> None:
    model = _model(
        (
            (FeatureKind.BODY, "body-main"),
            (FeatureKind.NECK, "neck"),
            (FeatureKind.CAP, "cap"),
            (FeatureKind.HANDLE_OPENING, "handle"),
        )
    )
    by_kind = {item.feature_kind: item for item in model.features}
    body = by_kind[FeatureKind.BODY]
    neck = by_kind[FeatureKind.NECK]
    cap = by_kind[FeatureKind.CAP]
    handle = by_kind[FeatureKind.HANDLE_OPENING]

    body_mapping = map_design_model_features_to_brep(
        model, _representation(model, (body.feature_id,), "revolve-body-op")
    )
    neck_mapping = map_design_model_features_to_brep(
        model, _representation(model, (neck.feature_id,), "revolve-neck-op")
    )
    cap_mapping = map_design_model_features_to_brep(
        model, _representation(model, (cap.feature_id,), "revolve-cap-op")
    )
    handle_mapping = map_design_model_features_to_brep(
        model,
        _representation(
            model,
            (body.feature_id, handle.feature_id),
            "cad-cut:handle-op",
        ),
    )

    assert _by_kind(body_mapping, FeatureKind.BODY).status == "MAPPED"
    assert _by_kind(body_mapping, FeatureKind.BODY).target_selector == "whole_output_solid"
    assert _by_kind(neck_mapping, FeatureKind.NECK).status == "MAPPED"
    assert _by_kind(cap_mapping, FeatureKind.CAP).status == "MAPPED"
    handle_reference = _by_kind(handle_mapping, FeatureKind.HANDLE_OPENING)
    assert handle_reference.status == "MAPPED_COARSE"
    assert handle_reference.target_selector == "boolean_result_solid"
    assert handle_reference.reference_scope == "modifier_operation_result"


def test_ambiguous_shared_solid_and_unresolved_features_are_explicit() -> None:
    model = _model(
        (
            (FeatureKind.BODY, "body-main"),
            (FeatureKind.NECK, "neck"),
            (FeatureKind.CAP, "cap"),
        )
    )
    representation = _representation(
        model,
        tuple(item.feature_id for item in model.features),
        "loft-shared-solid-op",
    )
    mapping = map_design_model_features_to_brep(model, representation)

    assert all(item.status == "AMBIGUOUS" for item in mapping.references)
    assert all(
        "multiple_features_share_one_output_solid" in item.evidence_codes
        for item in mapping.references
    )
    assert mapping.as_dict()["preview_indices_used"] is False
    assert mapping.as_dict()["native_topology_hashes_used_as_authority"] is False
    assert mapping.as_dict()["universal_topological_identity_claimed"] is False

    absent_lineage = _representation(model, (model.features[0].feature_id,), "body-only-op")
    unresolved = map_design_model_features_to_brep(model, absent_lineage)
    assert _by_kind(unresolved, FeatureKind.NECK).status == "UNRESOLVED"
    assert _by_kind(unresolved, FeatureKind.CAP).evidence_codes == (
        "feature_not_in_source_operation_lineage",
    )


def test_topology_contributor_change_invalidates_prior_unique_mapping() -> None:
    model = _model(((FeatureKind.BODY, "body-main"),))
    initial_feature = model.features[0]
    initial = map_design_model_features_to_brep(
        model,
        _representation(model, (initial_feature.feature_id,), "body-op-r1"),
    )
    extra_feature = DesignModelFeatureReference(
        stable_feature_id("package", FeatureKind.BODY, "body-insert"),
        "package",
        FeatureKind.BODY,
        "body-insert",
    )
    changed_model = revise_design_model_revision(
        model,
        parameters=model.parameters,
        features=(*model.features, extra_feature),
        actor_id="operator-1",
        reason="Add a second named body contributor during topology regeneration.",
        created_at_utc="2026-10-04T12:02:00Z",
    )
    changed = map_design_model_features_to_brep(
        changed_model,
        _representation(
            changed_model,
            (initial_feature.feature_id, extra_feature.feature_id),
            "loft-op-r2",
        ),
    )

    assert initial.references[0].status == "MAPPED"
    assert (
        next(
            item for item in changed.references if item.feature_id == initial_feature.feature_id
        ).status
        == "AMBIGUOUS"
    )
    assert (
        next(
            item for item in changed.references if item.feature_id == initial_feature.feature_id
        ).named_reference_id
        == initial.references[0].named_reference_id
    )


def test_ordinary_parameter_regeneration_preserves_named_reference_id() -> None:
    model = _model(((FeatureKind.BODY, "body-main"),))
    regenerated_model = revise_design_model_revision(
        model,
        parameters=(
            DesignModelParameter(
                "nominal_extent",
                2.5,
                ParameterType.NUMBER,
                "mm_unverified",
            ),
        ),
        features=model.features,
        actor_id="operator-1",
        reason="Regenerate the same named body at updated parameters.",
        created_at_utc="2026-10-04T12:01:00Z",
    )
    original_mapping = map_design_model_features_to_brep(
        model, _representation(model, (model.features[0].feature_id,), "body-op-r1", 2.0)
    )
    regenerated_mapping = map_design_model_features_to_brep(
        regenerated_model,
        _representation(
            regenerated_model,
            (regenerated_model.features[0].feature_id,),
            "body-op-r2",
            2.5,
        ),
    )

    assert original_mapping.references[0].named_reference_id == (
        regenerated_mapping.references[0].named_reference_id
    )
    assert original_mapping.revision_id != regenerated_mapping.revision_id
    assert regenerated_mapping.source_design_model_revision_id == regenerated_model.revision_id


def test_boolean_result_lineage_retains_handle_reference_without_face_claim() -> None:
    _scan, base_model, _detection, model, handle = _opening()
    box = importlib.import_module("OCP.BRepPrimAPI").BRepPrimAPI_MakeBox(1.0, 4.0, 8.0).Shape()
    shape_build = _registered_shape_build(
        base_model,
        "test-parent-brep",
        (base_model.features[0].feature_id,),
        box,
        1,
    )
    from packlab_core.cad_brep import _representation_from_lineage

    parent = _representation_from_lineage(
        base_model,
        "test-parent-brep",
        (base_model.features[0].feature_id,),
        shape_build,
    )
    boolean = cut_design_model_feature(model, parent, handle.feature_id)
    assert boolean.representation is not None
    assert boolean.representation.source_feature_ids == (
        handle.feature_id,
        base_model.features[0].feature_id,
    )

    mapping = map_design_model_features_to_brep(model, boolean.representation)
    mapped_handle = next(
        item for item in mapping.references if item.feature_id == handle.feature_id
    )

    assert handle.feature_id in mapping.source_feature_ids
    assert mapped_handle.status == "MAPPED_COARSE"
    assert mapped_handle.target_selector == "boolean_result_solid"
    assert mapped_handle.target_subshape_type == "SOLID"
