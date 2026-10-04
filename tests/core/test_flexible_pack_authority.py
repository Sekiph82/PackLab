from __future__ import annotations

import pytest

from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    bind_design_model_parent,
    create_standalone_design_geometry_root,
)
from packlab_core.flexible_pack_authority import (
    FlexiblePackAuthorityError,
    flexible_pack_authority_handoff,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.measurement_report import (
    MeasurementReportContext,
    MeasurementReportError,
    build_measurement_report,
    render_measurement_report_markdown,
)
from packlab_core.pouch_family import PouchFamilyDimensions, build_pouch_family
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.tube_family import TubeFamilyDimensions, build_tube_family

PROJECT = "flexible-pack-authority-project"
NOW = "2026-10-04T12:00:00Z"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _standalone_model():
    root = create_standalone_design_geometry_root(
        project_id=PROJECT,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="nominal-input:pouch-session",
        scale_state=ScaleState.RELATIVE,
        unit_provenance_id="unit-selection:relative",
        actor_id="operator-1",
        reason="Create an authored flexible-pack design root.",
        created_at_utc=NOW,
    )
    return build_pouch_family(
        root,
        PouchFamilyDimensions(120.0, 180.0, 8.0, 10.0, 12.0, 6.0, 6.0),
        component_id="pouch-main",
        actor_id="operator-1",
        reason="Create a nominal pouch design.",
        created_at_utc=NOW,
    ).model


def _captured_tube_family():
    scan_id = "scan-master:flexible-fixture"
    scan = ScanMasterRevision(
        scan_id,
        PROJECT,
        MESH,
        {
            "scan_master_revision_id": scan_id,
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(MESH),
            "reconstruction_revision_id": "reconstruction:flexible-fixture",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-provenance:flexible-fixture",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    parent = bind_design_model_parent(
        scan,
        actor_id="operator-1",
        reason="Select the exact test Scan Master.",
        created_at_utc=NOW,
    )
    return build_tube_family(
        parent,
        TubeFamilyDimensions(100.0, 40.0, 15.0, 28.0, 10.0, 12.0, 16.0, 14.0, 8.0, 2.0),
        component_id="tube-main",
        actor_id="operator-1",
        reason="Create the scan-bound test tube design.",
        created_at_utc=NOW,
    )


def _captured_model():
    return _captured_tube_family().model


def test_authority_handoff_discloses_explicit_standalone_and_captured_parents():
    standalone = _standalone_model()
    captured = _captured_model()
    standalone_payload = flexible_pack_authority_handoff(standalone)
    captured_payload = flexible_pack_authority_handoff(captured)

    assert standalone_payload == flexible_pack_authority_handoff(standalone)
    assert standalone_payload["parent_authority"]["kind"] == "STANDALONE_DESIGN_GEOMETRY"  # type: ignore[index]
    assert standalone_payload["parent_authority"]["captured_ancestry_exists"] is False  # type: ignore[index]
    assert "scan_master_revision_id" not in standalone_payload["parent_authority"]  # type: ignore[operator]
    assert captured_payload["parent_authority"]["kind"] == "CAPTURED_SCAN_MASTER"  # type: ignore[index]
    assert (
        captured_payload["parent_authority"]["scan_master_revision_id"]
        == "scan-master:flexible-fixture"
    )  # type: ignore[index]
    for payload in (standalone_payload, captured_payload):
        assert payload["scan_master_promotion_allowed"] is False
        assert payload["captured_geometry_authority"] is False
        assert payload["mold_use_authorized"] is False
        assert payload["manufacturing_authority"] is False
        assert payload["certified_volume_claimed"] is False
        assert payload["physical_tolerance_claimed"] is False
        assert payload["metadata_only_handoff"] is True
    pouch_payload = build_pouch_family(
        create_standalone_design_geometry_root(
            project_id=PROJECT,
            source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
            source_provenance_id="nominal-input:pouch-session",
            scale_state=ScaleState.RELATIVE,
            unit_provenance_id="unit-selection:relative",
            actor_id="operator-1",
            reason="Create an authored flexible-pack design root.",
            created_at_utc=NOW,
        ),
        PouchFamilyDimensions(120.0, 180.0, 8.0, 10.0, 12.0, 6.0, 6.0),
        component_id="pouch-main",
        actor_id="operator-1",
        reason="Create a nominal pouch design.",
        created_at_utc=NOW,
    ).as_dict()
    assert pouch_payload["authority_and_limitations"] == standalone_payload
    assert (
        pouch_payload["preview"]["authority_and_limitations"]["flexible_pack_design_only"] is True
    )  # type: ignore[index]
    captured_preview = _captured_tube_family().preview.as_dict()
    assert captured_preview["authority_and_limitations"]["flexible_pack_design_only"] is True  # type: ignore[index]


@pytest.mark.parametrize(
    "target",
    [
        "SCAN_MASTER",
        "CAPTURED_GEOMETRY",
        "MOLD_AUTHORITY",
        "MANUFACTURING_AUTHORITY",
        "CERTIFIED_VOLUME",
        "PHYSICAL_TOLERANCE",
    ],
)
def test_flexible_pack_handoff_rejects_authority_promotion(target):
    with pytest.raises(
        FlexiblePackAuthorityError, match="flexible_pack_authority_promotion_forbidden"
    ):
        flexible_pack_authority_handoff(_standalone_model(), requested_authority=target)


def test_measurement_report_carries_standalone_design_authority_without_capture_claims():
    model = _standalone_model()
    context = MeasurementReportContext(
        project_id=PROJECT,
        project_revision="project-revision:design-only",
        source_revision_id=model.revision_id,
        source_geometry_id=model.revision_id,
        normalized_geometry_revision=model.revision_id,
        scale_provenance_id=None,
        scale_state=ScaleState.RELATIVE,
        coordinate_unit="reconstruction_units",
    )
    report = build_measurement_report(
        context,
        (),
        flexible_pack_model=model,
        expected_flexible_pack_model_revision_id=model.revision_id,
    )
    payload = report.as_dict()
    assert payload["flexible_pack_authority"] == flexible_pack_authority_handoff(model)
    assert payload["authority_and_limitations"]["certified_measurement_claimed"] is False  # type: ignore[index]
    markdown = render_measurement_report_markdown(report)
    assert "Flexible-pack design authority" in markdown
    assert "not certified volume, physical tolerance" in markdown


def test_measurement_report_rejects_stale_or_incomplete_flexible_pack_binding():
    model = _standalone_model()
    context = MeasurementReportContext(
        project_id=PROJECT,
        project_revision="project-revision:design-only",
        source_revision_id=model.revision_id,
        source_geometry_id=model.revision_id,
        normalized_geometry_revision=model.revision_id,
        scale_provenance_id=None,
        scale_state=ScaleState.RELATIVE,
        coordinate_unit="reconstruction_units",
    )
    with pytest.raises(
        MeasurementReportError, match="flexible_pack_report_model_or_context_mismatch"
    ):
        build_measurement_report(
            context,
            (),
            flexible_pack_model=model,
            expected_flexible_pack_model_revision_id="design-model:stale",
        )
    with pytest.raises(MeasurementReportError, match="flexible_pack_model_arguments_incomplete"):
        build_measurement_report(context, (), flexible_pack_model=model)


def test_measurement_report_preserves_captured_parent_mode_without_promotion():
    model = _captured_model()
    context = MeasurementReportContext(
        project_id=PROJECT,
        project_revision="project-revision:captured-design",
        source_revision_id=model.fitted_to_scan_master_revision_id,
        source_geometry_id=model.fitted_to_scan_master_revision_id,
        normalized_geometry_revision=model.fitted_to_scan_master_revision_id,
        scale_provenance_id=model.scale_provenance_id,
        scale_state=model.scale_state,
        coordinate_unit=model.coordinate_unit,
    )
    report = build_measurement_report(
        context,
        (),
        flexible_pack_model=model,
        expected_flexible_pack_model_revision_id=model.revision_id,
    )
    assert (
        report.as_dict()["flexible_pack_authority"]["parent_authority"]["kind"]
        == "CAPTURED_SCAN_MASTER"
    )  # type: ignore[index]
    assert report.as_dict()["flexible_pack_authority"]["scan_master_promotion_allowed"] is False  # type: ignore[index]
