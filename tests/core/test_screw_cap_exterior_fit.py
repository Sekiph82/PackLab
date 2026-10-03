from __future__ import annotations

from dataclasses import replace

import pytest
from test_closure_separation_candidates import _inputs

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.closure_separation_candidates import (
    ClosureSeparationStatus,
    create_closure_separation_candidates,
)
from packlab_core.component_cleanup import _components
from packlab_core.cross_section_measurement import CrossSectionSelection, measure_cross_section
from packlab_core.design_model import ParameterType
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import mesh_sha256
from packlab_core.screw_cap_exterior_fit import (
    ScrewCapExteriorFitStatus,
    fit_screw_cap_exterior,
)


def _inputs_with_sections():
    scan, neck_finish, fit, zones, model = _inputs()
    closure = create_closure_separation_candidates(
        scan,
        neck_finish,
        fit,
        zones,
        model,
        expected_scan_master_revision_id=scan.revision_id,
        expected_model_revision_id=model.revision_id,
        actor_id="operator-1",
        reason="Create parent-bound cap candidate.",
        created_at_utc="2026-10-03T18:01:00Z",
    )
    assert closure.model is not None
    candidate = next(item for item in closure.candidates if item.role == "closure-candidate")
    component = next(
        item
        for item in _components(scan.mesh)
        if item.component_id == candidate.source_mesh_component_id
    )
    indices = {
        z: tuple(
            sorted(
                {
                    vertex
                    for triangle_index in component.triangle_indices
                    for vertex in scan.mesh.triangles[triangle_index]
                    if scan.mesh.vertices[vertex][2] == z
                }
            )
        )
        for z in (15.0, 15.5, 16.0)
    }
    geometry = NormalizedMeasurementGeometry(
        "normalized-r1",
        "geometry-r1",
        scan.mesh.vertices,
        ScaleState.METRIC_UNVERIFIED,
        "mm_unverified",
        "scale-r1",
        0.02,
        "mm_per_reconstruction_unit",
    )
    sections = tuple(
        measure_cross_section(
            geometry,
            CrossSectionSelection(
                f"cap-z-{z:g}",
                geometry.source_geometry_id,
                geometry.normalized_geometry_revision,
                point_indices,
                (0.0, 0.0, z),
                (0.0, 0.0, 1.0),
                1e-9,
            ),
            current_geometry_id=geometry.source_geometry_id,
            current_normalized_geometry_revision=geometry.normalized_geometry_revision,
            current_scale_provenance_id=geometry.scale_provenance_id,
        )
        for z, point_indices in indices.items()
    )
    return scan, neck_finish, fit, zones, closure, sections


def _fit(scan, neck_finish, fit, zones, closure, sections):
    assert closure.model is not None
    return fit_screw_cap_exterior(
        scan,
        closure,
        neck_finish,
        fit,
        zones,
        sections,
        expected_scan_master_revision_id=scan.revision_id,
        expected_model_revision_id=closure.model.revision_id,
        actor_id="operator-1",
        reason="Fit observed cap exterior from sections.",
        created_at_utc="2026-10-03T18:02:00Z",
    )


def test_cylindrical_exterior_fit_records_observed_dimensions_and_stable_graph() -> None:
    args = _inputs_with_sections()
    before = mesh_sha256(args[0].mesh)
    first = _fit(*args)
    repeated = _fit(*args)

    assert first.status is ScrewCapExteriorFitStatus.FITTED
    assert first == repeated
    assert dict(first.parameters)["screw_cap_exterior_diameter"] == pytest.approx(5.0)
    assert dict(first.parameters)["screw_cap_exterior_height"] == pytest.approx(1.0)
    assert first.model is not None
    assert first.model.previous_revision_id == args[4].model.revision_id
    assert first.model.coordinate_unit == "mm_unverified"
    assert first.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.model.mold_use_authorized is False
    assert mesh_sha256(args[0].mesh) == before
    payload = next(
        item.as_dict()["value"]
        for item in first.model.parameters
        if item.parameter_id.startswith("screw_cap_exterior_")
    )
    assert isinstance(payload, dict)
    assert payload["thread_standard_inferred"] is False
    assert payload["internal_thread_geometry_inferred"] is False
    assert payload["seal_performance_inferred"] is False
    assert payload["manufacturing_dimensions_inferred"] is False
    assert all(item.value_type is ParameterType.OBJECT for item in first.model.parameters)
    assert first.review_required is True


def test_sparse_and_high_residual_sections_require_review_without_graph_edit() -> None:
    args = _inputs_with_sections()
    sparse = _fit(*(*args[:5], args[5][:1]))
    assert sparse.status is ScrewCapExteriorFitStatus.REVIEW_REQUIRED
    assert sparse.model is None
    assert "cross_section_support_sparse" in sparse.reasons

    no_sections = _fit(*(*args[:5], ()))
    assert no_sections.status is ScrewCapExteriorFitStatus.REVIEW_REQUIRED
    assert no_sections.model is None
    assert "cross_section_support_missing" in no_sections.reasons

    noisy = (replace(args[5][0], maximum_radial_residual=0.5), *args[5][1:])
    high_residual = _fit(*(*args[:5], noisy))
    assert high_residual.status is ScrewCapExteriorFitStatus.REVIEW_REQUIRED
    assert high_residual.model is None
    assert high_residual.maximum_radial_residual == 0.5
    assert "cross_section_residual_exceeds_policy" in high_residual.reasons


def test_wrong_capture_parent_or_ambiguous_cross_section_height_rejects() -> None:
    args = _inputs_with_sections()
    bad_parent = replace(args[5][0], source_geometry_id="other-geometry")
    with pytest.raises(ValueError, match="cross_section_parent_quality_or_range_invalid"):
        _fit(*(*args[:5], (bad_parent, *args[5][1:])))

    duplicate_height = replace(args[5][1], center=args[5][0].center)
    with pytest.raises(ValueError, match="duplicate_cross_section_height"):
        _fit(*(*args[:5], (args[5][0], duplicate_height, args[5][2])))

    ambiguous = replace(args[4], status=ClosureSeparationStatus.AMBIGUOUS)
    with pytest.raises(ValueError, match="closure_candidate_parent_or_authority_mismatch"):
        _fit(*(*args[:4], ambiguous, args[5]))
