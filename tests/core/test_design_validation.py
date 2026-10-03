from __future__ import annotations

import hashlib

from packlab_core.cross_section import circle_section
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
from packlab_core.design_operations import LoftSectionInput, create_loft_operation
from packlab_core.design_profile import ProfilePoint, create_design_profile
from packlab_core.design_validation import (
    DesignValidationPolicy,
    NumericBound,
    validate_design_model,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _model(*, relative: bool = False, dimensions: tuple[float, ...] = (2, 20, 60, 90)):
    scale_state = ScaleState.RELATIVE if relative else ScaleState.METRIC_UNVERIFIED
    scan_id = f"scan-master:{hashlib.sha256(b'validation-parent').hexdigest()}"
    binding = bind_design_model_parent(
        ScanMasterRevision(
            scan_id,
            PROJECT,
            MESH,
            {
                "scan_master_revision_id": scan_id,
                "project_id": PROJECT,
                "authority_class": "SCAN_MASTER",
                "output_geometry_sha256": mesh_sha256(MESH),
                "reconstruction_revision_id": "reconstruction-r1",
                "scale_state": scale_state.value,
                "scale_provenance_id": "scale-r1",
                "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
                "mold_use_authorized": False,
            },
        ),
        actor_id="operator-1",
        reason="Initial selection.",
        created_at_utc="2026-10-03T12:00:00Z",
    )
    unit = "reconstruction_units" if relative else "mm_unverified"
    parameters = tuple(
        DesignModelParameter(name, value, ParameterType.NUMBER, unit)
        for name, value in zip(
            ("base-height", "body-height", "shoulder-height", "neck-height"), dimensions
        )
    )
    features = tuple(
        DesignModelFeatureReference(
            stable_feature_id("container", kind, semantic),
            "container",
            kind,
            semantic,
        )
        for kind, semantic in (
            (FeatureKind.BODY, "body"),
            (FeatureKind.BASE, "section-base"),
            (FeatureKind.SHOULDER, "section-top"),
        )
    )
    return create_design_model_revision(
        binding,
        package_family=PackageFamily.BOTTLE,
        parameters=parameters,
        features=features,
        actor_id="operator-1",
        reason="Validation fixture.",
        created_at_utc="2026-10-03T12:30:00Z",
    )


def test_valid_ordered_dimensions_and_bounds_pass_without_mutation() -> None:
    model = _model()
    snapshot = tuple(parameter.value for parameter in model.parameters)
    policy = DesignValidationPolicy(
        numeric_bounds=tuple(
            NumericBound(name, 0.0, 120.0, "mm_unverified")
            for name in ("base-height", "body-height", "shoulder-height", "neck-height")
        ),
        ordered_parameter_ids=(
            "base-height",
            "body-height",
            "shoulder-height",
            "neck-height",
        ),
        available_scan_master_revision_ids=(model.fitted_to_scan_master_revision_id,),
    )
    report = validate_design_model(model, policy=policy)
    assert report.valid is True
    assert report.as_dict()["status"] == "VALID"
    assert tuple(parameter.value for parameter in model.parameters) == snapshot
    assert report.as_dict()["mutated_or_clamped_parameters"] is False


def test_out_of_bounds_and_base_body_neck_contradictions_are_deterministic() -> None:
    model = _model(dimensions=(-1, 30, 20, 15))
    policy = DesignValidationPolicy(
        numeric_bounds=(NumericBound("base-height", 0.0, 100.0, "mm_unverified"),),
        ordered_parameter_ids=(
            "base-height",
            "body-height",
            "shoulder-height",
            "neck-height",
        ),
    )
    first = validate_design_model(model, policy=policy)
    repeat = validate_design_model(model, policy=policy)
    assert first.valid is False
    assert first.as_dict() == repeat.as_dict()
    assert {item.code for item in first.issues} == {
        "parameter_order_contradiction",
        "parameter_out_of_bounds",
    }
    assert model.parameters[0].value == -1


def test_stale_scan_master_and_mixed_units_are_reported_explicitly() -> None:
    model = _model()
    relative_profile = create_design_profile(
        (ProfilePoint(0, 1), ProfilePoint(10, 2)), ScaleState.RELATIVE
    )
    relative_section = circle_section(
        "container", 4, scale_state=ScaleState.RELATIVE, point_count=16
    )
    report = validate_design_model(
        model,
        policy=DesignValidationPolicy(available_scan_master_revision_ids=("scan-master:other",)),
        profiles=(relative_profile,),
        cross_sections=(relative_section,),
    )
    codes = {item.code for item in report.issues}
    assert "scan_master_parent_stale" in codes
    assert "profile_unit_mismatch" in codes
    assert "cross_section_unit_mismatch" in codes


def test_relative_profile_and_section_units_match_reconstruction_units_contract() -> None:
    model = _model(relative=True)
    profile = create_design_profile((ProfilePoint(0, 1), ProfilePoint(10, 2)), ScaleState.RELATIVE)
    section = circle_section("container", 4, scale_state=ScaleState.RELATIVE, point_count=16)
    assert model.coordinate_unit == "reconstruction_units"
    assert validate_design_model(model, profiles=(profile,), cross_sections=(section,)).valid


def test_stale_operation_feature_and_section_input_are_diagnosed() -> None:
    model = _model()
    base_feature, top_feature = model.features[1:]
    bottom = circle_section("container", 4, point_count=16)
    top = circle_section("container", 3, point_count=16)
    operation = create_loft_operation(
        model,
        (
            LoftSectionInput(base_feature.feature_id, bottom, 0.0),
            LoftSectionInput(top_feature.feature_id, top, 20.0),
        ),
    )
    assert validate_design_model(
        model,
        cross_sections=(bottom, top),
        operations=(operation,),
    ).valid
    object.__setattr__(operation, "parent_feature_ids", ("deleted-feature", top_feature.feature_id))
    object.__setattr__(operation, "section_positions", (20.0, 0.0))
    report = validate_design_model(
        model,
        cross_sections=(bottom, top),
        operations=(operation,),
    )
    assert "operation_feature_reference_stale" in {issue.code for issue in report.issues}
    assert "loft_order_invalid" in {issue.code for issue in report.issues}


def test_ordered_dimensions_reject_relative_bound_unit_mix() -> None:
    model = _model(relative=True)
    report = validate_design_model(
        model,
        policy=DesignValidationPolicy(
            numeric_bounds=(NumericBound("base-height", 0.0, 5.0, "mm_unverified"),)
        ),
    )
    assert any(issue.code == "bounded_parameter_unit_mismatch" for issue in report.issues)
