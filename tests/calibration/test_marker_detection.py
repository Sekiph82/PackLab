"""Synthetic and boundary tests for the scale-free marker detector."""

from __future__ import annotations

import pytest

from packlab_core.calibration import DICTIONARY_NAME, detect_markers
from packlab_core.calibration.marker_detection import (
    MarkerPolicyError,
    _duplicate_marker_result,
    load_marker_policy,
    resolve_policy_dictionary,
)


class _FakeAruco:
    DICT_APRILTAG_36h11 = 3611
    DICT_4X4_50 = 450

    def __init__(self) -> None:
        self.requested: list[int] = []

    def getPredefinedDictionary(self, dictionary_id: int) -> tuple[str, int]:
        self.requested.append(dictionary_id)
        return ("dictionary", dictionary_id)


class _FakeCV2:
    def __init__(self) -> None:
        self.aruco = _FakeAruco()


def test_detector_dictionary_name_is_loaded_from_policy(repo_root) -> None:
    policy = load_marker_policy(
        repo_root / "schemas" / "packscan" / "calibration-marker-policy.json"
    )
    assert DICTIONARY_NAME == policy["opencv_dictionary"] == "DICT_APRILTAG_36h11"


def test_policy_dictionary_resolution_follows_policy_data() -> None:
    policy = load_marker_policy()
    fake_cv2 = _FakeCV2()

    dictionary = resolve_policy_dictionary(fake_cv2, policy)

    assert dictionary == ("dictionary", _FakeAruco.DICT_APRILTAG_36h11)
    assert fake_cv2.aruco.requested == [_FakeAruco.DICT_APRILTAG_36h11]

    substituted_policy = dict(policy)
    substituted_policy["opencv_dictionary"] = "DICT_4X4_50"
    substituted = resolve_policy_dictionary(fake_cv2, substituted_policy)

    assert substituted == ("dictionary", _FakeAruco.DICT_4X4_50)
    assert fake_cv2.aruco.requested[-1] == _FakeAruco.DICT_4X4_50


def test_unsupported_policy_dictionary_fails_clearly() -> None:
    policy = dict(load_marker_policy())
    policy["opencv_dictionary"] = "DICT_DOES_NOT_EXIST"

    with pytest.raises(MarkerPolicyError, match="unsupported_marker_dictionary"):
        resolve_policy_dictionary(_FakeCV2(), policy)


def test_unsupported_image_shapes_are_non_fatal() -> None:
    class FakeImage:
        shape = (100, 100, 4)
        dtype = "uint8"

    result = detect_markers(FakeImage())
    assert result.status == "invalid_input"
    assert result.errors == ("unsupported_image_shape_or_dtype",)


def test_synthetic_marker_has_ordered_pixel_corners_and_no_scale_fields() -> None:
    cv2 = pytest.importorskip("cv2")
    import numpy as np

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    marker = cv2.aruco.generateImageMarker(dictionary, 0, 160, borderBits=1)
    image = np.full((240, 240), 255, dtype=np.uint8)
    image[40:200, 40:200] = marker
    result = detect_markers(image)
    assert result.status == "detected"
    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.marker_id == 0
    assert len(observation.corners_px) == 4
    assert observation.provenance["dictionary"] == DICTIONARY_NAME
    assert observation.provenance["coordinate_unit"] == "image_pixels"
    assert "scale_mm" not in observation.quality


def test_duplicate_ids_are_flagged_without_crash() -> None:
    duplicate = _duplicate_marker_result([[7], [7]])
    assert duplicate is not None
    assert duplicate.status == "invalid"
    assert duplicate.errors == ("duplicate_marker_id",)


def test_synthetic_duplicate_scene_remains_bounded_if_detected() -> None:
    cv2 = pytest.importorskip("cv2")
    import numpy as np

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    marker = cv2.aruco.generateImageMarker(dictionary, 0, 100, borderBits=1)
    image = np.full((130, 230), 255, dtype=np.uint8)
    image[15:115, 15:115] = marker
    image[15:115, 115:215] = marker
    result = detect_markers(image)
    assert result.status in {"invalid", "detected", "no_markers"}
    if result.status == "invalid":
        assert "duplicate_marker_id" in result.errors
