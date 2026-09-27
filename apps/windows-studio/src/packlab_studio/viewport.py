"""PackLab-owned viewport scene, camera and deterministic Qt-raster adapter."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Self

from PySide6.QtCore import QPointF, QSize
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF


class ViewportErrorCode(StrEnum):
    MISSING = "missing"
    EMPTY = "empty"
    CORRUPT = "corrupt"
    UNSUPPORTED = "unsupported"


class ViewportLoadError(ValueError):
    def __init__(self, code: ViewportErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


Point3 = tuple[float, float, float]
Triangle = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class Bounds:
    minimum: Point3
    maximum: Point3

    @property
    def center(self) -> Point3:
        return tuple((low + high) / 2 for low, high in zip(self.minimum, self.maximum))  # type: ignore[return-value]

    @property
    def extent(self) -> Point3:
        return tuple(high - low for low, high in zip(self.minimum, self.maximum))  # type: ignore[return-value]

    @property
    def radius(self) -> float:
        return max(math.sqrt(sum(value * value for value in self.extent)) / 2, 1.0)


@dataclass(frozen=True, slots=True)
class MeshGeometry:
    vertices: tuple[Point3, ...]
    triangles: tuple[Triangle, ...]
    normals: tuple[Point3, ...] = ()

    @property
    def bounds(self) -> Bounds:
        return _bounds(self.vertices)


@dataclass(frozen=True, slots=True)
class PointCloudGeometry:
    points: tuple[Point3, ...]

    @property
    def bounds(self) -> Bounds:
        return _bounds(self.points)


Geometry = MeshGeometry | PointCloudGeometry


def _bounds(points: Iterable[Point3]) -> Bounds:
    values = tuple(points)
    if not values:
        raise ViewportLoadError(ViewportErrorCode.EMPTY, "geometry has no points")
    return Bounds(
        tuple(min(point[index] for point in values) for index in range(3)),  # type: ignore[arg-type]
        tuple(max(point[index] for point in values) for index in range(3)),  # type: ignore[arg-type]
    )


def _parse_float_triplet(parts: list[str], line_number: int) -> Point3:
    try:
        if len(parts) < 3:
            raise ValueError
        return float(parts[0]), float(parts[1]), float(parts[2])
    except ValueError as error:
        raise ViewportLoadError(ViewportErrorCode.CORRUPT, f"invalid point at line {line_number}") from error


def load_geometry(path: str | Path) -> Geometry:
    """Load repository-safe text mesh/point-cloud formats without rewriting them."""

    source = Path(path)
    if not source.is_file():
        raise ViewportLoadError(ViewportErrorCode.MISSING, "geometry file is missing")
    suffix = source.suffix.lower()
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ViewportLoadError(ViewportErrorCode.CORRUPT, "geometry file cannot be read as text") from error
    if suffix == ".obj":
        return _load_obj(lines)
    if suffix == ".ply":
        return _load_ascii_ply(lines)
    if suffix in {".xyz", ".pts", ".pcd"}:
        return _load_points(lines, pcd=suffix == ".pcd")
    raise ViewportLoadError(ViewportErrorCode.UNSUPPORTED, f"unsupported geometry format: {suffix}")


def _load_obj(lines: list[str]) -> MeshGeometry:
    vertices: list[Point3] = []
    triangles: list[Triangle] = []
    for number, line in enumerate(lines, 1):
        parts = line.strip().split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] == "v":
            vertices.append(_parse_float_triplet(parts[1:], number))
        elif parts[0] == "f":
            if len(parts) < 4:
                raise ViewportLoadError(ViewportErrorCode.CORRUPT, f"invalid face at line {number}")
            indices: list[int] = []
            for token in parts[1:]:
                try:
                    index = int(token.split("/")[0])
                    indices.append(index - 1 if index > 0 else len(vertices) + index)
                except ValueError as error:
                    raise ViewportLoadError(ViewportErrorCode.CORRUPT, f"invalid face at line {number}") from error
            triangles.extend((indices[0], indices[index], indices[index + 1]) for index in range(1, len(indices) - 1))
    _validate_triangles(vertices, triangles)
    if not vertices:
        raise ViewportLoadError(ViewportErrorCode.EMPTY, "OBJ has no vertices")
    return MeshGeometry(tuple(vertices), tuple(triangles))


def _load_ascii_ply(lines: list[str]) -> MeshGeometry:
    if not lines or lines[0].strip() != "ply":
        raise ViewportLoadError(ViewportErrorCode.CORRUPT, "PLY header is missing")
    vertex_count = face_count = None
    end_header = None
    for index, line in enumerate(lines[1:], 1):
        parts = line.split()
        if parts[:2] == ["format", "ascii"]:
            continue
        if parts[:2] == ["element", "vertex"]:
            vertex_count = int(parts[2])
        elif parts[:2] == ["element", "face"]:
            face_count = int(parts[2])
        elif line.strip() == "end_header":
            end_header = index + 1
            break
    if vertex_count is None or face_count is None or end_header is None:
        raise ViewportLoadError(ViewportErrorCode.CORRUPT, "PLY ASCII header is incomplete")
    if len(lines) < end_header + vertex_count + face_count:
        raise ViewportLoadError(ViewportErrorCode.CORRUPT, "PLY payload is truncated")
    vertices = tuple(_parse_float_triplet(lines[end_header + index].split(), end_header + index + 1) for index in range(vertex_count))
    triangles: list[Triangle] = []
    for index in range(face_count):
        parts = lines[end_header + vertex_count + index].split()
        try:
            count = int(parts[0])
            values = [int(value) for value in parts[1 : count + 1]]
        except (ValueError, IndexError) as error:
            raise ViewportLoadError(ViewportErrorCode.CORRUPT, "PLY face is malformed") from error
        if len(values) < 3:
            raise ViewportLoadError(ViewportErrorCode.CORRUPT, "PLY face has fewer than three indices")
        triangles.extend((values[0], values[item], values[item + 1]) for item in range(1, len(values) - 1))
    _validate_triangles(list(vertices), triangles)
    return MeshGeometry(vertices, tuple(triangles))


def _load_points(lines: list[str], *, pcd: bool) -> PointCloudGeometry:
    points: list[Point3] = []
    data_started = not pcd
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if pcd and stripped.lower() == "data ascii":
            data_started = True
            continue
        if pcd and not data_started:
            continue
        points.append(_parse_float_triplet(stripped.split(), number))
    if not points:
        raise ViewportLoadError(ViewportErrorCode.EMPTY, "point cloud has no points")
    return PointCloudGeometry(tuple(points))


def _validate_triangles(vertices: list[Point3], triangles: list[Triangle]) -> None:
    if any(index < 0 or index >= len(vertices) for triangle in triangles for index in triangle):
        raise ViewportLoadError(ViewportErrorCode.CORRUPT, "triangle index is outside the vertex buffer")


@dataclass(frozen=True, slots=True)
class ViewportCamera:
    target: Point3 = (0.0, 0.0, 0.0)
    distance: float = 100.0
    yaw_degrees: float = 0.0
    pitch_degrees: float = 20.0
    pan_x: float = 0.0
    pan_y: float = 0.0

    def orbit(self, delta_yaw: float, delta_pitch: float) -> Self:
        return self.__class__(
            self.target,
            self.distance,
            self.yaw_degrees + delta_yaw,
            max(-89.0, min(89.0, self.pitch_degrees + delta_pitch)),
            self.pan_x,
            self.pan_y,
        )

    def pan(self, delta_x: float, delta_y: float) -> Self:
        return self.__class__(self.target, self.distance, self.yaw_degrees, self.pitch_degrees, self.pan_x + delta_x, self.pan_y + delta_y)

    def zoom(self, factor: float) -> Self:
        if factor <= 0:
            raise ValueError("zoom factor must be positive")
        return self.__class__(self.target, max(0.001, self.distance * factor), self.yaw_degrees, self.pitch_degrees, self.pan_x, self.pan_y)

    def fit(self, bounds: Bounds) -> Self:
        return self.__class__(bounds.center, max(bounds.radius * 2.4, 0.001), self.yaw_degrees, self.pitch_degrees, 0.0, 0.0)

    def reset(self) -> Self:
        return self.__class__()

    def to_dict(self) -> dict[str, object]:
        return {
            "target": list(self.target),
            "distance": self.distance,
            "yaw_degrees": self.yaw_degrees,
            "pitch_degrees": self.pitch_degrees,
            "pan_x": self.pan_x,
            "pan_y": self.pan_y,
        }

    @classmethod
    def from_dict(cls, value: object) -> Self:
        if not isinstance(value, dict):
            raise ValueError("camera state must be an object")
        target = tuple(float(item) for item in value["target"])
        if len(target) != 3:
            raise ValueError("camera target must have three coordinates")
        return cls(target, float(value["distance"]), float(value["yaw_degrees"]), float(value["pitch_degrees"]), float(value["pan_x"]), float(value["pan_y"]))


class ViewportRenderMode(StrEnum):
    SOLID = "solid"
    WIREFRAME = "wireframe"
    NORMALS = "normals"
    POINT_CLOUD = "point-cloud"


@dataclass(frozen=True, slots=True)
class GridSpec:
    spacing_mm: float
    major_every: int = 5
    unit: str = "mm"

    @property
    def label(self) -> str:
        return f"{self.spacing_mm:g} mm"


def grid_spec(camera_distance: float) -> GridSpec:
    return GridSpec(choose_grid_spacing(camera_distance))


def axis_metadata() -> tuple[dict[str, object], ...]:
    """PackLab's right-handed X-right/Y-up/Z-out-of-screen visual convention."""

    return (
        {"axis": "X", "direction": (1.0, 0.0, 0.0), "color": "#ef476f"},
        {"axis": "Y", "direction": (0.0, 1.0, 0.0), "color": "#06d6a0"},
        {"axis": "Z", "direction": (0.0, 0.0, 1.0), "color": "#118ab2"},
    )


@dataclass(frozen=True, slots=True)
class ViewportState:
    camera: ViewportCamera = field(default_factory=ViewportCamera)
    grid_visible: bool = True
    axes_visible: bool = True
    scale_cues_visible: bool = True
    render_mode: ViewportRenderMode = ViewportRenderMode.SOLID
    selected_object_id: str | None = None
    visibility: dict[str, bool] = field(default_factory=dict)
    point_size: int = 3

    def to_dict(self) -> dict[str, object]:
        return {
            "camera": self.camera.to_dict(),
            "grid_visible": self.grid_visible,
            "axes_visible": self.axes_visible,
            "scale_cues_visible": self.scale_cues_visible,
            "render_mode": self.render_mode.value,
            "selected_object_id": self.selected_object_id,
            "visibility": dict(sorted(self.visibility.items())),
            "point_size": self.point_size,
        }

    @classmethod
    def from_dict(cls, value: object) -> Self:
        if not isinstance(value, dict):
            raise ValueError("viewport state must be an object")
        visibility = value.get("visibility", {})
        if not isinstance(visibility, dict):
            raise ValueError("viewport visibility must be an object")
        return cls(
            camera=ViewportCamera.from_dict(value["camera"]),
            grid_visible=bool(value.get("grid_visible", True)),
            axes_visible=bool(value.get("axes_visible", True)),
            scale_cues_visible=bool(value.get("scale_cues_visible", True)),
            render_mode=ViewportRenderMode(value.get("render_mode", ViewportRenderMode.SOLID)),
            selected_object_id=value.get("selected_object_id"),
            visibility={str(key): bool(item) for key, item in visibility.items()},
            point_size=max(1, int(value.get("point_size", 3))),
        )


class SceneObjectKind(StrEnum):
    SCAN_MESH = "scan-mesh"
    DESIGN_MODEL = "design-model"
    CAP = "cap"
    LABEL = "label"
    REFERENCE_GEOMETRY = "reference-geometry"


@dataclass(frozen=True, slots=True)
class SceneObject:
    object_id: str
    kind: SceneObjectKind
    geometry: Geometry | None = None
    visible: bool = True
    selectable: bool = True


class SceneModel:
    def __init__(self) -> None:
        self._objects: dict[str, SceneObject] = {}
        self._selected: str | None = None

    @property
    def selected_object_id(self) -> str | None:
        return self._selected

    def objects(self) -> tuple[SceneObject, ...]:
        return tuple(self._objects[key] for key in sorted(self._objects))

    def add(self, scene_object: SceneObject) -> None:
        if scene_object.object_id in self._objects:
            raise ValueError(f"duplicate scene object ID: {scene_object.object_id}")
        self._objects[scene_object.object_id] = scene_object

    def get(self, object_id: str) -> SceneObject:
        return self._objects[object_id]

    def select(self, object_id: str | None) -> bool:
        if object_id is None:
            self._selected = None
            return True
        item = self._objects.get(object_id)
        if item is None or not item.visible or not item.selectable:
            self._selected = None
            return False
        self._selected = object_id
        return True

    def set_visible(self, object_id: str, visible: bool) -> None:
        item = self._objects[object_id]
        self._objects[object_id] = SceneObject(item.object_id, item.kind, item.geometry, visible, item.selectable)
        if not visible and self._selected == object_id:
            self._selected = None

    def visible_objects(self) -> tuple[SceneObject, ...]:
        return tuple(item for item in self.objects() if item.visible)

    def bounds(self) -> Bounds:
        points = [point for item in self.visible_objects() if item.geometry is not None for point in _geometry_points(item.geometry)]
        return _bounds(points)


def _geometry_points(geometry: Geometry) -> tuple[Point3, ...]:
    return geometry.vertices if isinstance(geometry, MeshGeometry) else geometry.points


class QtRasterViewportAdapter:
    backend_name = "qt-raster-qimage"
    backend_version = "PySide6/Qt QImage-QPainter"

    def load(self, path: str | Path) -> Geometry:
        return load_geometry(path)

    def capabilities(self) -> dict[str, object]:
        return {"headless": True, "software_rendering": True, "native_gpu": False, "backend": self.backend_name}

    def render(self, scene: SceneModel, state: ViewportState, size: QSize = QSize(960, 640)) -> QImage:
        image = QImage(size, QImage.Format.Format_ARGB32)
        image.fill(QColor("#101820"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if state.grid_visible:
            self._draw_grid(painter, state.camera, size, show_label=state.scale_cues_visible)
        if state.axes_visible:
            self._draw_axes(painter, state.camera, size)
        for item in scene.visible_objects():
            if item.geometry is not None:
                self._draw_geometry(painter, item, state, size)
        painter.end()
        return image

    def _project(self, point: Point3, camera: ViewportCamera, size: QSize) -> QPointF | None:
        x, y, z = (point[index] - camera.target[index] for index in range(3))
        yaw = math.radians(camera.yaw_degrees)
        pitch = math.radians(camera.pitch_degrees)
        x1 = math.cos(yaw) * x + math.sin(yaw) * z
        z1 = -math.sin(yaw) * x + math.cos(yaw) * z
        y1 = math.cos(pitch) * y - math.sin(pitch) * z1
        z2 = math.sin(pitch) * y + math.cos(pitch) * z1 + camera.distance
        if z2 <= 0.001:
            return None
        scale = min(size.width(), size.height()) * 0.8 / camera.distance
        return QPointF(size.width() / 2 + (x1 + camera.pan_x) * scale / z2 * camera.distance, size.height() / 2 - (y1 + camera.pan_y) * scale / z2 * camera.distance)

    def _draw_geometry(self, painter: QPainter, item: SceneObject, state: ViewportState, size: QSize) -> None:
        assert item.geometry is not None
        selected = item.object_id == state.selected_object_id
        color = QColor("#ffd166") if selected else QColor("#4cc9f0")
        if isinstance(item.geometry, PointCloudGeometry) or state.render_mode is ViewportRenderMode.POINT_CLOUD:
            painter.setPen(QPen(color, state.point_size))
            for point in _geometry_points(item.geometry):
                projected = self._project(point, state.camera, size)
                if projected is not None:
                    painter.drawPoint(projected)
            return
        painter.setPen(QPen(color, 1.5 if selected else 1.0))
        for triangle in item.geometry.triangles:
            points = [self._project(item.geometry.vertices[index], state.camera, size) for index in triangle]
            if any(point is None for point in points):
                continue
            polygon = QPolygonF([point for point in points if point is not None])
            if state.render_mode is ViewportRenderMode.WIREFRAME:
                painter.drawPolygon(polygon)
            else:
                painter.setBrush(QColor(color.red(), color.green(), color.blue(), 80))
                painter.drawPolygon(polygon)
        if state.render_mode is ViewportRenderMode.NORMALS:
            self._draw_normals(painter, item.geometry, state.camera, size, color)

    def _draw_normals(self, painter: QPainter, mesh: MeshGeometry, camera: ViewportCamera, size: QSize, color: QColor) -> None:
        painter.setPen(QPen(QColor("#f72585"), 1.0))
        for index, point in enumerate(mesh.vertices):
            normal = mesh.normals[index] if index < len(mesh.normals) else _temporary_vertex_normal(mesh, index)
            endpoint: Point3 = tuple(point[axis] + normal[axis] * max(mesh.bounds.radius * 0.08, 0.1) for axis in range(3))  # type: ignore[assignment]
            start = self._project(point, camera, size)
            end = self._project(endpoint, camera, size)
            if start is not None and end is not None:
                painter.drawLine(start, end)

    def _draw_grid(self, painter: QPainter, camera: ViewportCamera, size: QSize, *, show_label: bool) -> None:
        spec = grid_spec(camera.distance)
        spacing = spec.spacing_mm
        painter.setPen(QPen(QColor("#324b60" if show_label else "#263746"), 1.0))
        extent = spacing * 10
        for index in range(-10, 11):
            offset = index * spacing
            for start, end in [((-extent, 0.0, offset), (extent, 0.0, offset)), ((offset, 0.0, -extent), (offset, 0.0, extent))]:
                first = self._project(start, camera, size)
                second = self._project(end, camera, size)
                if first is not None and second is not None:
                    painter.drawLine(first, second)
        # The label is exposed through GridSpec/state metadata. Keeping the
        # raster path line-only makes the offscreen adapter deterministic on
        # hosts whose Qt text raster plugin is unavailable.

    def _draw_axes(self, painter: QPainter, camera: ViewportCamera, size: QSize) -> None:
        origin = self._project((0.0, 0.0, 0.0), camera, size)
        if origin is None:
            return
        for axis, endpoint in zip(axis_metadata(), ((40.0, 0.0, 0.0), (0.0, 40.0, 0.0), (0.0, 0.0, 40.0))):
            projected = self._project(endpoint, camera, size)
            if projected is not None:
                painter.setPen(QPen(QColor(str(axis["color"])), 2.0))
                painter.drawLine(origin, projected)


def _temporary_vertex_normal(mesh: MeshGeometry, vertex_index: int) -> Point3:
    normals: list[Point3] = []
    for triangle in mesh.triangles:
        if vertex_index not in triangle:
            continue
        a, b, c = (mesh.vertices[index] for index in triangle)
        ab = tuple(b[index] - a[index] for index in range(3))
        ac = tuple(c[index] - a[index] for index in range(3))
        normal = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
        normals.append(normal)
    if not normals:
        return (0.0, 1.0, 0.0)
    result = tuple(sum(normal[index] for normal in normals) for index in range(3))
    length = math.sqrt(sum(value * value for value in result)) or 1.0
    return tuple(value / length for value in result)  # type: ignore[return-value]


def choose_grid_spacing(camera_distance: float) -> float:
    """Choose a stable 1/2/5 millimetre visual cue without changing world units."""

    target = max(camera_distance / 8, 0.001)
    exponent = math.floor(math.log10(target))
    base = 10**exponent
    return min((1.0, 2.0, 5.0), key=lambda candidate: abs(candidate * base - target)) * base


class ViewportService:
    """Production-facing, backend-independent viewport service."""

    def __init__(self, adapter: QtRasterViewportAdapter | None = None) -> None:
        self.adapter = adapter or QtRasterViewportAdapter()
        self.scene = SceneModel()
        self.state = ViewportState()

    def load(self, object_id: str, kind: SceneObjectKind, path: str | Path) -> SceneObject:
        geometry = self.adapter.load(path)
        item = SceneObject(object_id, kind, geometry)
        self.scene.add(item)
        self.state = self._state(visibility={**self.state.visibility, object_id: True})
        return item

    def add_geometry(self, object_id: str, kind: SceneObjectKind, geometry: Geometry) -> SceneObject:
        item = SceneObject(object_id, kind, geometry)
        self.scene.add(item)
        self.state = self._state(visibility={**self.state.visibility, object_id: True})
        return item

    def orbit(self, delta_yaw: float, delta_pitch: float) -> None:
        self.state = self._state(camera=self.state.camera.orbit(delta_yaw, delta_pitch))

    def pan(self, delta_x: float, delta_y: float) -> None:
        self.state = self._state(camera=self.state.camera.pan(delta_x, delta_y))

    def zoom(self, factor: float) -> None:
        self.state = self._state(camera=self.state.camera.zoom(factor))

    def fit_to_view(self) -> None:
        self.state = self._state(camera=self.state.camera.fit(self.scene.bounds()))

    def reset_camera(self) -> None:
        self.state = self._state(camera=self.state.camera.reset())

    def select(self, object_id: str | None) -> bool:
        selected = self.scene.select(object_id)
        self.state = self._state(selected_object_id=self.scene.selected_object_id)
        return selected

    def set_visible(self, object_id: str, visible: bool) -> None:
        self.scene.set_visible(object_id, visible)
        self.state = self._state(visibility={**self.state.visibility, object_id: visible}, selected_object_id=self.scene.selected_object_id)

    def render(self, size: QSize = QSize(960, 640)) -> QImage:
        return self.adapter.render(self.scene, self.state, size)

    def grid_spec(self) -> GridSpec:
        return grid_spec(self.state.camera.distance)

    def axes(self) -> tuple[dict[str, object], ...]:
        return axis_metadata()

    def state_dict(self) -> dict[str, object]:
        return self.state.to_dict()

    def restore_state(self, value: object) -> None:
        restored = ViewportState.from_dict(value)
        for object_id, visible in restored.visibility.items():
            if object_id in {item.object_id for item in self.scene.objects()}:
                self.scene.set_visible(object_id, visible)
        self.scene.select(restored.selected_object_id)
        self.state = self._state(
            camera=restored.camera,
            grid_visible=restored.grid_visible,
            axes_visible=restored.axes_visible,
            scale_cues_visible=restored.scale_cues_visible,
            render_mode=restored.render_mode,
            selected_object_id=self.scene.selected_object_id,
            visibility={item.object_id: item.visible for item in self.scene.objects()},
            point_size=restored.point_size,
        )

    def _state(self, **changes: object) -> ViewportState:
        values = {
            "camera": self.state.camera,
            "grid_visible": self.state.grid_visible,
            "axes_visible": self.state.axes_visible,
            "scale_cues_visible": self.state.scale_cues_visible,
            "render_mode": self.state.render_mode,
            "selected_object_id": self.state.selected_object_id,
            "visibility": self.state.visibility,
            "point_size": self.state.point_size,
        }
        values.update(changes)
        return ViewportState(**values)  # type: ignore[arg-type]
