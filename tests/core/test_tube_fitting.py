from __future__ import annotations

import math
from dataclasses import replace

import pytest

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.cross_section_measurement import (
    CrossSectionMeasurement,
    CrossSectionSelection,
    measure_cross_section,
)
from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    create_standalone_design_geometry_root,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.tube_family import TubeFamilyDimensions
from packlab_core.tube_fitting import (
    TubeDimensionEvidence,
    TubeFitAuthorityMode,
    TubeFittingError,
    fit_tube_family,
)

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
NOW = "2026-10-04T12:00:00Z"
SCALE_ID = "scale-provenance:tube-family-fixture"
SCAN_ID = "scan-master:tube-family-fixture"
DIMENSIONS = TubeFamilyDimensions(
    body_length=90.0,
    body_diameter=35.0,
    shoulder_length=15.0,
    shoulder_diameter=22.0,
    neck_length=8.0,
    neck_diameter=10.0,
    cap_height=18.0,
    cap_diameter=12.0,
    crimp_length=5.0,
    crimp_thickness=1.5,
)
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _captured_parent():
    scan = ScanMasterRevision(
        SCAN_ID,
        PROJECT,
        MESH,
        {
            "scan_master_revision_id": SCAN_ID,
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(MESH),
            "reconstruction_revision_id": "reconstruction:tube-family-fixture",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": SCALE_ID,
            "parent_object_geometry_revision_id": "captured-tube-geometry-r1",
            "alignment_transform": {"transform": {"transform_id": "normalized-tube-r1"}},
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    from packlab_core.design_model_binding import bind_design_model_parent

    parent = bind_design_model_parent(
        scan,
        actor_id="operator-1",
        reason="Select exact captured tube parent.",
        created_at_utc=NOW,
    )
    return scan, parent


def _captured_diameter_measurement(
    normalized_revision: str = "normalized-tube-r1",
) -> CrossSectionMeasurement:
    count = 64
    points = tuple(
        (
            17.5 * math.cos(math.tau * index / count),
            17.5 * math.sin(math.tau * index / count),
            0.0,
        )
        for index in range(count)
    )
    geometry = NormalizedMeasurementGeometry(
        normalized_revision,
        "captured-tube-geometry-r1",
        points,
        ScaleState.METRIC_UNVERIFIED,
        "mm_unverified",
        SCALE_ID,
        0.02,
        "mm_per_reconstruction_unit",
    )
    selection = CrossSectionSelection(
        "tube-body-section-r1",
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        tuple(range(count)),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        1e-8,
    )
    return measure_cross_section(
        geometry,
        selection,
        current_geometry_id=geometry.source_geometry_id,
        current_normalized_geometry_revision=geometry.normalized_geometry_revision,
        current_scale_provenance_id=SCALE_ID,
    )


def _mixed_evidence():
    sources = []
    measurement = _captured_diameter_measurement()
    for name in (
        "body_length",
        "body_diameter",
        "shoulder_length",
        "shoulder_diameter",
        "neck_length",
        "neck_diameter",
        "cap_height",
        "cap_diameter",
        "crimp_length",
        "crimp_thickness",
    ):
        value = getattr(DIMENSIONS, name)
        if name == "body_diameter":
            sources.append(
                TubeDimensionEvidence.from_captured_measurement(
                    name,
                    measurement,
                    value_field="major_diameter",
                    captured_scan_master_revision_id=SCAN_ID,
                )
            )
        else:
            sources.append(
                TubeDimensionEvidence.from_reference_dimension(
                    name,
                    value,
                    coordinate_unit="mm_unverified",
                    source_id=f"reference:tube:{name}:r1",
                )
            )
    return tuple(sources)


def _standalone_root():
    return create_standalone_design_geometry_root(
        project_id=PROJECT,
        source_kind=StandaloneDesignGeometrySourceKind.REFERENCE_DIMENSIONS,
        source_provenance_id="reference:tube-dimension-set:r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="unit-selection:mm-unverified",
        actor_id="operator-1",
        reason="Use explicitly referenced nominal tube dimensions.",
        created_at_utc=NOW,
    )


def test_mixed_tube_fit_keeps_capture_reference_and_model_sources_separate() -> None:
    scan, parent = _captured_parent()
    kwargs = {
        "authority_mode": TubeFitAuthorityMode.CAPTURED_SCAN_MASTER,
        "component_id": "captured-tube-fit",
        "actor_id": "operator-1",
        "reason": "Fit nominal tube dimensions from separately typed sources.",
        "created_at_utc": NOW,
        "scan_master": scan,
    }
    first = fit_tube_family(parent, DIMENSIONS, _mixed_evidence(), **kwargs)
    second = fit_tube_family(parent, DIMENSIONS, _mixed_evidence(), **kwargs)
    payload = first.as_dict()
    assert first.revision_id == second.revision_id
    assert first.family.model.revision_id == second.family.model.revision_id
    assert first.authority_mode is TubeFitAuthorityMode.CAPTURED_SCAN_MASTER
    assert len(payload["captured_measurements"]) == 1
    assert len(payload["reference_dimensions"]) == 9
    assert payload["user_authored_dimensions"] == []
    assert len(payload["modeled_parameters"]) == 10
    assert payload["captured_measurements"][0]["captured_scan_master_revision_id"] == SCAN_ID
    assert payload["captured_measurements"][0]["measurement_artifact_type"] == (
        "CrossSectionMeasurement"
    )
    assert payload["parent_authority"]["scan_master_revision_id"] == SCAN_ID
    assert payload["parent_authority"]["scan_master_geometry_sha256"] == mesh_sha256(scan.mesh)
    assert payload["flexible_wall_deformation_inferred"] is False
    assert payload["wall_thickness_inferred"] is False
    assert payload["material_inferred"] is False
    assert payload["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    with pytest.raises(TubeFittingError, match="revision_id_mismatch"):
        replace(first, revision_id="tube-fit:tampered")


def test_reference_only_tube_fit_uses_explicit_standalone_authority_and_unverified_units() -> None:
    evidence = tuple(
        TubeDimensionEvidence.from_reference_dimension(
            name,
            getattr(DIMENSIONS, name),
            coordinate_unit="mm_unverified",
            source_id=f"reference:tube:{name}:r1",
        )
        for name in (
            "body_length",
            "body_diameter",
            "shoulder_length",
            "shoulder_diameter",
            "neck_length",
            "neck_diameter",
            "cap_height",
            "cap_diameter",
            "crimp_length",
            "crimp_thickness",
        )
    )
    fit = fit_tube_family(
        _standalone_root(),
        DIMENSIONS,
        evidence,
        authority_mode=TubeFitAuthorityMode.STANDALONE_DESIGN_GEOMETRY,
        component_id="reference-tube-fit",
        actor_id="operator-1",
        reason="Fit tube to explicitly sourced nominal reference dimensions.",
        created_at_utc=NOW,
    )
    payload = fit.as_dict()
    assert payload["parent_authority_mode"] == "STANDALONE_DESIGN_GEOMETRY"
    assert payload["captured_measurements"] == []
    assert len(payload["reference_dimensions"]) == 10
    assert fit.family.model.coordinate_unit == "mm_unverified"
    assert fit.family.model.standalone_root == _standalone_root()
    assert fit.family.model.fitted_to_scan_master_revision_id is None
    assert "scan_master_revision_id" not in fit.as_dict()["parent_authority"]
    assert fit.as_dict()["coordinate_unit"] == "mm_unverified"


def test_user_authored_inputs_keep_their_source_class_under_standalone_root() -> None:
    authored_root = create_standalone_design_geometry_root(
        project_id=PROJECT,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="operator-dimension-set:r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="unit-selection:mm-unverified",
        actor_id="operator-1",
        reason="Author nominal tube dimensions directly.",
        created_at_utc=NOW,
    )
    evidence = tuple(
        TubeDimensionEvidence.from_reference_dimension(
            name,
            getattr(DIMENSIONS, name),
            coordinate_unit="mm_unverified",
            source_id=f"operator-input:tube:{name}:r1",
            user_authored=True,
        )
        for name in (
            "body_length",
            "body_diameter",
            "shoulder_length",
            "shoulder_diameter",
            "neck_length",
            "neck_diameter",
            "cap_height",
            "cap_diameter",
            "crimp_length",
            "crimp_thickness",
        )
    )
    fit = fit_tube_family(
        authored_root,
        DIMENSIONS,
        evidence,
        authority_mode=TubeFitAuthorityMode.STANDALONE_DESIGN_GEOMETRY,
        component_id="user-authored-tube-fit",
        actor_id="operator-1",
        reason="Fit user-authored nominal tube dimensions.",
        created_at_utc=NOW,
    )
    assert fit.as_dict()["captured_measurements"] == []
    assert fit.as_dict()["reference_dimensions"] == []
    assert len(fit.as_dict()["user_authored_dimensions"]) == 10


def test_tube_fit_rejects_missing_contradictory_mixed_parent_and_unit_evidence() -> None:
    scan, captured_parent = _captured_parent()
    evidence = _mixed_evidence()
    kwargs = {
        "authority_mode": TubeFitAuthorityMode.CAPTURED_SCAN_MASTER,
        "component_id": "tube-fit-invalid",
        "actor_id": "operator-1",
        "reason": "Validate fail-closed tube fit inputs.",
        "created_at_utc": NOW,
        "scan_master": scan,
    }
    with pytest.raises(TubeFittingError, match="dimension_evidence_incomplete"):
        fit_tube_family(captured_parent, DIMENSIONS, evidence[:-1], **kwargs)
    contradictory = (
        TubeDimensionEvidence.from_reference_dimension(
            "body_length",
            91.0,
            coordinate_unit="mm_unverified",
            source_id="reference:tube:conflict:r1",
        ),
        *evidence[1:],
    )
    with pytest.raises(TubeFittingError, match="dimension_evidence_contradictory"):
        fit_tube_family(captured_parent, DIMENSIONS, contradictory, **kwargs)
    with pytest.raises(TubeFittingError, match="standalone_tube_fit_cannot_claim_captured"):
        fit_tube_family(
            _standalone_root(),
            DIMENSIONS,
            evidence,
            authority_mode=TubeFitAuthorityMode.STANDALONE_DESIGN_GEOMETRY,
            component_id="tube-fit-standalone-mixed",
            actor_id="operator-1",
            reason="Stand-alone source cannot claim captured fit inputs.",
            created_at_utc=NOW,
        )
    with pytest.raises(TubeFittingError, match="captured_tube_fit_parent_binding_required"):
        fit_tube_family(
            _standalone_root(),
            DIMENSIONS,
            evidence,
            authority_mode=TubeFitAuthorityMode.CAPTURED_SCAN_MASTER,
            component_id="tube-fit-wrong-mode",
            actor_id="operator-1",
            reason="Reject selected mode mismatch.",
            created_at_utc=NOW,
            scan_master=scan,
        )
    captured_entry = next(
        item for item in evidence if item.source_kind.value == "CAPTURED_MEASUREMENT"
    )
    wrong_scan_evidence = tuple(
        replace(item, captured_scan_master_revision_id="scan-master:other")
        if item is captured_entry
        else item
        for item in evidence
    )
    with pytest.raises(TubeFittingError, match="measurement_scan_master_mismatch"):
        fit_tube_family(captured_parent, DIMENSIONS, wrong_scan_evidence, **kwargs)
    wrong_unit_evidence = tuple(
        replace(item, coordinate_unit="reconstruction_units")
        if item.source_kind.value == "REFERENCE_DIMENSION"
        else item
        for item in evidence
    )
    with pytest.raises(TubeFittingError, match="dimension_unit_mismatch"):
        fit_tube_family(captured_parent, DIMENSIONS, wrong_unit_evidence, **kwargs)


def test_tube_fit_rejects_measurements_from_another_normalized_parent() -> None:
    scan, parent = _captured_parent()
    wrong_measurement = _captured_diameter_measurement("normalized-tube-other")
    evidence = tuple(
        TubeDimensionEvidence.from_captured_measurement(
            item.parameter_id,
            wrong_measurement,
            value_field="major_diameter",
            captured_scan_master_revision_id=SCAN_ID,
        )
        if item.source_kind.value == "CAPTURED_MEASUREMENT"
        else item
        for item in _mixed_evidence()
    )
    with pytest.raises(TubeFittingError, match="measurement_geometry_parent_mismatch"):
        fit_tube_family(
            parent,
            DIMENSIONS,
            evidence,
            authority_mode=TubeFitAuthorityMode.CAPTURED_SCAN_MASTER,
            component_id="wrong-normalized-parent",
            actor_id="operator-1",
            reason="Reject stale normalized measurement ancestry.",
            created_at_utc=NOW,
            scan_master=scan,
        )
