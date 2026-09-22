"""Machine checks for the single selected OpenCV calibration dictionary."""

from __future__ import annotations

import json
from pathlib import Path


def _policy(repo_root: Path) -> dict[str, object]:
    path = repo_root / "schemas" / "packscan" / "calibration-marker-policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _reserved(policy: dict[str, object], marker_id: int) -> bool:
    active = policy["reserved_calibration_ids"]
    assert isinstance(active, dict)
    return active["first"] <= marker_id <= active["last"]


def test_policy_is_machine_testable_and_packscan_compatible(repo_root: Path) -> None:
    policy = _policy(repo_root)
    assert policy["policy_version"] == "1.0.0"
    assert policy["packscan_marker_family"] == "apriltag"
    assert policy["opencv_dictionary"] == "DICT_APRILTAG_36h11"
    assert policy["opencv_python_constant"] == "cv.aruco.DICT_APRILTAG_36h11"
    assert policy["opencv_lookup_api"] == "cv.aruco.getPredefinedDictionary"
    assert policy["dictionary_bits_per_dimension"] == 6
    assert policy["dictionary_marker_count"] == 587
    assert policy["minimum_hamming_distance"] == 11
    nominal = policy["minimum_nominal_marker_side"]
    assert isinstance(nominal, dict)
    assert nominal == {
        "value": 40,
        "unit": "mm",
        "status": "guidance_only",
        "physical_accuracy_claim": False,
    }


def test_reserved_and_boundary_ids_are_explicit(repo_root: Path) -> None:
    policy = _policy(repo_root)
    assert _reserved(policy, 0)
    assert _reserved(policy, 63)
    assert not _reserved(policy, 64)
    bounds = policy["dictionary_id_bounds"]
    assert isinstance(bounds, dict)
    assert bounds == {"first": 0, "last": 586}
    assert bounds["first"] <= 0 <= bounds["last"]
    assert bounds["first"] <= 586 <= bounds["last"]
    assert not bounds["first"] <= -1 <= bounds["last"]
    assert not bounds["first"] <= 587 <= bounds["last"]
