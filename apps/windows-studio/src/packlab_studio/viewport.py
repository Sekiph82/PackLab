"""PackLab-owned viewport scene, camera and deterministic Qt-raster adapter."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Self

import numpy as np
from PySide6.QtCore import QPointF, QSize
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF

from packlab_core.visual_reference import VisualReferenceRecord


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
Color = tuple[int, int, int]


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
    colors: tuple[Color, ...] = ()  # optional per-point sRGB, same length as points

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
        raise ViewportLoadError(
            ViewportErrorCode.CORRUPT, f"invalid point at line {line_number}"
        ) from error


def load_geometry(path: str | Path) -> Geometry:
    """Load repository-safe text mesh/point-cloud formats without rewriting them."""

    source = Path(path)
    if not source.is_file():
        raise ViewportLoadError(ViewportErrorCode.MISSING, "geometry file is missing")
    suffix = source.suffix.lower()
    if suffix == ".ply":
        try:
            return _load_ply(source.read_bytes())
        except OSError as error:
            raise ViewportLoadError(ViewportErrorCode.CORRUPT, "PLY cannot be read") from error
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ViewportLoadError(
            ViewportErrorCode.CORRUPT, "geometry file cannot be read as text"
        ) from error
    if suffix == ".obj":
        return _load_obj(lines)
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
                    raise ViewportLoadError(
                        ViewportErrorCode.CORRUPT, f"invalid face at line {number}"
                    ) from error
            triangles.extend(
                (indices[0], indices[index], indices[index + 1])
                for index in range(1, len(indices) - 1)
            )
    _validate_triangles(vertices, triangles)
    if not vertices:
        raise ViewportLoadError(ViewportErrorCode.EMPTY, "OBJ has no vertices")
    return MeshGeometry(tuple(vertices), tuple(triangles))


_PLY_TYPES = {
    "char": "i1", "int8": "i1", "uchar": "u1", "uint8": "u1",
    "short": "i2", "int16": "i2", "ushort": "u2", "uint16": "u2",
    "int": "i4", "int32": "i4", "uint": "u4", "uint32": "u4",
    "float": "f4", "float32": "f4", "double": "f8", "float64": "f8",
}  # fmt: skip

# (element name, count, [(property name, scalar dtype or (list count dtype, item dtype))])
PlyProperty = tuple[str, str | tuple[str, str]]
PlyElement = tuple[str, int, list[PlyProperty]]


def _ply_corrupt(message: str) -> ViewportLoadError:
    return ViewportLoadError(ViewportErrorCode.CORRUPT, message)


def _load_ply(data: bytes) -> Geometry:
    """Load ASCII or binary little-endian PLY meshes and (colored) point clouds."""

    marker = data.find(b"end_header")
    if not data.startswith(b"ply") or marker < 0:
        raise _ply_corrupt("PLY header is missing")
    newline = data.find(b"\n", marker)
    body_start = newline + 1 if newline >= 0 else len(data)
    fmt = ""
    elements: list[PlyElement] = []
    for raw in data[:marker].decode("ascii", "replace").splitlines()[1:]:
        parts = raw.split()
        try:
            if parts[:1] == ["format"]:
                fmt = parts[1]
            elif parts[:1] == ["element"]:
                elements.append((parts[1], int(parts[2]), []))
            elif parts[:2] == ["property", "list"]:
                elements[-1][2].append((parts[4], (_PLY_TYPES[parts[2]], _PLY_TYPES[parts[3]])))
            elif parts[:1] == ["property"]:
                elements[-1][2].append((parts[2], _PLY_TYPES[parts[1]]))
        except (IndexError, KeyError, ValueError) as error:
            raise _ply_corrupt("PLY header is malformed") from error
    if fmt not in {"ascii", "binary_little_endian"}:
        raise ViewportLoadError(ViewportErrorCode.UNSUPPORTED, f"PLY format {fmt!r} is unsupported")
    columns: dict[str, np.ndarray] = {}
    faces: list[list[int]] | np.ndarray
    if fmt == "ascii":
        faces = _read_ascii_ply(data[body_start:], elements, columns)
    else:
        faces = _read_binary_ply(data, body_start, elements, columns)
    if not all(axis in columns for axis in "xyz"):
        raise _ply_corrupt("PLY vertex positions are missing")
    xyz = np.stack([columns[axis] for axis in "xyz"], axis=1).astype(np.float64)
    if not len(xyz):
        raise ViewportLoadError(ViewportErrorCode.EMPTY, "PLY has no vertices")
    if not np.isfinite(xyz).all():
        raise _ply_corrupt("PLY vertex positions are not finite")
    vertices: tuple[Point3, ...] = tuple(map(tuple, xyz.tolist()))
    if len(faces):
        triangles: list[Triangle] = []
        for face in faces:
            indices = [int(value) for value in face]
            if len(indices) < 3:
                raise _ply_corrupt("PLY face has fewer than three indices")
            triangles.extend(
                (indices[0], indices[item], indices[item + 1])
                for item in range(1, len(indices) - 1)
            )
        _validate_triangles(list(vertices), triangles)
        return MeshGeometry(vertices, tuple(triangles))
    colors: tuple[Color, ...] = ()
    for names in (("red", "green", "blue"), ("r", "g", "b")):
        if all(name in columns for name in names):
            rgb = np.stack([columns[name] for name in names], axis=1).astype(np.float64)
            if columns[names[0]].dtype.kind == "f" and rgb.max(initial=0.0) <= 1.0:
                rgb = rgb * 255.0  # some writers store 0..1 floats
            clipped = np.clip(rgb, 0, 255).astype(np.uint8)
            colors = tuple(map(tuple, clipped.tolist()))
            break
    return PointCloudGeometry(vertices, colors)


def _read_ascii_ply(
    body: bytes, elements: list[PlyElement], columns: dict[str, np.ndarray]
) -> list[list[int]]:
    tokens = body.split()
    position = 0
    faces: list[list[int]] = []
    for name, count, properties in elements:
        if not any(isinstance(kind, tuple) for _, kind in properties):
            width = len(properties)
            chunk = tokens[position : position + count * width]
            if len(chunk) < count * width:
                raise _ply_corrupt("PLY payload is truncated")
            try:
                table = np.array(chunk, dtype=np.float64).reshape(count, width)
            except ValueError as error:
                raise _ply_corrupt("PLY value is malformed") from error
            position += count * width
            if name == "vertex":
                for column, (prop, _kind) in enumerate(properties):
                    columns[prop] = table[:, column]
            continue
        if name == "vertex":
            raise ViewportLoadError(
                ViewportErrorCode.UNSUPPORTED, "ASCII PLY vertex list properties are unsupported"
            )
        for _ in range(count):
            for prop, kind in properties:
                try:
                    if isinstance(kind, tuple):
                        length = int(tokens[position])
                        chunk = tokens[position + 1 : position + 1 + length]
                        if len(chunk) != length:
                            raise IndexError
                        position += 1 + length
                        if name == "face" and prop in {"vertex_indices", "vertex_index"}:
                            faces.append([int(item) for item in chunk])
                    else:
                        float(tokens[position])
                        position += 1
                except (IndexError, ValueError) as error:
                    raise _ply_corrupt("PLY payload is truncated or malformed") from error
    return faces


def _read_binary_ply(
    data: bytes, offset: int, elements: list[PlyElement], columns: dict[str, np.ndarray]
) -> list[list[int]] | np.ndarray:
    raw = np.frombuffer(data, dtype=np.uint8)
    faces: list[list[int]] | np.ndarray = []
    for name, count, properties in elements:
        # Fixed-layout scalar prefix up to the first list property.
        prefix: list[tuple[str, str]] = []
        for prop, kind in properties:
            if isinstance(kind, tuple):
                break
            prefix.append((prop, "<" + kind))
        lists: list[tuple[str, tuple[str, str]]] = []
        for prop, kind in properties[len(prefix) :]:
            if not isinstance(kind, tuple):
                raise ViewportLoadError(
                    ViewportErrorCode.UNSUPPORTED,
                    "PLY scalars after list properties are unsupported",
                )
            lists.append((prop, kind))
        prefix_dtype = np.dtype(prefix) if prefix else None
        prefix_size = prefix_dtype.itemsize if prefix_dtype is not None else 0
        if not lists:
            size = prefix_size * count
            if offset + size > len(data):
                raise _ply_corrupt("PLY payload is truncated")
            if name == "vertex" and prefix_dtype is not None:
                table = np.frombuffer(data, dtype=prefix_dtype, count=count, offset=offset)
                for prop, _ in prefix:
                    columns[prop] = table[prop]
            offset += size
            continue
        if name == "face" and not prefix and len(lists) == 1 and count:
            count_type, item_type = lists[0][1]
            fixed = np.dtype([("n", "<" + count_type), ("v", "<" + item_type, (3,))])
            if offset + fixed.itemsize * count <= len(data):
                table = np.frombuffer(data, dtype=fixed, count=count, offset=offset)
                if (table["n"] == 3).all():
                    faces = table["v"].astype(np.int64)
                    offset += fixed.itemsize * count
                    continue
        # ponytail: Python walk over variable-length lists (OpenMVS view_indices),
        # about 1 s per 200k records; vectorize if larger dense clouds become common.
        starts = np.empty(count, dtype=np.int64)
        face_rows: list[list[int]] = []
        for record in range(count):
            starts[record] = offset
            offset += prefix_size
            for prop, (count_type, item_type) in lists:
                count_size = np.dtype(count_type).itemsize
                if offset + count_size > len(data):
                    raise _ply_corrupt("PLY payload is truncated")
                length = int(np.frombuffer(data, "<" + count_type, 1, offset)[0])
                offset += count_size
                item_size = np.dtype(item_type).itemsize * length
                if offset + item_size > len(data):
                    raise _ply_corrupt("PLY payload is truncated")
                if name == "face" and prop in {"vertex_indices", "vertex_index"}:
                    face_rows.append(np.frombuffer(data, "<" + item_type, length, offset).tolist())
                offset += item_size
        if name == "face":
            faces = face_rows
        if name == "vertex" and prefix_dtype is not None:
            gathered = raw[starts[:, None] + np.arange(prefix_size)]
            table = np.ascontiguousarray(gathered).view(prefix_dtype).reshape(count)
            for prop, _ in prefix:
                columns[prop] = table[prop]
    return faces


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
        raise ViewportLoadError(
            ViewportErrorCode.CORRUPT, "triangle index is outside the vertex buffer"
        )


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
        return self.__class__(
            self.target,
            self.distance,
            self.yaw_degrees,
            self.pitch_degrees,
            self.pan_x + delta_x,
            self.pan_y + delta_y,
        )

    def zoom(self, factor: float) -> Self:
        if factor <= 0:
            raise ValueError("zoom factor must be positive")
        return self.__class__(
            self.target,
            max(0.001, self.distance * factor),
            self.yaw_degrees,
            self.pitch_degrees,
            self.pan_x,
            self.pan_y,
        )

    def fit(self, bounds: Bounds) -> Self:
        return self.__class__(
            bounds.center,
            max(bounds.radius * 2.4, 0.001),
            self.yaw_degrees,
            self.pitch_degrees,
            0.0,
            0.0,
        )

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
        return cls(
            target,
            float(value["distance"]),
            float(value["yaw_degrees"]),
            float(value["pitch_degrees"]),
            float(value["pan_x"]),
            float(value["pan_y"]),
        )


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
    AI_VISUAL_REFERENCE = "ai-visual-reference"
    CAP = "cap"
    LABEL = "label"
    REFERENCE_GEOMETRY = "reference-geometry"


class SceneObjectId(StrEnum):
    SCAN_MESH = "scan-mesh"
    DESIGN_MODEL = "design-model"
    AI_VISUAL_REFERENCE = "ai-visual-reference"
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
    visual_reference: VisualReferenceRecord | None = None

    def __post_init__(self) -> None:
        is_ai_reference = self.kind is SceneObjectKind.AI_VISUAL_REFERENCE
        if is_ai_reference != (self.visual_reference is not None):
            raise ValueError("AI visual reference scene objects require their generated record")

    def to_dict(self) -> dict[str, object]:
        value: dict[str, object] = {
            "object_id": self.object_id,
            "kind": self.kind.value,
            "visible": self.visible,
            "selectable": self.selectable,
            "has_geometry": self.geometry is not None,
        }
        if self.kind is SceneObjectKind.AI_VISUAL_REFERENCE:
            assert self.visual_reference is not None
            value.update(
                authority_class="AI_VISUAL_REFERENCE",
                generated=True,
                caveat="Unseen geometry may be invented by the generator.",
                visual_reference=self.visual_reference.as_dict(),
            )
        return value


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

    def remove(self, object_id: str) -> SceneObject:
        item = self._objects.pop(object_id)
        if self._selected == object_id:
            self._selected = None
        return item

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

    def clear_selection(self) -> None:
        self._selected = None

    def set_visible(self, object_id: str, visible: bool) -> None:
        item = self._objects[object_id]
        self._objects[object_id] = SceneObject(
            item.object_id,
            item.kind,
            item.geometry,
            visible,
            item.selectable,
            item.visual_reference,
        )
        if not visible and self._selected == object_id:
            self._selected = None

    def visible_objects(self) -> tuple[SceneObject, ...]:
        return tuple(item for item in self.objects() if item.visible)

    def snapshot(self) -> dict[str, object]:
        return {
            "objects": [item.to_dict() for item in self.objects()],
            "selected_object_id": self._selected,
        }

    def bounds(self) -> Bounds:
        points = [
            point
            for item in self.visible_objects()
            if item.geometry is not None
            for point in _geometry_points(item.geometry)
        ]
        return _bounds(points)


def _geometry_points(geometry: Geometry) -> tuple[Point3, ...]:
    return geometry.vertices if isinstance(geometry, MeshGeometry) else geometry.points


_SPLAT_THRESHOLD = 20_000  # uncolored clouds above this use the vectorized splat path


class QtRasterViewportAdapter:
    backend_name = "qt-raster-qimage"
    backend_version = "PySide6/Qt QImage-QPainter"

    def __init__(self) -> None:
        # Last splatted cloud's numpy arrays (cloud kept alive so id() stays valid).
        self._arrays: dict[int, tuple[PointCloudGeometry, np.ndarray, np.ndarray]] = {}

    def load(self, path: str | Path) -> Geometry:
        return load_geometry(path)

    def capabilities(self) -> dict[str, object]:
        return {
            "headless": True,
            "software_rendering": True,
            "native_gpu": False,
            "backend": self.backend_name,
        }

    def render(
        self, scene: SceneModel, state: ViewportState, size: QSize = QSize(960, 640)
    ) -> QImage:
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
        has_visible_ai_reference = any(
            item.kind is SceneObjectKind.AI_VISUAL_REFERENCE for item in scene.visible_objects()
        )
        if has_visible_ai_reference:
            painter.setPen(QPen(QColor("#101820"), 1.0))
            painter.setBrush(QColor("#ffd166"))
            painter.drawRoundedRect(8, 8, min(size.width() - 16, 360), 48, 5, 5)
            painter.setPen(QPen(QColor("#101820"), 1.0))
            painter.drawText(16, 26, "AI Visual Reference · GENERATED")
            painter.drawText(16, 44, "Unseen geometry may be invented.")
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
        return QPointF(
            size.width() / 2 + (x1 + camera.pan_x) * scale / z2 * camera.distance,
            size.height() / 2 - (y1 + camera.pan_y) * scale / z2 * camera.distance,
        )

    def _draw_geometry(
        self, painter: QPainter, item: SceneObject, state: ViewportState, size: QSize
    ) -> None:
        assert item.geometry is not None
        selected = item.object_id == state.selected_object_id
        color = QColor("#ffd166") if selected else QColor("#4cc9f0")
        if isinstance(item.geometry, PointCloudGeometry) and (
            item.geometry.colors or len(item.geometry.points) > _SPLAT_THRESHOLD
        ):
            self._splat_points(painter, item.geometry, state, size, color)
            return
        if (
            isinstance(item.geometry, PointCloudGeometry)
            or state.render_mode is ViewportRenderMode.POINT_CLOUD
        ):
            painter.setPen(QPen(color, state.point_size))
            for point in _geometry_points(item.geometry):
                projected = self._project(point, state.camera, size)
                if projected is not None:
                    painter.drawPoint(projected)
            return
        painter.setPen(QPen(color, 1.5 if selected else 1.0))
        for triangle in item.geometry.triangles:
            points = [
                self._project(item.geometry.vertices[index], state.camera, size)
                for index in triangle
            ]
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

    def _splat_points(
        self,
        painter: QPainter,
        cloud: PointCloudGeometry,
        state: ViewportState,
        size: QSize,
        color: QColor,
    ) -> None:
        """Vectorized far-to-near square splats; same projection as ``_project``."""

        cached = self._arrays.get(id(cloud))
        if cached is None or cached[0] is not cloud:
            points = np.asarray(cloud.points, dtype=np.float64).reshape(-1, 3)
            if cloud.colors and len(cloud.colors) == len(cloud.points):
                rgb = np.asarray(cloud.colors, dtype=np.uint32).reshape(-1, 3)
                packed = 0xFF000000 | (rgb[:, 0] << 16) | (rgb[:, 1] << 8) | rgb[:, 2]
            else:
                packed = np.full(len(points), color.rgba(), dtype=np.uint32)
            self._arrays = {id(cloud): (cloud, points, packed.astype(np.uint32))}
            cached = self._arrays[id(cloud)]
        _, points, packed = cached
        camera = state.camera
        width, height = size.width(), size.height()
        x, y, z = (points - np.asarray(camera.target)).T
        yaw = math.radians(camera.yaw_degrees)
        pitch = math.radians(camera.pitch_degrees)
        x1 = math.cos(yaw) * x + math.sin(yaw) * z
        z1 = -math.sin(yaw) * x + math.cos(yaw) * z
        y1 = math.cos(pitch) * y - math.sin(pitch) * z1
        z2 = math.sin(pitch) * y + math.cos(pitch) * z1 + camera.distance
        visible = z2 > 0.001
        scale = min(width, height) * 0.8
        with np.errstate(divide="ignore", invalid="ignore"):
            sx = width / 2 + (x1 + camera.pan_x) * scale / z2
            sy = height / 2 - (y1 + camera.pan_y) * scale / z2
        visible &= np.isfinite(sx) & np.isfinite(sy)
        visible &= (sx > -2) & (sx < width + 2) & (sy > -2) & (sy < height + 2)
        order = np.nonzero(visible)[0]
        order = order[np.argsort(-z2[order], kind="stable")]  # far first, near wins
        px = np.round(sx[order]).astype(np.int64)
        py = np.round(sy[order]).astype(np.int64)
        values = packed[order]
        buffer = np.zeros((height, width), dtype=np.uint32)
        half = max(1, state.point_size) // 2
        for dy in range(-half, max(1, state.point_size) - half):
            for dx in range(-half, max(1, state.point_size) - half):
                cx, cy = px + dx, py + dy
                inside = (cx >= 0) & (cx < width) & (cy >= 0) & (cy < height)
                buffer[cy[inside], cx[inside]] = values[inside]
        image = QImage(buffer.data, width, height, width * 4, QImage.Format.Format_ARGB32)
        painter.drawImage(0, 0, image)

    def _draw_normals(
        self,
        painter: QPainter,
        mesh: MeshGeometry,
        camera: ViewportCamera,
        size: QSize,
        color: QColor,
    ) -> None:
        painter.setPen(QPen(QColor("#f72585"), 1.0))
        for index, point in enumerate(mesh.vertices):
            normal = (
                mesh.normals[index]
                if index < len(mesh.normals)
                else _temporary_vertex_normal(mesh, index)
            )
            endpoint: Point3 = tuple(
                point[axis] + normal[axis] * max(mesh.bounds.radius * 0.08, 0.1)
                for axis in range(3)
            )  # type: ignore[assignment]
            start = self._project(point, camera, size)
            end = self._project(endpoint, camera, size)
            if start is not None and end is not None:
                painter.drawLine(start, end)

    def _draw_grid(
        self, painter: QPainter, camera: ViewportCamera, size: QSize, *, show_label: bool
    ) -> None:
        spec = grid_spec(camera.distance)
        spacing = spec.spacing_mm
        painter.setPen(QPen(QColor("#324b60" if show_label else "#263746"), 1.0))
        extent = spacing * 10
        for index in range(-10, 11):
            offset = index * spacing
            for start, end in [
                ((-extent, 0.0, offset), (extent, 0.0, offset)),
                ((offset, 0.0, -extent), (offset, 0.0, extent)),
            ]:
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
        for axis, endpoint in zip(
            axis_metadata(), ((40.0, 0.0, 0.0), (0.0, 40.0, 0.0), (0.0, 0.0, 40.0))
        ):
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
        normal = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
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

    def add_geometry(
        self, object_id: str, kind: SceneObjectKind, geometry: Geometry
    ) -> SceneObject:
        item = SceneObject(object_id, kind, geometry)
        self.scene.add(item)
        self.state = self._state(visibility={**self.state.visibility, object_id: True})
        return item

    def add_visual_reference(
        self,
        record: VisualReferenceRecord,
        geometry: Geometry,
    ) -> SceneObject:
        """Add generated display geometry with its non-authoritative provenance."""

        if not isinstance(record, VisualReferenceRecord):
            raise ValueError("visual_reference_record_required")
        item = SceneObject(
            record.reference_id,
            SceneObjectKind.AI_VISUAL_REFERENCE,
            geometry,
            visual_reference=record,
        )
        self.scene.add(item)
        self.state = self._state(visibility={**self.state.visibility, item.object_id: True})
        return item

    def remove_visual_reference(self, reference_id: str) -> None:
        """Remove only the selected visual-reference layer."""

        item = self.scene.get(reference_id)
        if item.kind is not SceneObjectKind.AI_VISUAL_REFERENCE:
            raise ValueError("removal_requires_ai_visual_reference")
        self.scene.remove(reference_id)
        visibility = dict(self.state.visibility)
        visibility.pop(reference_id, None)
        self.state = self._state(
            visibility=visibility,
            selected_object_id=self.scene.selected_object_id,
        )

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

    def clear_selection(self) -> None:
        self.scene.clear_selection()
        self.state = self._state(selected_object_id=None)

    def set_visible(self, object_id: str, visible: bool) -> None:
        self.scene.set_visible(object_id, visible)
        self.state = self._state(
            visibility={**self.state.visibility, object_id: visible},
            selected_object_id=self.scene.selected_object_id,
        )

    def set_render_mode(self, mode: ViewportRenderMode) -> None:
        self.state = self._state(render_mode=ViewportRenderMode(mode))

    def normals_status(self, object_id: str) -> str:
        item = self.scene.get(object_id)
        if not isinstance(item.geometry, MeshGeometry):
            return "unavailable"
        if item.geometry.normals:
            return "source-provided"
        if item.geometry.triangles:
            return "temporary-derived"
        return "unavailable"

    def lod_plan(self, object_id: str, policy=None):
        from .viewport_lod import LODPolicy, geometry_count

        selected_policy = policy or LODPolicy()
        return selected_policy.plan(geometry_count(self.scene.get(object_id).geometry))  # type: ignore[arg-type]

    def display_geometry(self, object_id: str, policy=None):
        from .viewport_lod import LODPolicy, display_geometry

        selected_policy = policy or LODPolicy()
        item = self.scene.get(object_id)
        if item.geometry is None:
            raise ValueError("scene object has no geometry")
        return display_geometry(item.geometry, selected_policy)

    def scene_snapshot(self) -> dict[str, object]:
        """Stable object-tree/inspector seam; widgets do not own scene truth."""

        return self.scene.snapshot()

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
