from __future__ import annotations

import hashlib
import typing

import pytest

from packlab_core.cad_adapter import _shape_for_handle
from packlab_core.cad_brep import CadBrepError, loft_design_model_to_brep
from packlab_core.cross_section import (
    CrossSectionError,
    CrossSectionSymmetry,
    SectionPoint,
    circle_section,
    create_cross_section,
    ellipse_section,
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
from packlab_core.design_operations import (
    DesignOperationError,
    LoftSectionInput,
    create_loft_operation,
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


def _rounded_jerrycan_section(z_index: int, scale_state: ScaleState, asymmetric: bool):
    shift_x = float(z_index * 2) if asymmetric else 0.0
    shift_y = float(z_index) if asymmetric else 0.0
    points = tuple(
        SectionPoint(x + shift_x, y + shift_y)
        for x, y in (
            (-30.0, -18.0),
            (24.0, -18.0),
            (32.0, -11.0),
            (32.0, 11.0),
            (24.0, 18.0),
            (-24.0, 18.0),
            (-32.0, 11.0),
            (-32.0, -11.0),
        )
    )
    return create_cross_section(
        "jerrycan",
        points,
        symmetry=CrossSectionSymmetry.NONE,
        scale_state=scale_state,
    )


def _model(scale_state: ScaleState, parent_mode: str, feature_ids: tuple[str, ...]):
    features = tuple(
        DesignModelFeatureReference(
            feature_id,
            "jerrycan",
            FeatureKind.BODY,
            f"loft-section-{index}",
        )
        for index, feature_id in enumerate(feature_ids)
    )
    if parent_mode == "standalone":
        unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
        root = create_standalone_design_geometry_root(
            project_id=PROJECT_ID,
            source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
            source_provenance_id="nominal-input:cad-loft-fixture",
            scale_state=scale_state,
            unit_provenance_id=f"unit-choice:{unit}",
            actor_id="operator-1",
            reason="Create a CAD loft fixture.",
            created_at_utc=NOW,
        )
        return create_standalone_design_model_revision(
            root,
            package_family=PackageFamily.JERRYCAN,
            features=features,
            actor_id="operator-1",
            reason="Create a CAD loft fixture.",
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
            "reconstruction_revision_id": "reconstruction:cad-loft-fixture",
            "scale_state": scale_state.value,
            "scale_provenance_id": "scale-provenance:cad-loft-fixture",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    parent = bind_design_model_parent(
        scan,
        actor_id="operator-1",
        reason="Bind CAD loft fixture to captured authority.",
        created_at_utc=NOW,
    )
    return create_design_model_revision(
        parent,
        package_family=PackageFamily.JERRYCAN,
        features=features,
        actor_id="operator-1",
        reason="Create a CAD loft fixture.",
        created_at_utc=NOW,
    )


def _loft_inputs(
    scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED,
    parent_mode: str = "standalone",
    asymmetric: bool = False,
):
    feature_ids = tuple(
        stable_feature_id("jerrycan", FeatureKind.BODY, f"loft-section-{index}")
        for index in range(3)
    )
    model = _model(scale_state, parent_mode, feature_ids)
    if asymmetric:
        sections = tuple(
            LoftSectionInput(
                feature_ids[index],
                _rounded_jerrycan_section(index, scale_state, asymmetric=True),
                float(index * 50),
            )
            for index in range(3)
        )
    else:
        sections = tuple(
            LoftSectionInput(
                feature_ids[index],
                ellipse_section(
                    "jerrycan",
                    (32.0, 34.0, 18.0)[index],
                    (20.0, 22.0, 12.0)[index],
                    point_count=16,
                    scale_state=scale_state,
                ),
                float(index * 50),
            )
            for index in range(3)
        )
    operation = create_loft_operation(model, sections)
    return model, sections, operation


def test_elliptical_jerrycan_loft_builds_one_deterministic_solid() -> None:
    model, sections, operation = _loft_inputs()
    original = model.as_dict()

    first = loft_design_model_to_brep(model, sections, operation)
    second = loft_design_model_to_brep(model, sections, operation)

    assert first.solid_count == 1
    assert first.geometry_sha256 == second.geometry_sha256
    assert first.revision_id == second.revision_id
    assert first.shape_handle.handle_id == second.shape_handle.handle_id
    assert not _shape_for_handle(first.shape_handle).IsNull()
    assert first.source_input_ids == tuple(item.section.section_id for item in sections)
    assert first.profile_sample_count is None
    assert first.as_dict()["profile_sampling"] is None
    assert model.as_dict() == original
    assert first.as_dict()["authority_class"] == "DERIVED_CAD_BREP"
    assert first.as_dict()["scan_master_promoted"] is False
    assert first.as_dict()["design_model_replaced"] is False
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.mold_use_authorized is False


def test_asymmetric_rounded_sections_and_order_are_preserved() -> None:
    model, sections, operation = _loft_inputs(asymmetric=True)

    revision = loft_design_model_to_brep(model, sections, operation)

    assert all(item.section.symmetry is CrossSectionSymmetry.NONE for item in sections)
    assert operation.input_ids == tuple(item.section.section_id for item in sections)
    assert operation.section_positions == (0.0, 50.0, 100.0)
    assert revision.source_input_ids == operation.input_ids


def test_loft_preserves_parent_modes_and_units() -> None:
    for parent_mode, scale_state, unit, kind in (
        ("captured", ScaleState.RELATIVE, "reconstruction_units", "CAPTURED_SCAN_MASTER"),
        (
            "captured",
            ScaleState.METRIC_UNVERIFIED,
            "mm_unverified",
            "CAPTURED_SCAN_MASTER",
        ),
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
    ):
        model, sections, operation = _loft_inputs(scale_state, parent_mode)
        revision = loft_design_model_to_brep(model, sections, operation)
        assert revision.coordinate_unit == unit
        assert revision.scale_state is scale_state
        assert revision.as_dict()["parent_authority"]["kind"] == kind
        assert revision.parent_authority_revision_id == (
            model.standalone_root.revision_id
            if model.standalone_root is not None
            else model.parent_binding_revision_id
        )
        assert revision.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"


def test_reordered_or_mismatched_sections_fail_closed() -> None:
    model, sections, operation = _loft_inputs()

    with pytest.raises(CadBrepError, match="inputs_stale_or_reordered"):
        loft_design_model_to_brep(model, tuple(reversed(sections)), operation)

    different_topology = circle_section("jerrycan", 10.0, point_count=12)
    mismatched = (
        sections[0],
        LoftSectionInput(sections[1].feature_id, different_topology, sections[1].axial_position),
        sections[2],
    )
    with pytest.raises(CadBrepError, match="inputs_stale_or_reordered"):
        loft_design_model_to_brep(model, mismatched, operation)

    with pytest.raises(DesignOperationError, match="section_topology_mismatch"):
        create_loft_operation(model, mismatched)


def test_invalid_section_area_is_rejected_and_missing_inputs_do_not_heal() -> None:
    with pytest.raises(CrossSectionError, match="area_degenerate"):
        create_cross_section(
            "jerrycan",
            (SectionPoint(0.0, 0.0), SectionPoint(2.0, 0.0), SectionPoint(4.0, 0.0)),
            symmetry=CrossSectionSymmetry.NONE,
        )

    model, sections, _ = _loft_inputs()
    with pytest.raises(CadBrepError, match="section_topology_orientation_or_unit_mismatch"):
        inconsistent_orientation = tuple(
            LoftSectionInput(item.feature_id, _reversed_section(item.section), item.axial_position)
            if index == 1
            else item
            for index, item in enumerate(sections)
        )
        inconsistent_operation = create_loft_operation(model, inconsistent_orientation)
        loft_design_model_to_brep(model, inconsistent_orientation, inconsistent_operation)


def _reversed_section(section):
    return create_cross_section(
        section.component_id,
        tuple(reversed(section.points)),
        symmetry=CrossSectionSymmetry.NONE,
        scale_state=section.scale_state,
    )


def test_public_loft_contracts_do_not_expose_backend_types() -> None:
    model, sections, operation = _loft_inputs()
    revision = loft_design_model_to_brep(model, sections, operation)

    assert "OCP" not in str(typing.get_type_hints(loft_design_model_to_brep))
    assert "OCP" not in str(revision.as_dict())
