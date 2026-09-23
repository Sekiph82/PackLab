"""Static geometry checks for the reproducible calibration-mat SVG sources."""

from __future__ import annotations

import copy
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

SVG_NS = "{http://www.w3.org/2000/svg}"
MARKER_SIDE_MM = 40.0
REFERENCE_BAR_MM = 100.0


def _mm(value: str) -> float:
    assert value.endswith("mm")
    return float(value[:-2])


def _number(value: str) -> float:
    return float(value)


def _root_copy(path: Path) -> ET.Element:
    root = ET.parse(path).getroot()
    return copy.deepcopy(root)


def _marker_rect(marker: ET.Element) -> ET.Element:
    rect = marker.find(f"{SVG_NS}rect")
    assert rect is not None
    return rect


def _assert_reference_bar(root: ET.Element) -> None:
    reference_bar = root.find(f"{SVG_NS}g[@id='reference-bar']")
    assert reference_bar is not None
    assert reference_bar.attrib["data-length-mm"] == "100"
    rect = reference_bar.find(f"{SVG_NS}rect")
    assert rect is not None
    rect_x = _number(rect.attrib["x"])
    rect_width = _number(rect.attrib["width"])
    assert rect_width == pytest.approx(REFERENCE_BAR_MM)

    ticks = reference_bar.find(f"{SVG_NS}path")
    assert ticks is not None
    tick_x_values = [
        float(match.group(1)) for match in re.finditer(r"M([0-9.]+) ", ticks.attrib["d"])
    ]
    assert min(tick_x_values) == pytest.approx(rect_x)
    assert max(tick_x_values) == pytest.approx(rect_x + REFERENCE_BAR_MM)
    assert max(tick_x_values) - min(tick_x_values) == pytest.approx(REFERENCE_BAR_MM)


def _assert_mat_geometry(
    root: ET.Element, width_mm: float, height_mm: float, x_distance_mm: float, y_distance_mm: float
) -> None:
    assert _mm(root.attrib["width"]) == pytest.approx(width_mm)
    assert _mm(root.attrib["height"]) == pytest.approx(height_mm)
    assert [_number(part) for part in root.attrib["viewBox"].split()] == pytest.approx(
        [0.0, 0.0, width_mm, height_mm]
    )
    assert _number(root.attrib["data-page-width-mm"]) == pytest.approx(width_mm)
    assert _number(root.attrib["data-page-height-mm"]) == pytest.approx(height_mm)
    assert _number(root.attrib["data-marker-side-mm"]) == pytest.approx(MARKER_SIDE_MM)
    assert _number(root.attrib["data-reference-distance-x-mm"]) == pytest.approx(x_distance_mm)
    assert _number(root.attrib["data-reference-distance-y-mm"]) == pytest.approx(y_distance_mm)
    assert _number(root.attrib["data-reference-bar-mm"]) == pytest.approx(REFERENCE_BAR_MM)
    assert root.attrib["data-policy"] == "DICT_APRILTAG_36h11"

    page = root.find(f"{SVG_NS}rect")
    assert page is not None
    assert _number(page.attrib["width"]) == pytest.approx(width_mm)
    assert _number(page.attrib["height"]) == pytest.approx(height_mm)

    markers = root.findall(f"{SVG_NS}g[@data-marker-id]")
    assert [marker.attrib["data-marker-id"] for marker in markers] == ["0", "1", "2", "3"]
    assert all(marker.attrib["data-marker-family"] == "apriltag" for marker in markers)
    assert all(marker.attrib["data-dictionary"] == "DICT_APRILTAG_36h11" for marker in markers)
    assert all(marker.attrib["data-side-length-mm"] == "40" for marker in markers)

    centers: dict[str, tuple[float, float]] = {}
    for marker in markers:
        rect = _marker_rect(marker)
        x = _number(rect.attrib["x"])
        y = _number(rect.attrib["y"])
        width = _number(rect.attrib["width"])
        height = _number(rect.attrib["height"])
        assert width == pytest.approx(MARKER_SIDE_MM)
        assert height == pytest.approx(MARKER_SIDE_MM)
        centers[marker.attrib["data-marker-id"]] = (x + width / 2.0, y + height / 2.0)

    assert centers["1"][0] - centers["0"][0] == pytest.approx(x_distance_mm)
    assert centers["3"][0] - centers["2"][0] == pytest.approx(x_distance_mm)
    assert centers["2"][1] - centers["0"][1] == pytest.approx(y_distance_mm)
    assert centers["3"][1] - centers["1"][1] == pytest.approx(y_distance_mm)

    _assert_reference_bar(root)


def _assert_mat(path: Path, width: str, height: str, x_distance: str, y_distance: str) -> None:
    _assert_mat_geometry(
        _root_copy(path), float(width), float(height), float(x_distance), float(y_distance)
    )


def test_a4_and_a3_geometry_is_encoded_in_mm(repo_root: Path) -> None:
    _assert_mat(
        repo_root / "assets/calibration/a4-packlab-calibration-mat.svg", "210", "297", "150", "207"
    )
    _assert_mat(
        repo_root / "assets/calibration/a3-packlab-calibration-mat.svg", "297", "420", "237", "330"
    )


def test_geometry_boundary_detects_page_scaling(repo_root: Path) -> None:
    root = _root_copy(repo_root / "assets/calibration/a4-packlab-calibration-mat.svg")
    root.attrib["viewBox"] = "0 0 211 297"
    with pytest.raises(AssertionError):
        _assert_mat_geometry(root, 210.0, 297.0, 150.0, 207.0)


def test_geometry_boundary_detects_marker_drift_with_unchanged_metadata(
    repo_root: Path,
) -> None:
    root = _root_copy(repo_root / "assets/calibration/a4-packlab-calibration-mat.svg")
    marker_0 = root.find(f"{SVG_NS}g[@id='marker-0']")
    assert marker_0 is not None
    _marker_rect(marker_0).attrib["width"] = "41"
    with pytest.raises(AssertionError):
        _assert_mat_geometry(root, 210.0, 297.0, 150.0, 207.0)


def test_geometry_boundary_detects_reference_bar_drift_with_unchanged_metadata(
    repo_root: Path,
) -> None:
    root = _root_copy(repo_root / "assets/calibration/a4-packlab-calibration-mat.svg")
    reference_bar = root.find(f"{SVG_NS}g[@id='reference-bar']")
    assert reference_bar is not None
    rect = reference_bar.find(f"{SVG_NS}rect")
    assert rect is not None
    rect.attrib["width"] = "101"
    with pytest.raises(AssertionError):
        _assert_mat_geometry(root, 210.0, 297.0, 150.0, 207.0)
