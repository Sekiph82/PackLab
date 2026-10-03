"""PackLab-owned point-cloud and triangle-mesh boundary for Open3D."""

from __future__ import annotations

import importlib
import importlib.metadata
import math
import platform
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from types import ModuleType
from typing import Any

OPEN3D_DISTRIBUTION = "open3d"
OPEN3D_VERSION = "0.20.0"
GEOMETRY_ADAPTER_CONTRACT = "packlab.geometry-analysis-adapter.v1"

type Point3 = tuple[float, float, float]
type Triangle = tuple[int, int, int]
type Open3DLoader = Callable[[], ModuleType]


class CapabilityStatus(StrEnum):
    """The observed state of the installed Open3D geometry capability."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class GeometryAdapterError(ValueError):
    """Base error for invalid geometry or an unusable Open3D capability."""


class InvalidGeometry(GeometryAdapterError):
    """Raised when geometry does not satisfy the PackLab value contract."""


class GeometryCapabilityUnavailable(GeometryAdapterError):
    """Raised when the selected Open3D capability cannot safely be used."""


def _vector3(value: object, field: str) -> Point3:
    if not isinstance(value, tuple) or len(value) != 3:
        raise InvalidGeometry(f"{field} entries must be three-value tuples")
    converted: list[float] = []
    for component in value:
        if isinstance(component, bool) or not isinstance(component, (int, float)):
            raise InvalidGeometry(f"{field} components must be finite numbers")
        number = float(component)
        if not math.isfinite(number):
            raise InvalidGeometry(f"{field} components must be finite numbers")
        converted.append(number)
    return (converted[0], converted[1], converted[2])


def _vectors(value: object, field: str) -> tuple[Point3, ...] | None:
    if value is None:
        return None
    if not isinstance(value, tuple):
        raise InvalidGeometry(f"{field} must be a tuple when provided")
    return tuple(_vector3(item, field) for item in value)


@dataclass(frozen=True, slots=True)
class PointCloudData:
    """Backend-neutral point samples and optional per-point attributes."""

    points: tuple[Point3, ...]
    colors: tuple[Point3, ...] | None = None
    normals: tuple[Point3, ...] | None = None

    def __post_init__(self) -> None:
        points = _vectors(self.points, "points")
        colors = _vectors(self.colors, "colors")
        normals = _vectors(self.normals, "normals")
        if points is None:
            raise InvalidGeometry("points are required")
        if colors is not None and len(colors) != len(points):
            raise InvalidGeometry("colors must match the point count")
        if normals is not None and len(normals) != len(points):
            raise InvalidGeometry("normals must match the point count")
        if colors is not None and any(
            not 0.0 <= channel <= 1.0 for rgb in colors for channel in rgb
        ):
            raise InvalidGeometry("color channels must be in the closed interval [0, 1]")
        object.__setattr__(self, "points", points)
        object.__setattr__(self, "colors", colors)
        object.__setattr__(self, "normals", normals)


@dataclass(frozen=True, slots=True)
class TriangleMeshData:
    """Backend-neutral triangle mesh and optional vertex attributes."""

    vertices: tuple[Point3, ...]
    triangles: tuple[Triangle, ...]
    vertex_colors: tuple[Point3, ...] | None = None
    vertex_normals: tuple[Point3, ...] | None = None

    def __post_init__(self) -> None:
        vertices = _vectors(self.vertices, "vertices")
        colors = _vectors(self.vertex_colors, "vertex_colors")
        normals = _vectors(self.vertex_normals, "vertex_normals")
        if vertices is None:
            raise InvalidGeometry("vertices are required")
        if not isinstance(self.triangles, tuple):
            raise InvalidGeometry("triangles must be a tuple")
        triangles: list[Triangle] = []
        for face in self.triangles:
            if not isinstance(face, tuple) or len(face) != 3:
                raise InvalidGeometry("triangle entries must contain three vertex indices")
            if any(isinstance(index, bool) or not isinstance(index, int) for index in face):
                raise InvalidGeometry("triangle vertex indices must be integers")
            if len(set(face)) != 3 or any(index < 0 or index >= len(vertices) for index in face):
                raise InvalidGeometry("triangle vertex indices must be distinct and in range")
            triangles.append((face[0], face[1], face[2]))
        if colors is not None and len(colors) != len(vertices):
            raise InvalidGeometry("vertex_colors must match the vertex count")
        if normals is not None and len(normals) != len(vertices):
            raise InvalidGeometry("vertex_normals must match the vertex count")
        if colors is not None and any(not 0.0 <= c <= 1.0 for rgb in colors for c in rgb):
            raise InvalidGeometry("color channels must be in the closed interval [0, 1]")
        object.__setattr__(self, "vertices", vertices)
        object.__setattr__(self, "triangles", tuple(triangles))
        object.__setattr__(self, "vertex_colors", colors)
        object.__setattr__(self, "vertex_normals", normals)


@dataclass(frozen=True, slots=True)
class Open3DCapability:
    """Observed package, platform, build and geometry-operation evidence."""

    contract: str
    status: CapabilityStatus
    distribution: str
    expected_version: str
    observed_version: str | None
    python_version: str
    platform: str
    machine: str
    build_config: tuple[tuple[str, bool | str], ...]
    operations: tuple[str, ...]
    detail: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self) | {"status": self.status.value}


@dataclass(frozen=True, slots=True)
class PointCloudRegistrationOutput:
    """PackLab-owned values returned from one pinned Open3D point-to-point ICP run."""

    transformation: tuple[float, ...]
    fitness: float
    inlier_rmse: float
    correspondences: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class MeshSurfaceDistanceOutput:
    """PackLab-owned point-to-triangle-surface distances and target topology facts."""

    distances: tuple[float, ...]
    signed: bool
    target_watertight: bool
    target_self_intersecting: bool


def _load_open3d() -> ModuleType:
    """Import the installed package only; this boundary never installs or downloads."""

    return importlib.import_module("open3d")


def _metadata_version() -> str | None:
    try:
        return importlib.metadata.version(OPEN3D_DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError:
        return None


def _capability(
    status: CapabilityStatus,
    observed_version: str | None,
    build_config: tuple[tuple[str, bool | str], ...],
    operations: tuple[str, ...],
    detail: str,
) -> Open3DCapability:
    return Open3DCapability(
        contract=GEOMETRY_ADAPTER_CONTRACT,
        status=status,
        distribution=OPEN3D_DISTRIBUTION,
        expected_version=OPEN3D_VERSION,
        observed_version=observed_version,
        python_version=platform.python_version(),
        platform=platform.platform(),
        machine=platform.machine(),
        build_config=build_config,
        operations=operations,
        detail=detail,
    )


def probe_open3d(loader: Open3DLoader = _load_open3d) -> Open3DCapability:
    """Probe the installed Open3D build without network or subprocess fallbacks."""

    try:
        module = loader()
    except ModuleNotFoundError as exc:
        return _capability(
            CapabilityStatus.UNAVAILABLE,
            _metadata_version(),
            (),
            (),
            f"Open3D import unavailable ({exc.name or 'module not found'})",
        )
    except (ImportError, OSError) as exc:
        return _capability(
            CapabilityStatus.UNKNOWN,
            _metadata_version(),
            (),
            (),
            f"Open3D import failed ({type(exc).__name__})",
        )

    version_value = getattr(module, "__version__", None)
    version = version_value if isinstance(version_value, str) else _metadata_version()
    raw_config = getattr(module, "_build_config", None)
    if not isinstance(raw_config, Mapping):
        return _capability(
            CapabilityStatus.UNKNOWN,
            version,
            (),
            (),
            "Open3D build configuration is unavailable",
        )
    config = tuple(
        sorted(
            (key, value)
            for key, value in raw_config.items()
            if isinstance(key, str) and isinstance(value, (bool, str))
        )
    )
    geometry = getattr(module, "geometry", None)
    utility = getattr(module, "utility", None)
    operations: list[str] = []
    if callable(getattr(geometry, "PointCloud", None)) and callable(
        getattr(utility, "Vector3dVector", None)
    ):
        operations.append("point_cloud_conversion")
    if (
        callable(getattr(geometry, "TriangleMesh", None))
        and callable(getattr(utility, "Vector3dVector", None))
        and callable(getattr(utility, "Vector3iVector", None))
    ):
        operations.append("triangle_mesh_conversion")
        if callable(
            getattr(getattr(geometry, "TriangleMesh", None), "simplify_quadric_decimation", None)
        ):
            operations.append("triangle_mesh_quadric_decimation")
    registration = getattr(getattr(module, "pipelines", None), "registration", None)
    if all(
        callable(getattr(registration, name, None))
        for name in (
            "registration_icp",
            "TransformationEstimationPointToPoint",
            "ICPConvergenceCriteria",
        )
    ):
        operations.append("point_to_point_registration")
    tensor_geometry = getattr(getattr(module, "t", None), "geometry", None)
    raycasting_scene = getattr(tensor_geometry, "RaycastingScene", None)
    tensor_mesh = getattr(getattr(tensor_geometry, "TriangleMesh", None), "from_legacy", None)
    if callable(raycasting_scene) and callable(tensor_mesh):
        operations.append("triangle_mesh_surface_distance")

    if version != OPEN3D_VERSION:
        status = CapabilityStatus.UNKNOWN
        detail = f"observed Open3D version {version!r}; expected exact pin {OPEN3D_VERSION}"
    elif not {"point_cloud_conversion", "triangle_mesh_conversion"}.issubset(operations):
        status = CapabilityStatus.UNKNOWN
        detail = "the pinned Open3D build is missing a required geometry conversion capability"
    else:
        status = CapabilityStatus.AVAILABLE
        detail = f"exact Open3D {OPEN3D_VERSION} import and geometry capabilities verified"
    return _capability(status, version, config, tuple(operations), detail)


def _nested_attribute(module: ModuleType, parent: str, name: str) -> Any:
    container = getattr(module, parent, None)
    value = getattr(container, name, None)
    if not callable(value):
        raise GeometryCapabilityUnavailable(
            f"Open3D geometry capability is missing {parent}.{name}"
        )
    return value


def _from_vector(values: Any) -> tuple[Point3, ...]:
    try:
        return tuple((float(row[0]), float(row[1]), float(row[2])) for row in values)
    except (IndexError, TypeError, ValueError, OverflowError) as exc:
        raise GeometryAdapterError("Open3D returned malformed three-dimensional geometry") from exc


def _from_triangles(values: Any) -> tuple[Triangle, ...]:
    try:
        return tuple((int(row[0]), int(row[1]), int(row[2])) for row in values)
    except (IndexError, TypeError, ValueError, OverflowError) as exc:
        raise GeometryAdapterError("Open3D returned malformed triangle indices") from exc


class Open3DGeometryAdapter:
    """Convert PackLab-owned geometry values through the pinned Open3D API."""

    def __init__(self, loader: Open3DLoader = _load_open3d) -> None:
        self._loader = loader

    def probe(self) -> Open3DCapability:
        return probe_open3d(self._loader)

    def round_trip_point_cloud(self, cloud: PointCloudData) -> PointCloudData:
        module = self._require_module()
        point_cloud_type = _nested_attribute(module, "geometry", "PointCloud")
        vector3d = _nested_attribute(module, "utility", "Vector3dVector")
        converted = point_cloud_type()
        converted.points = vector3d(cloud.points)
        if cloud.colors is not None:
            converted.colors = vector3d(cloud.colors)
        if cloud.normals is not None:
            converted.normals = vector3d(cloud.normals)
        return PointCloudData(
            points=_from_vector(converted.points),
            colors=_from_vector(converted.colors) if cloud.colors is not None else None,
            normals=_from_vector(converted.normals) if cloud.normals is not None else None,
        )

    def round_trip_triangle_mesh(self, mesh: TriangleMeshData) -> TriangleMeshData:
        module = self._require_module()
        mesh_type = _nested_attribute(module, "geometry", "TriangleMesh")
        vector3d = _nested_attribute(module, "utility", "Vector3dVector")
        vector3i = _nested_attribute(module, "utility", "Vector3iVector")
        converted = mesh_type()
        converted.vertices = vector3d(mesh.vertices)
        converted.triangles = vector3i(mesh.triangles)
        if mesh.vertex_colors is not None:
            converted.vertex_colors = vector3d(mesh.vertex_colors)
        if mesh.vertex_normals is not None:
            converted.vertex_normals = vector3d(mesh.vertex_normals)
        return TriangleMeshData(
            vertices=_from_vector(converted.vertices),
            triangles=_from_triangles(converted.triangles),
            vertex_colors=(
                _from_vector(converted.vertex_colors) if mesh.vertex_colors is not None else None
            ),
            vertex_normals=(
                _from_vector(converted.vertex_normals) if mesh.vertex_normals is not None else None
            ),
        )

    def simplify_triangle_mesh(
        self,
        mesh: TriangleMeshData,
        *,
        target_triangle_count: int,
        maximum_error: float,
        boundary_weight: float,
    ) -> TriangleMeshData:
        """Run Open3D quadric decimation and return only PackLab-owned values."""
        module = self._require_module()
        mesh_type = _nested_attribute(module, "geometry", "TriangleMesh")
        vector3d = _nested_attribute(module, "utility", "Vector3dVector")
        vector3i = _nested_attribute(module, "utility", "Vector3iVector")
        converted = mesh_type()
        converted.vertices = vector3d(mesh.vertices)
        converted.triangles = vector3i(mesh.triangles)
        if mesh.vertex_colors is not None:
            converted.vertex_colors = vector3d(mesh.vertex_colors)
        if mesh.vertex_normals is not None:
            converted.vertex_normals = vector3d(mesh.vertex_normals)
        simplify_method = getattr(converted, "simplify_quadric_decimation", None)
        if not callable(simplify_method):
            raise GeometryCapabilityUnavailable(
                "Open3D geometry capability is missing TriangleMesh.simplify_quadric_decimation"
            )
        result = simplify_method(
            target_number_of_triangles=target_triangle_count,
            maximum_error=maximum_error,
            boundary_weight=boundary_weight,
        )
        return TriangleMeshData(
            vertices=_from_vector(result.vertices),
            triangles=_from_triangles(result.triangles),
            vertex_colors=(
                _from_vector(result.vertex_colors)
                if mesh.vertex_colors is not None
                and len(result.vertex_colors) == len(result.vertices)
                else None
            ),
            vertex_normals=(
                _from_vector(result.vertex_normals)
                if mesh.vertex_normals is not None
                and len(result.vertex_normals) == len(result.vertices)
                else None
            ),
        )

    def register_point_clouds(
        self,
        source: PointCloudData,
        target: PointCloudData,
        *,
        initial_transform: tuple[float, ...],
        maximum_correspondence_distance: float,
        relative_fitness: float,
        relative_rmse: float,
        maximum_iterations: int,
    ) -> PointCloudRegistrationOutput:
        """Run rigid point-to-point ICP and expose no Open3D-owned result objects."""

        module = self._require_module()
        registration = getattr(getattr(module, "pipelines", None), "registration", None)
        registration_icp = getattr(registration, "registration_icp", None)
        estimator_type = getattr(registration, "TransformationEstimationPointToPoint", None)
        criteria_type = getattr(registration, "ICPConvergenceCriteria", None)
        if not callable(registration_icp):
            raise GeometryCapabilityUnavailable(
                "Open3D geometry capability is missing point-to-point ICP registration"
            )
        if not callable(estimator_type):
            raise GeometryCapabilityUnavailable(
                "Open3D geometry capability is missing point-to-point ICP estimation"
            )
        if not callable(criteria_type):
            raise GeometryCapabilityUnavailable(
                "Open3D geometry capability is missing ICP convergence criteria"
            )
        if len(initial_transform) != 16 or any(
            not math.isfinite(value) for value in initial_transform
        ):
            raise InvalidGeometry("registration initial transform must contain 16 finite values")
        if (
            not math.isfinite(maximum_correspondence_distance)
            or maximum_correspondence_distance <= 0
            or not math.isfinite(relative_fitness)
            or relative_fitness < 0
            or not math.isfinite(relative_rmse)
            or relative_rmse < 0
            or isinstance(maximum_iterations, bool)
            or not isinstance(maximum_iterations, int)
            or maximum_iterations < 1
        ):
            raise InvalidGeometry("registration convergence criteria are invalid")

        source_cloud = self.round_trip_point_cloud(source)
        target_cloud = self.round_trip_point_cloud(target)
        point_cloud_type = _nested_attribute(module, "geometry", "PointCloud")
        vector3d = _nested_attribute(module, "utility", "Vector3dVector")
        converted_source = point_cloud_type()
        converted_source.points = vector3d(source_cloud.points)
        converted_target = point_cloud_type()
        converted_target.points = vector3d(target_cloud.points)
        criteria = criteria_type(
            relative_fitness=relative_fitness,
            relative_rmse=relative_rmse,
            max_iteration=maximum_iterations,
        )
        result = registration_icp(
            converted_source,
            converted_target,
            maximum_correspondence_distance,
            [list(initial_transform[index : index + 4]) for index in range(0, 16, 4)],
            estimator_type(with_scaling=False),
            criteria,
        )
        matrix = tuple(float(value) for row in result.transformation for value in row)
        if len(matrix) != 16 or any(not math.isfinite(value) for value in matrix):
            raise GeometryAdapterError("Open3D returned a malformed registration transform")
        fitness = float(result.fitness)
        inlier_rmse = float(result.inlier_rmse)
        correspondences = tuple(
            sorted((int(pair[0]), int(pair[1])) for pair in result.correspondence_set)
        )
        if not math.isfinite(fitness) or (not math.isfinite(inlier_rmse) and correspondences):
            raise GeometryAdapterError("Open3D returned non-finite registration statistics")
        return PointCloudRegistrationOutput(matrix, fitness, inlier_rmse, correspondences)

    def compute_mesh_surface_distances(
        self,
        mesh: TriangleMeshData,
        query: PointCloudData,
        *,
        signed: bool,
        maximum_query_points: int = 50_000,
    ) -> MeshSurfaceDistanceOutput:
        """Measure query points to exact mesh triangles through Open3D ray casting."""

        if not isinstance(mesh, TriangleMeshData) or not mesh.vertices or not mesh.triangles:
            raise InvalidGeometry("surface-distance target must be a non-empty triangle mesh")
        if not isinstance(query, PointCloudData) or not query.points:
            raise InvalidGeometry("surface-distance query point cloud must be non-empty")
        if (
            isinstance(maximum_query_points, bool)
            or not isinstance(maximum_query_points, int)
            or maximum_query_points < 1
            or maximum_query_points > 100_000
            or len(query.points) > maximum_query_points
        ):
            raise InvalidGeometry("surface-distance query point bound exceeded")
        if not isinstance(signed, bool):
            raise InvalidGeometry("surface-distance signed policy must be boolean")
        if len(mesh.triangles) > 1_000_000:
            raise InvalidGeometry("surface-distance target triangle bound exceeded")

        module = self._require_module()
        legacy_type = _nested_attribute(module, "geometry", "TriangleMesh")
        vector3d = _nested_attribute(module, "utility", "Vector3dVector")
        vector3i = _nested_attribute(module, "utility", "Vector3iVector")
        legacy_mesh = legacy_type()
        legacy_mesh.vertices = vector3d(mesh.vertices)
        legacy_mesh.triangles = vector3i(mesh.triangles)
        watertight = bool(legacy_mesh.is_watertight())
        self_intersecting_check = getattr(legacy_mesh, "is_self_intersecting", None)
        self_intersecting = (
            bool(self_intersecting_check()) if callable(self_intersecting_check) else True
        )
        if signed and (not watertight or self_intersecting):
            raise InvalidGeometry(
                "signed surface distance requires a watertight, non-self-intersecting mesh"
            )

        tensor_geometry = getattr(getattr(module, "t", None), "geometry", None)
        tensor_mesh_type = getattr(tensor_geometry, "TriangleMesh", None)
        raycasting_scene_type = getattr(tensor_geometry, "RaycastingScene", None)
        tensor_module = getattr(module, "core", None)
        tensor_factory = getattr(tensor_module, "Tensor", None)
        dtype = getattr(getattr(tensor_module, "Dtype", None), "Float32", None)
        from_legacy = getattr(tensor_mesh_type, "from_legacy", None)
        if (
            not callable(from_legacy)
            or not callable(raycasting_scene_type)
            or not callable(tensor_factory)
            or dtype is None
        ):
            raise GeometryCapabilityUnavailable(
                "Open3D geometry capability is missing triangle-mesh surface distance"
            )
        tensor_mesh = from_legacy(legacy_mesh)
        scene = raycasting_scene_type()
        scene.add_triangles(tensor_mesh)
        query_tensor = tensor_factory(query.points, dtype=dtype)
        if signed:
            distance_tensor = scene.compute_signed_distance(query_tensor, nthreads=1, nsamples=3)
        else:
            distance_tensor = scene.compute_distance(query_tensor, nthreads=1)
        distances = tuple(float(value) for value in distance_tensor.numpy().reshape(-1))
        if len(distances) != len(query.points) or any(
            not math.isfinite(value) for value in distances
        ):
            raise GeometryAdapterError("Open3D returned malformed surface distances")
        return MeshSurfaceDistanceOutput(distances, signed, watertight, self_intersecting)

    def _require_module(self) -> ModuleType:
        capability = self.probe()
        if capability.status is not CapabilityStatus.AVAILABLE:
            raise GeometryCapabilityUnavailable(capability.detail)
        return self._loader()


__all__ = [
    "GEOMETRY_ADAPTER_CONTRACT",
    "OPEN3D_DISTRIBUTION",
    "OPEN3D_VERSION",
    "CapabilityStatus",
    "GeometryAdapterError",
    "GeometryCapabilityUnavailable",
    "InvalidGeometry",
    "MeshSurfaceDistanceOutput",
    "Open3DCapability",
    "Open3DGeometryAdapter",
    "PointCloudRegistrationOutput",
    "Point3",
    "PointCloudData",
    "Triangle",
    "TriangleMeshData",
    "probe_open3d",
]
