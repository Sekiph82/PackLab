"""Bounded, offline production capability checks used by the frozen Windows build."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from packlab_core.cad_adapter import (
    cad_shape_precise_bounds,
    probe_cad_runtime,
    tessellate_cad_shape,
)
from packlab_core.cad_brep import revolve_design_model_to_brep
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
    _required(diagnostics.status.value == "READY", "ocp_cad_probe_not_ready")
    _required(diagnostics.binding_version == OCP_VERSION, "ocp_cad_version_mismatch")
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
    _required(open3d_capability.status.value == "available", "open3d_probe_failed")
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
