from __future__ import annotations

import math
from dataclasses import replace

import pytest

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.closure_separation_candidates import (
    ClosureSeparationPolicy,
    ClosureSeparationStatus,
    create_closure_separation_candidates,
)
from packlab_core.cross_section_measurement import CrossSectionSelection, measure_cross_section
from packlab_core.cross_section_overlay import CanonicalAxis
from packlab_core.design_model import PackageFamily, create_design_model_revision
from packlab_core.design_profile_fit import (
    ProfileTransitionAnchor,
    ProfileTransitionKind,
    fit_design_profile,
)
from packlab_core.design_profile_zones import detect_design_profile_zones
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.horizontal_section import extract_horizontal_section
from packlab_core.neck_finish_candidates import (
    NeckSectionEvidence,
    measure_neck_finish_candidates,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.scan_master_profile import extract_scan_master_vertical_profile
from packlab_core.vertical_profile import extract_vertical_profile

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"


def _scan_mesh(*, connected_cap: bool = False, extra: bool = False):
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    ring_records: list[tuple[float, float, tuple[int, ...]]] = []

    def add_ring(radius: float, z: float) -> tuple[int, ...]:
        indices = []
        for index in range(64):
            angle = math.tau * index / 64
            indices.append(len(vertices))
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), z))
        return tuple(indices)

    previous = None
    for index in range(31):
        z = index / 2
        radius = 5.0 if z <= 1.5 else 6.0 if z <= 8.0 else 2.5
        current = add_ring(radius, z)
        ring_records.append((z, radius, current))
        if previous is not None:
            for index in range(64):
                following = (index + 1) % 64
                triangles.extend(
                    (
                        (previous[index], previous[following], current[following]),
                        (previous[index], current[following], current[index]),
                    )
                )
        previous = current
    assert previous is not None
    cap_rings = (
        (previous, add_ring(2.5, 15.5), add_ring(2.5, 16.0))
        if connected_cap
        else tuple(add_ring(2.5, z) for z in (15.0, 15.5, 16.0))
    )
    ring_records.extend(
        (z, 2.5, ring) for z, ring in zip((15.0, 15.5, 16.0), cap_rings, strict=True)
    )
    for lower, upper in zip(cap_rings, cap_rings[1:]):
        for index in range(64):
            following = (index + 1) % 64
            triangles.extend(
                (
                    (lower[index], lower[following], upper[following]),
                    (lower[index], upper[following], upper[index]),
                )
            )
    if extra:
        debris_bottom = add_ring(2.5, 15.0)
        debris_middle = add_ring(2.5, 15.5)
        debris_top = add_ring(2.5, 16.0)
        for index in range(64):
            following = (index + 1) % 64
            triangles.extend(
                (
                    (debris_bottom[index], debris_bottom[following], debris_middle[following]),
                    (debris_bottom[index], debris_middle[following], debris_middle[index]),
                    (debris_middle[index], debris_middle[following], debris_top[following]),
                    (debris_middle[index], debris_top[following], debris_top[index]),
                )
            )
        ring_records.extend(
            ((15.0, 2.5, debris_bottom), (15.5, 2.5, debris_middle), (16.0, 2.5, debris_top))
        )
    grouped: dict[float, list[int]] = {}
    for z, _, indices in ring_records:
        grouped.setdefault(z, []).extend(indices)
    return TriangleMeshData(tuple(vertices), tuple(triangles)), tuple(
        (z, tuple(sorted(set(indices)))) for z, indices in sorted(grouped.items())
    )


def _inputs(*, connected_cap: bool = False, extra: bool = False):
    mesh, rings = _scan_mesh(connected_cap=connected_cap, extra=extra)
    scan_id = f"scan-master-closure-{int(connected_cap)}-{int(extra)}"
    scan = ScanMasterRevision(
        scan_id,
        PROJECT,
        mesh,
        {
            "scan_master_revision_id": scan_id,
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(mesh),
            "reconstruction_revision_id": "reconstruction-r1",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-r1",
            "parent_object_geometry_revision_id": "geometry-r1",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    measurement_geometry = NormalizedMeasurementGeometry(
        "normalized-r1",
        "geometry-r1",
        mesh.vertices,
        ScaleState.METRIC_UNVERIFIED,
        "mm_unverified",
        "scale-r1",
        0.02,
        "mm_per_reconstruction_unit",
    )
    vertical = extract_vertical_profile(
        measurement_geometry,
        plane_origin=(0.0, 0.0, 0.0),
        horizontal_direction=(1.0, 0.0, 0.0),
        lateral_tolerance=0.21,
        current_geometry_id=measurement_geometry.source_geometry_id,
        current_normalized_geometry_revision=measurement_geometry.normalized_geometry_revision,
        current_scale_provenance_id=measurement_geometry.scale_provenance_id,
    )
    neck_sections = []
    for z, indices in rings:
        section = extract_horizontal_section(
            measurement_geometry,
            z,
            slab_half_width=0.0,
            current_geometry_id=measurement_geometry.source_geometry_id,
            current_normalized_geometry_revision=measurement_geometry.normalized_geometry_revision,
            current_scale_provenance_id=measurement_geometry.scale_provenance_id,
        )
        selection = CrossSectionSelection(
            f"selection-z{z:g}",
            measurement_geometry.source_geometry_id,
            measurement_geometry.normalized_geometry_revision,
            indices,
            (0.0, 0.0, z),
            (0.0, 0.0, 1.0),
            1e-9,
        )
        measured = measure_cross_section(
            measurement_geometry,
            selection,
            current_geometry_id=measurement_geometry.source_geometry_id,
            current_normalized_geometry_revision=measurement_geometry.normalized_geometry_revision,
            current_scale_provenance_id=measurement_geometry.scale_provenance_id,
        )
        neck_sections.append(NeckSectionEvidence(section, measured))
    neck_finish = measure_neck_finish_candidates(
        measurement_geometry,
        tuple(neck_sections),
        vertical,
        current_geometry_id=measurement_geometry.source_geometry_id,
        current_normalized_geometry_revision=measurement_geometry.normalized_geometry_revision,
        current_scale_provenance_id=measurement_geometry.scale_provenance_id,
    )
    profile_evidence = extract_scan_master_vertical_profile(
        scan,
        expected_scan_master_revision_id=scan.revision_id,
        axis=CanonicalAxis.Z,
        plane_origin=(0.0, 0.0, 0.0),
        front_direction=(1.0, 0.0, 0.0),
        lateral_tolerance=0.3,
        band_count=16,
        minimum_band_samples=3,
        outlier_mad_multiplier=4.5,
        actor_id="operator-1",
        reason="Extract closure fixture profile evidence.",
        created_at_utc="2026-10-03T18:00:00Z",
    )
    fit = fit_design_profile(
        profile_evidence,
        transition_anchors=(
            ProfileTransitionAnchor(ProfileTransitionKind.BASE, 3),
            ProfileTransitionAnchor(ProfileTransitionKind.SHOULDER, 12),
        ),
        smoothing_strength=0.0,
        window_radius=2,
        maximum_relative_adjustment=0.25,
    )
    assert fit.profile is not None, (fit.status, fit.uncertainty_codes, len(fit.residuals))
    zones = detect_design_profile_zones(
        fit,
        expected_fit_id=fit.fit_id,
        component_id="container",
    )
    model = create_design_model_revision(
        fit.parent_binding,
        package_family=PackageFamily.BOTTLE,
        actor_id="operator-1",
        reason="Create closure candidate model parent.",
        created_at_utc="2026-10-03T18:00:00Z",
    )
    return scan, neck_finish, fit, zones, model


def _create(scan, neck_finish, fit, zones, model, **kwargs):
    return create_closure_separation_candidates(
        scan,
        neck_finish,
        fit,
        zones,
        model,
        expected_scan_master_revision_id=scan.revision_id,
        expected_model_revision_id=model.revision_id,
        actor_id="operator-1",
        reason="Assess captured cap/body separation evidence.",
        created_at_utc="2026-10-03T18:01:00Z",
        **kwargs,
    )


def test_clear_upper_component_creates_stable_parent_bound_design_candidates() -> None:
    scan, neck_finish, fit, zones, model = _inputs()
    before_digest = mesh_sha256(scan.mesh)
    first = _create(scan, neck_finish, fit, zones, model)
    repeated = _create(scan, neck_finish, fit, zones, model)

    assert zones.review_required is False
    assert len(neck_finish.candidates) == 1
    assert neck_finish.candidates[0].ambiguity_review_required is False
    assert first.status is ClosureSeparationStatus.CANDIDATE_CREATED
    assert first == repeated
    assert len(first.candidates) == 2
    assert {item.role for item in first.candidates} == {"body", "closure-candidate"}
    assert first.model is not None
    assert first.model.revision_id != model.revision_id
    assert first.model.fitted_to_scan_master_revision_id == scan.revision_id
    assert first.model.scan_master_geometry_sha256 == before_digest
    assert first.model.coordinate_unit == "mm_unverified"
    assert first.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.model.mold_use_authorized is False
    assert tuple(item.feature.feature_id for item in first.candidates) == tuple(
        item.feature.feature_id for item in repeated.candidates
    )
    metadata = first.as_dict()
    assert metadata["scan_master_mutated"] is False
    assert metadata["closure_geometry_invented"] is False
    assert all(item["closure_identity_confirmed"] is False for item in metadata["candidates"])
    assert mesh_sha256(scan.mesh) == before_digest


def test_single_connected_scan_and_weak_support_do_not_create_candidates() -> None:
    scan, neck_finish, fit, zones, model = _inputs(connected_cap=True)
    no_split = _create(scan, neck_finish, fit, zones, model)
    assert no_split.status is ClosureSeparationStatus.NO_SEPARATION_EVIDENCE
    assert no_split.model is None
    assert no_split.candidates == ()

    scan, neck_finish, fit, zones, model = _inputs()
    weak_policy = ClosureSeparationPolicy(minimum_support_sections=99)
    weak = _create(scan, neck_finish, fit, zones, model, policy=weak_policy)
    assert weak.status is ClosureSeparationStatus.NO_SEPARATION_EVIDENCE
    assert weak.model is None
    assert "unique_neck_finish_support_missing" in weak.reasons


def test_multiple_components_stale_parents_and_unsupported_profile_evidence_fail_closed() -> None:
    scan, neck_finish, fit, zones, model = _inputs(extra=True)
    ambiguous = _create(scan, neck_finish, fit, zones, model)
    assert ambiguous.status is ClosureSeparationStatus.AMBIGUOUS
    assert ambiguous.model is None
    assert ambiguous.candidates == ()

    scan, neck_finish, fit, zones, model = _inputs()
    with pytest.raises(ValueError, match="selected_scan_master_parent_stale_or_invalid"):
        create_closure_separation_candidates(
            scan,
            neck_finish,
            fit,
            zones,
            model,
            expected_scan_master_revision_id="stale-scan",
            expected_model_revision_id=model.revision_id,
            actor_id="operator-1",
            reason="Reject stale parent.",
            created_at_utc="2026-10-03T18:01:00Z",
        )

    uncertain_zones = replace(zones, review_required=True)
    with pytest.raises(ValueError, match="profile_zones_ambiguous_stale_or_unauthorized"):
        _create(scan, neck_finish, fit, uncertain_zones, model)
