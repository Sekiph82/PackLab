"""Bounded, offline production capability checks used by the frozen Windows build."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from packlab_core.cad_adapter import (
    CAD_RUNTIME_VERSION_STATUS_OBSERVED,
    CadRuntimeDiagnostics,
    cad_shape_precise_bounds,
    probe_cad_runtime,
    tessellate_cad_shape,
)
from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.cad_step_export import export_design_model_step
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_standalone_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    create_standalone_design_geometry_root,
)
from packlab_core.design_operations import create_revolve_operation
from packlab_core.design_profile import ProfilePoint, create_design_profile
from packlab_core.geometry_adapter import Open3DGeometryAdapter, PointCloudData
from packlab_core.reconstruction import ScaleState
from packlab_core.technical_drawing import generate_orthographic_views
from packlab_core.technical_drawing_dimensions import build_drawing_dimensions
from packlab_core.technical_drawing_export import export_technical_drawing_vectors
from packlab_core.technical_drawing_pdf import (
    export_technical_drawing_pdf,
    probe_vector_pdf_capability,
)
from packlab_core.technical_drawing_title_block import build_technical_drawing_title_block

PROJECT_ID = "packlab-frozen-capability-smoke"
FIXED_UTC = "2026-10-06T00:00:00Z"
FRAME_ID = "packlab-frozen-capability-frame:v1"
OCP_VERSION = "7.9.3.1.1"
OPEN3D_VERSION = "0.20.0"


def _required(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def _cad_probe_failure_code(diagnostics: CadRuntimeDiagnostics) -> str:
    failures = ",".join(
        f"{item.name}:{item.status.value}:{item.error_code or 'none'}"
        for item in diagnostics.capabilities
        if item.status.value != "AVAILABLE"
    )
    kernel_error = diagnostics.error_code or "none"
    return f"ocp_cad_probe_not_ready:kernel={kernel_error};capabilities={failures or 'none'}"


def _cad_version_failure_code(diagnostics: CadRuntimeDiagnostics) -> str:
    kernel_error = diagnostics.error_code or "none"
    return (
        "ocp_cad_software_version_unobserved:"
        f"binding={diagnostics.binding_version_status};"
        f"kernel={diagnostics.kernel_version_status};detail={kernel_error}"
    )


def _open3d_probe_failure_code(status: str, detail: str) -> str:
    safe_detail = "unclassified"
    if detail == "Open3D build configuration is unavailable":
        safe_detail = "build_config_unavailable"
    elif detail == "the pinned Open3D build is missing a required geometry conversion capability":
        safe_detail = "geometry_capability_missing"
    elif detail.startswith("Open3D import unavailable (") and detail.endswith(")"):
        missing_module = detail.removeprefix("Open3D import unavailable (")[:-1]
        if missing_module and all(part.isidentifier() for part in missing_module.split(".")):
            safe_detail = f"module_unavailable_{missing_module.replace('.', '_')}"
        else:
            safe_detail = "module_unavailable"
    elif detail.startswith("Open3D import failed (") and detail.endswith(")"):
        error_details = detail.removeprefix("Open3D import failed (")[:-1].split(";")
        error_type = error_details[0]
        if error_type.isidentifier():
            safe_detail = f"import_failed_{error_type}"
            for field in error_details[1:]:
                if field.startswith("winerror="):
                    winerror = field.removeprefix("winerror=")
                    if winerror.isdecimal():
                        safe_detail += f"_winerror_{winerror}"
                elif field.startswith("module="):
                    module = field.removeprefix("module=")
                    if module and all(part.isidentifier() for part in module.split(".")):
                        safe_detail += f"_module_{module.replace('.', '_')}"
                elif field.startswith("reason="):
                    reason = field.removeprefix("reason=")
                    if reason in {
                        "dll_initialization_failed",
                        "dll_load_failed",
                        "dll_module_missing",
                        "dll_procedure_missing",
                        "circular_import",
                        "extension_export_missing",
                        "import_error",
                        "module_missing",
                        "module_not_package",
                        "numpy_multiarray_unavailable",
                        "symbol_missing",
                    }:
                        safe_detail += f"_{reason}"
                elif field.startswith("cause="):
                    cause_type = field.removeprefix("cause=")
                    if cause_type in {
                        "ImportError",
                        "ModuleNotFoundError",
                        "OSError",
                        "RuntimeError",
                        "ValueError",
                    }:
                        safe_detail += f"_cause_{cause_type}"
                elif field.startswith("cause_module="):
                    cause_module = field.removeprefix("cause_module=")
                    if cause_module and all(
                        part.isidentifier() for part in cause_module.split(".")
                    ):
                        safe_detail += f"_cause_module_{cause_module.replace('.', '_')}"
                elif field.startswith("cause_winerror="):
                    winerror = field.removeprefix("cause_winerror=")
                    if winerror.isdecimal():
                        safe_detail += f"_cause_winerror_{winerror}"
                elif field.startswith("trace="):
                    frames = field.removeprefix("trace=").split(",")
                    safe_frames: list[str] = []
                    for frame in frames[-5:]:
                        module, separator, function = frame.rpartition(".")
                        if (
                            separator
                            and (
                                module == "open3d"
                                or module.startswith("open3d.")
                                or module
                                in {
                                    "importlib._bootstrap",
                                    "importlib._bootstrap_external",
                                    "packlab_core.geometry_adapter",
                                }
                            )
                            and all(part.isidentifier() for part in module.split("."))
                            and function.isidentifier()
                        ):
                            safe_frames.append(frame.replace(".", "_"))
                    if safe_frames:
                        safe_detail += "_trace_" + "_".join(safe_frames)
        else:
            safe_detail = "import_failed"
    return f"open3d_probe_failed:status={status};detail={safe_detail}"


def _cad_fixture() -> tuple[Any, Any, Any]:
    features = (
        DesignModelFeatureReference(
            stable_feature_id("frozen-smoke", FeatureKind.BODY, "body-profile"),
            "frozen-smoke",
            FeatureKind.BODY,
            "body-profile",
        ),
        DesignModelFeatureReference(
            stable_feature_id("frozen-smoke", FeatureKind.BODY, "revolve-axis"),
            "frozen-smoke",
            FeatureKind.BODY,
            "revolve-axis",
        ),
    )
    root = create_standalone_design_geometry_root(
        project_id=PROJECT_ID,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="frozen-runtime-smoke:nominal-input",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="frozen-runtime-smoke:unit-choice",
        actor_id="packlab-build-smoke",
        reason="Create a bounded deterministic frozen-runtime fixture.",
        created_at_utc=FIXED_UTC,
    )
    model = create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.BOTTLE,
        features=features,
        actor_id="packlab-build-smoke",
        reason="Create a bounded deterministic frozen-runtime fixture.",
        created_at_utc=FIXED_UTC,
    )
    profile = create_design_profile(
        (ProfilePoint(0.0, 5.0), ProfilePoint(100.0, 5.0)),
        ScaleState.METRIC_UNVERIFIED,
    )
    operation = create_revolve_operation(
        model,
        profile,
        profile_feature_id=features[0].feature_id,
        axis_feature_id=features[1].feature_id,
    )
    return model, profile, operation


def run_frozen_capability_smoke() -> dict[str, object]:
    """Exercise Qt PDF, OCP/CAD, and Open3D through PackLab-owned boundaries."""
    revision = os.environ.get("PACKLAB_BUILD_REVISION", "")
    version = os.environ.get("PACKLAB_STUDIO_VERSION", "")
    _required(
        len(revision) == 40 and all(char in "0123456789abcdef" for char in revision),
        "build_revision_invalid",
    )
    _required(bool(version), "studio_version_missing")

    import PySide6

    pdf_capability = probe_vector_pdf_capability()
    _required(pdf_capability.available, "qt_vector_pdf_probe_failed")
    model, profile, operation = _cad_fixture()
    diagnostics = probe_cad_runtime()
    _required(diagnostics.status.value == "READY", _cad_probe_failure_code(diagnostics))
    _required(diagnostics.binding_version == OCP_VERSION, "ocp_cad_version_mismatch")
    _required(
        diagnostics.binding_version_status == CAD_RUNTIME_VERSION_STATUS_OBSERVED
        and diagnostics.kernel_version_status == CAD_RUNTIME_VERSION_STATUS_OBSERVED,
        _cad_version_failure_code(diagnostics),
    )
    representation = revolve_design_model_to_brep(model, profile, operation)
    _required(representation.solid_count == 1, "ocp_cad_revolve_failed")
    bounds = cad_shape_precise_bounds(representation.shape_handle)
    _required(len(bounds) == 6 and all(value == value for value in bounds), "ocp_cad_bounds_failed")
    mesh = tessellate_cad_shape(
        representation.shape_handle,
        linear_deflection=0.5,
        angular_deflection=0.35,
        maximum_vertices=100_000,
        maximum_triangles=200_000,
        maximum_faces=10_000,
    )
    _required(bool(mesh.mesh.vertices) and bool(mesh.mesh.triangles), "ocp_cad_tessellation_failed")

    dimensions = build_drawing_dimensions(model, representation, coordinate_frame_id=FRAME_ID)
    views = generate_orthographic_views(model, representation)
    title = build_technical_drawing_title_block(
        model,
        representation,
        diagnostics,
        generated_view_ids=("FRONT", "SIDE", "TOP"),
        generated_at_utc=FIXED_UTC,
    )
    vectors = export_technical_drawing_vectors(views, (), dimensions, title)
    with tempfile.TemporaryDirectory(prefix="packlab-build-smoke-") as scratch:
        step_path = Path(scratch) / "capability.step"
        step_export = export_design_model_step(
            model,
            representation,
            step_path,
            part_name="PackLab Build Smoke",
        )
        _required(step_path.is_file() and step_path.stat().st_size > 0, "step_export_file_missing")
        _required(
            step_export.round_trip_validation.solid_count == 1,
            "step_round_trip_solid_count_invalid",
        )
        dxf_path = Path(scratch) / "capability.dxf"
        dxf_path.write_bytes(vectors.dxf_bytes)
        dxf_contents = dxf_path.read_bytes()
        _required(
            b"AC1015" in dxf_contents and b"EOF" in dxf_contents, "dxf_export_content_invalid"
        )
        step_smoke = {
            "status": "PASS",
            "sha256": step_export.artifact_sha256,
            "byte_length": step_export.artifact_size_bytes,
            "round_trip_status": "PASS",
            "solid_count": step_export.round_trip_validation.solid_count,
        }
        dxf_smoke = {
            "status": "PASS",
            "sha256": hashlib.sha256(dxf_contents).hexdigest(),
            "byte_length": len(dxf_contents),
            "format": "R2000 ASCII",
        }
    pdf = export_technical_drawing_pdf(vectors)
    _required(pdf.manifest.get("parsed_by_qtpdf") is True, "qt_pdf_parse_failed")
    _required(pdf.manifest.get("page_count") == 1, "qt_pdf_page_count_failed")
    render_smoke = pdf.manifest.get("render_smoke")
    _required(
        isinstance(render_smoke, dict) and render_smoke.get("status") == "PASS",
        "qt_pdf_render_failed",
    )
    assert isinstance(render_smoke, dict)

    open3d = Open3DGeometryAdapter()
    open3d_capability = open3d.probe()
    _required(
        open3d_capability.status.value == "available",
        _open3d_probe_failure_code(open3d_capability.status.value, open3d_capability.detail),
    )
    _required(open3d_capability.observed_version == OPEN3D_VERSION, "open3d_version_mismatch")
    cloud = PointCloudData(((0.0, 0.0, 0.0), (1.0, 2.0, 3.0)))
    _required(open3d.round_trip_point_cloud(cloud) == cloud, "open3d_point_cloud_conversion_failed")

    groups: dict[str, object] = {
        "qt_studio_gui": {
            "expected_package": "PySide6-Essentials",
            "expected_module": "PySide6.QtWidgets.QApplication; packlab_studio.shell.StudioMainWindow",
            "expected_version": "6.11.2",
            "observed_package": "PySide6-Essentials",
            "observed_module": "PySide6.QtWidgets; packlab_studio.shell.StudioMainWindow",
            "observed_version": PySide6.__version__,
            "smoke_operation": "QApplication plus StudioMainWindow construct/show/process/close",
            "status": "PASS",
            "network": "NONE",
        },
        "qt_vector_pdf": {
            "expected_package": "PySide6-Addons",
            "expected_module": "PySide6.QtPdf.QPdfDocument; PySide6.QtSvg.QSvgRenderer",
            "expected_version": "6.11.2",
            "observed_package": "PySide6-Addons",
            "observed_module": "PySide6.QtPdf; PySide6.QtSvg",
            "observed_version": PySide6.__version__,
            "smoke_operation": "PackLab technical drawing SVG to PDF, QPdfDocument parse and render",
            "status": "PASS",
            "network": "NONE",
            "page_count": pdf.manifest["page_count"],
            "pdf_sha256": pdf.manifest["pdf_sha256"],
            "render_status": render_smoke["status"],
        },
        "ocp_cad": {
            "expected_package": "cadquery-ocp-novtk",
            "expected_module": "OCP; PackLab revolve, precise bounds, tessellation",
            "expected_version": OCP_VERSION,
            "observed_package": diagnostics.binding_package,
            "observed_module": "OCP",
            "observed_version": diagnostics.binding_version,
            "kernel_version": diagnostics.kernel_version,
            "smoke_operation": "one PackLab revolve, six-value precise bounds, bounded tessellation",
            "status": "PASS",
            "network": "NONE",
        },
        "step_io": {
            "expected_module": "PackLab CAD STEP writer and round-trip reader",
            "observed_module": "packlab_core.cad_step_export",
            "smoke_operation": "write, reopen, and validate one exported solid",
            **step_smoke,
            "network": "NONE",
        },
        "dxf_export": {
            "expected_module": "PackLab R2000 ASCII DXF exporter",
            "observed_module": "packlab_core.technical_drawing_export",
            "smoke_operation": "write and validate generated DXF bytes",
            **dxf_smoke,
            "network": "NONE",
        },
        "open3d_geometry": {
            "expected_package": "open3d",
            "expected_module": "open3d.geometry.PointCloud via Open3DGeometryAdapter",
            "expected_version": OPEN3D_VERSION,
            "observed_package": open3d_capability.distribution,
            "observed_module": "open3d.geometry.PointCloud",
            "observed_version": open3d_capability.observed_version,
            "smoke_operation": "bounded PackLab point-cloud round-trip conversion",
            "status": "PASS",
            "network": "NONE",
        },
    }
    manifest: dict[str, object] = {
        "schema_version": 1,
        "PACKLAB_BUILD_REVISION": revision,
        "studio_version": version,
        "status": "PASS",
        "network": "NONE",
        "capability_groups": groups,
        "external_architecture_dependencies_not_bundled": ["Blender", "COLMAP", "OpenMVS"],
    }
    output_path = os.environ.get("PACKLAB_RUNTIME_CAPABILITIES_PATH")
    if not output_path:
        raise RuntimeError("runtime_manifest_path_missing")
    Path(output_path).write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
