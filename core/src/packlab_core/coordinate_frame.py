"""Versioned PackLab normalized-frame transform contract."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass

from .reconstruction import ScaleState

PACKLAB_NORMALIZED_FRAME = "packlab_right_handed_x_right_y_front_z_up_v1"
TRANSFORM_CONVENTION = "row_major_4x4_column_vectors_v1"
FRONT_AXIS = "+Y"
UP_AXIS = "+Z"
RIGHT_AXIS = "+X"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
Matrix4 = tuple[float, ...]
Point3 = tuple[float, float, float]


class CoordinateFrameError(ValueError):
    """Raised when a frame transform is malformed or unit semantics conflict."""


@dataclass(frozen=True, slots=True)
class NormalizedFrameTransform:
    """Non-destructive mapping between explicitly named reconstruction frames.

    Matrices are row-major homogeneous transforms and multiply column vectors:
    ``p_target = M * p_source``. The 3x3 linear block may contain a proper
    rotation and one uniform positive scale, but no shear or reflection.
    """

    transform_id: str
    source_frame: str
    target_frame: str
    reconstruction_revision: str
    scale_state: ScaleState
    input_unit: str
    coordinate_unit: str
    matrix: Matrix4
    method: str
    scale_provenance_id: str
    parent_transform_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in (
            "transform_id",
            "source_frame",
            "target_frame",
            "reconstruction_revision",
            "scale_provenance_id",
        ):
            value = getattr(self, field)
            if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
                raise CoordinateFrameError(f"{field}_must_be_explicit_safe_identifier")
        if not isinstance(self.method, str) or not self.method.strip() or len(self.method) > 256:
            raise CoordinateFrameError("method_must_be_nonempty_text_under_256_characters")
        if not isinstance(self.scale_state, ScaleState):
            raise CoordinateFrameError("scale_state_invalid")
        if self.scale_state is ScaleState.RELATIVE:
            valid_units = {"reconstruction_units"}
        elif self.scale_state is ScaleState.METRIC_UNVERIFIED:
            valid_units = {"reconstruction_units", "mm_unverified"}
        elif self.scale_state is ScaleState.METRIC_VERIFIED:
            valid_units = {"reconstruction_units", "mm"}
        else:
            raise CoordinateFrameError("scale_state_invalid")
        if self.input_unit not in valid_units or self.coordinate_unit not in valid_units:
            raise CoordinateFrameError("coordinate_unit_conflicts_with_scale_state")
        if len(self.matrix) != 16 or not all(_finite(value) for value in self.matrix):
            raise CoordinateFrameError("transform_matrix_must_contain_16_finite_values")
        if any(
            abs(value - expected) > 1e-10
            for value, expected in zip(self.matrix[12:16], (0.0, 0.0, 0.0, 1.0), strict=True)
        ):
            raise CoordinateFrameError("transform_matrix_must_be_affine")
        _validate_similarity(self.matrix)
        if len(set(self.parent_transform_ids)) != len(self.parent_transform_ids):
            raise CoordinateFrameError("parent_transform_ids_must_be_unique")

    def apply_point(self, point: Point3) -> Point3:
        if len(point) != 3 or not all(_finite(value) for value in point):
            raise CoordinateFrameError("point_must_be_finite_3d")
        return tuple(
            sum(self.matrix[row * 4 + column] * point[column] for column in range(3))
            + self.matrix[row * 4 + 3]
            for row in range(3)
        )  # type: ignore[return-value]

    def inverse(self) -> NormalizedFrameTransform:
        matrix = _inverse_similarity(self.matrix)
        transform_id = _derived_id("inverse", (self.transform_id,), matrix)
        return NormalizedFrameTransform(
            transform_id=transform_id,
            source_frame=self.target_frame,
            target_frame=self.source_frame,
            reconstruction_revision=self.reconstruction_revision,
            scale_state=self.scale_state,
            input_unit=self.coordinate_unit,
            coordinate_unit=self.input_unit,
            matrix=matrix,
            method="inverse",
            scale_provenance_id=self.scale_provenance_id,
            parent_transform_ids=(self.transform_id,),
        )

    def then(self, following: NormalizedFrameTransform) -> NormalizedFrameTransform:
        """Compose ``following`` after this transform (M = M_following * M_self)."""

        if self.target_frame != following.source_frame:
            raise CoordinateFrameError("transform_frame_chain_mismatch")
        if self.reconstruction_revision != following.reconstruction_revision:
            raise CoordinateFrameError("transform_reconstruction_revision_mismatch")
        if self.scale_state is not following.scale_state:
            raise CoordinateFrameError("transform_scale_state_mismatch")
        if self.scale_provenance_id != following.scale_provenance_id:
            raise CoordinateFrameError("transform_scale_provenance_mismatch")
        if self.coordinate_unit != following.input_unit:
            raise CoordinateFrameError("transform_unit_chain_mismatch")
        matrix = _multiply(following.matrix, self.matrix)
        parents = (self.transform_id, following.transform_id)
        return NormalizedFrameTransform(
            transform_id=_derived_id("compose", parents, matrix),
            source_frame=self.source_frame,
            target_frame=following.target_frame,
            reconstruction_revision=self.reconstruction_revision,
            scale_state=self.scale_state,
            input_unit=self.input_unit,
            coordinate_unit=following.coordinate_unit,
            matrix=matrix,
            method="compose",
            scale_provenance_id=self.scale_provenance_id,
            parent_transform_ids=parents,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.normalized-frame-transform.v1",
            "transform_id": self.transform_id,
            "source_frame": self.source_frame,
            "target_frame": self.target_frame,
            "reconstruction_revision": self.reconstruction_revision,
            "scale_state": self.scale_state.value,
            "input_unit": self.input_unit,
            "coordinate_unit": self.coordinate_unit,
            "matrix_convention": TRANSFORM_CONVENTION,
            "matrix": list(self.matrix),
            "axes": {
                "right": RIGHT_AXIS,
                "front": FRONT_AXIS,
                "up": UP_AXIS,
                "handedness": "right",
            },
            "method": self.method,
            "scale_provenance_id": self.scale_provenance_id,
            "parent_transform_ids": list(self.parent_transform_ids),
            "mutates_source_geometry": False,
        }


def coordinate_unit_for_scale_state(scale_state: ScaleState) -> str:
    if scale_state is ScaleState.RELATIVE:
        return "reconstruction_units"
    if scale_state is ScaleState.METRIC_UNVERIFIED:
        return "mm_unverified"
    if scale_state is ScaleState.METRIC_VERIFIED:
        return "mm"
    raise CoordinateFrameError("scale_state_invalid")


def serialize_frame_transform(transform: NormalizedFrameTransform) -> bytes:
    return json.dumps(
        transform.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _validate_similarity(matrix: Matrix4) -> None:
    columns = tuple(tuple(matrix[row * 4 + column] for row in range(3)) for column in range(3))
    lengths = tuple(math.sqrt(sum(value * value for value in column)) for column in columns)
    if any(length <= 1e-12 for length in lengths):
        raise CoordinateFrameError("transform_linear_block_singular")
    if max(lengths) - min(lengths) > max(lengths) * 1e-8:
        raise CoordinateFrameError("transform_must_use_uniform_scale")
    for first in range(3):
        for second in range(first + 1, 3):
            dot = sum(columns[first][axis] * columns[second][axis] for axis in range(3))
            if abs(dot) > lengths[first] * lengths[second] * 1e-8:
                raise CoordinateFrameError("transform_must_not_contain_shear")
    a, b, c = columns
    determinant = (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - b[0] * (a[1] * c[2] - a[2] * c[1])
        + c[0] * (a[1] * b[2] - a[2] * b[1])
    )
    if determinant <= 0.0:
        raise CoordinateFrameError("transform_must_be_right_handed")


def _inverse_similarity(matrix: Matrix4) -> Matrix4:
    scale_squared = sum(matrix[index] ** 2 for index in (0, 4, 8))
    inverse = [0.0] * 16
    for row in range(3):
        for column in range(3):
            inverse[row * 4 + column] = matrix[column * 4 + row] / scale_squared
    for row in range(3):
        inverse[row * 4 + 3] = -sum(
            inverse[row * 4 + column] * matrix[column * 4 + 3] for column in range(3)
        )
    inverse[15] = 1.0
    return tuple(inverse)


def _multiply(first: Matrix4, second: Matrix4) -> Matrix4:
    return tuple(
        sum(first[row * 4 + index] * second[index * 4 + column] for index in range(4))
        for row in range(4)
        for column in range(4)
    )


def _derived_id(operation: str, parents: tuple[str, ...], matrix: Matrix4) -> str:
    payload = {
        "operation": operation,
        "parents": list(parents),
        "matrix": list(matrix),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return f"frame-transform:{digest}"


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
