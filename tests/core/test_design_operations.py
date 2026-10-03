from __future__ import annotations

import hashlib

import pytest

from packlab_core.cross_section import circle_section
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.design_operations import (
    DesignOperationError,
    LoftSectionInput,
    OperationKind,
    create_loft_operation,
    create_revolve_operation,
)
from packlab_core.design_profile import ProfilePoint, create_design_profile
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _model():
    scan_id = f"scan-master:{hashlib.sha256(b'parent').hexdigest()}"
    binding = bind_design_model_parent(
        ScanMasterRevision(
            scan_id,
            PROJECT,
            MESH,
            {
                "scan_master_revision_id": scan_id,
                "project_id": PROJECT,
                "authority_class": "SCAN_MASTER",
                "output_geometry_sha256": mesh_sha256(MESH),
                "reconstruction_revision_id": "reconstruction-r1",
                "scale_state": ScaleState.METRIC_UNVERIFIED.value,
                "scale_provenance_id": "scale-r1",
                "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
                "mold_use_authorized": False,
            },
        ),
        actor_id="operator-1",
        reason="Initial selection.",
        created_at_utc="2026-10-03T12:00:00Z",
    )
    features = tuple(
        DesignModelFeatureReference(
            stable_feature_id("container", kind, semantic),
            "container",
            kind,
            semantic,
        )
        for kind, semantic in (
            (FeatureKind.BODY, "body"),
            (FeatureKind.NECK, "axis"),
            (FeatureKind.BASE, "section-base"),
            (FeatureKind.SHOULDER, "section-shoulder"),
        )
    )
    model = create_design_model_revision(
        binding,
        package_family=PackageFamily.BOTTLE,
        features=features,
        actor_id="operator-1",
        reason="Initial operation graph.",
        created_at_utc="2026-10-03T12:30:00Z",
    )
    return model, features


def test_revolve_operation_is_deterministic_and_contains_only_parametric_truth() -> None:
    model, features = _model()
    profile = create_design_profile(
        (ProfilePoint(0.0, 5.0), ProfilePoint(100.0, 5.0)),
        ScaleState.METRIC_UNVERIFIED,
    )
    first = create_revolve_operation(
        model,
        profile,
        profile_feature_id=features[0].feature_id,
        axis_feature_id=features[1].feature_id,
    )
    repeat = create_revolve_operation(
        model,
        profile,
        profile_feature_id=features[0].feature_id,
        axis_feature_id=features[1].feature_id,
    )
    assert first.kind is OperationKind.REVOLVE
    assert first.operation_id == repeat.operation_id
    assert first.coordinate_unit == "mm_unverified"
    assert first.as_dict()["authority_class"] == "DESIGN_MODEL_OPERATION"
    assert first.as_dict()["output_geometry"] is None
    assert "mesh" not in str(first.as_dict()).lower()
    assert "cad" not in str(first.as_dict()).lower()


def test_revolve_rejects_invalid_axis_angle_units_and_stale_features() -> None:
    model, features = _model()
    profile = create_design_profile(
        (ProfilePoint(0.0, 5.0), ProfilePoint(100.0, 5.0)),
        ScaleState.METRIC_UNVERIFIED,
    )
    with pytest.raises(DesignOperationError, match="axis_direction_must_be_unit_length"):
        create_revolve_operation(
            model,
            profile,
            profile_feature_id=features[0].feature_id,
            axis_feature_id=features[1].feature_id,
            axis_direction=(0.0, 0.0, 2.0),
        )
    with pytest.raises(DesignOperationError, match="revolve_angle_out_of_range"):
        create_revolve_operation(
            model,
            profile,
            profile_feature_id=features[0].feature_id,
            axis_feature_id=features[1].feature_id,
            angle_degrees=361.0,
        )
    with pytest.raises(DesignOperationError, match="operation_feature_reference_stale_or_missing"):
        create_revolve_operation(
            model,
            profile,
            profile_feature_id="missing-feature",
            axis_feature_id=features[1].feature_id,
        )
    relative = create_design_profile(
        (ProfilePoint(0.0, 1.0), ProfilePoint(5.0, 2.0)), ScaleState.RELATIVE
    )
    with pytest.raises(DesignOperationError, match="revolve_profile_unit_mismatch"):
        create_revolve_operation(
            model,
            relative,
            profile_feature_id=features[0].feature_id,
            axis_feature_id=features[1].feature_id,
        )


def test_loft_requires_ordered_unique_sections_and_is_deterministic() -> None:
    model, features = _model()
    bottom = circle_section("container", 12.0, point_count=16)
    shoulder = circle_section("container", 8.0, point_count=16)
    sections = (
        LoftSectionInput(features[2].feature_id, bottom, 0.0),
        LoftSectionInput(features[3].feature_id, shoulder, 50.0),
    )
    first = create_loft_operation(model, sections)
    repeat = create_loft_operation(model, sections)
    assert first.kind is OperationKind.LOFT
    assert first.operation_id == repeat.operation_id
    assert first.section_positions == (0.0, 50.0)
    assert first.input_ids == (bottom.section_id, shoulder.section_id)
    with pytest.raises(DesignOperationError, match="loft_sections_must_be_strictly_ordered"):
        create_loft_operation(model, tuple(reversed(sections)))
    with pytest.raises(DesignOperationError, match="loft_section_count_out_of_range"):
        create_loft_operation(model, (sections[0],))
    topology_mismatch = (
        sections[0],
        LoftSectionInput(
            features[3].feature_id,
            circle_section("container", 8.0, point_count=20),
            50.0,
        ),
    )
    with pytest.raises(DesignOperationError, match="loft_section_topology_mismatch"):
        create_loft_operation(model, topology_mismatch)
    stale = (LoftSectionInput("missing-feature", bottom, 0.0), sections[1])
    with pytest.raises(DesignOperationError, match="operation_feature_reference_stale_or_missing"):
        create_loft_operation(model, stale)
