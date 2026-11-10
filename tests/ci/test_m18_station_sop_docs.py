"""Dry-run contract checks for the M18 scan-station and SOP planning documents."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from packlab_core.packaging_asset import _IDENTIFIER

DOCS = Path(__file__).resolve().parents[2] / "docs" / "development"
M18_DOCS = {
    "PL-0396": "PL-0396_SCAN_STATION_STARTER_BOM.md",
    "PL-0397": "PL-0397_SCAN_STATION_LIGHTING_AND_CAMERA_LAYOUT.md",
    "PL-0398": "PL-0398_CROSS_POLARIZATION_EVALUATION.md",
    "PL-0399": "PL-0399_REMOVABLE_SCAN_TREATMENT_PROCEDURE.md",
    "PL-0400": "PL-0400_OPERATOR_CAPTURE_CHECKLIST.md",
    "PL-0402": "PL-0402_PACKAGING_ASSET_NAMING_AND_IDS.md",
    "PL-0413": "PL-0413_SAMPLE_TO_LIBRARY_SOP_DRAFT.md",
}


def _text(task: str) -> str:
    return (DOCS / M18_DOCS[task]).read_text(encoding="utf-8")


@pytest.mark.parametrize("task", sorted(M18_DOCS))
def test_doc_states_no_physical_or_kenya_acceptance(task: str) -> None:
    text = _text(task).lower()
    assert re.search(r"\bno\b[^.]{0,120}\b(physical|kenya|station|sample)", text), task
    assert "kenya" in text, task


@pytest.mark.parametrize(
    "proposed",
    ["PKG-000001", "CMP-000001", "ASM-000001", "SKU-000001", "CAP-000001",
     "SYNTHETIC-TEST-PKG-0001", "SYNTHETIC-TEST-CAP-0001"],
)
def test_pl0402_proposed_ids_fit_runtime_identifier_contract(proposed: str) -> None:
    assert _IDENTIFIER.fullmatch(proposed)
    assert len(proposed) <= 40
    assert proposed in _text("PL-0402")


def test_pl0402_example_filename_meets_its_own_bounds() -> None:
    text = _text("PL-0402")
    example = "SYNTHETIC-TEST-PKG-0001__SYNTHETIC-TEST-CAP-0001__VIEW-0001__0001.jpg"
    assert example in text
    asset, capture, view, tail = example.split("__")
    sequence, ext = tail.split(".")
    assert len(asset) <= 40 and len(capture) <= 40 and len(view) <= 16
    assert re.fullmatch(r"\d{4}", sequence) and ext in {"jpg", "png", "heic", "dng"}
    assert len(example) <= 180 and example.isascii()


def test_pl0400_checklist_covers_task_scope_in_order() -> None:
    text = _text("PL-0400")
    headings = re.findall(r"^## ([A-F])\. ", text, flags=re.M)
    assert headings == list("ABCDEF")
    lower = text.lower()
    for topic in ("cleaning", "label", "glare", "reflection", "capture sequence", "calibration"):
        assert topic in lower, topic


def test_pl0413_sop_stages_follow_required_lifecycle() -> None:
    headings = re.findall(r"^## (\d)\. (.+)$", _text("PL-0413"), flags=re.M)
    assert [int(n) for n, _ in headings] == list(range(1, 9))
    joined = " | ".join(title.lower() for _, title in headings)
    order = ["receive", "clean", "calibrat", "capture", "reconstruct", "fit", "review", "library", "backup"]
    positions = [joined.index(word) for word in order]
    assert positions == sorted(positions)


def test_pl0397_layout_references_executable_dry_run() -> None:
    text = _text("PL-0397")
    assert "core/src/packlab_core/scan_station_layout.py" in text
    assert "tests/core/test_scan_station_layout.py" in text
    assert "1300 mm above the tabletop" in text
    assert "1300 mm above the tabletop" in _text("PL-0396")


def test_pl0399_treatment_defaults_to_none_and_gates_every_use() -> None:
    text = _text("PL-0399")
    assert "Default: do not apply a surface treatment" in text
    assert len(re.findall(r"^\d\. \*\*", text, flags=re.M)) >= 7
