"""PL-0426 prototype: bind turntable angle events to captured photos (hardware-agnostic).

A turntable driver (none is integrated; PL-0425 is hardware-gated) reports one event per
capture: the photo sequence it triggered, the commanded angle and, when the device can
measure it, the measured angle. This module binds those events to PackScan photo records
by sequence, emits the per-photo ``capture_mode.parameters`` used by the turntable
PackScan mode (``angle_unit``/``angle_convention``/``frame_count``/``frame_index``/
``angle_deg``, schemas/packscan/manifest.schema.json), and provides the equivalent
virtual-camera transform the turntable adapter needs (OPENREALITY_INTEGRATION_ARCHITECTURE
section 10). PackScan's frozen ``clockwise_from_reference`` convention is read as: the
platter turns clockwise **as seen from above** (looking down the station +z axis).

This is a sync report; the caller writes each bound photo's parameters into that frame's
PackScan manifest (one turntable ``capture_mode`` per manifest).

It never invents an angle: a photo without exactly one matching event stays unbound.
Angles are device-reported, not observed geometry; physical calibration of the turntable
remains pending. Without a turntable the manual/guided-orbit workflow is unchanged.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

TURNTABLE_SYNC_CONTRACT: Final = "packlab.turntable-angle-sync.v1"
DEFAULT_ANGLE_TOLERANCE_DEG: Final = 0.5
_MAX_EVENTS: Final = 4096
_SOURCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")


class TurntableSyncError(ValueError):
    """Raised for malformed events or photo records."""


def _angle(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise TurntableSyncError(f"{name}_invalid")
    if not 0.0 <= float(value) < 360.0:
        raise TurntableSyncError(f"{name}_out_of_range")
    return float(value) + 0.0  # normalise -0.0


@dataclass(frozen=True, slots=True)
class TurntableAngleEvent:
    sequence: int
    commanded_angle_deg: float
    measured_angle_deg: float | None
    source_id: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence < 0
        ):
            raise TurntableSyncError("event_sequence_invalid")
        object.__setattr__(
            self, "commanded_angle_deg", _angle(self.commanded_angle_deg, "commanded_angle")
        )
        if self.measured_angle_deg is not None:
            object.__setattr__(
                self, "measured_angle_deg", _angle(self.measured_angle_deg, "measured_angle")
            )
        if not isinstance(self.source_id, str) or not _SOURCE_ID.fullmatch(self.source_id):
            raise TurntableSyncError("event_source_id_invalid")


def _angular_difference(a: float, b: float) -> float:
    delta = abs(a - b) % 360.0
    return min(delta, 360.0 - delta)


def synchronize_turntable_angles(
    photos: Sequence[tuple[str, int]],
    events: Sequence[TurntableAngleEvent],
    *,
    tolerance_deg: float = DEFAULT_ANGLE_TOLERANCE_DEG,
) -> dict[str, object]:
    """Bind events to ``(photo_id, sequence)`` records; return an auditable sync report."""
    if (
        isinstance(tolerance_deg, bool)
        or not isinstance(tolerance_deg, (int, float))
        or not math.isfinite(tolerance_deg)
        or not 0.0 < tolerance_deg <= 10.0
    ):
        raise TurntableSyncError("tolerance_invalid")
    if not isinstance(events, Sequence) or len(events) > _MAX_EVENTS:
        raise TurntableSyncError("events_invalid")
    if any(not isinstance(event, TurntableAngleEvent) for event in events):
        raise TurntableSyncError("events_invalid")
    if not isinstance(photos, Sequence) or not 1 <= len(photos) <= _MAX_EVENTS:
        raise TurntableSyncError("photos_invalid")
    sequences: dict[int, str] = {}
    photo_ids: set[str] = set()
    for record in photos:
        if (
            not isinstance(record, tuple)
            or len(record) != 2
            or not isinstance(record[0], str)
            or not record[0]
            or isinstance(record[1], bool)
            or not isinstance(record[1], int)
            or record[1] < 0
        ):
            raise TurntableSyncError("photo_record_invalid")
        if record[1] in sequences or record[0] in photo_ids:
            raise TurntableSyncError("photo_sequence_or_id_duplicate")
        sequences[record[1]] = record[0]
        photo_ids.add(record[0])

    by_sequence: dict[int, list[TurntableAngleEvent]] = {}
    for event in events:
        by_sequence.setdefault(event.sequence, []).append(event)
    ordered = sorted(sequences)
    frame_count = len(ordered)
    bound: list[dict[str, object]] = []
    unbound: list[dict[str, object]] = []
    for frame_index, sequence in enumerate(ordered):
        photo_id = sequences[sequence]
        matches = by_sequence.get(sequence, [])
        if len(matches) != 1:
            reason = "no_angle_event" if not matches else "multiple_angle_events"
            unbound.append({"photo_id": photo_id, "sequence": sequence, "reason_code": reason})
            continue
        event = matches[0]
        measured = event.measured_angle_deg
        if measured is not None and (
            _angular_difference(measured, event.commanded_angle_deg) > tolerance_deg
        ):
            unbound.append(
                {
                    "photo_id": photo_id,
                    "sequence": sequence,
                    "reason_code": "measured_angle_outside_tolerance",
                    "angular_error_deg": _angular_difference(measured, event.commanded_angle_deg),
                }
            )
            continue
        angle = measured if measured is not None else event.commanded_angle_deg
        bound.append(
            {
                "photo_id": photo_id,
                "sequence": sequence,
                "capture_mode_parameters": {
                    "angle_unit": "deg",
                    "angle_convention": "clockwise_from_reference",
                    "frame_count": frame_count,
                    "frame_index": frame_index,
                    "angle_deg": angle,
                },
                "angle_source": "DEVICE_MEASURED" if measured is not None else "DEVICE_COMMANDED",
                "source_id": event.source_id,
            }
        )
    orphan_sequences = sorted(set(by_sequence) - set(sequences))
    angles = sorted(
        {
            float(item["capture_mode_parameters"]["angle_deg"])  # type: ignore[index]
            for item in bound
        }
    )
    # Distinct angles only: a repeated angle is not a 360-degree gap (review P2-1).
    gaps = (
        [360.0]
        if len(angles) == 1
        else [(angles[(i + 1) % len(angles)] - angles[i]) % 360.0 for i in range(len(angles))]
    )
    return {
        "contract": TURNTABLE_SYNC_CONTRACT,
        "authority": "DEVICE_REPORTED_ANGLES_NOT_OBSERVED_GEOMETRY",
        "physical_calibration_status": "PENDING_TURNTABLE_CALIBRATION",
        "status": "COMPLETE" if not unbound and not orphan_sequences else "INCOMPLETE",
        "tolerance_deg": float(tolerance_deg),
        "frame_count": frame_count,
        "bound_photos": bound,
        "unbound_photos": unbound,
        "orphan_event_sequences": orphan_sequences,
        "largest_angular_gap_deg": max(gaps) if gaps else None,
    }


def virtual_camera_to_world(
    camera_to_world: Sequence[float], turntable_angle_deg: float
) -> tuple[float, ...]:
    """Equivalent pose of a fixed camera in the object's frame after a turntable rotation.

    PackScan angles are ``clockwise_from_reference`` seen from above: the object rotates by
    -angle about the station +z axis (PL-0397 frame: origin on the turntable axis, z up).
    Seen from the object, the camera moves by the inverse rotation:
    ``R_z(+angle) @ camera_to_world`` (row-major 4x4 in and out). The pose must be a rigid
    transform in the z-up station frame (ARKit y-up poses must be converted first).
    """
    angle = math.radians(_angle(turntable_angle_deg, "turntable_angle"))
    if len(camera_to_world) != 16 or any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in camera_to_world
    ):
        raise TurntableSyncError("camera_to_world_invalid")
    m0 = [float(v) for v in camera_to_world]
    rows = (m0[0:3], m0[4:7], m0[8:11])
    orthonormal = all(
        abs(sum(a * b for a, b in zip(rows[i], rows[j], strict=True)) - (1.0 if i == j else 0.0))
        < 1e-6
        for i in range(3)
        for j in range(3)
    )
    if not orthonormal or m0[12:16] != [0.0, 0.0, 0.0, 1.0]:
        raise TurntableSyncError("camera_to_world_not_rigid")
    c, s = math.cos(angle), math.sin(angle)
    rotation = (c, -s, 0.0, 0.0, s, c, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    m = [float(v) for v in camera_to_world]
    return tuple(
        sum(rotation[row * 4 + k] * m[k * 4 + col] for k in range(4))
        for row in range(4)
        for col in range(4)
    )


__all__ = [
    "DEFAULT_ANGLE_TOLERANCE_DEG",
    "TURNTABLE_SYNC_CONTRACT",
    "TurntableAngleEvent",
    "TurntableSyncError",
    "synchronize_turntable_angles",
    "virtual_camera_to_world",
]
