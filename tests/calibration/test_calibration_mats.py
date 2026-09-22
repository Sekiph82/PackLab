"""Static geometry checks for the reproducible calibration-mat SVG sources."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


def _assert_mat(path: Path, width: str, height: str, x_distance: str, y_distance: str) -> None:
    root = ET.parse(path).getroot()
    assert root.attrib["data-page-width-mm"] == width
    assert root.attrib["data-page-height-mm"] == height
    assert root.attrib["data-marker-side-mm"] == "40"
    assert root.attrib["data-reference-distance-x-mm"] == x_distance
    assert root.attrib["data-reference-distance-y-mm"] == y_distance
    assert root.attrib["data-reference-bar-mm"] == "100"
    assert root.attrib["data-policy"] == "DICT_APRILTAG_36h11"
    markers = root.findall("{http://www.w3.org/2000/svg}g[@data-marker-id]")
    assert [marker.attrib["data-marker-id"] for marker in markers] == ["0", "1", "2", "3"]
    assert all(marker.attrib["data-marker-family"] == "apriltag" for marker in markers)
    assert all(marker.attrib["data-dictionary"] == "DICT_APRILTAG_36h11" for marker in markers)
    assert all(marker.attrib["data-side-length-mm"] == "40" for marker in markers)
    reference_bar = root.find("{http://www.w3.org/2000/svg}g[@id='reference-bar']")
    assert reference_bar is not None
    assert reference_bar.attrib["data-length-mm"] == "100"


def test_a4_and_a3_geometry_is_encoded_in_mm(repo_root: Path) -> None:
    _assert_mat(
        repo_root / "assets/calibration/a4-packlab-calibration-mat.svg", "210", "297", "150", "207"
    )
    _assert_mat(
        repo_root / "assets/calibration/a3-packlab-calibration-mat.svg", "297", "420", "237", "330"
    )


def test_geometry_boundary_detects_page_scaling(repo_root: Path) -> None:
    with pytest.raises(AssertionError):
        _assert_mat(
            repo_root / "assets/calibration/a4-packlab-calibration-mat.svg",
            "211",
            "297",
            "150",
            "207",
        )
