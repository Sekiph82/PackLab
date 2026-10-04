from __future__ import annotations

from dataclasses import replace

import pytest

from packlab_core.design_deviation_report import (
    DeviationReportError,
    calculate_design_deviation_report,
)
from packlab_core.design_history import DesignModelHistory, EditTargetKind, create_edit_command
from packlab_core.design_model import (
    DesignModelParameter,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_standalone_design_model_revision,
)
from packlab_core.design_model_binding import (
    DesignModelBindingError,
    StandaloneDesignGeometrySourceKind,
    bind_design_model_parent,
    create_standalone_design_geometry_root,
)
from packlab_core.design_serialization import deserialize_design_model, serialize_design_model
from packlab_core.design_validation import DesignValidationPolicy, validate_design_model
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.tube_family import TubeFamilyDimensions, TubeFamilyError, build_tube_family

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
NOW = "2026-10-04T12:00:00Z"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _root(scale: ScaleState = ScaleState.METRIC_UNVERIFIED):
    return create_standalone_design_geometry_root(
        project_id=PROJECT,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="nominal-input:operator-session-1",
        scale_state=scale,
        unit_provenance_id="unit-selection:mm-unverified",
        actor_id="operator-1",
        reason="Start from user-authored nominal package dimensions.",
        created_at_utc=NOW,
    )


def _model(root=None):
    selected_root = _root() if root is None else root
    return create_standalone_design_model_revision(
        selected_root,
        package_family=PackageFamily.OTHER,
        parameters=(
            DesignModelParameter(
                "height", 100.0, ParameterType.NUMBER, selected_root.coordinate_unit
            ),
        ),
        actor_id="operator-1",
        reason="Initial standalone design graph.",
        created_at_utc=NOW,
    )


def _captured_parent():
    scan_id = "scan-master:tube-family-fixture"
    scan = ScanMasterRevision(
        scan_id,
        PROJECT,
        MESH,
        {
            "scan_master_revision_id": scan_id,
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(MESH),
            "reconstruction_revision_id": "reconstruction:tube-family-fixture",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-provenance:tube-family-fixture",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    return bind_design_model_parent(
        scan,
        actor_id="operator-1",
        reason="Select exact tube-family Scan Master parent.",
        created_at_utc=NOW,
    )


def test_standalone_root_is_deterministic_versioned_and_has_no_captured_ancestry() -> None:
    root = _root()
    repeat = _root()
    assert root == repeat
    assert root.revision_id == repeat.revision_id
    payload = root.as_dict()
    assert payload["authority_class"] == "STANDALONE_DESIGN_GEOMETRY"
    assert payload["captured_ancestry_exists"] is False
    assert payload["mold_use_authorized"] is False
    assert payload["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert not any("scan_master" in key or "reconstruction_revision" in key for key in payload)
    with pytest.raises(DesignModelBindingError, match="standalone_root_digest_mismatch"):
        replace(root, unit_provenance_id="unit-selection:tampered")


def test_standalone_model_round_trip_and_generic_validation_keep_authority_explicit() -> None:
    model = _model()
    encoded = serialize_design_model(model)
    restored = deserialize_design_model(encoded)
    assert restored.model == model
    assert serialize_design_model(restored.model) == encoded
    data = model.as_dict()
    assert data["contract"] == "packlab.design-model.v2"
    assert "parent_authority" in data
    assert not any("scan_master" in key or "scale_provenance" in key for key in data)
    assert validate_design_model(model).valid

    required_captured = validate_design_model(
        model,
        policy=DesignValidationPolicy(available_scan_master_revision_ids=("scan-master:one",)),
    )
    assert [issue.code for issue in required_captured.issues] == ["captured_parent_required"]


def test_standalone_history_preserves_root_through_edit_undo_and_redo() -> None:
    model = _model()
    before = model.parameters[0]
    after = DesignModelParameter("height", 120.0, ParameterType.NUMBER, before.unit)
    command = create_edit_command(
        model.revision_id, EditTargetKind.PARAMETER, "height", before, after
    )
    edited = DesignModelHistory(model).apply(
        command,
        actor_id="operator-1",
        reason="Increase nominal height.",
        created_at_utc="2026-10-04T12:01:00Z",
    )
    undone = edited.undo(actor_id="operator-1", created_at_utc="2026-10-04T12:02:00Z")
    redone = undone.redo(actor_id="operator-1", created_at_utc="2026-10-04T12:03:00Z")
    assert edited.current_revision.standalone_root == model.standalone_root
    assert undone.current_revision.standalone_root == model.standalone_root
    assert redone.current_revision.standalone_root == model.standalone_root
    assert redone.current_revision.parent_kind == model.parent_kind


def test_captured_only_deviation_service_rejects_standalone_model_before_geometry_access() -> None:
    with pytest.raises(DeviationReportError, match="captured_scan_master_parent_required"):
        calculate_design_deviation_report(
            None,  # type: ignore[arg-type]
            _model(),
            None,  # type: ignore[arg-type]
            (),
            expected_scan_master_revision_id="scan-master:one",
            expected_scan_master_geometry_sha256="0" * 64,
        )


def test_tube_family_builds_deterministic_semantic_graph_for_standalone_geometry() -> None:
    root = _root(ScaleState.RELATIVE)
    dimensions = TubeFamilyDimensions(
        body_length=90.0,
        body_diameter=35.0,
        shoulder_length=15.0,
        shoulder_diameter=22.0,
        neck_length=8.0,
        neck_diameter=10.0,
        cap_height=18.0,
        cap_diameter=12.0,
        crimp_length=5.0,
        crimp_thickness=1.5,
    )
    kwargs = {
        "component_id": "tube-component",
        "actor_id": "operator-1",
        "reason": "Create a nominal tube family preview.",
        "created_at_utc": NOW,
    }
    first = build_tube_family(root, dimensions, **kwargs)
    second = build_tube_family(root, dimensions, **kwargs)
    assert first.model == second.model
    assert first.preview == second.preview
    assert first.model.package_family is PackageFamily.TUBE
    assert {feature.feature_kind for feature in first.model.features} == {
        FeatureKind.BODY,
        FeatureKind.SHOULDER,
        FeatureKind.NECK,
        FeatureKind.CAP,
        FeatureKind.CRIMP,
    }
    assert len(first.sections) == 6
    assert first.model.standalone_root == root
    assert first.model.coordinate_unit == "reconstruction_units"
    assert first.as_dict()["mold_use_authorized"] is False
    assert first.as_dict()["flexible_wall_deformation_claimed"] is False
    assert first.as_dict()["cad_or_brep_generated"] is False
    assert first.preview.standalone_root_revision_id == root.revision_id
    assert "scan_master_revision_id" not in first.preview.as_dict()
    assert "scan_master_geometry_sha256" not in first.preview.as_dict()
    assert serialize_design_model(first.model)


def test_tube_family_uses_existing_captured_parent_path() -> None:
    dimensions = TubeFamilyDimensions(
        body_length=90.0,
        body_diameter=35.0,
        shoulder_length=15.0,
        shoulder_diameter=22.0,
        neck_length=8.0,
        neck_diameter=10.0,
        cap_height=18.0,
        cap_diameter=12.0,
        crimp_length=5.0,
        crimp_thickness=1.5,
    )
    tube = build_tube_family(
        _captured_parent(),
        dimensions,
        component_id="captured-tube",
        actor_id="operator-1",
        reason="Create scan-bound tube parametric family.",
        created_at_utc=NOW,
    )
    assert tube.model.parent_kind.value == "CAPTURED_SCAN_MASTER"
    assert tube.model.fitted_to_scan_master_revision_id == "scan-master:tube-family-fixture"
    assert tube.model.standalone_root is None
    assert tube.model.scale_provenance_id == "scale-provenance:tube-family-fixture"
    assert tube.preview.scan_master_revision_id == "scan-master:tube-family-fixture"
    assert tube.preview.standalone_root_revision_id is None
    assert "scan_master_revision_id" in tube.preview.as_dict()


def test_tube_family_rejects_impossible_dimensions() -> None:
    with pytest.raises(TubeFamilyError, match="tube_dimension_relationship_impossible"):
        TubeFamilyDimensions(
            body_length=90.0,
            body_diameter=15.0,
            shoulder_length=15.0,
            shoulder_diameter=22.0,
            neck_length=8.0,
            neck_diameter=10.0,
            cap_height=18.0,
            cap_diameter=12.0,
            crimp_length=5.0,
            crimp_thickness=1.5,
        )
