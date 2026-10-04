"""PackLab-owned CAD values and capability diagnostics over the selected OCCT binding."""

from __future__ import annotations

import ctypes
import importlib
import importlib.metadata
import math
import platform
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .cross_section import CrossSection
from .design_model import DesignModelParentKind, DesignModelRevision
from .design_profile import DesignProfile
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
    "CadCapability",
    "CadCapabilityStatus",
    "CadCrossSectionInput",
    "CadPoint2",
    "CadProfileControlPoint",
    "CadProfileInput",
    "CadRuntimeDiagnostics",
    "CadRuntimeStatus",
    "CadShapeHandle",
    "cross_section_to_cad_input",
    "probe_cad_runtime",
    "profile_to_cad_input",
    "shape_handle_for_model",
]
