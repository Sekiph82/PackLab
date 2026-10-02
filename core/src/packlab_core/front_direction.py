"""Versioned, provenance-bound selection of an object's horizontal front."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Literal

FRONT_DIRECTION_VERSION = "front_direction_horizontal_v1"
FRONT_DIRECTION_CONTRACT = "packlab.front-direction.v1"
HORIZONTAL_TOLERANCE = 1e-9
Vector3 = tuple[float, float, float]
FrontDirectionSource = Literal["operator_selection", "bounded_algorithmic_candidate"]


class FrontDirectionError(ValueError):
    """Raised when front evidence is invalid, stale, or ambiguous."""


@dataclass(frozen=True, slots=True)
class FrontDirectionRecord:
    revision_id: str
    source: FrontDirectionSource
    direction: Vector3
    actor_id: str
    evidence_id: str
    base_plane_selection_id: str
    upright_alignment_id: str
    geometry_id: str
    reconstruction_revision: str
    camera_solution_revision: str
    coordinate_unit: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": FRONT_DIRECTION_CONTRACT,
            "version": FRONT_DIRECTION_VERSION,
            "revision_id": self.revision_id,
            "source": self.source,
            "direction_canonical_xyz": list(self.direction),
            "actor_id": self.actor_id,
            "evidence_id": self.evidence_id,
            "parents": {
                "base_plane_selection_id": self.base_plane_selection_id,
                "upright_alignment_id": self.upright_alignment_id,
                "geometry_id": self.geometry_id,
                "reconstruction_revision": self.reconstruction_revision,
                "camera_solution_revision": self.camera_solution_revision,
            },
            "coordinate_unit": self.coordinate_unit,
            "physical_front_verified": False,
        }


def select_front_direction(
    direction: Vector3,
    *,
    source: FrontDirectionSource,
    actor_id: str,
    evidence_id: str,
    base_plane_selection_id: str,
    upright_alignment_id: str,
    geometry_id: str,
    reconstruction_revision: str,
    camera_solution_revision: str,
    coordinate_unit: str,
) -> FrontDirectionRecord:
    """Normalize a supplied horizontal direction and bind it to its parents.

    This function never proposes a physical front. The caller must provide the
    selected direction and identify whether it came from an operator or a
    bounded candidate process.
    """

    if source not in ("operator_selection", "bounded_algorithmic_candidate"):
        raise FrontDirectionError("front_direction_source_invalid")
    for name, value in (
        ("actor_id", actor_id),
        ("evidence_id", evidence_id),
        ("base_plane_selection_id", base_plane_selection_id),
        ("upright_alignment_id", upright_alignment_id),
        ("geometry_id", geometry_id),
        ("reconstruction_revision", reconstruction_revision),
        ("camera_solution_revision", camera_solution_revision),
        ("coordinate_unit", coordinate_unit),
    ):
        if not isinstance(value, str) or not value.strip():
            raise FrontDirectionError(f"{name}_required")
    unit_direction = _normalize_horizontal(direction)
    # Normalize serialized floating point representation and remove negative zero.
    unit_direction = tuple(
        0.0 if round(value, 12) == 0 else round(value, 12) for value in unit_direction
    )  # type: ignore[assignment]
    identity: dict[str, object] = {
        "version": FRONT_DIRECTION_VERSION,
        "source": source,
        "direction": unit_direction,
        "actor_id": actor_id,
        "evidence_id": evidence_id,
        "base_plane_selection_id": base_plane_selection_id,
        "upright_alignment_id": upright_alignment_id,
        "geometry_id": geometry_id,
        "reconstruction_revision": reconstruction_revision,
        "camera_solution_revision": camera_solution_revision,
        "coordinate_unit": coordinate_unit,
    }
    revision_id = (
        "front:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    return FrontDirectionRecord(
        revision_id,
        source,
        unit_direction,
        actor_id,
        evidence_id,
        base_plane_selection_id,
        upright_alignment_id,
        geometry_id,
        reconstruction_revision,
        camera_solution_revision,
        coordinate_unit,
    )


def append_front_direction_revision(
    history: object,
    record: FrontDirectionRecord,
    *,
    current_parent_ids: dict[str, str],
) -> list[dict[str, object]]:
    """Return append-only metadata after verifying the record's current parents."""

    expected = {
        "base_plane_selection_id": record.base_plane_selection_id,
        "upright_alignment_id": record.upright_alignment_id,
        "geometry_id": record.geometry_id,
        "reconstruction_revision": record.reconstruction_revision,
        "camera_solution_revision": record.camera_solution_revision,
    }
    if current_parent_ids != expected:
        raise FrontDirectionError("front_direction_stale_parent_revision")
    if not isinstance(history, list):
        raise FrontDirectionError("front_direction_history_malformed")
    normalized_history: list[dict[str, object]] = []
    for prior in history:
        if not isinstance(prior, dict) or prior.get("contract") != FRONT_DIRECTION_CONTRACT:
            raise FrontDirectionError("front_direction_history_malformed")
        normalized_history.append(dict(prior))
    if any(prior.get("revision_id") == record.revision_id for prior in normalized_history):
        raise FrontDirectionError("front_direction_revision_already_exists")
    normalized_history.append(record.as_dict())
    return normalized_history


def serialize_front_direction(record: FrontDirectionRecord) -> bytes:
    return json.dumps(
        record.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _normalize_horizontal(direction: Vector3) -> Vector3:
    if len(direction) != 3 or any(
        not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value)
        for value in direction
    ):
        raise FrontDirectionError("front_direction_must_be_finite_3d")
    if abs(direction[2]) > HORIZONTAL_TOLERANCE:
        raise FrontDirectionError("front_direction_must_be_horizontal")
    magnitude = math.hypot(direction[0], direction[1])
    if magnitude <= 1e-12:
        raise FrontDirectionError("front_direction_degenerate")
    return (direction[0] / magnitude, direction[1] / magnitude, 0.0)
