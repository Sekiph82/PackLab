"""Static checks for the physical verification boundary and blank template."""

from __future__ import annotations

from pathlib import Path


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
