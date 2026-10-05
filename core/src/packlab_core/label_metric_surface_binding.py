"""Exact, fail-closed metric surface bindings and derived label dielines."""

from __future__ import annotations

import hashlib
import importlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .cad_adapter import CadAdapterError, cad_shape_geometry_digest, sample_cad_surface_regions
from .cad_brep import CadBrepRepresentationRevision
from .cad_label_surface_analysis import CadLabelSurfaceAnalysis, analyze_cad_label_surfaces
from .design_model import DesignModelRevision
from .label_zone import LabelZoneKind
from .label_zone_placement import LabelZonePlacementRevision
from .reconstruction import ScaleState

LABEL_METRIC_SURFACE_BINDING_CONTRACT = "packlab.label-metric-surface-binding.v1"
LABEL_DIELINE_CONTRACT = "packlab.label-dieline-revision.v1"
_TOLERANCE = 1e-7


class LabelMetricSurfaceBindingError(ValueError):
    """Raised when exact metric surface authority cannot be established."""


@dataclass(frozen=True, slots=True)
class LabelMetricSurfaceBinding:
    revision_id: str
    zone_id: str
    placement_revision_id: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    parent_kind: str
    parent_authority_revision_id: str
    analysis_revision_id: str
    analysis_region_id: str
    mapping_mode: str
    host_width_mm_unverified: float
    host_height_mm_unverified: float
    mapping_parameters: tuple[tuple[str, float | str], ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.mapping_mode not in {"PLANAR_RECTANGULAR", "CYLINDRICAL_WRAP"}:
            raise LabelMetricSurfaceBindingError("label_metric_mapping_mode_unsupported")
        if (
            self.host_width_mm_unverified <= 0.0
            or self.host_height_mm_unverified <= 0.0
            or not math.isfinite(self.host_width_mm_unverified)
            or not math.isfinite(self.host_height_mm_unverified)
            or any(
                isinstance(value, float) and not math.isfinite(value)
                for _, value in self.mapping_parameters
            )
        ):
            raise LabelMetricSurfaceBindingError("label_metric_dimensions_invalid")
        if self.revision_id != "label-metric-surface-binding:" + _digest(_binding_identity(self)):
            raise LabelMetricSurfaceBindingError("label_metric_binding_identity_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": LABEL_METRIC_SURFACE_BINDING_CONTRACT,
            "authority_class": "DERIVED_METRIC_LABEL_SURFACE_BINDING",
            "revision_id": self.revision_id,
            "zone_id": self.zone_id,
            "placement_revision_id": self.placement_revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep": {
                "revision_id": self.source_brep_revision_id,
                "geometry_sha256": self.source_brep_geometry_sha256,
            },
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "analysis_revision_id": self.analysis_revision_id,
            "analysis_region_id": self.analysis_region_id,
            "mapping_mode": self.mapping_mode,
            "coordinate_unit": "mm_unverified",
            "host_width": self.host_width_mm_unverified,
            "host_height": self.host_height_mm_unverified,
            "mapping_parameters": dict(self.mapping_parameters),
            "limitations": list(self.limitations),
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "physical_fit_inferred": False,
            "manufacturing_authorized": False,
        }


@dataclass(frozen=True, slots=True)
class LabelDielineRevision:
    revision_id: str
    binding: LabelMetricSurfaceBinding
    zone_id: str
    placement_revision_id: str
    mapping_mode: str
    coordinate_unit: str
    boundary_vertices: tuple[tuple[float, float], ...]
    winding: str
    width: float
    height: float
    extents: tuple[float, float, float, float]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.coordinate_unit != "mm_unverified"
            or self.zone_id != self.binding.zone_id
            or self.placement_revision_id != self.binding.placement_revision_id
            or self.mapping_mode != self.binding.mapping_mode
            or len(self.boundary_vertices) != 4
            or not all(math.isfinite(value) for point in self.boundary_vertices for value in point)
            or not math.isfinite(self.width)
            or not math.isfinite(self.height)
            or self.width <= 0.0
            or self.height <= 0.0
            or self.winding
            != ("COUNTERCLOCKWISE" if _signed_area(self.boundary_vertices) > 0 else "CLOCKWISE")
            or self.revision_id != "label-dieline:" + _digest(_dieline_identity(self))
        ):
            raise LabelMetricSurfaceBindingError("label_dieline_identity_or_geometry_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": LABEL_DIELINE_CONTRACT,
            "authority_class": "DERIVED_LABEL_DIELINE",
            "revision_id": self.revision_id,
            "zone_id": self.zone_id,
            "placement_revision_id": self.placement_revision_id,
            "source_design_model_revision_id": self.binding.source_design_model_revision_id,
            "source_brep_revision_id": self.binding.source_brep_revision_id,
            "source_brep_geometry_sha256": self.binding.source_brep_geometry_sha256,
            "parent_authority": {
                "kind": self.binding.parent_kind,
                "revision_id": self.binding.parent_authority_revision_id,
            },
            "analysis_revision_id": self.binding.analysis_revision_id,
            "analysis_region_id": self.binding.analysis_region_id,
            "metric_surface_binding_revision_id": self.binding.revision_id,
            "mapping_mode": self.mapping_mode,
            "source_to_dieline_mapping": self.binding.as_dict()["mapping_parameters"],
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "coordinate_unit": self.coordinate_unit,
            "boundary_vertices": [list(point) for point in self.boundary_vertices],
            "winding": self.winding,
            "width": self.width,
            "height": self.height,
            "extents": list(self.extents),
            "limitations": list(self.limitations),
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "print_fit_verified": False,
            "manufacturing_authorized": False,
            "mold_use_authorized": False,
            "regulatory_approval": False,
        }


def create_label_metric_surface_binding(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    placement: LabelZonePlacementRevision,
    analysis: CadLabelSurfaceAnalysis,
    analysis_region_id: str,
) -> LabelMetricSurfaceBinding:
    """Bind one selected analysis region to its exact planar or cylindrical BREP face."""
    _validate_inputs(model, representation, placement, analysis)
    zone = placement.label_zone
    if (
        model.scale_state is not ScaleState.METRIC_UNVERIFIED
        or model.coordinate_unit != "mm_unverified"
    ):
        raise LabelMetricSurfaceBindingError("label_metric_scale_must_be_mm_unverified")
    candidate = next(
        (item for item in analysis.candidates if item.analysis_region_id == analysis_region_id),
        None,
    )
    if candidate is None:
        raise LabelMetricSurfaceBindingError("label_metric_analysis_region_not_found")
    if candidate.component_id != zone.component_id:
        raise LabelMetricSurfaceBindingError("label_metric_component_mismatch")
    try:
        verified_analysis = analyze_cad_label_surfaces(model, representation, analysis.policy)
    except (CadAdapterError, TypeError, ValueError) as error:
        raise LabelMetricSurfaceBindingError(
            "label_metric_analysis_candidate_revalidation_failed"
        ) from error
    if verified_analysis != analysis:
        raise LabelMetricSurfaceBindingError("label_metric_analysis_revision_stale_or_tampered")
    try:
        if cad_shape_geometry_digest(representation.shape_handle) != representation.geometry_sha256:
            raise LabelMetricSurfaceBindingError("label_metric_brep_digest_mismatch")
        regions = sample_cad_surface_regions(
            representation.shape_handle,
            samples_per_axis=analysis.policy.samples_per_axis,
            maximum_faces=analysis.policy.maximum_faces,
            maximum_regions=analysis.policy.maximum_regions,
            maximum_differential_samples=analysis.policy.maximum_differential_samples,
        )
    except CadAdapterError as error:
        raise LabelMetricSurfaceBindingError("label_metric_exact_brep_analysis_failed") from error

    expected_points = tuple(
        sorted(set(tuple(round(v, 9) for v in point) for point in candidate.support_points))
    )
    matched_faces: list[tuple[str, Any]] = []
    for region in regions:
        observed_points = tuple(
            sorted({tuple(round(v, 9) for v in sample.point) for sample in region.support_points})
        )
        if observed_points == expected_points and region._runtime_face is not None:
            matched_faces.append((region.surface_type, region._runtime_face))
    distinct_faces: list[tuple[str, Any]] = []
    for surface_type, face in matched_faces:
        if not any(face.IsSame(existing) for _, existing in distinct_faces):
            distinct_faces.append((surface_type, face))
    if len(distinct_faces) != 1:
        raise LabelMetricSurfaceBindingError("label_metric_host_surface_resolution_ambiguous")
    surface_type, face = distinct_faces[0]

    if zone.zone_kind in {LabelZoneKind.FRONT, LabelZoneKind.BACK}:
        if surface_type != "GeomAbs_Plane":
            raise LabelMetricSurfaceBindingError("label_metric_planar_host_required")
        width, height, parameters = _planar_rectangle(face, zone.zone_kind)
        mapping_mode = "PLANAR_RECTANGULAR"
    elif zone.zone_kind is LabelZoneKind.WRAP:
        if surface_type != "GeomAbs_Cylinder":
            raise LabelMetricSurfaceBindingError("label_metric_cylindrical_host_required")
        width, height, parameters = _cylindrical_wrap(face)
        mapping_mode = "CYLINDRICAL_WRAP"
    else:
        raise LabelMetricSurfaceBindingError("label_metric_zone_kind_unsupported")

    identity: dict[str, object] = {
        "contract": LABEL_METRIC_SURFACE_BINDING_CONTRACT,
        "zone_id": zone.zone_id,
        "placement_revision_id": placement.revision_id,
        "source_design_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "source_brep_geometry_sha256": representation.geometry_sha256,
        "parent_kind": representation.parent_kind.value,
        "parent_authority_revision_id": representation.parent_authority_revision_id,
        "analysis_revision_id": analysis.revision_id,
        "analysis_region_id": candidate.analysis_region_id,
        "mapping_mode": mapping_mode,
        "host_width_mm_unverified": width,
        "host_height_mm_unverified": height,
        "mapping_parameters": dict(parameters),
        "tolerance": _TOLERANCE,
    }
    return LabelMetricSurfaceBinding(
        "label-metric-surface-binding:" + _digest(identity),
        zone.zone_id,
        placement.revision_id,
        model.revision_id,
        representation.revision_id,
        representation.geometry_sha256,
        representation.parent_kind.value,
        representation.parent_authority_revision_id,
        analysis.revision_id,
        candidate.analysis_region_id,
        mapping_mode,
        width,
        height,
        parameters,
        (
            "Physical accuracy validation is deferred.",
            "Print fit is not verified.",
            "No bleed or safe margin is included.",
            "No material shrink or manufacturing compensation is included.",
            "No mold, manufacturing, or regulatory authorization is implied.",
        ),
    )


def create_label_dieline(
    binding: LabelMetricSurfaceBinding,
    placement: LabelZonePlacementRevision,
) -> LabelDielineRevision:
    """Create the immutable normalized-zone outline in explicitly unverified mm."""
    if not isinstance(binding, LabelMetricSurfaceBinding):
        raise LabelMetricSurfaceBindingError("label_metric_binding_required")
    if not isinstance(placement, LabelZonePlacementRevision):
        raise LabelMetricSurfaceBindingError("label_metric_placement_required")
    if (
        binding.zone_id != placement.zone_id
        or binding.placement_revision_id != placement.revision_id
    ):
        raise LabelMetricSurfaceBindingError("label_metric_placement_stale")
    if placement.label_zone.scale_state is not ScaleState.METRIC_UNVERIFIED:
        raise LabelMetricSurfaceBindingError("label_metric_scale_must_be_mm_unverified")
    b = placement.boundary
    u0, v0, u1, v1 = b.u_min, b.v_min, b.u_max, b.v_max
    w, h = binding.host_width_mm_unverified, binding.host_height_mm_unverified
    if binding.mapping_mode == "PLANAR_RECTANGULAR":
        u_sign = -1.0 if placement.label_zone.zone_kind is LabelZoneKind.BACK else 1.0
        vertices = (
            (u0 * w * u_sign, v0 * h),
            (u1 * w * u_sign, v0 * h),
            (u1 * w * u_sign, v1 * h),
            (u0 * w * u_sign, v1 * h),
        )
    elif binding.mapping_mode == "CYLINDRICAL_WRAP":
        vertices = ((u0 * w, v0 * h), (u1 * w, v0 * h), (u1 * w, v1 * h), (u0 * w, v1 * h))
    else:
        raise LabelMetricSurfaceBindingError("label_metric_mapping_mode_unsupported")
    if not all(math.isfinite(value) for point in vertices for value in point):
        raise LabelMetricSurfaceBindingError("label_metric_output_non_finite")
    xs, ys = tuple(point[0] for point in vertices), tuple(point[1] for point in vertices)
    extents = min(xs), min(ys), max(xs), max(ys)
    width, height = extents[2] - extents[0], extents[3] - extents[1]
    if width <= 0.0 or height <= 0.0:
        raise LabelMetricSurfaceBindingError("label_metric_output_degenerate")
    limitations = binding.limitations + (
        "Dieline coordinates are mm_unverified design geometry only.",
    )
    identity = {
        "contract": LABEL_DIELINE_CONTRACT,
        "binding_revision_id": binding.revision_id,
        "zone_id": binding.zone_id,
        "placement_revision_id": placement.revision_id,
        "mapping_mode": binding.mapping_mode,
        "coordinate_unit": "mm_unverified",
        "boundary_vertices": [list(point) for point in vertices],
        "winding": "COUNTERCLOCKWISE" if _signed_area(vertices) > 0 else "CLOCKWISE",
        "width": width,
        "height": height,
        "extents": list(extents),
        "limitations": list(limitations),
    }
    return LabelDielineRevision(
        "label-dieline:" + _digest(identity),
        binding,
        binding.zone_id,
        placement.revision_id,
        binding.mapping_mode,
        "mm_unverified",
        vertices,
        str(identity["winding"]),
        width,
        height,
        extents,
        limitations,
    )


def _validate_inputs(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    placement: LabelZonePlacementRevision,
    analysis: CadLabelSurfaceAnalysis,
) -> None:
    if not isinstance(model, DesignModelRevision):
        raise LabelMetricSurfaceBindingError("label_metric_model_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise LabelMetricSurfaceBindingError("label_metric_brep_required")
    if not isinstance(placement, LabelZonePlacementRevision):
        raise LabelMetricSurfaceBindingError("label_metric_placement_required")
    if not isinstance(analysis, CadLabelSurfaceAnalysis):
        raise LabelMetricSurfaceBindingError("label_metric_analysis_required")
    zone = placement.label_zone
    if (
        zone.source_design_model_revision_id != model.revision_id
        or zone.source_brep_revision_id != representation.revision_id
        or zone.source_brep_geometry_sha256 != representation.geometry_sha256
        or zone.parent_kind is not model.parent_kind
        or zone.parent_authority_revision_id
        != (
            model.standalone_root.revision_id
            if model.standalone_root
            else model.parent_binding_revision_id
        )
        or zone.scale_state is not model.scale_state
        or zone.coordinate_unit != model.coordinate_unit
        or zone.component_id != analysis.component_id
        or analysis.source_design_model_revision_id != model.revision_id
        or analysis.source_brep_revision_id != representation.revision_id
        or analysis.source_brep_geometry_sha256 != representation.geometry_sha256
        or analysis.parent_authority_revision_id != representation.parent_authority_revision_id
        or analysis.scale_state != representation.scale_state.value
        or analysis.coordinate_unit != representation.coordinate_unit
    ):
        raise LabelMetricSurfaceBindingError("label_metric_source_provenance_mismatch")
    if (
        representation.scale_state is ScaleState.RELATIVE
        or representation.coordinate_unit != "mm_unverified"
    ):
        raise LabelMetricSurfaceBindingError("label_metric_scale_must_be_mm_unverified")
    try:
        digest = cad_shape_geometry_digest(representation.shape_handle)
    except CadAdapterError as error:
        raise LabelMetricSurfaceBindingError("label_metric_brep_unavailable") from error
    if digest != representation.geometry_sha256:
        raise LabelMetricSurfaceBindingError("label_metric_brep_digest_mismatch")


def _planar_rectangle(
    face: Any, zone_kind: LabelZoneKind
) -> tuple[float, float, tuple[tuple[str, float | str], ...]]:
    modules = _ocp_modules()
    adaptor = modules["adaptor"].BRepAdaptor_Surface(face, True)
    bounds = modules["tools"].BRepTools.UVBounds_s(face)
    u0, u1, v0, v1 = (float(value) for value in bounds)
    if not all(math.isfinite(value) for value in (u0, u1, v0, v1)) or u1 <= u0 or v1 <= v0:
        raise LabelMetricSurfaceBindingError("label_metric_planar_bounds_invalid")
    wires = _explore(face, modules["topabs"].TopAbs_WIRE, modules["topexp"].TopExp_Explorer)
    if len(wires) != 1:
        raise LabelMetricSurfaceBindingError("label_metric_planar_trim_must_be_single_rectangle")
    edges = _explore(wires[0], modules["topabs"].TopAbs_EDGE, modules["topexp"].TopExp_Explorer)
    if len(edges) != 4:
        raise LabelMetricSurfaceBindingError("label_metric_planar_trim_must_be_single_rectangle")
    for edge in edges:
        curve = modules["adaptor"].BRepAdaptor_Curve(modules["topods"].TopoDS.Edge_s(edge))
        kind = getattr(curve.GetType(), "name", str(curve.GetType()).split(".")[-1])
        if kind != "GeomAbs_Line":
            raise LabelMetricSurfaceBindingError(
                "label_metric_planar_trim_must_be_single_rectangle"
            )
    classifier = modules["classifier"].BRepClass_FaceClassifier()
    topabs = modules["topabs"]
    for u, v in ((u0, v0), (u0, v1), (u1, v0), (u1, v1), ((u0 + u1) / 2, (v0 + v1) / 2)):
        classifier.Perform(face, modules["gp"].gp_Pnt2d(u, v), _TOLERANCE)
        if classifier.State() not in {topabs.TopAbs_IN, topabs.TopAbs_ON}:
            raise LabelMetricSurfaceBindingError("label_metric_planar_trim_not_rectangle")
    plane = adaptor.Plane()
    axis = plane.Axis().Direction()
    nx, ny, nz = float(axis.X()), float(axis.Y()), float(axis.Z())
    if face.Orientation() == topabs.TopAbs_REVERSED:
        nx, ny, nz = -nx, -ny, -nz
    expected_y = 1.0 if zone_kind is LabelZoneKind.FRONT else -1.0
    if abs(nx) > _TOLERANCE or abs(nz) > _TOLERANCE or abs(ny - expected_y) > _TOLERANCE:
        raise LabelMetricSurfaceBindingError("label_metric_planar_frame_incompatible")
    points = [adaptor.Value(u, v) for u, v in ((u0, v0), (u0, v1), (u1, v0), (u1, v1))]
    coords = [(float(p.X()), float(p.Y()), float(p.Z())) for p in points]
    xs, zs = [p[0] for p in coords], [p[2] for p in coords]
    width, height = max(xs) - min(xs), max(zs) - min(zs)
    if min(width, height) <= _TOLERANCE:
        raise LabelMetricSurfaceBindingError("label_metric_planar_dimensions_degenerate")
    if any(abs(p[1] - coords[0][1]) > _TOLERANCE for p in coords):
        raise LabelMetricSurfaceBindingError("label_metric_planar_domain_not_rectangular")
    vertices = _explore(wires[0], topabs.TopAbs_VERTEX, modules["topexp"].TopExp_Explorer)
    topods = modules["topods"].TopoDS
    brep = importlib.import_module("OCP.BRep").BRep_Tool
    vertex_points: list[tuple[float, float, float]] = []
    for vertex in vertices:
        typed = topods.Vertex_s(vertex)
        point = brep.Pnt_s(typed)
        xyz = (float(point.X()), float(point.Y()), float(point.Z()))
        if not any(_points_close(xyz, existing) for existing in vertex_points):
            vertex_points.append(xyz)
    if len(vertex_points) != 4:
        raise LabelMetricSurfaceBindingError("label_metric_planar_trim_must_be_single_rectangle")
    expected_corners = {
        (x, y, z) for x in (min(xs), max(xs)) for y in (coords[0][1],) for z in (min(zs), max(zs))
    }
    if any(
        not any(_points_close(point, corner) for corner in expected_corners)
        for point in vertex_points
    ):
        raise LabelMetricSurfaceBindingError("label_metric_planar_domain_not_rectangular")
    if any(
        not any(_points_close(corner, point) for point in vertex_points)
        for corner in expected_corners
    ):
        raise LabelMetricSurfaceBindingError("label_metric_planar_domain_not_rectangular")
    return width, height, (("frame", "PACKLAB_FRONT_BACK"), ("orientation", zone_kind.value))


def _cylindrical_wrap(face: Any) -> tuple[float, float, tuple[tuple[str, float | str], ...]]:
    modules = _ocp_modules()
    adaptor = modules["adaptor"].BRepAdaptor_Surface(face, True)
    cylinder = adaptor.Cylinder()
    radius = float(cylinder.Radius())
    axis = cylinder.Axis().Direction()
    ax, ay, az = float(axis.X()), float(axis.Y()), float(axis.Z())
    if (
        radius <= _TOLERANCE
        or not math.isfinite(radius)
        or abs(ax) > _TOLERANCE
        or abs(ay) > _TOLERANCE
        or abs(az - 1.0) > _TOLERANCE
    ):
        raise LabelMetricSurfaceBindingError("label_metric_cylinder_axis_incompatible")
    u0, u1, v0, v1 = (float(value) for value in modules["tools"].BRepTools.UVBounds_s(face))
    span, height = u1 - u0, v1 - v0
    if (
        not all(math.isfinite(value) for value in (u0, u1, v0, v1, span, height))
        or abs(span - 2.0 * math.pi) > _TOLERANCE
        or height <= _TOLERANCE
    ):
        raise LabelMetricSurfaceBindingError("label_metric_cylinder_trim_unsupported")
    wires = _explore(face, modules["topabs"].TopAbs_WIRE, modules["topexp"].TopExp_Explorer)
    if len(wires) != 1:
        raise LabelMetricSurfaceBindingError("label_metric_cylinder_trim_unsupported")
    edges = _explore(wires[0], modules["topabs"].TopAbs_EDGE, modules["topexp"].TopExp_Explorer)
    topods = modules["topods"].TopoDS
    edge_types = []
    for edge in edges:
        curve = modules["adaptor"].BRepAdaptor_Curve(topods.Edge_s(edge))
        edge_type = getattr(curve.GetType(), "name", str(curve.GetType()).split(".")[-1])
        edge_types.append(edge_type)
    if (
        len(edge_types) != 4
        or edge_types.count("GeomAbs_Circle") != 2
        or edge_types.count("GeomAbs_Line") != 2
    ):
        raise LabelMetricSurfaceBindingError("label_metric_cylinder_trim_unsupported")
    position = cylinder.Position()
    x_direction, y_direction = position.XDirection(), position.YDirection()
    if (
        abs(float(x_direction.X()) - 1.0) > _TOLERANCE
        or abs(float(x_direction.Y())) > _TOLERANCE
        or abs(float(y_direction.X())) > _TOLERANCE
        or abs(float(y_direction.Y()) - 1.0) > _TOLERANCE
    ):
        raise LabelMetricSurfaceBindingError("label_metric_cylinder_seam_incompatible")
    return (
        2.0 * math.pi * radius,
        height,
        (
            ("radius_mm_unverified", radius),
            ("axis", "Z"),
            ("seam", "+Y"),
            ("azimuth_direction", "+Y_TO_PLUS_X"),
        ),
    )


def _ocp_modules() -> dict[str, Any]:
    return {
        "adaptor": importlib.import_module("OCP.BRepAdaptor"),
        "tools": importlib.import_module("OCP.BRepTools"),
        "topabs": importlib.import_module("OCP.TopAbs"),
        "topexp": importlib.import_module("OCP.TopExp"),
        "topods": importlib.import_module("OCP.TopoDS"),
        "classifier": importlib.import_module("OCP.BRepClass"),
        "gp": importlib.import_module("OCP.gp"),
    }


def _explore(shape: Any, kind: Any, explorer_type: Any) -> list[Any]:
    explorer = explorer_type(shape, kind)
    found = []
    while explorer.More():
        found.append(explorer.Current())
        explorer.Next()
    return found


def _signed_area(points: tuple[tuple[float, float], ...]) -> float:
    return (
        sum(
            points[index][0] * points[(index + 1) % len(points)][1]
            - points[(index + 1) % len(points)][0] * points[index][1]
            for index in range(len(points))
        )
        / 2.0
    )


def _points_close(left: tuple[float, float, float], right: tuple[float, float, float]) -> bool:
    return all(abs(a - b) <= _TOLERANCE for a, b in zip(left, right, strict=True))


def _binding_identity(binding: LabelMetricSurfaceBinding) -> dict[str, object]:
    return {
        "contract": LABEL_METRIC_SURFACE_BINDING_CONTRACT,
        "zone_id": binding.zone_id,
        "placement_revision_id": binding.placement_revision_id,
        "source_design_model_revision_id": binding.source_design_model_revision_id,
        "source_brep_revision_id": binding.source_brep_revision_id,
        "source_brep_geometry_sha256": binding.source_brep_geometry_sha256,
        "parent_kind": binding.parent_kind,
        "parent_authority_revision_id": binding.parent_authority_revision_id,
        "analysis_revision_id": binding.analysis_revision_id,
        "analysis_region_id": binding.analysis_region_id,
        "mapping_mode": binding.mapping_mode,
        "host_width_mm_unverified": binding.host_width_mm_unverified,
        "host_height_mm_unverified": binding.host_height_mm_unverified,
        "mapping_parameters": dict(binding.mapping_parameters),
        "tolerance": _TOLERANCE,
    }


def _dieline_identity(dieline: LabelDielineRevision) -> dict[str, object]:
    return {
        "contract": LABEL_DIELINE_CONTRACT,
        "binding_revision_id": dieline.binding.revision_id,
        "zone_id": dieline.binding.zone_id,
        "placement_revision_id": dieline.placement_revision_id,
        "mapping_mode": dieline.mapping_mode,
        "coordinate_unit": "mm_unverified",
        "boundary_vertices": [list(point) for point in dieline.boundary_vertices],
        "winding": dieline.winding,
        "width": dieline.width,
        "height": dieline.height,
        "extents": list(dieline.extents),
        "limitations": list(dieline.limitations),
    }


def _digest(value: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


__all__ = [
    "LABEL_DIELINE_CONTRACT",
    "LABEL_METRIC_SURFACE_BINDING_CONTRACT",
    "LabelDielineRevision",
    "LabelMetricSurfaceBinding",
    "LabelMetricSurfaceBindingError",
    "create_label_dieline",
    "create_label_metric_surface_binding",
]
