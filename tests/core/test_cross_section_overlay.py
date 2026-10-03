from __future__ import annotations

import hashlib

import pytest

from packlab_core.cross_section_overlay import (
    CanonicalAxis,
    CanonicalPlaneSelection,
    CrossSectionOverlayError,
    compare_scan_design_cross_sections,
    serialize_cross_section_overlay,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_design_heatmap import DesignModelGeometryReference
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "f3343d5e-bf9c-44ab-b519-bbdfca5401a0"
SCAN_ID = "scan-master-section-fixture-r1"
FRAME = "packlab-normalized-frame-v1"
PROVENANCE = "scale-provenance-section-fixture-r1"
PLANE = CanonicalPlaneSelection(CanonicalAxis.X, 0.5)


def _cube(y_offset: float = 0.0) -> TriangleMeshData:
    vertices = (
        (0.0, y_offset, 0.0),
        (1.0, y_offset, 0.0),
        (1.0, y_offset + 1.0, 0.0),
        (0.0, y_offset + 1.0, 0.0),
        (0.0, y_offset, 1.0),
        (1.0, y_offset, 1.0),
        (1.0, y_offset + 1.0, 1.0),
        (0.0, y_offset + 1.0, 1.0),
    )
    triangles = (
        (0, 2, 1),
        (0, 3, 2),
        (4, 5, 6),
        (4, 6, 7),
        (0, 1, 5),
        (0, 5, 4),
        (1, 2, 6),
        (1, 6, 5),
        (2, 3, 7),
        (2, 7, 6),
        (3, 0, 4),
        (3, 4, 7),
    )
    return TriangleMeshData(vertices, triangles)


def _scan(mesh: TriangleMeshData, *, scale: ScaleState = ScaleState.METRIC_UNVERIFIED):
    raw_digest = hashlib.sha256(b"synthetic observed section evidence").hexdigest()
    state = scale.value
    manifest = {
        "scan_master_revision_id": SCAN_ID,
        "authority_class": "SCAN_MASTER",
        "scale_state": state,
        "scale_provenance_id": PROVENANCE,
        "scale_provenance": {"provenance_id": PROVENANCE, "scale_state": state},
        "project_id": PROJECT,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "output_geometry_sha256": mesh_sha256(mesh),
        "raw_capture_revision_id": "raw-capture-section-r1",
        "raw_capture_sha256": raw_digest,
        "parent_object_geometry_source_input_digest": raw_digest,
        "reconstruction_revision_id": "reconstruction-section-r1",
        "object_geometry_revision_id": "object-geometry-section-r1",
        "parent_object_geometry_revision_id": "object-geometry-section-r1",
        "alignment_transform": {
            "transform": {
                "target_frame": FRAME,
                "reconstruction_revision": "reconstruction-section-r1",
            },
            "parents": {"object_capture_geometry_id": "object-geometry-section-r1"},
        },
    }
    return ScanMasterRevision(SCAN_ID, PROJECT, mesh, manifest)


def _design(mesh: TriangleMeshData, *, parent: str = SCAN_ID, scale=ScaleState.METRIC_UNVERIFIED):
    return DesignModelGeometryReference(
        "design-model-section-fixture-r1",
        PROJECT,
        parent,
        mesh,
        mesh_sha256(mesh),
        FRAME,
        scale,
        PROVENANCE,
    )


def test_matching_and_offset_profiles_bind_parents_plane_and_deviation() -> None:
    scan = _scan(_cube())
    matching = compare_scan_design_cross_sections(scan, _design(_cube()), PLANE)
    repeat = compare_scan_design_cross_sections(scan, _design(_cube()), PLANE)
    assert matching.overlay_id == repeat.overlay_id
    assert matching.scan_master_section.segments == matching.design_model_section.segments
    assert matching.scan_to_design.maximum == pytest.approx(0.0)
    assert matching.design_to_scan.maximum == pytest.approx(0.0)

    offset = compare_scan_design_cross_sections(scan, _design(_cube(0.2)), PLANE)
    assert offset.scan_to_design.maximum == pytest.approx(0.2, abs=1e-12)
    assert offset.design_to_scan.maximum == pytest.approx(0.2, abs=1e-12)
    record = offset.as_dict()
    assert record["plane"] == {
        "kind": "canonical_axis_plane",
        "axis": "x",
        "position": 0.5,
        "u_axis": "y",
        "v_axis": "z",
        "units": "mm_unverified",
    }
    assert record["parents"]["design_model_fitted_to_scan_master_revision_id"] == SCAN_ID
    assert record["deviation_summary"]["is_manufacturing_tolerance"] is False
    assert serialize_cross_section_overlay(offset) == serialize_cross_section_overlay(
        compare_scan_design_cross_sections(scan, _design(_cube(0.2)), PLANE)
    )


def test_open_surface_section_does_not_close_or_invent_missing_geometry() -> None:
    open_mesh = TriangleMeshData(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 1.0)),
        ((0, 1, 2),),
    )
    plane = CanonicalPlaneSelection(CanonicalAxis.X, 0.5)
    result = compare_scan_design_cross_sections(_scan(open_mesh), _design(open_mesh), plane)
    record = result.as_dict()
    assert len(result.scan_master_section.segments) == 1
    assert record["closure_invented"] is False
    assert record["sections"]["scan_master"]["closure_invented"] is False
    assert record["captured_evidence_interpolated"] is False
    assert record["surface_interpolation"] == (
        "linear_intersection_with_existing_mesh_triangles_only"
    )


def test_missing_sections_stale_parent_and_plane_selection_fail_closed() -> None:
    scan = _scan(_cube())
    with pytest.raises(CrossSectionOverlayError, match="selected_plane_has_no_mesh_section"):
        compare_scan_design_cross_sections(
            scan, _design(_cube()), CanonicalPlaneSelection(CanonicalAxis.X, 2.0)
        )
    with pytest.raises(CrossSectionOverlayError, match="design_model_parent_stale"):
        compare_scan_design_cross_sections(scan, _design(_cube(), parent="older-scan-r0"), PLANE)
    with pytest.raises(CrossSectionOverlayError, match="scan_master_mesh_evidence_empty"):
        compare_scan_design_cross_sections(_scan(TriangleMeshData((), ())), _design(_cube()), PLANE)
    with pytest.raises(CrossSectionOverlayError, match="canonical_plane_position_must_be_finite"):
        CanonicalPlaneSelection(CanonicalAxis.Z, float("nan"))


def test_scale_unit_propagation_relative_state_and_authority_limits() -> None:
    relative_scan = _scan(_cube(), scale=ScaleState.RELATIVE)
    relative = compare_scan_design_cross_sections(
        relative_scan,
        _design(_cube(), scale=ScaleState.RELATIVE),
        PLANE,
    )
    record = relative.as_dict()
    assert relative.scale_state is ScaleState.RELATIVE
    assert record["scale"]["coordinate_unit"] == "reconstruction_units"
    assert record["scale"]["physical_accuracy_validation_status"] == ("DEFERRED_OWNER_VALIDATION")
    assert record["scale"]["mold_use_authorized"] is False
    with pytest.raises(CrossSectionOverlayError, match="design_model_coordinate_or_scale_mismatch"):
        compare_scan_design_cross_sections(
            _scan(_cube()), _design(_cube(), scale=ScaleState.RELATIVE), PLANE
        )
