from __future__ import annotations

from dataclasses import replace

import pytest
from test_closure_separation_candidates import _inputs, _scan_mesh

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.cross_section_measurement import CrossSectionSelection
from packlab_core.design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    FeatureKind,
    ParameterType,
    revise_design_model_revision,
    stable_feature_id,
)
from packlab_core.mating_references import (
    MatingReferenceStatus,
    create_neck_closure_mating_references,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import mesh_sha256


def _fixture():
    scan, _, profile_fit, zones, original_model = _inputs()
    mesh, rings = _scan_mesh()
    assert mesh == scan.mesh
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
    neck_zone = zones.boundaries[-1]
    neck_feature = DesignModelFeatureReference(
        neck_zone.feature_id,
        neck_zone.component_id,
        FeatureKind.NECK,
        neck_zone.semantic_key,
    )
    closure_component_id = "closure-component"
    closure_semantic_key = "closure:observed-cap"
    closure_feature = DesignModelFeatureReference(
        stable_feature_id(closure_component_id, FeatureKind.CAP, closure_semantic_key),
        closure_component_id,
        FeatureKind.CAP,
        closure_semantic_key,
    )
    model = revise_design_model_revision(
        original_model,
        parameters=original_model.parameters,
        features=(neck_feature, closure_feature),
        actor_id="operator-1",
        reason="Add stable neck and closure features for mating references.",
        created_at_utc="2026-10-03T18:20:00Z",
    )
    rings_by_z = dict(rings)

    def selections(label: str, heights: tuple[float, ...]):
        return tuple(
            CrossSectionSelection(
                f"{label}-z{height:g}",
                geometry.source_geometry_id,
                geometry.normalized_geometry_revision,
                rings_by_z[height],
                (0.0, 0.0, height),
                (0.0, 0.0, 1.0),
                1e-9,
            )
            for height in heights
        )

    neck_sections = selections("neck", (9.0, 9.5))
    closure_sections = selections("closure", (15.5, 16.0))
    return scan, geometry, model, neck_feature, closure_feature, neck_sections, closure_sections


def _create(args, *, geometry=None, closure_feature_id=None):
    scan, source_geometry, model, neck_feature, closure_feature, neck_sections, closure_sections = (
        args
    )
    return create_neck_closure_mating_references(
        scan,
        source_geometry if geometry is None else geometry,
        model,
        neck_feature.feature_id,
        closure_feature.feature_id if closure_feature_id is None else closure_feature_id,
        neck_sections,
        closure_sections,
        expected_scan_master_revision_id=scan.revision_id,
        expected_model_revision_id=model.revision_id,
        actor_id="operator-1",
        reason="Create parent-bound neck and closure reference planes.",
        created_at_utc="2026-10-03T18:21:00Z",
    )


def test_coaxial_references_create_canonical_axis_and_explicit_offset_planes() -> None:
    args = _fixture()
    digest = mesh_sha256(args[0].mesh)
    first = _create(args)
    repeated = _create(args)

    assert first.status is MatingReferenceStatus.ALIGNED
    assert first == repeated
    assert first.reference_set_id == repeated.reference_set_id
    assert first.neck_plane.reference_id == repeated.neck_plane.reference_id
    assert first.closure_plane.reference_id == repeated.closure_plane.reference_id
    assert first.canonical_axis_origin == pytest.approx((0.0, 0.0, 0.0))
    assert first.canonical_axis_direction == (0.0, 0.0, 1.0)
    assert first.neck_plane.offset_from_axis_origin == pytest.approx(9.5)
    assert first.closure_plane.offset_from_axis_origin == pytest.approx(15.5)
    assert first.inter_plane_offset == pytest.approx(6.0)
    assert first.model is not None
    assert first.model.previous_revision_id == args[2].revision_id
    assert first.coordinate_unit == "mm_unverified"
    assert first.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.model.mold_use_authorized is False
    assert mesh_sha256(args[0].mesh) == digest
    report = first.as_dict()
    assert report["thread_compatibility_claimed"] is False
    assert report["seal_compatibility_claimed"] is False
    assert report["manufacturing_alignment_claimed"] is False

    node = next(
        item for item in first.model.parameters if item.parameter_id.startswith("mating_reference_")
    )
    payload = node.as_dict()["value"]
    assert isinstance(payload, dict)
    assert payload["source_model_revision_id"] == args[2].revision_id
    assert payload["neck_feature_id"] == args[3].feature_id
    assert payload["closure_feature_id"] == args[4].feature_id
    assert payload["seal_compatibility_claimed"] is False


def test_stale_features_reject_and_noncoaxial_axis_returns_review_mismatch() -> None:
    args = _fixture()
    with pytest.raises(ValueError, match="closure_feature_stale_or_ambiguous"):
        _create(args, closure_feature_id="missing-closure-feature")

    scan, geometry, *_ = args
    shifted_indices = {
        index for index, point in enumerate(geometry.points) if point[2] in {15.5, 16.0}
    }
    shifted_points = tuple(
        (point[0] + 1.0, point[1], point[2]) if index in shifted_indices else point
        for index, point in enumerate(geometry.points)
    )
    shifted_geometry = replace(geometry, points=shifted_points)
    mismatch = _create(args, geometry=shifted_geometry)
    assert mismatch.status is MatingReferenceStatus.AXIS_MISMATCH_REVIEW_REQUIRED
    assert mismatch.review_required is True
    assert mismatch.model is None
    assert mismatch.axis_misalignment == pytest.approx(1.0)
    assert mismatch.closure_plane.origin[0] == pytest.approx(1.0)
    assert mismatch.coordinate_unit == "mm_unverified"
    assert mesh_sha256(scan.mesh) == mismatch.scan_master_geometry_sha256


def test_reference_feature_ids_and_parameter_survive_ordinary_model_edit() -> None:
    result = _create(_fixture())
    assert result.model is not None
    previous_feature_ids = tuple(item.feature_id for item in result.model.features)
    mating_parameter = next(
        item
        for item in result.model.parameters
        if item.parameter_id.startswith("mating_reference_")
    )
    edited = revise_design_model_revision(
        result.model,
        parameters=(
            *result.model.parameters,
            DesignModelParameter("unrelated_edit", 1, ParameterType.INTEGER),
        ),
        features=result.model.features,
        actor_id="operator-1",
        reason="Edit an unrelated editable parameter.",
        created_at_utc="2026-10-03T18:22:00Z",
    )
    assert tuple(item.feature_id for item in edited.features) == previous_feature_ids
    retained = next(
        item for item in edited.parameters if item.parameter_id == mating_parameter.parameter_id
    )
    assert retained == mating_parameter
    payload = retained.as_dict()["value"]
    assert isinstance(payload, dict)
    assert payload["reference_set_id"] == result.reference_set_id
    assert payload["source_model_revision_id"] == result.source_model_revision_id
