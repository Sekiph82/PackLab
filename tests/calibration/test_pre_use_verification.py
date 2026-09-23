"""Static checks for the physical verification boundary and blank template."""

from __future__ import annotations

import re
from pathlib import Path

Policy = dict[str, float]


def _procedure_policy(text: str) -> Policy:
    marker = re.search(r"marker side and bar readings must be within\s+`±([0-9.]+) mm`", text)
    centre = re.search(r"centre-distance reading must be\s+within `±([0-9.]+) mm`", text)
    page = re.search(
        r"page dimensions must be within `±([0-9.]+) mm` for A4 and\s+`±([0-9.]+) mm` for A3",
        text,
    )
    assert marker is not None
    assert centre is not None
    assert page is not None
    marker_tolerance = float(marker.group(1))
    centre_tolerance = float(centre.group(1))
    a4_page_tolerance = float(page.group(1))
    a3_page_tolerance = float(page.group(2))
    return {
        "page_width_a4": a4_page_tolerance,
        "page_height_a4": a4_page_tolerance,
        "page_width_a3": a3_page_tolerance,
        "page_height_a3": a3_page_tolerance,
        "marker_side": marker_tolerance,
        "reference_bar": marker_tolerance,
        "marker_centre_x": centre_tolerance,
        "marker_centre_y": centre_tolerance,
    }


def _table_rows(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("| ") or "---" in line:
            continue
        columns = [column.strip().strip("`") for column in line.strip("|").split("|")]
        if len(columns) == 6 and columns[0] != "Field":
            rows[columns[0]] = columns[4]
    return rows


def _template_policy(text: str) -> Policy:
    rows = _table_rows(text)

    def page_tolerance(field: str) -> tuple[float, float]:
        match = re.fullmatch(r"A4 ±([0-9.]+) / A3 ±([0-9.]+)", rows[field])
        assert match is not None
        return float(match.group(1)), float(match.group(2))

    def scalar(field: str) -> float:
        match = re.fullmatch(r"±([0-9.]+)", rows[field])
        assert match is not None
        return float(match.group(1))

    page_width_a4, page_width_a3 = page_tolerance("Page width")
    page_height_a4, page_height_a3 = page_tolerance("Page height")
    return {
        "page_width_a4": page_width_a4,
        "page_height_a4": page_height_a4,
        "page_width_a3": page_width_a3,
        "page_height_a3": page_height_a3,
        "marker_side": scalar("Marker side — ID 0"),
        "reference_bar": scalar("Reference bar"),
        "marker_centre_x": scalar("Marker-centre distance X"),
        "marker_centre_y": scalar("Marker-centre distance Y"),
    }


def _assert_matching_policy(procedure_text: str, template_text: str) -> None:
    assert _procedure_policy(procedure_text) == _template_policy(template_text)


def test_procedure_contains_multiple_distances_tolerances_and_reprint_gate(repo_root: Path) -> None:
    text = (repo_root / "docs/calibration/pre-use-verification.md").read_text(encoding="utf-8")
    for fragment in (
        "100 mm",
        "40 mm",
        "150 x 207 mm",
        "237 x 330 mm",
        "±0.5 mm",
        "±1.0 mm",
        "REJECTED_SCALING",
        "100% / actual size",
        "fit-to-page",
    ):
        assert fragment in text
    assert "camera accuracy" in text
    assert "nominal" in text and "owner_measured_geometry" in text


def test_procedure_and_template_tolerance_policies_match_semantically(
    repo_root: Path,
) -> None:
    procedure = (repo_root / "docs/calibration/pre-use-verification.md").read_text(encoding="utf-8")
    template = (repo_root / "docs/calibration/verification-record-template.md").read_text(
        encoding="utf-8"
    )
    _assert_matching_policy(procedure, template)


def test_tolerance_policy_drift_is_detected(repo_root: Path) -> None:
    procedure = (repo_root / "docs/calibration/pre-use-verification.md").read_text(encoding="utf-8")
    template = (repo_root / "docs/calibration/verification-record-template.md").read_text(
        encoding="utf-8"
    )
    drifted_template = template.replace(
        "| Page width | `[210 or 297]` | `UNRECORDED` | `UNRECORDED` | "
        "`A4 ±1.0 / A3 ±1.5` | `UNRECORDED` |",
        "| Page width | `[210 or 297]` | `UNRECORDED` | `UNRECORDED` | "
        "`A4 ±1.0 / A3 ±1.0` | `UNRECORDED` |",
    )
    assert drifted_template != template
    try:
        _assert_matching_policy(procedure, drifted_template)
    except AssertionError:
        pass
    else:
        raise AssertionError("procedure/template A3 width tolerance drift was not detected")


def test_template_has_blank_owner_measurements_and_no_acceptance_claim(repo_root: Path) -> None:
    text = (repo_root / "docs/calibration/verification-record-template.md").read_text(
        encoding="utf-8"
    )
    assert "record_version: `1.0.0`" in text
    assert text.count("UNRECORDED") >= 12
    assert "final_status: `UNRECORDED`" in text
    assert "ACCEPTED_FOR_CAPTURE" in text
    assert "REJECTED_SCALING" in text
    assert "2026-" not in text
    assert "Owner measured mm — reading 1" in text
