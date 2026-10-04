"""PackLab-owned CAD values and capability diagnostics over the selected OCCT binding."""

from __future__ import annotations

import ctypes
import hashlib
import importlib
import importlib.metadata
import math
import platform
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .cross_section import CrossSection
from .design_model import DesignModelParentKind, DesignModelRevision
from .design_operations import (
    MAX_LOFT_SECTIONS,
    DesignOperation,
    LoftSectionInput,
    OperationKind,
)
from .design_profile import DesignProfile
from .geometry_adapter import TriangleMeshData
from .reconstruction import ScaleState

CAD_BINDING_PACKAGE = "cadquery-ocp-novtk"
CAD_RUNTIME_VERSION_STATUS_OBSERVED = "OBSERVED"
CAD_RUNTIME_VERSION_STATUS_UNAVAILABLE = "UNAVAILABLE"
PHYSICAL_VALIDATION_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class CadAdapterError(ValueError):
    """Raised when PackLab-owned CAD input or source authority is invalid."""


class CadCapabilityStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class CadRuntimeStatus(StrEnum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class CadCapability:
    name: str
    status: CadCapabilityStatus
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class CadRuntimeDiagnostics:
    status: CadRuntimeStatus
    binding_package: str
    binding_version: str | None
    binding_version_status: str
    kernel_version: str | None
    kernel_version_status: str
    platform_system: str
    platform_machine: str
    capabilities: tuple[CadCapability, ...]
    error_code: str | None = None

    def capability(self, name: str) -> CadCapability | None:
        """Return one named capability without exposing backend-owned objects."""
        return next((item for item in self.capabilities if item.name == name), None)


@dataclass(frozen=True, slots=True)
class CadProfileControlPoint:
    axial: float
    radius: float
    tangent: float | None


@dataclass(frozen=True, slots=True)
class CadProfileInput:
    source_profile_id: str
    points: tuple[CadProfileControlPoint, ...]
    scale_state: ScaleState
    coordinate_unit: str
    physical_accuracy_validation_status: str = PHYSICAL_VALIDATION_DEFERRED
    mold_use_authorized: bool = False


@dataclass(frozen=True, slots=True)
class CadPoint2:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class CadCrossSectionInput:
    source_section_id: str
    component_id: str
    points: tuple[CadPoint2, ...]
    symmetry: str
    center_x: float
    center_y: float
    scale_state: ScaleState
    coordinate_unit: str
    physical_accuracy_validation_status: str = PHYSICAL_VALIDATION_DEFERRED
    mold_use_authorized: bool = False


@dataclass(frozen=True, slots=True)
class CadShapeHandle:
    """Opaque PackLab reference; no OCCT class or native shape escapes the adapter."""

    handle_id: str
    source_design_model_revision_id: str
    parent_kind: DesignModelParentKind
    parent_authority_revision_id: str
    scale_state: ScaleState
    coordinate_unit: str
    physical_accuracy_validation_status: str = PHYSICAL_VALIDATION_DEFERRED
    mold_use_authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.handle_id, str) or not self.handle_id.startswith("cad-shape:"):
            raise CadAdapterError("cad_shape_handle_id_invalid")
        if (
            not isinstance(self.source_design_model_revision_id, str)
            or not self.source_design_model_revision_id
        ):
            raise CadAdapterError("cad_source_design_model_revision_required")
        if not isinstance(self.parent_kind, DesignModelParentKind):
            raise CadAdapterError("cad_parent_authority_kind_invalid")
        if (
            not isinstance(self.parent_authority_revision_id, str)
            or not self.parent_authority_revision_id
        ):
            raise CadAdapterError("cad_parent_authority_revision_required")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state not in {
            ScaleState.RELATIVE,
            ScaleState.METRIC_UNVERIFIED,
        }:
            raise CadAdapterError("cad_scale_state_unauthorized")
        expected_unit = (
            "reconstruction_units" if self.scale_state is ScaleState.RELATIVE else "mm_unverified"
        )
        if self.coordinate_unit != expected_unit:
            raise CadAdapterError("cad_coordinate_unit_mismatch")
        if self.physical_accuracy_validation_status != PHYSICAL_VALIDATION_DEFERRED:
            raise CadAdapterError("cad_physical_validation_must_remain_deferred")
        if self.mold_use_authorized is not False:
            raise CadAdapterError("cad_mold_use_forbidden")


@dataclass(frozen=True, slots=True)
class CadShapeBuild:
    """PackLab-owned metadata for one locally generated BREP solid."""

    shape_handle: CadShapeHandle
    geometry_sha256: str
    solid_count: int


@dataclass(frozen=True, slots=True)
class CadBooleanBuild:
    """PackLab-owned result of one validated CAD cut."""

    shape_build: CadShapeBuild
    topology_valid: bool
    kernel_operation_done: bool


@dataclass(frozen=True, slots=True)
class CadTopologySnapshot:
    """PackLab-owned counts and non-repairing OCCT topology observations."""

    kernel_valid: bool
    solid_count: int
    shell_count: int
    closed_shell_count: int
    open_edge_count: int
    nonmanifold_edge_count: int
    invalid_statuses: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CadTessellationData:
    """Bounded backend-neutral tessellation extracted from a copied CAD shape."""

    mesh: TriangleMeshData
    face_count: int
    linear_deflection: float
    angular_deflection: float
    maximum_vertices: int
    maximum_triangles: int
    maximum_faces: int


_SHAPE_REGISTRY: dict[str, tuple[str, Any]] = {}
_SHAPE_REGISTRY_LOCK = threading.RLock()


def profile_to_cad_input(profile: DesignProfile) -> CadProfileInput:
    """Copy PackLab profile values deterministically without changing axes or units."""
    if not isinstance(profile, DesignProfile):
        raise CadAdapterError("design_profile_required")
    return CadProfileInput(
        source_profile_id=profile.profile_id,
        points=tuple(
            CadProfileControlPoint(point.axial, point.radius, point.tangent)
            for point in profile.points
        ),
        scale_state=profile.scale_state,
        coordinate_unit=profile.coordinate_unit,
    )


def cross_section_to_cad_input(section: CrossSection) -> CadCrossSectionInput:
    """Copy the ordered PackLab section and preserve its exact unit/scale authority."""
    if not isinstance(section, CrossSection):
        raise CadAdapterError("cross_section_required")
    return CadCrossSectionInput(
        source_section_id=section.section_id,
        component_id=section.component_id,
        points=tuple(CadPoint2(point.x, point.y) for point in section.points),
        symmetry=section.symmetry.value,
        center_x=section.center_x,
        center_y=section.center_y,
        scale_state=section.scale_state,
        coordinate_unit=section.coordinate_unit,
    )


def shape_handle_for_model(handle_id: str, model: DesignModelRevision) -> CadShapeHandle:
    """Create an opaque reference pinned to one exact Design Model and parent authority."""
    if not isinstance(model, DesignModelRevision):
        raise CadAdapterError("design_model_revision_required")
    parent_revision = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if parent_revision is None:
        raise CadAdapterError("design_model_parent_authority_missing")
    return CadShapeHandle(
        handle_id=handle_id,
        source_design_model_revision_id=model.revision_id,
        parent_kind=model.parent_kind,
        parent_authority_revision_id=parent_revision,
        scale_state=model.scale_state,
        coordinate_unit=model.coordinate_unit,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
    )


def build_revolved_shape(
    model: DesignModelRevision,
    profile: DesignProfile,
    operation: DesignOperation,
    *,
    profile_sample_count: int = 257,
) -> CadShapeBuild:
    """Build and register a validated single-solid revolve behind an opaque handle."""
    _validate_revolve_inputs(model, profile, operation, profile_sample_count)
    polygon = _closed_profile_polygon(profile, profile_sample_count)
    module_gp = importlib.import_module("OCP.gp")
    module_builder = importlib.import_module("OCP.BRepBuilderAPI")
    module_primitive = importlib.import_module("OCP.BRepPrimAPI")
    module_check = importlib.import_module("OCP.BRepCheck")
    module_top_exp = importlib.import_module("OCP.TopExp")
    module_top_abs = importlib.import_module("OCP.TopAbs")

    axis = operation.axis_direction
    origin = operation.axis_origin
    assert axis is not None and origin is not None
    reference = (1.0, 0.0, 0.0) if abs(axis[0]) < 0.9 else (0.0, 1.0, 0.0)
    radial = _unit_vector(_cross_product(axis, reference))
    points = tuple(
        module_gp.gp_Pnt(
            origin[0] + axial * axis[0] + radius * radial[0],
            origin[1] + axial * axis[1] + radius * radial[1],
            origin[2] + axial * axis[2] + radius * radial[2],
        )
        for axial, radius in polygon
    )
    wire_builder = module_builder.BRepBuilderAPI_MakeWire()
    for left, right in zip(points, (*points[1:], points[0])):
        edge = module_builder.BRepBuilderAPI_MakeEdge(left, right)
        if not edge.IsDone():
            raise CadAdapterError("revolve_profile_edge_build_failed")
        wire_builder.Add(edge.Edge())
    if not wire_builder.IsDone():
        raise CadAdapterError("revolve_profile_wire_build_failed")
    face_builder = module_builder.BRepBuilderAPI_MakeFace(wire_builder.Wire())
    if not face_builder.IsDone():
        raise CadAdapterError("revolve_profile_face_build_failed")
    axis_line = module_gp.gp_Ax1(module_gp.gp_Pnt(*origin), module_gp.gp_Dir(*axis))
    revolver = module_primitive.BRepPrimAPI_MakeRevol(face_builder.Face(), axis_line, 2.0 * math.pi)
    revolver.Build()
    if not revolver.IsDone():
        raise CadAdapterError("revolve_brep_build_failed")
    shape = revolver.Shape()
    if shape.IsNull() or not module_check.BRepCheck_Analyzer(shape).IsValid():
        raise CadAdapterError("revolve_brep_topology_invalid")
    explorer = module_top_exp.TopExp_Explorer(shape, module_top_abs.TopAbs_SOLID)
    solid_count = 0
    while explorer.More():
        solid_count += 1
        explorer.Next()
    if solid_count != 1:
        raise CadAdapterError("revolve_brep_single_solid_required")

    return _shape_build_result(model, operation, shape, solid_count)


def build_lofted_shape(
    model: DesignModelRevision,
    sections: tuple[LoftSectionInput, ...],
    operation: DesignOperation,
) -> CadShapeBuild:
    """Build a loft from exact ordered section wires without reordering or gap healing."""
    _validate_loft_inputs(model, sections, operation)
    gp = importlib.import_module("OCP.gp")
    builder = importlib.import_module("OCP.BRepBuilderAPI")
    loft_module = importlib.import_module("OCP.BRepOffsetAPI")
    check_module = importlib.import_module("OCP.BRepCheck")
    top_exp = importlib.import_module("OCP.TopExp")
    top_abs = importlib.import_module("OCP.TopAbs")
    brep_tool = importlib.import_module("OCP.BRep")
    loft = loft_module.BRepOffsetAPI_ThruSections(True, False, 1e-6)
    loft.CheckCompatibility(False)

    for section_input in sections:
        points = tuple(
            gp.gp_Pnt(point.x, point.y, section_input.axial_position)
            for point in section_input.section.points
        )
        wire_builder = builder.BRepBuilderAPI_MakeWire()
        for left, right in zip(points, (*points[1:], points[0])):
            edge = builder.BRepBuilderAPI_MakeEdge(left, right)
            if not edge.IsDone():
                raise CadAdapterError("loft_section_edge_build_failed")
            wire_builder.Add(edge.Edge())
        if not wire_builder.IsDone():
            raise CadAdapterError("loft_section_wire_build_failed")
        wire = wire_builder.Wire()
        if not brep_tool.BRep_Tool.IsClosed_s(wire):
            raise CadAdapterError("loft_section_wire_not_closed")
        loft.AddWire(wire)

    loft.Build()
    if not loft.IsDone():
        raise CadAdapterError("loft_brep_build_failed")
    shape = loft.Shape()
    if shape.IsNull() or not check_module.BRepCheck_Analyzer(shape).IsValid():
        raise CadAdapterError("loft_brep_topology_invalid")
    explorer = top_exp.TopExp_Explorer(shape, top_abs.TopAbs_SOLID)
    solid_count = 0
    while explorer.More():
        solid_count += 1
        explorer.Next()
    if solid_count != 1:
        raise CadAdapterError("loft_brep_single_solid_required")
    return _shape_build_result(model, operation, shape, solid_count)


def build_polygon_prism_cut(
    model: DesignModelRevision,
    parent_handle: CadShapeHandle,
    *,
    operation_id: str,
    input_ids: tuple[str, ...],
    profile: tuple[tuple[float, float, float], ...],
    extrusion: tuple[float, float, float],
) -> CadBooleanBuild:
    """Cut an explicit planar polygon prism from one registered Design Model BREP."""
    if not isinstance(model, DesignModelRevision):
        raise CadAdapterError("design_model_revision_required")
    if not isinstance(parent_handle, CadShapeHandle):
        raise CadAdapterError("cad_parent_shape_handle_required")
    if (
        parent_handle.parent_kind is not model.parent_kind
        or parent_handle.parent_authority_revision_id
        != (
            model.standalone_root.revision_id
            if model.standalone_root
            else model.parent_binding_revision_id
        )
        or parent_handle.scale_state is not model.scale_state
        or parent_handle.coordinate_unit != model.coordinate_unit
    ):
        raise CadAdapterError("cad_parent_shape_authority_mismatch")
    if (
        not isinstance(operation_id, str)
        or not operation_id
        or not isinstance(input_ids, tuple)
        or not input_ids
    ):
        raise CadAdapterError("cad_boolean_provenance_invalid")
    if (
        not isinstance(profile, tuple)
        or len(profile) < 3
        or any(
            not isinstance(point, tuple)
            or len(point) != 3
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in point
            )
            for point in profile
        )
        or not isinstance(extrusion, tuple)
        or len(extrusion) != 3
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in extrusion
        )
        or sum(value * value for value in extrusion) <= 0.0
    ):
        raise CadAdapterError("cad_boolean_tool_invalid")
    parent_shape = _shape_for_handle(parent_handle)
    check = importlib.import_module("OCP.BRepCheck")
    top_abs = importlib.import_module("OCP.TopAbs")
    top_exp = importlib.import_module("OCP.TopExp")
    if parent_shape.IsNull() or not check.BRepCheck_Analyzer(parent_shape).IsValid():
        raise CadAdapterError("cad_boolean_parent_topology_invalid")
    parent_solids = top_exp.TopExp_Explorer(parent_shape, top_abs.TopAbs_SOLID)
    if not parent_solids.More():
        raise CadAdapterError("cad_boolean_parent_solid_missing")

    gp = importlib.import_module("OCP.gp")
    builder = importlib.import_module("OCP.BRepBuilderAPI")
    primitive = importlib.import_module("OCP.BRepPrimAPI")
    points = tuple(gp.gp_Pnt(*point) for point in profile)
    wire_builder = builder.BRepBuilderAPI_MakePolygon()
    for point in points:
        wire_builder.Add(point)
    wire_builder.Close()
    if not wire_builder.IsDone():
        raise CadAdapterError("cad_boolean_tool_wire_invalid")
    face_builder = builder.BRepBuilderAPI_MakeFace(wire_builder.Wire())
    if not face_builder.IsDone():
        raise CadAdapterError("cad_boolean_tool_face_invalid")
    tool_builder = primitive.BRepPrimAPI_MakePrism(face_builder.Face(), gp.gp_Vec(*extrusion), True)
    tool_builder.Build()
    if not tool_builder.IsDone() or tool_builder.Shape().IsNull():
        raise CadAdapterError("cad_boolean_tool_prism_invalid")

    common = importlib.import_module("OCP.BRepAlgoAPI").BRepAlgoAPI_Common(
        parent_shape, tool_builder.Shape()
    )
    common.Build()
    if not common.IsDone() or common.Shape().IsNull():
        raise CadAdapterError("cad_boolean_intersection_check_failed")
    common_solids = top_exp.TopExp_Explorer(common.Shape(), top_abs.TopAbs_SOLID)
    if not common_solids.More():
        raise CadAdapterError("cad_boolean_tool_does_not_intersect_body")

    boolean = importlib.import_module("OCP.BRepAlgoAPI").BRepAlgoAPI_Cut(
        parent_shape, tool_builder.Shape()
    )
    boolean.Build()
    if not boolean.IsDone():
        raise CadAdapterError("cad_boolean_kernel_cut_failed")
    result = boolean.Shape()
    if result.IsNull():
        raise CadAdapterError("cad_boolean_result_empty")
    if not check.BRepCheck_Analyzer(result).IsValid():
        raise CadAdapterError("cad_boolean_result_topology_invalid")
    explorer = top_exp.TopExp_Explorer(result, top_abs.TopAbs_SOLID)
    solid_count = 0
    while explorer.More():
        solid_count += 1
        explorer.Next()
    if solid_count != 1:
        raise CadAdapterError("cad_boolean_result_single_solid_required")
    shape_build = _registered_shape_build(model, operation_id, input_ids, result, solid_count)
    return CadBooleanBuild(shape_build, True, True)


def cad_shape_bounds(handle: CadShapeHandle) -> tuple[float, float, float, float, float, float]:
    """Return deterministic axis-aligned bounds for one opaque registered shape."""
    shape = _shape_for_handle(handle)
    box = importlib.import_module("OCP.Bnd").Bnd_Box()
    importlib.import_module("OCP.BRepBndLib").BRepBndLib.Add_s(shape, box)
    bounds = box.Get()
    if len(bounds) != 6 or any(not math.isfinite(value) for value in bounds):
        raise CadAdapterError("cad_shape_bounds_invalid")
    return tuple(float(value) for value in bounds)  # type: ignore[return-value]


def tessellate_cad_shape(
    handle: CadShapeHandle,
    *,
    linear_deflection: float,
    angular_deflection: float,
    maximum_vertices: int,
    maximum_triangles: int,
    maximum_faces: int,
) -> CadTessellationData:
    """Mesh a copy of one registered shape with explicit tolerances and work bounds."""
    if not isinstance(handle, CadShapeHandle):
        raise CadAdapterError("cad_shape_handle_required")
    for value, code in (
        (linear_deflection, "cad_tessellation_linear_deflection_invalid"),
        (angular_deflection, "cad_tessellation_angular_deflection_invalid"),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise CadAdapterError(code)
    if not 1e-5 <= float(linear_deflection) <= 10.0:
        raise CadAdapterError("cad_tessellation_linear_deflection_out_of_bounds")
    if not 1e-4 <= float(angular_deflection) <= math.pi / 2.0:
        raise CadAdapterError("cad_tessellation_angular_deflection_out_of_bounds")
    from .design_preview import MAX_PREVIEW_TRIANGLES, MAX_PREVIEW_VERTICES

    limits = (
        (maximum_vertices, MAX_PREVIEW_VERTICES, "cad_tessellation_vertex_limit_invalid"),
        (maximum_triangles, MAX_PREVIEW_TRIANGLES, "cad_tessellation_triangle_limit_invalid"),
        (maximum_faces, 10_000, "cad_tessellation_face_limit_invalid"),
    )
    for value, maximum, code in limits:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
            raise CadAdapterError(code)

    shape = _shape_for_handle(handle)
    if shape.IsNull():
        raise CadAdapterError("cad_tessellation_shape_null")
    builder = importlib.import_module("OCP.BRepBuilderAPI")
    top_abs = importlib.import_module("OCP.TopAbs")
    top_exp = importlib.import_module("OCP.TopExp")
    topods = importlib.import_module("OCP.TopoDS")
    face_explorer = top_exp.TopExp_Explorer(shape, top_abs.TopAbs_FACE)
    faces = []
    while face_explorer.More():
        faces.append(topods.TopoDS.Face_s(face_explorer.Current()))
        if len(faces) > maximum_faces:
            raise CadAdapterError("cad_tessellation_face_work_bound_exceeded")
        face_explorer.Next()
    if not faces:
        raise CadAdapterError("cad_tessellation_faces_required")

    # copyMesh=False prevents reuse of or attachment to source triangulations.
    copied_shape = builder.BRepBuilderAPI_Copy(shape, True, False).Shape()
    mesher_module = importlib.import_module("OCP.BRepMesh")
    mesher = mesher_module.BRepMesh_IncrementalMesh(
        copied_shape,
        float(linear_deflection),
        False,
        float(angular_deflection),
        False,
    )
    mesher.Perform()
    if not mesher.IsDone():
        raise CadAdapterError("cad_tessellation_kernel_failed")

    brep_tool = importlib.import_module("OCP.BRep").BRep_Tool
    top_loc = importlib.import_module("OCP.TopLoc")
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    vertex_indices: dict[tuple[float, float, float], int] = {}
    explorer = top_exp.TopExp_Explorer(copied_shape, top_abs.TopAbs_FACE)
    while explorer.More():
        face = topods.TopoDS.Face_s(explorer.Current())
        location = top_loc.TopLoc_Location()
        triangulation = brep_tool.Triangulation_s(face, location)
        if triangulation is None:
            raise CadAdapterError("cad_tessellation_face_triangulation_missing")
        transform = location.Transformation()
        local_indices: dict[int, int] = {}
        for node_index in range(1, triangulation.NbNodes() + 1):
            point = triangulation.Node(node_index).Transformed(transform)
            vertex = (float(point.X()), float(point.Y()), float(point.Z()))
            index = vertex_indices.get(vertex)
            if index is None:
                if len(vertices) >= maximum_vertices:
                    raise CadAdapterError("cad_tessellation_vertex_work_bound_exceeded")
                index = len(vertices)
                vertex_indices[vertex] = index
                vertices.append(vertex)
            local_indices[node_index] = index
        reversed_face = face.Orientation() == top_abs.TopAbs_REVERSED
        for triangle_index in range(1, triangulation.NbTriangles() + 1):
            if len(triangles) >= maximum_triangles:
                raise CadAdapterError("cad_tessellation_triangle_work_bound_exceeded")
            n1, n2, n3 = triangulation.Triangle(triangle_index).Get()
            triangle = (
                local_indices[n1],
                local_indices[n3 if reversed_face else n2],
                local_indices[n2 if reversed_face else n3],
            )
            if len(set(triangle)) != 3:
                raise CadAdapterError("cad_tessellation_degenerate_triangle")
            triangles.append(triangle)
        explorer.Next()
    if not vertices or not triangles:
        raise CadAdapterError("cad_tessellation_mesh_empty")
    try:
        mesh = TriangleMeshData(tuple(vertices), tuple(triangles))
    except ValueError as error:
        raise CadAdapterError("cad_tessellation_mesh_invalid") from error
    return CadTessellationData(
        mesh,
        len(faces),
        float(linear_deflection),
        float(angular_deflection),
        maximum_vertices,
        maximum_triangles,
        maximum_faces,
    )


def inspect_shape_topology(handle: CadShapeHandle) -> CadTopologySnapshot:
    """Inspect a registered shape with OCCT without healing or mutating it."""
    shape = _shape_for_handle(handle)
    if shape.IsNull():
        raise CadAdapterError("cad_topology_shape_null")
    top_abs = importlib.import_module("OCP.TopAbs")
    top_exp = importlib.import_module("OCP.TopExp")
    check_module = importlib.import_module("OCP.BRepCheck")
    brep_tool = importlib.import_module("OCP.BRep").BRep_Tool

    def collect(shape_type: Any) -> tuple[Any, ...]:
        explorer = top_exp.TopExp_Explorer(shape, shape_type)
        found: list[Any] = []
        while explorer.More():
            found.append(explorer.Current())
            explorer.Next()
        return tuple(found)

    solids = collect(top_abs.TopAbs_SOLID)
    shells = collect(top_abs.TopAbs_SHELL)
    closed_shell_count = sum(1 for shell in shells if brep_tool.IsClosed_s(shell))
    edge_faces = importlib.import_module("OCP.TopTools").TopTools_IndexedDataMapOfShapeListOfShape()
    top_exp.TopExp.MapShapesAndAncestors_s(
        shape, top_abs.TopAbs_EDGE, top_abs.TopAbs_FACE, edge_faces
    )
    open_edge_count = 0
    nonmanifold_edge_count = 0
    for index in range(1, edge_faces.Extent() + 1):
        adjacent_faces = edge_faces.FindFromIndex(index).Size()
        if adjacent_faces == 1:
            open_edge_count += 1
        elif adjacent_faces > 2:
            nonmanifold_edge_count += 1

    analyzer = check_module.BRepCheck_Analyzer(shape)
    statuses: set[str] = set()
    for shape_name, shape_type in (
        ("vertex", top_abs.TopAbs_VERTEX),
        ("edge", top_abs.TopAbs_EDGE),
        ("wire", top_abs.TopAbs_WIRE),
        ("face", top_abs.TopAbs_FACE),
        ("shell", top_abs.TopAbs_SHELL),
        ("solid", top_abs.TopAbs_SOLID),
        ("compsolid", top_abs.TopAbs_COMPSOLID),
    ):
        for subshape in collect(shape_type):
            status_list = analyzer.Result(subshape).Status()
            while not status_list.IsEmpty():
                status = status_list.First()
                status_name = getattr(status, "name", str(status))
                if status_name != "BRepCheck_NoError":
                    statuses.add(f"{shape_name}:{status_name}")
                status_list.RemoveFirst()
    return CadTopologySnapshot(
        kernel_valid=analyzer.IsValid(),
        solid_count=len(solids),
        shell_count=len(shells),
        closed_shell_count=closed_shell_count,
        open_edge_count=open_edge_count,
        nonmanifold_edge_count=nonmanifold_edge_count,
        invalid_statuses=tuple(sorted(statuses)),
    )


def _shape_build_result(
    model: DesignModelRevision,
    operation: DesignOperation,
    shape: Any,
    solid_count: int,
) -> CadShapeBuild:
    return _registered_shape_build(
        model, operation.operation_id, operation.input_ids, shape, solid_count
    )


def _registered_shape_build(
    model: DesignModelRevision,
    operation_id: str,
    input_ids: tuple[str, ...],
    shape: Any,
    solid_count: int,
) -> CadShapeBuild:
    brep_tools = importlib.import_module("OCP.BRepTools")
    with tempfile.TemporaryDirectory(prefix="packlab-brep-digest-") as directory:
        brep_path = Path(directory) / "shape.brep"
        if not brep_tools.BRepTools.Write_s(shape, str(brep_path)):
            raise CadAdapterError("cad_brep_serialization_failed")
        geometry_digest = hashlib.sha256(brep_path.read_bytes()).hexdigest()
    handle_seed = "|".join((model.revision_id, operation_id, *input_ids, geometry_digest))
    handle_id = "cad-shape:" + hashlib.sha256(handle_seed.encode("utf-8")).hexdigest()
    parent_revision = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if parent_revision is None:
        raise CadAdapterError("design_model_parent_authority_missing")
    handle = CadShapeHandle(
        handle_id=handle_id,
        source_design_model_revision_id=model.revision_id,
        parent_kind=model.parent_kind,
        parent_authority_revision_id=parent_revision,
        scale_state=model.scale_state,
        coordinate_unit=model.coordinate_unit,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
    )
    with _SHAPE_REGISTRY_LOCK:
        registered = _SHAPE_REGISTRY.get(handle_id)
        if registered is not None and registered[0] != geometry_digest:
            raise CadAdapterError("cad_shape_handle_collision")
        _SHAPE_REGISTRY[handle_id] = (geometry_digest, shape)
    return CadShapeBuild(handle, geometry_digest, solid_count)


def _validate_loft_inputs(
    model: DesignModelRevision,
    sections: tuple[LoftSectionInput, ...],
    operation: DesignOperation,
) -> None:
    if not isinstance(model, DesignModelRevision):
        raise CadAdapterError("design_model_revision_required")
    if not isinstance(operation, DesignOperation) or operation.kind is not OperationKind.LOFT:
        raise CadAdapterError("loft_operation_required")
    if not isinstance(sections, tuple) or not 2 <= len(sections) <= MAX_LOFT_SECTIONS:
        raise CadAdapterError("loft_requires_ordered_sections")
    if any(not isinstance(item, LoftSectionInput) for item in sections):
        raise CadAdapterError("loft_section_input_invalid")
    if (
        operation.model_revision_id != model.revision_id
        or operation.scale_state is not model.scale_state
        or operation.coordinate_unit != model.coordinate_unit
        or operation.physical_accuracy_validation_status
        != model.physical_accuracy_validation_status
        or operation.physical_accuracy_validation_status != PHYSICAL_VALIDATION_DEFERRED
        or operation.mold_use_authorized is not False
        or model.mold_use_authorized is not False
        or operation.axis_origin is not None
        or operation.axis_direction is not None
        or operation.angle_degrees is not None
    ):
        raise CadAdapterError("loft_model_or_authority_mismatch")
    sections_by_id = tuple(item.section.section_id for item in sections)
    feature_ids = tuple(item.feature_id for item in sections)
    positions = tuple(item.axial_position for item in sections)
    if (
        operation.input_ids != sections_by_id
        or operation.section_positions != positions
        or operation.parent_feature_ids[: len(feature_ids)] != feature_ids
        or len(operation.parent_feature_ids) not in {len(feature_ids), len(feature_ids) + 1}
        or any(
            feature_id not in {feature.feature_id for feature in model.features}
            for feature_id in operation.parent_feature_ids
        )
    ):
        raise CadAdapterError("loft_operation_inputs_stale_or_reordered")
    if any(right <= left for left, right in zip(positions, positions[1:])):
        raise CadAdapterError("loft_sections_must_be_strictly_ordered")
    first = sections[0].section
    first_orientation = _cross_section_orientation(first)
    for item in sections:
        section = item.section
        if (
            section.component_id != first.component_id
            or section.coordinate_unit != model.coordinate_unit
            or section.scale_state is not model.scale_state
            or len(section.points) != len(first.points)
            or _cross_section_orientation(section) != first_orientation
        ):
            raise CadAdapterError("loft_section_topology_orientation_or_unit_mismatch")


def _cross_section_orientation(section: CrossSection) -> int:
    if not isinstance(section, CrossSection):
        raise CadAdapterError("loft_cross_section_required")
    points = section.points
    if len(points) < 3:
        raise CadAdapterError("loft_section_point_count_invalid")
    area_twice = sum(
        left.x * right.y - right.x * left.y for left, right in zip(points, (*points[1:], points[0]))
    )
    if not math.isfinite(area_twice) or area_twice == 0.0:
        raise CadAdapterError("loft_section_area_degenerate")
    return 1 if area_twice > 0.0 else -1


def _shape_for_handle(handle: CadShapeHandle) -> Any:
    """Resolve a live opaque handle for adapter-internal downstream CAD operations."""
    if not isinstance(handle, CadShapeHandle):
        raise CadAdapterError("cad_shape_handle_required")
    with _SHAPE_REGISTRY_LOCK:
        registered = _SHAPE_REGISTRY.get(handle.handle_id)
    if registered is None:
        raise CadAdapterError("cad_shape_handle_unavailable_in_runtime")
    return registered[1]


def _validate_revolve_inputs(
    model: DesignModelRevision,
    profile: DesignProfile,
    operation: DesignOperation,
    profile_sample_count: int,
) -> None:
    if not isinstance(model, DesignModelRevision):
        raise CadAdapterError("design_model_revision_required")
    if not isinstance(profile, DesignProfile):
        raise CadAdapterError("design_profile_required")
    if not isinstance(operation, DesignOperation) or operation.kind is not OperationKind.REVOLVE:
        raise CadAdapterError("revolve_operation_required")
    if (
        operation.model_revision_id != model.revision_id
        or operation.input_ids != (profile.profile_id,)
        or operation.scale_state is not model.scale_state
        or operation.coordinate_unit != model.coordinate_unit
        or profile.scale_state is not model.scale_state
        or profile.coordinate_unit != model.coordinate_unit
        or operation.physical_accuracy_validation_status
        != model.physical_accuracy_validation_status
        or operation.physical_accuracy_validation_status != PHYSICAL_VALIDATION_DEFERRED
        or operation.mold_use_authorized is not False
        or model.mold_use_authorized is not False
    ):
        raise CadAdapterError("revolve_model_profile_or_authority_mismatch")
    if len(operation.parent_feature_ids) != 2:
        raise CadAdapterError("revolve_profile_and_axis_features_required")
    if any(
        feature_id not in {feature.feature_id for feature in model.features}
        for feature_id in operation.parent_feature_ids
    ):
        raise CadAdapterError("revolve_feature_reference_stale_or_missing")
    if (
        operation.axis_origin is None
        or operation.axis_direction is None
        or operation.angle_degrees != 360.0
    ):
        raise CadAdapterError("closed_full_revolution_required")
    if (
        not isinstance(profile_sample_count, int)
        or isinstance(profile_sample_count, bool)
        or not 3 <= profile_sample_count <= 2048
    ):
        raise CadAdapterError("revolve_profile_sample_count_invalid")
    if (
        not isinstance(operation.axis_origin, tuple)
        or len(operation.axis_origin) != 3
        or not isinstance(operation.axis_direction, tuple)
        or len(operation.axis_direction) != 3
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in (*operation.axis_origin, *operation.axis_direction)
        )
    ):
        raise CadAdapterError("revolve_axis_values_must_be_finite")
    if abs(math.sqrt(sum(value * value for value in operation.axis_direction)) - 1.0) > 1e-9:
        raise CadAdapterError("revolve_axis_direction_must_be_unit_length")


def _closed_profile_polygon(
    profile: DesignProfile, sample_count: int
) -> tuple[tuple[float, float], ...]:
    samples = profile.sample(sample_count)
    if any(not math.isfinite(item.axial) or not math.isfinite(item.radius) for item in samples):
        raise CadAdapterError("revolve_profile_samples_must_be_finite")
    if any(item.radius < 0.0 for item in samples):
        raise CadAdapterError("revolve_profile_radius_must_be_nonnegative")
    if any(item.radius == 0.0 for item in samples[1:-1]):
        raise CadAdapterError("revolve_profile_must_not_touch_axis_interior")
    boundary = [(item.axial, item.radius) for item in samples]
    boundary.extend(((samples[-1].axial, 0.0), (samples[0].axial, 0.0)))
    polygon: list[tuple[float, float]] = []
    for point in boundary:
        if not polygon or point != polygon[-1]:
            polygon.append(point)
    if len(polygon) > 1 and polygon[0] == polygon[-1]:
        polygon.pop()
    if len(polygon) < 3 or _polygon_self_intersects(polygon):
        raise CadAdapterError("revolve_profile_must_form_simple_closed_region")
    area_twice = sum(
        left[0] * right[1] - right[0] * left[1]
        for left, right in zip(polygon, (*polygon[1:], polygon[0]))
    )
    if not math.isfinite(area_twice) or area_twice == 0.0:
        raise CadAdapterError("revolve_profile_region_degenerate")
    if area_twice < 0.0:
        polygon.reverse()
    return tuple(polygon)


def _polygon_self_intersects(polygon: list[tuple[float, float]]) -> bool:
    segments = tuple(zip(polygon, (*polygon[1:], polygon[0])))
    count = len(segments)
    for left_index, (left_start, left_end) in enumerate(segments):
        for right_index in range(left_index + 1, count):
            if right_index == left_index + 1 or (left_index == 0 and right_index == count - 1):
                continue
            right_start, right_end = segments[right_index]
            if _segments_intersect(left_start, left_end, right_start, right_end):
                return True
    return False


def _segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    def orientation(
        first: tuple[float, float], second: tuple[float, float], third: tuple[float, float]
    ) -> float:
        return (second[0] - first[0]) * (third[1] - first[1]) - (second[1] - first[1]) * (
            third[0] - first[0]
        )

    def on_segment(
        first: tuple[float, float], second: tuple[float, float], point: tuple[float, float]
    ) -> bool:
        return min(first[0], second[0]) <= point[0] <= max(first[0], second[0]) and min(
            first[1], second[1]
        ) <= point[1] <= max(first[1], second[1])

    first = orientation(a, b, c)
    second = orientation(a, b, d)
    third = orientation(c, d, a)
    fourth = orientation(c, d, b)
    if ((first > 0.0 and second < 0.0) or (first < 0.0 and second > 0.0)) and (
        (third > 0.0 and fourth < 0.0) or (third < 0.0 and fourth > 0.0)
    ):
        return True
    return (
        (first == 0.0 and on_segment(a, b, c))
        or (second == 0.0 and on_segment(a, b, d))
        or (third == 0.0 and on_segment(c, d, a))
        or (fourth == 0.0 and on_segment(c, d, b))
    )


def _cross_product(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _unit_vector(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if not math.isfinite(magnitude) or magnitude == 0.0:
        raise CadAdapterError("revolve_radial_basis_invalid")
    return tuple(value / magnitude for value in vector)  # type: ignore[return-value]


def probe_cad_runtime() -> CadRuntimeDiagnostics:
    """Probe the installed binding and kernel; never install, download, or fall back."""
    try:
        binding_module = _import_binding_module()
    except (ImportError, ModuleNotFoundError):
        return _unavailable_diagnostics("binding_import_unavailable")
    except Exception:
        return _unavailable_diagnostics("binding_import_failed")

    binding_version: str | None = None
    try:
        binding_version = importlib.metadata.version(CAD_BINDING_PACKAGE)
        binding_version_status = CAD_RUNTIME_VERSION_STATUS_OBSERVED
    except importlib.metadata.PackageNotFoundError:
        version_candidate = getattr(binding_module, "__version__", None)
        binding_version = version_candidate if isinstance(version_candidate, str) else None
        binding_version_status = (
            CAD_RUNTIME_VERSION_STATUS_OBSERVED
            if binding_version
            else CAD_RUNTIME_VERSION_STATUS_UNAVAILABLE
        )

    kernel_version, kernel_error = _observe_kernel_version()
    kernel_version_status = (
        CAD_RUNTIME_VERSION_STATUS_OBSERVED
        if kernel_version is not None
        else CAD_RUNTIME_VERSION_STATUS_UNAVAILABLE
    )
    capabilities = tuple(_probe_capability(name, probe) for name, probe in _CAPABILITY_PROBES)
    if all(item.status is CadCapabilityStatus.AVAILABLE for item in capabilities):
        status = CadRuntimeStatus.READY
    else:
        status = CadRuntimeStatus.PARTIAL
    return CadRuntimeDiagnostics(
        status=status,
        binding_package=CAD_BINDING_PACKAGE,
        binding_version=binding_version if isinstance(binding_version, str) else None,
        binding_version_status=binding_version_status,
        kernel_version=kernel_version,
        kernel_version_status=kernel_version_status,
        platform_system=platform.system(),
        platform_machine=platform.machine(),
        capabilities=capabilities,
        error_code=kernel_error,
    )


def _import_binding_module() -> Any:
    return importlib.import_module("OCP")


def _unavailable_diagnostics(error_code: str) -> CadRuntimeDiagnostics:
    names = tuple(name for name, _ in _CAPABILITY_PROBES)
    return CadRuntimeDiagnostics(
        status=CadRuntimeStatus.UNAVAILABLE,
        binding_package=CAD_BINDING_PACKAGE,
        binding_version=None,
        binding_version_status=CAD_RUNTIME_VERSION_STATUS_UNAVAILABLE,
        kernel_version=None,
        kernel_version_status=CAD_RUNTIME_VERSION_STATUS_UNAVAILABLE,
        platform_system=platform.system(),
        platform_machine=platform.machine(),
        capabilities=tuple(
            CadCapability(name, CadCapabilityStatus.UNAVAILABLE, error_code) for name in names
        ),
        error_code=error_code,
    )


def _probe_capability(name: str, probe: Callable[[], None]) -> CadCapability:
    try:
        probe()
    except (ImportError, ModuleNotFoundError):
        return CadCapability(
            name, CadCapabilityStatus.UNAVAILABLE, "capability_dependency_unavailable"
        )
    except Exception as error:
        return CadCapability(name, CadCapabilityStatus.ERROR, type(error).__name__)
    return CadCapability(name, CadCapabilityStatus.AVAILABLE)


def _make_box() -> Any:
    module = importlib.import_module("OCP.BRepPrimAPI")
    return module.BRepPrimAPI_MakeBox(10.0, 8.0, 6.0).Shape()


def _probe_brep() -> None:
    shape = _make_box()
    if shape.IsNull():
        raise RuntimeError("brep_construction_returned_null")


def _make_revolve() -> Any:
    gp = importlib.import_module("OCP.gp")
    builder = importlib.import_module("OCP.BRepBuilderAPI")
    primitive = importlib.import_module("OCP.BRepPrimAPI")
    points = (
        gp.gp_Pnt(2.0, 0.0, 0.0),
        gp.gp_Pnt(4.0, 0.0, 0.0),
        gp.gp_Pnt(4.0, 0.0, 5.0),
        gp.gp_Pnt(2.0, 0.0, 5.0),
    )
    wire_builder = builder.BRepBuilderAPI_MakeWire()
    for left, right in zip(points, (*points[1:], points[0])):
        wire_builder.Add(builder.BRepBuilderAPI_MakeEdge(left, right).Edge())
    face = builder.BRepBuilderAPI_MakeFace(wire_builder.Wire()).Face()
    axis = gp.gp_Ax1(gp.gp_Pnt(0.0, 0.0, 0.0), gp.gp_Dir(0.0, 0.0, 1.0))
    return primitive.BRepPrimAPI_MakeRevol(face, axis, 2.0 * math.pi).Shape()


def _probe_revolve() -> None:
    shape = _make_revolve()
    if shape.IsNull():
        raise RuntimeError("revolve_returned_null")


def _circle_wire(z_value: float, radius: float) -> Any:
    gp = importlib.import_module("OCP.gp")
    builder = importlib.import_module("OCP.BRepBuilderAPI")
    circle = gp.gp_Circ(gp.gp_Ax2(gp.gp_Pnt(0.0, 0.0, z_value), gp.gp_Dir(0.0, 0.0, 1.0)), radius)
    edge = builder.BRepBuilderAPI_MakeEdge(circle).Edge()
    return builder.BRepBuilderAPI_MakeWire(edge).Wire()


def _make_loft() -> Any:
    loft_module = importlib.import_module("OCP.BRepOffsetAPI")
    loft = loft_module.BRepOffsetAPI_ThruSections(True, False)
    loft.AddWire(_circle_wire(0.0, 3.0))
    loft.AddWire(_circle_wire(8.0, 2.0))
    loft.Build()
    return loft.Shape()


def _probe_loft() -> None:
    shape = _make_loft()
    if shape.IsNull():
        raise RuntimeError("loft_returned_null")


def _probe_boolean() -> None:
    module = importlib.import_module("OCP.BRepAlgoAPI")
    primitive = importlib.import_module("OCP.BRepPrimAPI")
    left = _make_box()
    right = primitive.BRepPrimAPI_MakeBox(
        importlib.import_module("OCP.gp").gp_Pnt(4.0, 0.0, 0.0), 6.0, 4.0, 6.0
    ).Shape()
    result = module.BRepAlgoAPI_Cut(left, right)
    result.Build()
    if result.Shape().IsNull():
        raise RuntimeError("boolean_cut_returned_null")


def _probe_topology() -> None:
    module = importlib.import_module("OCP.BRepCheck")
    if not module.BRepCheck_Analyzer(_make_box()).IsValid():
        raise RuntimeError("topology_validation_failed")


def _probe_tessellation() -> None:
    mesh_module = importlib.import_module("OCP.BRepMesh")
    explorer_module = importlib.import_module("OCP.TopExp")
    topabs = importlib.import_module("OCP.TopAbs")
    topo_ds = importlib.import_module("OCP.TopoDS")
    brep = importlib.import_module("OCP.BRep")
    top_loc = importlib.import_module("OCP.TopLoc")
    shape = _make_box()
    mesh_module.BRepMesh_IncrementalMesh(shape, 0.1).Perform()
    explorer = explorer_module.TopExp_Explorer(shape, topabs.TopAbs_FACE)
    triangle_count = 0
    while explorer.More():
        face = topo_ds.TopoDS.Face_s(explorer.Current())
        triangulation = brep.BRep_Tool.Triangulation_s(face, top_loc.TopLoc_Location())
        if triangulation is not None:
            triangle_count += triangulation.NbTriangles()
        explorer.Next()
    if triangle_count <= 0:
        raise RuntimeError("tessellation_empty")


def _write_step(path: Path) -> None:
    step = importlib.import_module("OCP.STEPControl")
    ifselect = importlib.import_module("OCP.IFSelect")
    writer = step.STEPControl_Writer()
    if writer.Transfer(_make_box(), step.STEPControl_AsIs) != ifselect.IFSelect_RetDone:
        raise RuntimeError("step_transfer_failed")
    if writer.Write(str(path)) != ifselect.IFSelect_RetDone:
        raise RuntimeError("step_write_failed")


def _probe_step_write() -> None:
    with tempfile.TemporaryDirectory(prefix="packlab-cad-probe-") as directory:
        path = Path(directory) / "capability.step"
        _write_step(path)
        if not path.is_file() or path.stat().st_size <= 0:
            raise RuntimeError("step_write_output_missing")


def _probe_step_read() -> None:
    step = importlib.import_module("OCP.STEPControl")
    ifselect = importlib.import_module("OCP.IFSelect")
    with tempfile.TemporaryDirectory(prefix="packlab-cad-probe-") as directory:
        path = Path(directory) / "capability.step"
        _write_step(path)
        reader = step.STEPControl_Reader()
        if reader.ReadFile(str(path)) != ifselect.IFSelect_RetDone:
            raise RuntimeError("step_read_failed")
        if reader.TransferRoots() <= 0:
            raise RuntimeError("step_root_transfer_failed")


def _probe_stl_write() -> None:
    stl = importlib.import_module("OCP.StlAPI")
    with tempfile.TemporaryDirectory(prefix="packlab-cad-probe-") as directory:
        path = Path(directory) / "capability.stl"
        shape = _make_box()
        importlib.import_module("OCP.BRepMesh").BRepMesh_IncrementalMesh(shape, 0.1).Perform()
        if stl.StlAPI_Writer().Write(shape, str(path)) is False:
            raise RuntimeError("stl_write_failed")
        if not path.is_file() or path.stat().st_size <= 0:
            raise RuntimeError("stl_write_output_missing")


_CAPABILITY_PROBES: tuple[tuple[str, Callable[[], None]], ...] = (
    ("brep_construction", _probe_brep),
    ("revolve", _probe_revolve),
    ("loft", _probe_loft),
    ("booleans", _probe_boolean),
    ("topology_validation", _probe_topology),
    ("tessellation", _probe_tessellation),
    ("step_write", _probe_step_write),
    ("step_read", _probe_step_read),
    ("stl_write", _probe_stl_write),
)


class _VsFixedFileInfo(ctypes.Structure):
    _fields_ = (("value", ctypes.c_uint32 * 13),)


def _observe_kernel_version() -> tuple[str | None, str | None]:
    if platform.system() != "Windows":
        return None, "kernel_version_resource_unavailable_on_platform"
    try:
        distribution = importlib.metadata.distribution(CAD_BINDING_PACKAGE)
    except importlib.metadata.PackageNotFoundError:
        return None, "binding_distribution_metadata_unavailable"
    kernel_files = tuple(
        Path(str(distribution.locate_file(item)))
        for item in distribution.files or ()
        if Path(item).name.casefold().startswith("tkernel-")
        and Path(item).suffix.casefold() == ".dll"
    )
    if len(kernel_files) != 1:
        return None, "kernel_binary_identity_unavailable"
    try:
        return _read_windows_file_version(kernel_files[0]), None
    except Exception:
        return None, "kernel_version_resource_unavailable"


def _read_windows_file_version(path: Path) -> str:
    version_api = ctypes.WinDLL("version", use_last_error=True)
    size_of = version_api.GetFileVersionInfoSizeW
    size_of.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32))
    size_of.restype = ctypes.c_uint32
    size = size_of(str(path), None)
    if size <= 0:
        raise OSError("file_version_resource_missing")
    data = ctypes.create_string_buffer(size)
    get_info = version_api.GetFileVersionInfoW
    get_info.argtypes = (ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p)
    get_info.restype = ctypes.c_int
    if not get_info(str(path), 0, size, data):
        raise OSError("file_version_read_failed")
    query = version_api.VerQueryValueW
    query.argtypes = (
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_uint32),
    )
    query.restype = ctypes.c_int
    value = ctypes.c_void_p()
    length = ctypes.c_uint32()
    if not query(data, "\\", ctypes.byref(value), ctypes.byref(length)):
        raise OSError("file_version_query_failed")
    fixed = ctypes.cast(value, ctypes.POINTER(_VsFixedFileInfo)).contents.value
    if fixed[0] != 0xFEEF04BD:
        raise ValueError("file_version_resource_invalid")
    parts = [
        fixed[2] >> 16,
        fixed[2] & 0xFFFF,
        fixed[3] >> 16,
        fixed[3] & 0xFFFF,
    ]
    while len(parts) > 3 and parts[-1] == 0:
        parts = parts[:-1]
    return ".".join(str(part) for part in parts)


__all__ = [
    "CAD_BINDING_PACKAGE",
    "CAD_RUNTIME_VERSION_STATUS_OBSERVED",
    "CAD_RUNTIME_VERSION_STATUS_UNAVAILABLE",
    "PHYSICAL_VALIDATION_DEFERRED",
    "CadAdapterError",
    "CadBooleanBuild",
    "CadCapability",
    "CadCapabilityStatus",
    "CadCrossSectionInput",
    "CadPoint2",
    "CadProfileControlPoint",
    "CadProfileInput",
    "CadRuntimeDiagnostics",
    "CadRuntimeStatus",
    "CadShapeBuild",
    "CadShapeHandle",
    "CadTessellationData",
    "CadTopologySnapshot",
    "build_lofted_shape",
    "build_polygon_prism_cut",
    "build_revolved_shape",
    "cad_shape_bounds",
    "cross_section_to_cad_input",
    "inspect_shape_topology",
    "probe_cad_runtime",
    "profile_to_cad_input",
    "shape_handle_for_model",
    "tessellate_cad_shape",
]
