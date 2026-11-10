"""Dry-run contract checks for the M18 scan-station and SOP planning documents.

These are structural and consistency checks; they do not replace an independent reading.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from packlab_core.packaging_asset import _IDENTIFIER
from packlab_core.scan_station_layout import min_stand_clearance_mm, pl0397_v02_layout

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
CLAIM = re.compile(r"\b(validated|accepted|production[- ]ready|certified|guaranteed)\b", re.I)
NEGATION = re.compile(
    r"\b(not|no|never|un\w+|until|unless|before|without|only|nor|remain\w*|pending|future|"
    r"if|whether|cannot|must|may|planning|proposed|separately|independently)\b",
    re.I,
)

# PL-0402 proposed grammar, mirrored from the document's "Proposed grammar" section.
TYPES = "PKG|CMP|ASM|SKU|CAP"
CANONICAL = re.compile(rf"^({TYPES})-[0-9]{{6}}$")
SYNTHETIC = re.compile(rf"^SYNTHETIC-TEST-({TYPES})-[0-9]{{4}}$")
VIEW = re.compile(r"^VIEW-[0-9]{4}$")
EXTENSIONS = {"jpg", "png", "heic", "dng"}


def _text(task: str) -> str:
    return (DOCS / M18_DOCS[task]).read_text(encoding="utf-8")


def _is_id(value: str, kinds: tuple[str, ...]) -> bool:
    match = CANONICAL.fullmatch(value) or SYNTHETIC.fullmatch(value)
    return bool(match) and match.group(1) in kinds and bool(_IDENTIFIER.fullmatch(value))


def capture_filename_ok(name: str) -> bool:
    if len(name) > 180 or not name.isascii() or name.count(".") != 1:
        return False
    stem, ext = name.split(".")
    parts = stem.split("__")
    return (
        ext in EXTENSIONS
        and len(parts) == 4
        and _is_id(parts[0], ("PKG", "CMP", "ASM"))
        and _is_id(parts[1], ("CAP",))
        and bool(VIEW.fullmatch(parts[2]))
        and bool(re.fullmatch(r"[0-9]{4}", parts[3]))
    )


@pytest.mark.parametrize("task", sorted(M18_DOCS))
def test_doc_keeps_no_physical_or_kenya_acceptance_boundary(task: str) -> None:
    text = _text(task).lower()
    assert re.search(r"\bno\b[^.]{0,120}\b(physical|kenya|station|sample)", text), task
    assert "kenya" in text, task


@pytest.mark.parametrize("task", sorted(M18_DOCS))
def test_doc_acceptance_words_are_always_qualified(task: str) -> None:
    for sentence in re.split(r"(?<=[.!?])\s+|\n", _text(task)):
        if CLAIM.search(sentence):
            assert NEGATION.search(sentence), f"{task}: unqualified claim: {sentence.strip()[:160]}"


def test_overclaim_guard_catches_an_unqualified_sentence() -> None:
    sentence = "The station is validated and production-ready for Kenya."
    assert CLAIM.search(sentence) and not NEGATION.search(sentence)


@pytest.mark.parametrize(
    "proposed",
    [
        "PKG-000001",
        "CMP-000001",
        "ASM-000001",
        "SKU-000001",
        "CAP-000001",
        "SYNTHETIC-TEST-PKG-0001",
        "SYNTHETIC-TEST-CAP-0001",
    ],
)
def test_pl0402_documented_ids_follow_grammar_and_runtime_contract(proposed: str) -> None:
    assert proposed in _text("PL-0402")
    assert _is_id(proposed, tuple(TYPES.split("|")))
    assert len(proposed) <= 40


@pytest.mark.parametrize(
    "bad",
    [
        "pkg-000001",
        "PKG-1",
        "PKG-0000001",
        "PKG 000001",
        "PKG-000001/1",
        "../PKG-000001",
        "PKG-KENYA-1L",
        "PKG-00000A",
        "XYZ-000001",
        "SYNTHETIC-TEST-PKG-01",
        " PKG-000001",
        "PKG-000001\n",
    ],
)
def test_pl0402_rejects_malformed_or_semantic_ids(bad: str) -> None:
    assert not _is_id(bad, tuple(TYPES.split("|")))


def test_pl0402_example_filename_meets_its_own_bounds() -> None:
    example = "SYNTHETIC-TEST-PKG-0001__SYNTHETIC-TEST-CAP-0001__VIEW-0001__0001.jpg"
    assert example in _text("PL-0402")
    assert capture_filename_ok(example)


@pytest.mark.parametrize(
    "bad",
    [
        "PKG-000001__CAP-000001__VIEW-0001__0001.exe",
        "PKG-000001__CAP-000001__VIEW-0001__001.jpg",
        "CAP-000001__PKG-000001__VIEW-0001__0001.jpg",
        "SKU-000001__CAP-000001__VIEW-0001__0001.jpg",
        "PKG-000001__CAP-000001__VIEW-0001__0001.tar.jpg",
        "PKG-000001__CAP-000001__2026-11-10__0001.jpg",
        "PKG-000001__CAP-000001__VIEW-0001.jpg",
        "PKG-000001__CAP-000001__VIEW-0001__0001.jpg" + "x" * 140,
        "PKG-000001__CAP-000001__VIEW-0001__0001.jpé",
    ],
)
def test_pl0402_rejects_bad_capture_filenames(bad: str) -> None:
    assert not capture_filename_ok(bad)


def test_pl0400_checklist_covers_task_scope_in_order() -> None:
    text = _text("PL-0400")
    assert re.findall(r"^## ([A-F])\. ", text, flags=re.M) == list("ABCDEF")
    lower = text.lower()
    for topic in ("cleaning", "label", "glare", "reflection", "capture sequence", "calibration"):
        assert topic in lower, topic
    assert "STOP" in text and "do not clean" in lower


def test_pl0413_sop_stages_follow_required_lifecycle() -> None:
    headings = re.findall(r"^## (\d)\. (.+)$", _text("PL-0413"), flags=re.M)
    assert [int(n) for n, _ in headings] == list(range(1, 9))
    joined = " | ".join(title.lower() for _, title in headings)
    order = [
        "receive",
        "clean",
        "calibrat",
        "capture",
        "reconstruct",
        "fit",
        "review",
        "library",
        "backup",
    ]
    positions = [joined.index(word) for word in order]
    assert positions == sorted(positions)


def test_pl0397_and_pl0396_values_match_the_checked_layout() -> None:
    layout = pl0397_v02_layout()
    doc = _text("PL-0397")
    bom = _text("PL-0396")
    left, right = layout.lights
    assert layout.camera_distance_mm == 800.0 and "800 mm horizontal distance" in doc
    assert layout.camera_heights_mm == (120.0, 200.0, 320.0) and "120 mm, 200 mm, and 320 mm" in doc
    assert (
        layout.camera_azimuths_deg == tuple(float(a) for a in range(0, 360, 30))
        and "30° increments" in doc
    )
    for light in (left, right):
        cx, cy, cz = light.emitting_points[12]
        assert math.hypot(cx, cy) == pytest.approx(300.0) and cz == 1300.0
        assert math.hypot(*light.stand_foot_xy) == pytest.approx(1300.0)
    assert math.degrees(
        math.atan2(right.emitting_points[12][0], right.emitting_points[12][1])
    ) == pytest.approx(90.0)
    assert math.degrees(math.atan2(*right.stand_foot_xy)) == pytest.approx(105.0)
    assert "300 mm from the turntable axis at azimuth −90°/+90°" in doc
    assert "1300 mm above the tabletop" in doc and "1300 mm above the tabletop" in bom
    assert (
        "1300 mm horizontal radius, azimuth −105°/+105°" in doc
        and "1300 mm radius and ±105°" in bom
    )
    assert min_stand_clearance_mm(layout) >= 450.0 + 100.0
    assert "core/src/packlab_core/scan_station_layout.py" in doc


def test_pl0398_trial_design_is_paired_preregistered_and_unclaimed() -> None:
    text = _text("PL-0398")
    lower = text.lower()
    assert "optional, paired evaluation mode" in text
    assert "do not make it the default" in lower
    for arm in (
        "baseline matched diffuse lights without polarizers",
        "parallel/co-polarized",
        "crossed light polarizers",
    ):
        assert arm in lower, arm
    for metric in (
        "tie-point",
        "reprojection residual",
        "surface coverage",
        "dimensional error",
        "readability",
    ):
        assert metric in lower, metric
    assert "choose acceptance thresholds before collecting physical data" in lower
    assert "reduces received light" in lower and "keep it fixed" in lower
    assert "transparent" in lower and "separately reported" in lower
    assert "no performance conclusion or physical acceptance is claimed" in lower


def test_pl0399_treatment_defaults_to_none_and_every_gate_is_named() -> None:
    text = _text("PL-0399")
    assert "Default: do not apply a surface treatment" in text
    gates = re.findall(r"^\d\. \*\*([^*]+):\*\*", text, flags=re.M)
    assert [g.lower() for g in gates] == [
        "need",
        "object authority and use",
        "product evidence",
        "site safety",
        "stop, incident response and disposition plan",
        "sacrificial compatibility test",
        "measurement validity",
    ]
    assert "every gate must pass" in text.lower()
