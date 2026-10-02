from __future__ import annotations

from dataclasses import replace

import pytest

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.capacity_estimation import (
    INTERIOR_CLOSURE_ASSUMPTION,
    CapacityEstimationError,
    InteriorVolumeRepresentation,
    estimate_capacity,
    serialize_capacity_estimate,
)
from packlab_core.reconstruction import ScaleState

BOX_VERTICES = (
    (0.0, 0.0, 0.0),
    (2.0, 0.0, 0.0),
    (2.0, 3.0, 0.0),
    (0.0, 3.0, 0.0),
    (0.0, 0.0, 4.0),
    (2.0, 0.0, 4.0),
    (2.0, 3.0, 4.0),
    (0.0, 3.0, 4.0),
)
BOX_TRIANGLES = (
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


def _geometry(state=ScaleState.RELATIVE):
    metric = state is not ScaleState.RELATIVE
    return NormalizedMeasurementGeometry(
        "normalized-r1",
        "exterior-geometry-r1",
        ((0.0, 0.0, 0.0), (10.0, 10.0, 10.0)),
        state,
        "mm_unverified" if metric else "reconstruction_units",
        "scale-r1" if metric else None,
        0.02 if metric else None,
        "mm_per_reconstruction_unit" if metric else None,
    )


def _interior(
    geometry,
    *,
    triangles=BOX_TRIANGLES,
    vertices=BOX_VERTICES,
    closure=INTERIOR_CLOSURE_ASSUMPTION,
):
    return InteriorVolumeRepresentation(
        "interior-shell-r1",
        "interior-revision-r1",
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        geometry.scale_provenance_id,
        geometry.coordinate_unit,
        tuple(vertices),
        tuple(triangles),
        "explicit-assumption-record-r1",
        closure,
    )


def _estimate(geometry, interior, *, requested_unit="native_cubed", current_scale="from_geometry"):
    return estimate_capacity(
        geometry,
        interior,
        requested_unit=requested_unit,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=(
            geometry.scale_provenance_id if current_scale == "from_geometry" else current_scale
        ),
    )


def test_known_synthetic_closed_interior_shell_has_expected_volume() -> None:
    geometry = _geometry()
    interior = _interior(geometry)
    estimate = _estimate(geometry, interior)
    assert estimate.source_volume == pytest.approx(24.0)
    assert estimate.capacity == pytest.approx(24.0)
    assert estimate.capacity_unit == "reconstruction_units^3"
    assert estimate.as_dict()["certified_volume_claimed"] is False
    assert estimate.as_dict()["exterior_geometry_used_as_interior"] is False
    assert estimate.as_dict()["wall_thickness_inferred"] is False


def test_open_nonmanifold_unknown_and_degenerate_interiors_are_rejected() -> None:
    geometry = _geometry()
    with pytest.raises(CapacityEstimationError, match="open_or_non_watertight"):
        _estimate(geometry, _interior(geometry, triangles=BOX_TRIANGLES[:-2]))
    with pytest.raises(CapacityEstimationError, match="non_manifold_edge"):
        _estimate(geometry, _interior(geometry, triangles=BOX_TRIANGLES + (BOX_TRIANGLES[0],)))
    with pytest.raises(CapacityEstimationError, match="closure_assumption_unknown"):
        _interior(geometry, closure="unknown")
    flat = tuple((x, y, 0.0) for x, y, _ in BOX_VERTICES)
    with pytest.raises(CapacityEstimationError, match="degenerate"):
        _estimate(geometry, _interior(geometry, vertices=flat))


@pytest.mark.parametrize("requested_unit", ["litre", "millilitre"])
def test_relative_and_metric_unverified_scale_cannot_claim_litre_units(requested_unit) -> None:
    geometry = _geometry(ScaleState.RELATIVE)
    with pytest.raises(CapacityEstimationError, match="require_verified_metric_scale"):
        _estimate(geometry, _interior(geometry), requested_unit=requested_unit)
    unverified = _geometry(ScaleState.METRIC_UNVERIFIED)
    with pytest.raises(CapacityEstimationError, match="require_verified_metric_scale"):
        _estimate(unverified, _interior(unverified), requested_unit=requested_unit)


def test_assumptions_provenance_and_deterministic_integration_are_recorded() -> None:
    geometry = _geometry()
    interior = _interior(geometry)
    first = _estimate(geometry, interior)
    second = _estimate(geometry, interior)
    assert first.estimate_id == second.estimate_id
    assert serialize_capacity_estimate(first) == serialize_capacity_estimate(second)
    payload = first.as_dict()
    assert payload["interior_representation"]["representation_id"] == interior.representation_id
    assert (
        payload["interior_representation"]["assumption_evidence_id"]
        == interior.assumption_evidence_id
    )
    assert payload["algorithm"]["closure_validation"].startswith("each undirected edge")
    assert payload["uncertainty_and_limitations"]["confidence_interval_estimated"] is False
    assert (
        payload["uncertainty_and_limitations"]["mesh_discretization_uncertainty"]
        == "not quantified"
    )
    assert payload["certified_volume_claimed"] is False


def test_stale_parent_and_unit_mismatched_interior_fail_closed() -> None:
    geometry = _geometry(ScaleState.METRIC_UNVERIFIED)
    interior = _interior(geometry)
    with pytest.raises(CapacityEstimationError, match="scale_provenance_parent_stale"):
        _estimate(geometry, interior, current_scale="scale-r2")
    with pytest.raises(CapacityEstimationError, match="coordinate_unit_mismatch"):
        _estimate(geometry, replace(interior, coordinate_unit="mm"))
    with pytest.raises(CapacityEstimationError, match="parent_mismatch"):
        _estimate(geometry, replace(interior, source_geometry_id="other-geometry"))
