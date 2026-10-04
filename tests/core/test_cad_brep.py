from __future__ import annotations

import hashlib
import typing

import pytest

from packlab_core.cad_adapter import _polygon_self_intersects, _shape_for_handle
from packlab_core.cad_brep import (
    CadBrepError,
    CadBrepRepresentationRevision,
    revolve_design_model_to_brep,
)
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_design_model_revision,
    create_standalone_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    bind_design_model_parent,
    create_standalone_design_geometry_root,
)
from packlab_core.design_operations import create_revolve_operation
from packlab_core.design_profile import (
    DesignProfile,
    ProfilePoint,
    ProfileSample,
    create_design_profile,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT_ID = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
NOW = "2026-10-04T12:00:00Z"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _features() -> tuple[DesignModelFeatureReference, DesignModelFeatureReference]:
    profile = DesignModelFeatureReference(
        stable_feature_id("bottle", FeatureKind.BODY, "body-profile"),
        "bottle",
        FeatureKind.BODY,
        "body-profile",
    )
    axis = DesignModelFeatureReference(
        stable_feature_id("bottle", FeatureKind.BODY, "revolve-axis"),
        "bottle",
        FeatureKind.BODY,
        "revolve-axis",
    )
    return profile, axis


def _model(scale_state: ScaleState, parent_mode: str, label: str = "cad-brep-fixture"):
    features = _features()
    if parent_mode == "standalone":
        unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
        root = create_standalone_design_geometry_root(
            project_id=PROJECT_ID,
            source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
            source_provenance_id=f"nominal-input:{label}",
            scale_state=scale_state,
            unit_provenance_id=f"unit-choice:{unit}",
            actor_id="operator-1",
            reason=f"Create a BREP test model: {label}.",
            created_at_utc=NOW,
        )
        return create_standalone_design_model_revision(
            root,
            package_family=PackageFamily.BOTTLE,
            features=features,
            actor_id="operator-1",
            reason=f"Create a BREP test model: {label}.",
            created_at_utc=NOW,
        )
    scan_id = f"scan-master:{hashlib.sha256(scale_state.value.encode()).hexdigest()}"
    scan = ScanMasterRevision(
        scan_id,
        PROJECT_ID,
        MESH,
        {
            "scan_master_revision_id": scan_id,
            "project_id": PROJECT_ID,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(MESH),
            "reconstruction_revision_id": "reconstruction:cad-brep-fixture",
            "scale_state": scale_state.value,
            "scale_provenance_id": "scale-provenance:cad-brep-fixture",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    parent = bind_design_model_parent(
        scan,
        actor_id="operator-1",
        reason="Bind BREP test model to captured authority.",
        created_at_utc=NOW,
    )
    return create_design_model_revision(
        parent,
        package_family=PackageFamily.BOTTLE,
        features=features,
        actor_id="operator-1",
        reason="Create a BREP test model.",
        created_at_utc=NOW,
    )


def _inputs(scale_state: ScaleState, parent_mode: str = "standalone"):
    model = _model(scale_state, parent_mode)
    profile = create_design_profile((ProfilePoint(0.0, 5.0), ProfilePoint(100.0, 5.0)), scale_state)
    operation = create_revolve_operation(
        model,
        profile,
        profile_feature_id=model.features[0].feature_id,
        axis_feature_id=model.features[1].feature_id,
    )
    return model, profile, operation


def test_cylinder_revolve_builds_one_deterministic_brep_solid() -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    original_model = model.as_dict()

    first = revolve_design_model_to_brep(model, profile, operation)
    second = revolve_design_model_to_brep(model, profile, operation)

    assert first.solid_count == 1
    assert first.geometry_sha256 == second.geometry_sha256
    assert first.revision_id == second.revision_id
    assert first.shape_handle.handle_id == second.shape_handle.handle_id
    assert not _shape_for_handle(first.shape_handle).IsNull()
    assert model.as_dict() == original_model
    assert first.as_dict()["authority_class"] == "DERIVED_CAD_BREP"
    assert first.as_dict()["scan_master_promoted"] is False
    assert first.as_dict()["design_model_replaced"] is False
    assert first.as_dict()["profile_sampling"] == {
        "method": "uniform_axial_samples_closed_to_revolve_axis",
        "sample_count": 257,
    }
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.coordinate_unit == "mm_unverified"
    assert first.mold_use_authorized is False


@pytest.mark.parametrize(
    ("parent_mode", "scale_state", "expected_unit", "parent_kind"),
    [
        ("captured", ScaleState.RELATIVE, "reconstruction_units", "CAPTURED_SCAN_MASTER"),
        ("captured", ScaleState.METRIC_UNVERIFIED, "mm_unverified", "CAPTURED_SCAN_MASTER"),
        (
            "standalone",
            ScaleState.RELATIVE,
            "reconstruction_units",
            "STANDALONE_DESIGN_GEOMETRY",
        ),
        (
            "standalone",
            ScaleState.METRIC_UNVERIFIED,
            "mm_unverified",
            "STANDALONE_DESIGN_GEOMETRY",
        ),
    ],
)
def test_brep_revision_preserves_parent_mode_and_unit(
    parent_mode: str, scale_state: ScaleState, expected_unit: str, parent_kind: str
) -> None:
    model, profile, operation = _inputs(scale_state, parent_mode)

    revision = revolve_design_model_to_brep(model, profile, operation)

    metadata = revision.as_dict()
    assert metadata["parent_authority"]["kind"] == parent_kind
    assert revision.source_design_model_revision_id == model.revision_id
    assert revision.parent_authority_revision_id == (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    assert revision.scale_state is scale_state
    assert revision.coordinate_unit == expected_unit
    assert revision.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert revision.mold_use_authorized is False


def test_revolve_rejects_stale_model_partial_sweep_and_unit_mismatch() -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    other_model = _model(ScaleState.METRIC_UNVERIFIED, "standalone", "different-model")
    other_profile = create_design_profile(
        (ProfilePoint(0.0, 2.0), ProfilePoint(100.0, 5.0)), ScaleState.METRIC_UNVERIFIED
    )
    partial = create_revolve_operation(
        model,
        profile,
        profile_feature_id=model.features[0].feature_id,
        axis_feature_id=model.features[1].feature_id,
        angle_degrees=180.0,
    )

    with pytest.raises(CadBrepError, match="model_profile_or_authority_mismatch"):
        revolve_design_model_to_brep(other_model, profile, operation)
    with pytest.raises(CadBrepError, match="model_profile_or_authority_mismatch"):
        revolve_design_model_to_brep(model, other_profile, operation)
    with pytest.raises(CadBrepError, match="closed_full_revolution_required"):
        revolve_design_model_to_brep(model, profile, partial)


@pytest.mark.parametrize(
    "points",
    [
        (ProfilePoint(0.0, 0.0), ProfilePoint(100.0, 0.0)),
        (ProfilePoint(0.0, 5.0), ProfilePoint(50.0, 0.0), ProfilePoint(100.0, 5.0)),
    ],
)
def test_degenerate_or_interior_axis_touching_profile_is_rejected(points) -> None:
    model = _model(ScaleState.METRIC_UNVERIFIED, "standalone")
    profile = create_design_profile(points, ScaleState.METRIC_UNVERIFIED)
    operation = create_revolve_operation(
        model,
        profile,
        profile_feature_id=model.features[0].feature_id,
        axis_feature_id=model.features[1].feature_id,
    )

    with pytest.raises(CadBrepError):
        revolve_design_model_to_brep(model, profile, operation)


def test_self_intersecting_profile_boundary_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    crossing_samples = tuple(
        ProfileSample(axial, radius, index / 3)
        for index, (axial, radius) in enumerate(((0.0, 2.0), (4.0, 4.0), (0.0, 4.0), (4.0, 2.0)))
    )
    monkeypatch.setattr(DesignProfile, "sample", lambda self, count: crossing_samples)

    with pytest.raises(CadBrepError, match="simple_closed_region"):
        revolve_design_model_to_brep(model, profile, operation)

    assert _polygon_self_intersects([(0.0, 2.0), (4.0, 4.0), (0.0, 4.0), (4.0, 2.0)])


def test_operation_feature_references_and_public_contracts_are_packlab_owned() -> None:
    model, profile, operation = _inputs(ScaleState.RELATIVE)
    revision = revolve_design_model_to_brep(model, profile, operation)

    assert set(operation.parent_feature_ids) == {item.feature_id for item in model.features}
    assert isinstance(revision, CadBrepRepresentationRevision)
    assert "OCP" not in str(typing.get_type_hints(CadBrepRepresentationRevision))
    assert "OCP" not in str(typing.get_type_hints(revolve_design_model_to_brep))
    assert "OCP" not in str(revision.as_dict())
