"""PL-0414 synthetic dry-run of the rescan/recapture decision tree on real QA producers."""

from __future__ import annotations

import pytest
from test_object_surface_texture_qa import _qa, _render
from test_pre_reconstruction_qa import _report, _sharp_samples
from test_recapture_sector_suggestions import _inputs, _known_gap_report

from packlab_core.object_geometry_coverage import (
    ObjectGeometryCoveragePolicy,
    build_object_geometry_coverage_report,
)
from packlab_core.pre_reconstruction_qa import GrayImageSamples, build_pre_reconstruction_qa
from packlab_core.recapture_sector_suggestions import (
    RecaptureSectorPolicy,
    suggest_recapture_sectors,
)
from packlab_core.rescan_decision import ACTIONS, RescanDecisionError, decide_rescan

PATH = "images/000.jpg"


def _clean_qa() -> dict:
    return build_pre_reconstruction_qa(
        _report(width=8, height=8), {PATH: _sharp_samples()}
    ).as_dict()


def _no_recapture() -> dict:
    geometry, registration, _coverage, _source = _inputs(registered=10)
    coverage = build_object_geometry_coverage_report(
        geometry,
        policy=ObjectGeometryCoveragePolicy(
            grid_resolution=2,
            minimum_selected_point_ratio=0.2,
            minimum_mean_support_ratio=0.7,
            minimum_projected_coverage_ratio=0.25,
        ),
    )
    policy = RecaptureSectorPolicy(minimum_projected_occupancy_ratio=0.25)
    report = suggest_recapture_sectors(geometry, registration, coverage, policy=policy).as_dict()
    assert report["decision"] == "no_recapture_indicated"
    return report


def test_clean_evidence_proceeds_only_to_review_and_is_deterministic() -> None:
    qa, recapture = _clean_qa(), _no_recapture()
    first = decide_rescan(qa, recapture)
    assert first == decide_rescan(qa, recapture)
    assert first["primary_action"] == "proceed_to_reconstruction_review"
    assert first["authority"] == "advisory_only_operator_confirms_every_action"
    assert len(first["source_evidence"]["qa_report_sha256"]) == 64


def test_known_missing_sector_routes_to_targeted_recapture_of_that_sector() -> None:
    decision = decide_rescan(_clean_qa(), _known_gap_report((0, 1, 2, 3, 4, 6, 7)))
    assert decision["primary_action"] == "targeted_recapture"
    assert decision["actions"][0]["sector_ids"] == ["az05-el00"]


def test_full_orbit_with_remaining_gap_requires_full_rescan() -> None:
    decision = decide_rescan(_clean_qa(), _known_gap_report(tuple(range(8))))
    assert decision["primary_action"] == "full_rescan"
    assert decision["actions"][0]["reason_codes"] == ["recapture_report_requires_full_rescan"]


def test_low_texture_hdpe_render_routes_to_surface_treatment_review() -> None:
    png, samples, mask = _render("syn_jerrycan_hdpe_matte_v01")
    decision = decide_rescan(_qa(png, samples, mask), _no_recapture())
    assert decision["primary_action"] == "surface_treatment_review"
    assert decision["actions"][0]["low_texture_view_fraction"] == 1.0


def test_dark_photo_is_retaken_by_photo_id() -> None:
    dark = GrayImageSamples(8, 8, bytes(64), "test-decoder", "1", 8, 8)
    qa = build_pre_reconstruction_qa(_report(width=8, height=8), {PATH: dark}).as_dict()
    decision = decide_rescan(qa, _no_recapture())
    assert decision["primary_action"] == "retake_flagged_photos"
    assert decision["actions"][0]["image_paths"] == [PATH]


def test_metadata_inconsistency_stops_before_any_capture_action() -> None:
    qa = build_pre_reconstruction_qa(
        _report(width=8, height=8), {PATH: GrayImageSamples(8, 8, bytes(64), "d", "1", 9, 9)}
    ).as_dict()
    assert qa["components"]["metadata_consistency"]["status"] == "failed"
    decision = decide_rescan(qa, _known_gap_report((0, 1, 2, 3, 4, 6, 7)))
    assert decision["primary_action"] == "stop_reimport_source"
    assert [item["action"] for item in decision["actions"]] == [
        action for action in ACTIONS if action in {item["action"] for item in decision["actions"]}
    ]
    assert "targeted_recapture" in {item["action"] for item in decision["actions"]}


def test_missing_recapture_or_decoder_evidence_never_proceeds() -> None:
    assert decide_rescan(_clean_qa())["primary_action"] == "manual_review_insufficient_evidence"
    undecoded = build_pre_reconstruction_qa(_report(width=8, height=8), {}).as_dict()
    decision = decide_rescan(undecoded, _no_recapture())
    assert decision["primary_action"] == "manual_review_insufficient_evidence"
    assert "sharpness" in decision["actions"][0]["unavailable_components"]


def test_wrong_contracts_are_rejected() -> None:
    with pytest.raises(RescanDecisionError):
        decide_rescan({"schema": "other"})
    with pytest.raises(RescanDecisionError):
        decide_rescan(_clean_qa(), {"contract": "other"})
