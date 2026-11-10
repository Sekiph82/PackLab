"""PL-0426 synthetic tests: turntable angle events bound to photos; no hardware involved."""

from __future__ import annotations

import math

import pytest

from packlab_core.turntable_sync import (
    TurntableAngleEvent,
    TurntableSyncError,
    synchronize_turntable_angles,
    virtual_camera_to_world,
)

SOURCE = "SYNTHETIC-turntable-sim"


def _orbit(count: int = 8, measured_error: float = 0.1):
    photos = tuple((f"photo-{index}", 10 + index) for index in range(count))
    events = tuple(
        TurntableAngleEvent(
            10 + index,
            360.0 * index / count,
            (360.0 * index / count + measured_error) % 360.0,
            SOURCE,
        )
        for index in range(count)
    )
    return photos, events


def test_complete_orbit_binds_every_photo_with_packscan_turntable_parameters() -> None:
    photos, events = _orbit()
    report = synchronize_turntable_angles(photos, events)
    assert report == synchronize_turntable_angles(photos, events)
    assert report["status"] == "COMPLETE"
    assert report["authority"] == "DEVICE_REPORTED_ANGLES_NOT_OBSERVED_GEOMETRY"
    bound = report["bound_photos"]
    assert [item["capture_mode_parameters"]["frame_index"] for item in bound] == list(range(8))
    assert all(item["capture_mode_parameters"]["frame_count"] == 8 for item in bound)
    assert bound[3]["capture_mode_parameters"]["angle_deg"] == pytest.approx(135.1)
    assert all(item["angle_source"] == "DEVICE_MEASURED" for item in bound)
    assert report["largest_angular_gap_deg"] == pytest.approx(45.0)


def test_missing_duplicate_orphan_and_out_of_tolerance_events_never_invent_angles() -> None:
    photos, events = _orbit()
    events = (
        *events[:2],  # photo-2 has no event
        events[3],
        events[3],  # photo-3 has two
        TurntableAngleEvent(14, 180.0, 183.0, SOURCE),  # photo-4 off by 3 degrees
        *events[5:],
        TurntableAngleEvent(99, 10.0, None, SOURCE),  # orphan
    )
    report = synchronize_turntable_angles(photos, events)
    assert report["status"] == "INCOMPLETE"
    reasons = {item["photo_id"]: item["reason_code"] for item in report["unbound_photos"]}
    assert reasons == {
        "photo-2": "no_angle_event",
        "photo-3": "multiple_angle_events",
        "photo-4": "measured_angle_outside_tolerance",
    }
    assert report["orphan_event_sequences"] == [99]
    assert {item["photo_id"] for item in report["bound_photos"]}.isdisjoint(reasons)


def test_commanded_angle_is_used_and_labelled_when_no_measurement_exists() -> None:
    report = synchronize_turntable_angles(
        (("photo-0", 0),), (TurntableAngleEvent(0, 359.9, None, SOURCE),)
    )
    item = report["bound_photos"][0]
    assert item["angle_source"] == "DEVICE_COMMANDED"
    assert item["capture_mode_parameters"]["angle_deg"] == pytest.approx(359.9)


def test_wraparound_error_is_measured_across_zero_degrees() -> None:
    report = synchronize_turntable_angles(
        (("photo-0", 0),), (TurntableAngleEvent(0, 359.9, 0.2, SOURCE),)
    )
    assert report["status"] == "COMPLETE"  # 0.3 degrees apart across the wrap


@pytest.mark.parametrize(
    "build",
    [
        lambda: TurntableAngleEvent(0, 360.0, None, SOURCE),
        lambda: TurntableAngleEvent(0, float("nan"), None, SOURCE),
        lambda: TurntableAngleEvent(True, 10.0, None, SOURCE),  # type: ignore[arg-type]
        lambda: TurntableAngleEvent(0, 10.0, None, "C:/devices/com3"),
        lambda: synchronize_turntable_angles((("a", 0), ("a", 1)), ()),
        lambda: synchronize_turntable_angles((("a", 0),), (), tolerance_deg=0.0),
    ],
)
def test_malformed_inputs_are_rejected(build) -> None:
    with pytest.raises(TurntableSyncError):
        build()


def test_virtual_camera_rotates_inversely_about_the_station_axis() -> None:
    # Camera 1 m along -y looking at the axis; after the object turns +90 degrees the
    # camera, seen from the object, is rotated by -90 degrees about z (now along -x).
    camera = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.3, 0.0, 0.0, 0.0, 1.0)
    pose = virtual_camera_to_world(camera, 90.0)
    assert (pose[3], pose[7], pose[11]) == pytest.approx((-1.0, 0.0, 0.3), abs=1e-12)
    assert virtual_camera_to_world(camera, 0.0) == pytest.approx(camera)
    # Rotation part stays orthonormal.
    rows = [pose[0:3], pose[4:7], pose[8:11]]
    for i in range(3):
        assert math.isclose(sum(v * v for v in rows[i]), 1.0)
    with pytest.raises(TurntableSyncError):
        virtual_camera_to_world(camera[:15], 10.0)
