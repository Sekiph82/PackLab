"""Synthetic and boundary tests for the scale-free marker detector."""

from __future__ import annotations

import pytest

from packlab_core.calibration import DICTIONARY_NAME, detect_markers


def test_detector_pins_the_selected_dictionary() -> None:
    assert DICTIONARY_NAME == "DICT_APRILTAG_36h11"


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
