from __future__ import annotations

from dataclasses import replace

import pytest
from test_closure_separation_candidates import _inputs, _scan_mesh

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.cross_section_measurement import CrossSectionSelection
from packlab_core.flip_top_exterior import (
    FlipTopExteriorStatus,
    fit_flip_top_exterior,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import mesh_sha256


def _fixture():
    scan, _, profile_fit, zones, model = _inputs()
    generated_mesh, rings = _scan_mesh()
    assert generated_mesh == scan.mesh
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
    indices_by_z = dict(rings)

    def selections(label: str, heights: tuple[float, ...]):
        return tuple(
            CrossSectionSelection(
                f"{label}-z{height:g}",
                geometry.source_geometry_id,
                geometry.normalized_geometry_revision,
                indices_by_z[height],
                (0.0, 0.0, height),
                (0.0, 0.0, 1.0),
                1e-9,
            )
            for height in heights
        )

    base = selections("base", (15.0, 15.5))
    lid = selections("lid", (15.5, 16.0))
    hinge = selections("hinge-reference", (15.0, 15.5))
    return scan, geometry, profile_fit, zones, model, base, lid, hinge, selections


def _fit(args, *, base=None, lid=None, hinge=None):
    scan, geometry, profile_fit, zones, model, base_default, lid_default, hinge_default, _ = args
    return fit_flip_top_exterior(
        scan,
        geometry,
        profile_fit,
        zones,
        model,
        base_default if base is None else base,
        lid_default if lid is None else lid,
        hinge_default if hinge is None else hinge,
        expected_scan_master_revision_id=scan.revision_id,
        expected_model_revision_id=model.revision_id,
        actor_id="operator-1",
        reason="Create review-required flip-top exterior candidate.",
        created_at_utc="2026-10-03T18:10:00Z",
    )


def test_synthetic_flip_top_exterior_is_editable_and_deterministic() -> None:
    args = _fixture()
    scan_digest = mesh_sha256(args[0].mesh)
    first = _fit(args)
    repeated = _fit(args)

    assert first.status is FlipTopExteriorStatus.FITTED
    assert first == repeated
    assert first.feature.feature_id == repeated.feature.feature_id
    assert first.model is not None
    assert first.model.previous_revision_id == args[4].revision_id
    assert first.model.coordinate_unit == "mm_unverified"
    assert first.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.model.mold_use_authorized is False
    assert first.base_diameter == pytest.approx(5.0)
    assert first.lid_envelope_diameter == pytest.approx(5.0)
    assert first.base_z_range == (15.0, 15.5)
    assert first.lid_z_range == (15.5, 16.0)
    assert first.hinge_reference_center == pytest.approx((0.0, 0.0, 15.25))
    assert first.review_required is True
    assert mesh_sha256(args[0].mesh) == scan_digest

    payload = next(
        item.as_dict()["value"]
        for item in first.model.parameters
        if item.parameter_id.startswith("flip_top_exterior_")
    )
    assert isinstance(payload, dict)
    assert payload["hinge_reference_region"]["hinge_mechanism_confirmed"] is False
    assert payload["latch_inferred"] is False
    assert payload["seal_performance_inferred"] is False
    assert payload["internal_mechanism_inferred"] is False
    assert payload["wall_thickness_inferred"] is False
    assert payload["manufacturing_dimensions_inferred"] is False
    assert first.as_dict()["scan_master_mutated"] is False


def test_sparse_or_hidden_hinge_reference_stays_review_required() -> None:
    args = _fixture()
    sparse = _fit(args, base=args[5][:1])
    assert sparse.status is FlipTopExteriorStatus.REVIEW_REQUIRED
    assert sparse.model is None
    assert sparse.hinge_reference_center is None
    assert "base_region_measurements_ambiguous" in sparse.reasons

    hidden_region = _fit(args, hinge=args[7][:1])
    assert hidden_region.status is FlipTopExteriorStatus.REVIEW_REQUIRED
    assert hidden_region.model is None
    assert "hinge_reference_region_ambiguous" in hidden_region.reasons


def test_ambiguous_exterior_and_stale_selection_fail_closed() -> None:
    args = _fixture()
    _, _, _, _, _, _, _, _, selections = args
    inconsistent_base = selections("base-mixed", (0.0, 14.0))
    ambiguous = _fit(args, base=inconsistent_base)
    assert ambiguous.status is FlipTopExteriorStatus.REVIEW_REQUIRED
    assert ambiguous.model is None
    assert "base_region_measurements_ambiguous" in ambiguous.reasons

    stale = replace(args[5][0], source_geometry_id="other-geometry")
    with pytest.raises(ValueError, match="base_section_selection_parent_or_plane_invalid"):
        _fit(args, base=(stale, args[5][1]))
