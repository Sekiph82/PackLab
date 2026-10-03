from __future__ import annotations

import pytest

from packlab_core.design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.jerrycan_grip_indent import (
    GripIndentError,
    GripIndentSide,
    GripIndentStatus,
    create_grip_indent_depth_edit,
    create_jerrycan_grip_indent,
    measure_jerrycan_grip_indent_evidence,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
REGION = (1.0, 1.0, 3.0, 3.0)
PROFILE = ((1.25, 1.25), (2.75, 1.25), (2.75, 2.75), (1.25, 2.75))


def _inputs(*, surface="supported", coverage_gaps=(), include_coverage=True):
    axis = tuple(index / 2 for index in range(9))
    vertices = []
    for z in axis:
        for x in axis:
            inside = REGION[0] <= x <= REGION[2] and REGION[1] <= z <= REGION[3]
            if surface == "supported":
                y = 1.0 if inside else 2.0
            elif surface == "ambiguous":
                y = 1.0 if inside and x < 2.0 else 2.0
            else:
                y = 2.0
            vertices.append((x, y, z))
    triangles = []
    for row in range(len(axis) - 1):
        for column in range(len(axis) - 1):
            first = row * len(axis) + column
            second = first + 1
            third = first + len(axis) + 1
            fourth = first + len(axis)
            triangles.extend(((first, second, third), (first, third, fourth)))
    mesh = TriangleMeshData(tuple(vertices), tuple(triangles))
    revision_id = "scan-master-grip-indent-fixture-r1"
    manifest = {
        "scan_master_revision_id": revision_id,
        "project_id": PROJECT,
        "authority_class": "SCAN_MASTER",
        "output_geometry_sha256": mesh_sha256(mesh),
        "reconstruction_revision_id": "reconstruction-r1",
        "scale_state": ScaleState.METRIC_UNVERIFIED.value,
        "scale_provenance_id": "scale-r1",
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
    }
    if include_coverage:
        manifest["coverage_gaps"] = list(coverage_gaps)
    scan = ScanMasterRevision(revision_id, PROJECT, mesh, manifest)
    binding = bind_design_model_parent(
        scan,
        actor_id="fixture-operator",
        reason="Create synthetic local indent evidence fixture.",
        created_at_utc="2026-10-04T12:00:00Z",
    )
    body = DesignModelFeatureReference(
        stable_feature_id("jerrycan", FeatureKind.BODY, "jerrycan-body-section:0001"),
        "jerrycan",
        FeatureKind.BODY,
        "jerrycan-body-section:0001",
    )
    frame = DesignModelParameter(
        "jerrycan_section_frame",
        {
            "vertical_axis": "+z",
            "side_axis": "x (left/right)",
            "front_back_axis": "y",
            "front_direction": "+y",
        },
        ParameterType.OBJECT,
    )
    model = create_design_model_revision(
        binding,
        package_family=PackageFamily.JERRYCAN,
        parameters=(frame,),
        features=(body,),
        actor_id="fixture-operator",
        reason="Create synthetic jerrycan body reference.",
        created_at_utc="2026-10-04T12:01:00Z",
    )
    return scan, model, body


def _evidence(scan, model, body):
    return measure_jerrycan_grip_indent_evidence(
        scan,
        model,
        body_feature_id=body.feature_id,
        region_id="left-panel-grip",
        region_bounds=REGION,
        ring_width=0.5,
        side=GripIndentSide.FRONT,
    )


def _create(scan, model, evidence):
    return create_jerrycan_grip_indent(
        scan,
        model,
        evidence,
        profile=PROFILE,
        actor_id="fixture-operator",
        reason="Initialize parametric local grip indent from supported synthetic Scan Master evidence.",
        created_at_utc="2026-10-04T12:02:00Z",
    )


def test_supported_scan_surface_initializes_bounded_parametric_indent() -> None:
    scan, model, body = _inputs()
    original_manifest = scan.manifest_bytes()
    original_digest = mesh_sha256(scan.mesh)
    evidence = _evidence(scan, model, body)
    feature_model = _create(scan, model, evidence)
    feature = next(
        item for item in feature_model.features if item.feature_kind is FeatureKind.GRIP_INDENT
    )
    payload = feature_model.as_dict()
    parameters = {item["parameter_id"]: item for item in payload["parameters"]}
    prefix = f"grip-indent:{feature.feature_id.rsplit(':', 1)[-1]}"

    assert evidence.status is GripIndentStatus.SUPPORTED
    assert evidence.coverage_ratio == pytest.approx(1.0)
    assert evidence.observed_depth == pytest.approx(1.0)
    assert evidence.depth_envelope == pytest.approx((1.0, 1.0))
    assert feature.feature_id == stable_feature_id(
        body.component_id, FeatureKind.GRIP_INDENT, "jerrycan-grip-indent:left-panel-grip"
    )
    assert parameters[f"{prefix}:depth"]["value"] == pytest.approx(1.0)
    assert parameters[f"{prefix}:depth_envelope"]["value"] == pytest.approx([1.0, 1.0])
    assert parameters[f"{prefix}:profile"]["value"] == [list(point) for point in PROFILE]
    assert parameters[f"{prefix}:depth"]["unit"] == "mm_unverified"
    assert payload["coordinate_unit"] == "mm_unverified"
    assert payload["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert payload["mold_use_authorized"] is False
    assert evidence.as_dict()["raw_scan_points_retained"] is False
    assert feature_model.fitted_to_scan_master_revision_id == scan.revision_id
    assert feature_model.scan_master_geometry_sha256 == original_digest
    assert scan.manifest_bytes() == original_manifest
    assert mesh_sha256(scan.mesh) == original_digest


def test_missing_or_ambiguous_local_surface_evidence_stays_review_required() -> None:
    scan, model, body = _inputs(include_coverage=False)
    missing_coverage = _evidence(scan, model, body)
    assert missing_coverage.status is GripIndentStatus.REVIEW_REQUIRED
    assert "scan_master_coverage_metadata_missing" in missing_coverage.uncertainty_codes
    with pytest.raises(GripIndentError, match="evidence_requires_review"):
        _create(scan, model, missing_coverage)

    scan, model, body = _inputs(surface="ambiguous")
    ambiguous = _evidence(scan, model, body)
    assert ambiguous.status is GripIndentStatus.REVIEW_REQUIRED
    assert "local_indent_depth_not_distinct_from_surface_support" in ambiguous.uncertainty_codes
    with pytest.raises(GripIndentError, match="evidence_requires_review"):
        _create(scan, model, ambiguous)

    scan, model, body = _inputs(coverage_gaps=("local front area occluded",))
    incomplete = _evidence(scan, model, body)
    assert incomplete.status is GripIndentStatus.REVIEW_REQUIRED
    assert "scan_master_has_declared_coverage_gaps" in incomplete.uncertainty_codes


def test_impossible_depth_and_out_of_region_profile_reject() -> None:
    scan, model, body = _inputs()
    evidence = _evidence(scan, model, body)
    with pytest.raises(GripIndentError, match="depth_outside_evidence_envelope"):
        create_jerrycan_grip_indent(
            scan,
            model,
            evidence,
            profile=PROFILE,
            depth=1.1,
            actor_id="fixture-operator",
            reason="Reject unsupported local indent depth.",
            created_at_utc="2026-10-04T12:02:00Z",
        )
    with pytest.raises(GripIndentError, match="profile_outside_region"):
        create_jerrycan_grip_indent(
            scan,
            model,
            evidence,
            profile=((0.5, 1.25), (2.75, 1.25), (2.75, 2.75), (0.5, 2.75)),
            actor_id="fixture-operator",
            reason="Reject a profile outside local Scan Master support.",
            created_at_utc="2026-10-04T12:02:00Z",
        )


def test_feature_and_parameter_identity_are_deterministic_and_depth_edit_is_bounded() -> None:
    scan, model, body = _inputs()
    evidence = _evidence(scan, model, body)
    first = _create(scan, model, evidence)
    second = _create(scan, model, evidence)

    first_feature = next(
        item for item in first.features if item.feature_kind is FeatureKind.GRIP_INDENT
    )
    second_feature = next(
        item for item in second.features if item.feature_kind is FeatureKind.GRIP_INDENT
    )
    assert first_feature == second_feature
    assert first.revision_id == second.revision_id
    with pytest.raises(GripIndentError, match="depth_outside_evidence_envelope"):
        create_grip_indent_depth_edit(first, first_feature.feature_id, 1.1)


def test_no_observed_recess_reports_no_indent() -> None:
    scan, model, body = _inputs(surface="flat")
    evidence = _evidence(scan, model, body)
    assert evidence.status is GripIndentStatus.NO_INDENT
    with pytest.raises(GripIndentError, match="evidence_requires_review"):
        _create(scan, model, evidence)
