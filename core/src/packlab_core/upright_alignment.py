"""Non-destructive, evidence-bound object-up alignment rotation."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass

from .base_plane import BasePlaneSelection

UPRIGHT_ALIGNMENT_VERSION = "shortest_arc_object_up_to_packlab_z_v1"
MANUAL_UPRIGHT_CORRECTION_VERSION = "manual_object_up_direction_override_v1"
MATRIX_CONVENTION = "row_major_4x4_column_vectors_v1"
QUATERNION_CONVENTION = "xyzw_unit_quaternion_v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]
Matrix4 = tuple[float, ...]


class UprightAlignmentError(ValueError):
    """Raised for stale, degenerate, or ambiguous upright evidence."""


@dataclass(frozen=True, slots=True)
class ManualUprightCorrection:
    correction_id: str
    actor_id: str
    evidence_id: str
    evidence_digest: str
    reason: str
    base_plane_selection_id: str
    geometry_id: str
    reconstruction_revision: str
    camera_solution_revision: str
    corrected_up_direction: Vector3

    def __post_init__(self) -> None:
        for field in (
            "correction_id",
            "actor_id",
            "evidence_id",
            "reason",
            "base_plane_selection_id",
            "geometry_id",
            "reconstruction_revision",
            "camera_solution_revision",
        ):
            if not isinstance(getattr(self, field), str) or not getattr(self, field).strip():
                raise UprightAlignmentError(f"manual_correction_{field}_required")
        if not isinstance(self.evidence_digest, str) or not _SHA256.fullmatch(self.evidence_digest):
            raise UprightAlignmentError("manual_correction_evidence_digest_invalid")
        _normalize_vector(self.corrected_up_direction)


@dataclass(frozen=True, slots=True)
class UprightAlignmentResult:
    alignment_id: str
    method_version: str
    selection_id: str
    geometry_id: str
    reconstruction_revision: str
    camera_solution_revision: str
    coordinate_unit: str
    base_plane_up_direction: Vector3
    source_up_direction: Vector3
    aligned_up_direction: Vector3
    quaternion_xyzw: Quaternion
    rotation_matrix: Matrix4
    correction_id: str | None
    correction_actor_id: str | None
    correction_evidence_id: str | None
    correction_evidence_digest: str | None

    def require_current_selection(self, selection: BasePlaneSelection) -> None:
        if (
            selection.selection_id != self.selection_id
            or selection.geometry_id != self.geometry_id
            or selection.reconstruction_revision != self.reconstruction_revision
            or selection.camera_solution_revision != self.camera_solution_revision
            or selection.coordinate_unit != self.coordinate_unit
        ):
            raise UprightAlignmentError("upright_alignment_stale_base_plane_selection")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.upright-alignment.v1",
            "alignment_id": self.alignment_id,
            "method_version": self.method_version,
            "base_plane_selection_id": self.selection_id,
            "parents": {
                "geometry_id": self.geometry_id,
                "reconstruction_revision": self.reconstruction_revision,
                "camera_solution_revision": self.camera_solution_revision,
            },
            "coordinate_unit": self.coordinate_unit,
            "base_plane_up_direction": list(self.base_plane_up_direction),
            "source_up_direction": list(self.source_up_direction),
            "aligned_up_direction": list(self.aligned_up_direction),
            "quaternion_convention": QUATERNION_CONVENTION,
            "quaternion_xyzw": list(self.quaternion_xyzw),
            "matrix_convention": MATRIX_CONVENTION,
            "rotation_matrix": list(self.rotation_matrix),
            "manual_correction": {
                "correction_id": self.correction_id,
                "actor_id": self.correction_actor_id,
                "evidence_id": self.correction_evidence_id,
                "evidence_digest": self.correction_evidence_digest,
                "version": (
                    MANUAL_UPRIGHT_CORRECTION_VERSION if self.correction_id is not None else None
                ),
            },
            "mutates_source_geometry": False,
            "baked_geometry_created": False,
            "front_direction_selected": False,
        }


def compute_upright_alignment(
    selection: BasePlaneSelection,
    correction: ManualUprightCorrection | None = None,
) -> UprightAlignmentResult:
    """Rotate the selected object-up direction to canonical +Z.

    The rotation is evidence only: it does not modify captured points, bake a
    normalized geometry asset, or select an object's front direction.
    """

    if correction is None:
        source = selection.candidate.normal
    else:
        if (
            correction.base_plane_selection_id != selection.selection_id
            or correction.geometry_id != selection.geometry_id
            or correction.reconstruction_revision != selection.reconstruction_revision
            or correction.camera_solution_revision != selection.camera_solution_revision
        ):
            raise UprightAlignmentError("manual_correction_parent_revision_mismatch")
        source = correction.corrected_up_direction
    base_plane_up = _normalize_vector(selection.candidate.normal)
    unit = _normalize_vector(source)
    dot = max(-1.0, min(1.0, unit[2]))
    if dot <= -1.0 + 1e-10:
        raise UprightAlignmentError(
            "antiparallel_up_direction_requires_explicit_nonambiguous_correction"
        )
    quaternion = _shortest_arc_to_positive_z(unit, dot)
    matrix = _quaternion_matrix(quaternion)
    aligned = _rotate(matrix, unit)
    if not all(math.isfinite(value) for value in (*quaternion, *matrix, *aligned)):
        raise UprightAlignmentError("upright_alignment_result_non_finite")
    identity = {
        "method_version": UPRIGHT_ALIGNMENT_VERSION,
        "selection_id": selection.selection_id,
        "geometry_id": selection.geometry_id,
        "reconstruction_revision": selection.reconstruction_revision,
        "camera_solution_revision": selection.camera_solution_revision,
        "base_plane_up": list(base_plane_up),
        "source_up": list(unit),
        "quaternion_xyzw": list(quaternion),
        "correction_id": None if correction is None else correction.correction_id,
        "correction_evidence_digest": None if correction is None else correction.evidence_digest,
    }
    alignment_id = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return UprightAlignmentResult(
        alignment_id,
        UPRIGHT_ALIGNMENT_VERSION,
        selection.selection_id,
        selection.geometry_id,
        selection.reconstruction_revision,
        selection.camera_solution_revision,
        selection.coordinate_unit,
        base_plane_up,
        unit,
        aligned,
        quaternion,
        matrix,
        None if correction is None else correction.correction_id,
        None if correction is None else correction.actor_id,
        None if correction is None else correction.evidence_id,
        None if correction is None else correction.evidence_digest,
    )


def serialize_upright_alignment(result: UprightAlignmentResult) -> bytes:
    return json.dumps(
        result.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _shortest_arc_to_positive_z(source: Vector3, dot: float) -> Quaternion:
    if dot >= 1.0 - 1e-12:
        return (0.0, 0.0, 0.0, 1.0)
    # source cross target(+Z); positive scalar part chooses the deterministic
    # shortest arc for all non-antiparallel inputs.
    cross = (source[1], -source[0], 0.0)
    scalar = 1.0 + dot
    magnitude = math.sqrt(sum(value * value for value in (*cross, scalar)))
    if magnitude <= 1e-12:
        raise UprightAlignmentError("up_direction_rotation_is_degenerate")
    return tuple(value / magnitude for value in (*cross, scalar))  # type: ignore[return-value]


def _quaternion_matrix(quaternion: Quaternion) -> Matrix4:
    x, y, z, w = quaternion
    return (
        1 - 2 * (y * y + z * z),
        2 * (x * y - z * w),
        2 * (x * z + y * w),
        0.0,
        2 * (x * y + z * w),
        1 - 2 * (x * x + z * z),
        2 * (y * z - x * w),
        0.0,
        2 * (x * z - y * w),
        2 * (y * z + x * w),
        1 - 2 * (x * x + y * y),
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )


def _rotate(matrix: Matrix4, vector: Vector3) -> Vector3:
    return (
        matrix[0] * vector[0] + matrix[1] * vector[1] + matrix[2] * vector[2],
        matrix[4] * vector[0] + matrix[5] * vector[1] + matrix[6] * vector[2],
        matrix[8] * vector[0] + matrix[9] * vector[1] + matrix[10] * vector[2],
    )


def _normalize_vector(vector: Vector3) -> Vector3:
    if len(vector) != 3 or any(
        not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value)
        for value in vector
    ):
        raise UprightAlignmentError("up_direction_must_be_finite_3d")
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude <= 1e-12:
        raise UprightAlignmentError("up_direction_degenerate")
    return (vector[0] / magnitude, vector[1] / magnitude, vector[2] / magnitude)
