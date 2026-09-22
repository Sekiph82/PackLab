"""Machine-level checks for the PackScan CoreMotion clock contract."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def test_motion_schema_freezes_two_clock_mapping_and_reference_frame(repo_root: Path) -> None:
    schema = _load_json(repo_root / "schemas" / "packscan" / "motion.schema.json")
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert properties["attitude_reference_frame"] == {"const": "xArbitraryZVertical"}

    synchronization = properties["synchronization"]
    assert isinstance(synchronization, dict)
    sync_properties = synchronization["properties"]
    assert isinstance(sync_properties, dict)
    assert sync_properties["source_clock"] == {
        "const": "coremotion_monotonic_seconds_since_boot"
    }
    assert sync_properties["target_clock"] == {"const": "photo_capture_utc"}
    mapping = sync_properties["mapping"]
    assert isinstance(mapping, dict)
    mapping_properties = mapping["properties"]
    assert isinstance(mapping_properties, dict)
    assert mapping_properties["equation"] == {
        "const": "utc = anchor_utc + (native_s - anchor_native_s)"
    }
    assert {"uncertainty_ms", "resolution_ms"} <= set(mapping_properties)


def test_native_monotonic_mapping_preserves_evidence_resolution() -> None:
    anchor_native = 12345.0
    anchor_utc = datetime(2026, 9, 22, 8, 59, 59, 750000, tzinfo=UTC)
    native_sample = 12345.25
    mapped = anchor_utc + timedelta(seconds=native_sample - anchor_native)
    assert mapped.isoformat().replace("+00:00", "Z") == "2026-09-22T09:00:00Z"


@pytest.mark.parametrize(
    "fixture_name",
    ["motion-invalid-unavailable-payload.json", "motion-invalid-available-missing-payload.json"],
)
def test_negative_motion_fixtures_target_status_payload_contradictions(
    repo_root: Path, fixture_name: str
) -> None:
    fixture = _load_json(repo_root / "tests" / "fixtures" / "packscan" / fixture_name)
    samples = fixture["samples"]
    assert isinstance(samples, list) and len(samples) == 1
    sample = samples[0]
    assert isinstance(sample, dict)
    if sample["status"] == "unavailable":
        assert "attitude" in sample and "rotation_rate_rad_s" in sample
    else:
        assert sample["status"] == "available"
        assert "attitude" not in sample and "rotation_rate_rad_s" not in sample
