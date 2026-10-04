from __future__ import annotations

import pytest

from packlab_core.design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelParentKind,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_design_model_revision,
    create_standalone_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    bind_design_model_parent,
    create_standalone_design_geometry_root,
)
from packlab_core.family_conversion import (
    FamilyConversionError,
    FeatureSemanticMapping,
    ParameterSemanticMapping,
    convert_package_family,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "family-conversion-project"
NOW = "2026-10-04T12:00:00Z"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _features():
    specifications = (
        ("body", FeatureKind.BODY, "bottle:body:v1"),
        ("neck", FeatureKind.NECK, "bottle:neck:v1"),
        ("cap", FeatureKind.CAP, "bottle:cap:v1"),
    )
    return tuple(
        DesignModelFeatureReference(
            stable_feature_id("bottle-main", kind, semantic),
            "bottle-main",
            kind,
            semantic,
        )
        for _name, kind, semantic in specifications
    )


def _standalone_model():
    root = create_standalone_design_geometry_root(
        project_id=PROJECT,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="nominal-input:conversion-fixture",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="unit-selection:mm-unverified",
        actor_id="operator-1",
        reason="Create source bottle-design root.",
        created_at_utc=NOW,
    )
    return create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.BOTTLE,
        parameters=(
            DesignModelParameter("body_width", 30.0, ParameterType.NUMBER, "mm_unverified"),
            DesignModelParameter("body_height", 80.0, ParameterType.NUMBER, "mm_unverified"),
            DesignModelParameter("cap_diameter", 20.0, ParameterType.NUMBER, "mm_unverified"),
        ),
        features=_features(),
        actor_id="operator-1",
        reason="Create a standalone source family.",
        created_at_utc=NOW,
    )


def _captured_model():
    scan_id = "scan-master:family-conversion-fixture"
    scan = ScanMasterRevision(
        scan_id,
        PROJECT,
        MESH,
        {
            "scan_master_revision_id": scan_id,
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(MESH),
            "reconstruction_revision_id": "reconstruction:family-conversion-fixture",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-provenance:family-conversion-fixture",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    parent = bind_design_model_parent(
        scan,
        actor_id="operator-1",
        reason="Select exact source Scan Master.",
        created_at_utc=NOW,
    )
    return create_design_model_revision(
        parent,
        package_family=PackageFamily.TUBE,
        parameters=(
            DesignModelParameter("body_width", 30.0, ParameterType.NUMBER, "mm_unverified"),
            DesignModelParameter("body_height", 80.0, ParameterType.NUMBER, "mm_unverified"),
        ),
        features=_features()[:2],
        actor_id="operator-1",
        reason="Create a captured source family.",
        created_at_utc=NOW,
    )


def _mappings(model, target_prefix="jerrycan"):
    by_semantic = {item.semantic_key: item for item in model.features}
    body = by_semantic["bottle:body:v1"]
    neck = by_semantic["bottle:neck:v1"]
    return (
        (
            FeatureSemanticMapping(
                body.feature_id,
                f"{target_prefix}-main",
                FeatureKind.BODY,
                f"{target_prefix}:body:v1",
            ),
            FeatureSemanticMapping(
                neck.feature_id,
                f"{target_prefix}-main",
                FeatureKind.NECK,
                f"{target_prefix}:neck:v1",
            ),
        ),
        (
            ParameterSemanticMapping("body_width", "jerrycan_body_width"),
            ParameterSemanticMapping("body_height", "jerrycan_body_height"),
        ),
    )


def test_same_family_conversion_is_noop_and_preserves_exact_revision():
    source = _standalone_model()
    result = convert_package_family(
        source,
        source.package_family,
        actor_id="operator-1",
        reason="Same-family conversion request.",
        created_at_utc=NOW,
    )
    assert result.no_op is True
    assert result.converted_model is source
    assert result.conversion_revision_id == source.revision_id
    assert source.previous_revision_id is None


def test_explicit_semantic_conversion_reports_unsupported_items_and_preserves_source():
    source = _standalone_model()
    original_payload = source.as_dict()
    feature_mappings, parameter_mappings = _mappings(source)
    unsupported_features = tuple(
        sorted(
            {item.feature_id for item in source.features}
            - {item.source_feature_id for item in feature_mappings}
        )
    )
    unsupported_parameters = ("cap_diameter",)
    result = convert_package_family(
        source,
        PackageFamily.JERRYCAN,
        feature_mappings=feature_mappings,
        parameter_mappings=parameter_mappings,
        unsupported_feature_ids=unsupported_features,
        unsupported_parameter_ids=unsupported_parameters,
        actor_id="operator-1",
        reason="Map bottle body and neck semantics into a jerrycan family.",
        created_at_utc="2026-10-04T12:01:00Z",
    )
    report = result.as_dict()
    assert result.no_op is False
    assert result.converted_model.revision_id != source.revision_id
    assert result.converted_model.previous_revision_id == source.revision_id
    assert result.converted_model.package_family is PackageFamily.JERRYCAN
    assert source.as_dict() == original_payload
    assert result.converted_model.standalone_root == source.standalone_root
    assert result.converted_model.parent_kind is DesignModelParentKind.STANDALONE_DESIGN_GEOMETRY
    assert result.converted_model.fitted_to_scan_master_revision_id is None
    assert result.converted_model.scan_master_geometry_sha256 is None
    assert report["unsupported_feature_ids"] == list(unsupported_features)
    assert report["unsupported_parameter_ids"] == ["cap_diameter"]
    assert report["unsupported_items_dropped_explicitly"] is True
    assert [item.parameter_id for item in result.converted_model.parameters] == [
        "jerrycan_body_height",
        "jerrycan_body_width",
    ]


def test_captured_conversion_preserves_exact_parent_and_is_deterministic():
    source = _captured_model()
    feature_mappings, parameter_mappings = _mappings(source, "flexible-pack")
    options = {
        "feature_mappings": feature_mappings,
        "parameter_mappings": parameter_mappings,
        "actor_id": "operator-1",
        "reason": "Convert mapped tube family to jerrycan family.",
        "created_at_utc": "2026-10-04T12:01:00Z",
    }
    first = convert_package_family(source, PackageFamily.FLEXIBLE_PACK, **options)
    second = convert_package_family(source, PackageFamily.FLEXIBLE_PACK, **options)

    assert first.conversion_revision_id == second.conversion_revision_id
    assert first.converted_model.parent_kind is DesignModelParentKind.CAPTURED_SCAN_MASTER
    assert first.converted_model.parent_binding_revision_id == source.parent_binding_revision_id
    assert (
        first.converted_model.fitted_to_scan_master_revision_id
        == source.fitted_to_scan_master_revision_id
    )
    assert first.converted_model.scan_master_geometry_sha256 == source.scan_master_geometry_sha256
    assert first.converted_model.scale_provenance_id == source.scale_provenance_id
    assert first.converted_model.previous_revision_id == source.revision_id
    assert first.converted_model.package_family is PackageFamily.FLEXIBLE_PACK
    assert (
        first.as_dict()["parent_authority"]["scan_master_revision_id"]
        == source.fitted_to_scan_master_revision_id
    )  # type: ignore[index]


def test_cross_authority_conversion_and_unreported_feature_loss_reject():
    source = _standalone_model()
    mappings, parameter_mappings = _mappings(source)
    with pytest.raises(
        FamilyConversionError, match="family_conversion_cross_authority_rebind_forbidden"
    ):
        convert_package_family(
            source,
            PackageFamily.JERRYCAN,
            feature_mappings=mappings,
            parameter_mappings=parameter_mappings,
            unsupported_feature_ids=tuple(
                sorted(
                    {item.feature_id for item in source.features}
                    - {item.source_feature_id for item in mappings}
                )
            ),
            unsupported_parameter_ids=("cap_diameter",),
            target_parent_kind=DesignModelParentKind.CAPTURED_SCAN_MASTER,
            actor_id="operator-1",
            reason="A parent authority switch must be rejected.",
            created_at_utc="2026-10-04T12:01:00Z",
        )
    with pytest.raises(
        FamilyConversionError, match="family_conversion_feature_coverage_incomplete"
    ):
        convert_package_family(
            source,
            PackageFamily.JERRYCAN,
            feature_mappings=mappings,
            parameter_mappings=parameter_mappings,
            unsupported_parameter_ids=("cap_diameter",),
            actor_id="operator-1",
            reason="An omitted feature requires an explicit unsupported report.",
            created_at_utc="2026-10-04T12:01:00Z",
        )
