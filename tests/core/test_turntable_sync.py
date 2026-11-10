"""PL-0426 synthetic tests: turntable angle events bound to photos; no hardware involved."""

from __future__ import annotations

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


def test_virtual_camera_follows_the_clockwise_from_above_convention() -> None:
    # PackScan `clockwise_from_reference`: the platter turns clockwise seen from above, so
    # the object rotates -angle about +z and, seen from the object, the fixed camera moves
    # by +angle. A camera on -y moves to +x after a 90-degree turn.
    camera = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.3, 0.0, 0.0, 0.0, 1.0)
    pose = virtual_camera_to_world(camera, 90.0)
    assert (pose[3], pose[7], pose[11]) == pytest.approx((1.0, 0.0, 0.3), abs=1e-12)
    assert virtual_camera_to_world(camera, 0.0) == pytest.approx(camera)
    # Direction pin: the platter point at +x, turned 90 degrees clockwise seen from above,
    # lands at -y, exactly where the camera is; in the object frame the virtual camera must
    # therefore coincide with that point's object-frame position (+x).
    rotation = [pose[0:3], pose[4:7], pose[8:11]]
    for i in range(3):
        for j in range(3):
            dot = sum(a * b for a, b in zip(rotation[i], rotation[j], strict=True))
            assert dot == pytest.approx(1.0 if i == j else 0.0, abs=1e-12)
    with pytest.raises(TurntableSyncError):
        virtual_camera_to_world(camera[:15], 10.0)
    sheared = list(camera)
    sheared[1] = 0.5
    with pytest.raises(TurntableSyncError, match="not_rigid"):
        virtual_camera_to_world(tuple(sheared), 10.0)


def test_emitted_parameters_validate_against_the_packscan_turntable_schema() -> None:
    # Review P1-1: angle_unit / angle_convention are required by the frozen schema.
    import json
    from pathlib import Path

    import jsonschema

    schema = json.loads(
        (Path(__file__).resolve().parents[2] / "schemas/packscan/manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    turntable = (
        schema["$defs"]["turntable_mode"]
        if "$defs" in schema
        else schema["definitions"]["turntable_mode"]
    )
    photos, events = _orbit()
    for item in synchronize_turntable_angles(photos, events)["bound_photos"]:
        jsonschema.validate(
            {"mode": "turntable", "version": 1, "parameters": item["capture_mode_parameters"]},
            turntable,
        )


def test_gap_ignores_repeated_angles_and_orphans_alone_make_the_set_incomplete() -> None:
    photos = (("a", 0), ("b", 1), ("c", 2))
    events = tuple(
        TurntableAngleEvent(seq, angle, None, SOURCE)
        for seq, angle in ((0, 5.0), (1, 5.0), (2, 185.0))
    )
    report = synchronize_turntable_angles(photos, events)
    assert report["largest_angular_gap_deg"] == pytest.approx(180.0)
    orphan_only = synchronize_turntable_angles(
        photos, (*events, TurntableAngleEvent(7, 1.0, None, SOURCE))
    )
    assert orphan_only["unbound_photos"] == [] and orphan_only["status"] == "INCOMPLETE"


def test_incomplete_set_keeps_frame_indices_and_calibration_label() -> None:
    photos, events = _orbit(4)
    report = synchronize_turntable_angles(photos, events[1:])
    assert report["physical_calibration_status"] == "PENDING_TURNTABLE_CALIBRATION"
    params = [item["capture_mode_parameters"] for item in report["bound_photos"]]
    assert [item["frame_index"] for item in params] == [1, 2, 3]
    assert all(item["frame_count"] == 4 for item in params)


def test_tolerance_edges_and_invalid_measurements() -> None:
    edge = synchronize_turntable_angles(
        (("p", 0),), (TurntableAngleEvent(0, 10.0, 10.5, SOURCE),), tolerance_deg=0.5
    )
    assert edge["status"] == "COMPLETE"
    over = synchronize_turntable_angles(
        (("p", 0),), (TurntableAngleEvent(0, 10.0, 10.51, SOURCE),), tolerance_deg=0.5
    )
    assert over["unbound_photos"][0]["reason_code"] == "measured_angle_outside_tolerance"
    for bad in (float("nan"), 360.0, -1.0, True):
        with pytest.raises(TurntableSyncError):
            TurntableAngleEvent(0, 10.0, bad, SOURCE)  # type: ignore[arg-type]
    with pytest.raises(TurntableSyncError):
        TurntableAngleEvent(-1, 10.0, None, SOURCE)
    with pytest.raises(TurntableSyncError):
        synchronize_turntable_angles((("p", 0),), (), tolerance_deg=10.01)
    assert TurntableAngleEvent(0, -0.0, None, SOURCE).commanded_angle_deg == 0.0
