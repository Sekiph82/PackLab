from __future__ import annotations

import hashlib
import typing

import pytest

from packlab_core import cad_adapter
from packlab_core.cross_section import CrossSectionSymmetry, SectionPoint, create_cross_section
from packlab_core.design_model import PackageFamily, create_design_model_revision
from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    bind_design_model_parent,
    create_standalone_design_geometry_root,
)
from packlab_core.design_profile import ProfilePoint, create_design_profile
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT_ID = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
NOW = "2026-10-04T12:00:00Z"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _captured_model(scale_state: ScaleState) -> object:
    scan_id = f"scan-master:{hashlib.sha256(scale_state.value.encode()).hexdigest()}"
    scan = ScanMasterRevision(
        scan_id,
        PROJECT_ID,
        MESH,
        {
            "scan_master_revision_id": scan_id,
            "project_id": PROJECT_ID,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(MESH),
            "reconstruction_revision_id": "reconstruction:cad-fixture",
            "scale_state": scale_state.value,
            "scale_provenance_id": "scale-provenance:cad-fixture",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    parent = bind_design_model_parent(
        scan,
        actor_id="operator-1",
        reason="Bind CAD adapter fixture to exact Scan Master.",
        created_at_utc=NOW,
    )
    return create_design_model_revision(
        parent,
        package_family=PackageFamily.BOTTLE,
        actor_id="operator-1",
        reason="CAD adapter fixture.",
        created_at_utc=NOW,
    )


def _standalone_model(scale_state: ScaleState) -> object:
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    root = create_standalone_design_geometry_root(
        project_id=PROJECT_ID,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="nominal-input:cad-fixture",
        scale_state=scale_state,
        unit_provenance_id=f"unit-choice:{unit}",
        actor_id="operator-1",
        reason="Create standalone CAD adapter fixture.",
        created_at_utc=NOW,
    )
    from packlab_core.design_model import create_standalone_design_model_revision

    return create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.OTHER,
        actor_id="operator-1",
        reason="CAD adapter fixture.",
        created_at_utc=NOW,
    )


@pytest.mark.parametrize(
    ("scale_state", "expected_unit"),
    [
        (ScaleState.RELATIVE, "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
    ],
)
def test_profile_conversion_is_deterministic_and_preserves_scale(
    scale_state: ScaleState, expected_unit: str
) -> None:
    profile = create_design_profile(
        (ProfilePoint(0.0, 2.0, 0.0), ProfilePoint(8.0, 3.0, 0.25)), scale_state
    )

    first = cad_adapter.profile_to_cad_input(profile)
    second = cad_adapter.profile_to_cad_input(profile)

    assert first == second
    assert first.source_profile_id == profile.profile_id
    assert tuple((point.axial, point.radius, point.tangent) for point in first.points) == (
        (0.0, 2.0, 0.0),
        (8.0, 3.0, 0.25),
    )
    assert first.scale_state is scale_state
    assert first.coordinate_unit == expected_unit
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.mold_use_authorized is False


@pytest.mark.parametrize(
    ("scale_state", "expected_unit"),
    [
        (ScaleState.RELATIVE, "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
    ],
)
def test_cross_section_conversion_preserves_order_symmetry_and_scale(
    scale_state: ScaleState, expected_unit: str
) -> None:
    section = create_cross_section(
        "container",
        (
            SectionPoint(-2.0, -1.0),
            SectionPoint(2.0, -1.0),
            SectionPoint(1.0, 2.0),
            SectionPoint(-2.0, 1.0),
        ),
        symmetry=CrossSectionSymmetry.NONE,
        scale_state=scale_state,
    )

    converted = cad_adapter.cross_section_to_cad_input(section)

    assert converted.source_section_id == section.section_id
    assert converted.component_id == "container"
    assert tuple((point.x, point.y) for point in converted.points) == tuple(
        (point.x, point.y) for point in section.points
    )
    assert converted.symmetry == CrossSectionSymmetry.NONE.value
    assert converted.scale_state is scale_state
    assert converted.coordinate_unit == expected_unit
    assert converted.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert converted.mold_use_authorized is False


@pytest.mark.parametrize(
    ("parent_kind", "scale_state"),
    [
        ("captured", ScaleState.RELATIVE),
        ("captured", ScaleState.METRIC_UNVERIFIED),
        ("standalone", ScaleState.RELATIVE),
        ("standalone", ScaleState.METRIC_UNVERIFIED),
    ],
)
def test_shape_handle_pins_design_model_parent_and_never_promotes_authority(
    parent_kind: str, scale_state: ScaleState
) -> None:
    model = (
        _captured_model(scale_state)
        if parent_kind == "captured"
        else _standalone_model(scale_state)
    )
    expected_parent = (
        model.parent_binding_revision_id
        if parent_kind == "captured"
        else model.standalone_root.revision_id
    )

    handle = cad_adapter.shape_handle_for_model("cad-shape:opaque-1", model)

    assert handle.source_design_model_revision_id == model.revision_id
    assert handle.parent_authority_revision_id == expected_parent
    assert handle.parent_kind is model.parent_kind
    assert handle.scale_state is scale_state
    assert handle.coordinate_unit == model.coordinate_unit
    assert handle.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert handle.mold_use_authorized is False
    assert not any(
        "OCP" in str(annotation) for annotation in typing.get_type_hints(type(handle)).values()
    )


def test_unavailable_binding_is_reported_without_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable() -> object:
        raise ModuleNotFoundError("OCP deliberately unavailable")

    monkeypatch.setattr(cad_adapter, "_import_binding_module", unavailable)

    diagnostics = cad_adapter.probe_cad_runtime()

    assert diagnostics.status is cad_adapter.CadRuntimeStatus.UNAVAILABLE
    assert diagnostics.binding_version is None
    assert diagnostics.kernel_version is None
    assert diagnostics.error_code == "binding_import_unavailable"
    assert diagnostics.capabilities
    assert all(
        item.status is cad_adapter.CadCapabilityStatus.UNAVAILABLE
        and item.error_code == "binding_import_unavailable"
        for item in diagnostics.capabilities
    )


def test_capability_failure_is_reported_independently(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cad_adapter,
        "_CAPABILITY_PROBES",
        (("brep_construction", lambda: (_ for _ in ()).throw(RuntimeError("probe failure"))),),
    )

    diagnostics = cad_adapter.probe_cad_runtime()

    assert diagnostics.status is cad_adapter.CadRuntimeStatus.PARTIAL
    assert diagnostics.capability("brep_construction") == cad_adapter.CadCapability(
        "brep_construction", cad_adapter.CadCapabilityStatus.ERROR, "RuntimeError"
    )


def test_selected_binding_reports_real_kernel_versions_and_capabilities() -> None:
    diagnostics = cad_adapter.probe_cad_runtime()

    assert diagnostics.status is cad_adapter.CadRuntimeStatus.READY
    assert diagnostics.binding_package == "cadquery-ocp-novtk"
    assert diagnostics.binding_version == "7.9.3.1.1"
    assert diagnostics.binding_version_status == "OBSERVED"
    assert diagnostics.kernel_version == "7.9.3"
    assert diagnostics.kernel_version_status == "OBSERVED"
    assert diagnostics.platform_system == "Windows"
    assert diagnostics.platform_machine in {"AMD64", "x86_64"}
    assert {item.name for item in diagnostics.capabilities} == {
        "brep_construction",
        "revolve",
        "loft",
        "booleans",
        "topology_validation",
        "tessellation",
        "step_write",
        "step_read",
        "stl_write",
    }
    assert all(
        item.status is cad_adapter.CadCapabilityStatus.AVAILABLE
        for item in diagnostics.capabilities
    )


def test_public_adapter_contracts_do_not_expose_backend_types() -> None:
    public_types = (
        cad_adapter.CadCapability,
        cad_adapter.CadRuntimeDiagnostics,
        cad_adapter.CadProfileControlPoint,
        cad_adapter.CadProfileInput,
        cad_adapter.CadPoint2,
        cad_adapter.CadCrossSectionInput,
        cad_adapter.CadShapeHandle,
    )
    for contract in public_types:
        assert all(
            "OCP" not in str(annotation) for annotation in typing.get_type_hints(contract).values()
        )
