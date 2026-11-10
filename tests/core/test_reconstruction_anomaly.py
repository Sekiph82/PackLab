from __future__ import annotations

import pytest
from test_geometry_statistics import _grid_with_floater, _tetrahedron

from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.geometry_statistics import compute_geometry_statistics
from packlab_core.reconstruction import ScaleState
from packlab_core.reconstruction_anomaly import detect_reconstruction_anomalies
from packlab_core.reconstruction_confidence import (
    RECONSTRUCTION_CONFIDENCE_CONTRACT,
    ReconstructionConfidenceReport,
)


def _confidence(*, observation="observed", threshold="meets_profile"):
    return ReconstructionConfidenceReport(
        {
            "contract": RECONSTRUCTION_CONFIDENCE_CONTRACT,
            "authority": "diagnostic_only_no_physical_accuracy_or_acceptance_claim",
            "observation_status": observation,
            "threshold_status": threshold,
            "acceptance_status": "not_evaluated",
        }
    )


def _statistics(mesh: TriangleMeshData, revision="scan-master-fixture-r1"):
    return compute_geometry_statistics(
        mesh,
        geometry_revision_id=revision,
        scale_state=ScaleState.RELATIVE,
    )


def test_detector_emits_deterministic_review_findings_bound_to_geometry_and_confidence() -> None:
    stats = _statistics(_grid_with_floater())
    confidence = _confidence(threshold="below_profile")
    first = detect_reconstruction_anomalies(stats, confidence)
    second = detect_reconstruction_anomalies(stats, confidence)

    assert first == second
    assert first.geometry_revision_id == stats.geometry_revision_id
    assert first.geometry_sha256 == stats.geometry_sha256
    assert first.confidence_report_sha256 == confidence.digest()
    assert first.status == "REVIEW_REQUIRED"
    codes = {item.code for item in first.findings}
    assert "mesh_disconnected_components" in codes
    assert "mesh_boundary_edges_present" in codes
    assert "confidence_below_profile" in codes
    payload = first.as_dict()
    assert payload["geometry_mutated"] is False
    assert payload["scan_master_replaced"] is False
    assert payload["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert "vertices" not in str(payload) and "path" not in str(payload)


def test_missing_evidence_is_incomplete_and_never_a_clean_result() -> None:
    report = detect_reconstruction_anomalies(None, None)
    assert report.status == "REVIEW_REQUIRED"
    assert {item.code for item in report.findings} == {
        "diagnostic_statistics_missing",
        "confidence_evidence_missing",
    }

    incomplete = detect_reconstruction_anomalies(
        _statistics(_tetrahedron()), _confidence(observation="incomplete")
    )
    assert incomplete.status == "REVIEW_REQUIRED"
    assert "confidence_evidence_incomplete" in {item.code for item in incomplete.findings}


def test_no_rule_triggered_remains_diagnostic_only_not_an_acceptance() -> None:
    report = detect_reconstruction_anomalies(_statistics(_tetrahedron()), _confidence())
    assert report.status == "NO_RULE_TRIGGERED_DIAGNOSTIC_ONLY"
    assert report.findings == ()
    assert report.as_dict()["authority_class"] == "DIAGNOSTIC_REVIEW_SUGGESTIONS_ONLY"
    assert report.as_dict()["mold_use_authorized"] is False


def test_path_like_revision_id_is_rejected_before_serialization() -> None:
    stats = _statistics(_tetrahedron(), revision="C:\\owner\\scan.obj")
    # Existing diagnostic records permit broad labels; this proposal surface narrows them.
    from dataclasses import replace

    unsafe = replace(stats, geometry_revision_id="C:\\owner\\scan.obj")
    try:
        detect_reconstruction_anomalies(unsafe, _confidence())
    except ValueError as error:
        assert str(error) == "geometry_revision_id_invalid"
    else:
        raise AssertionError("path-like revision identifier was serialized")


def _replace_stats(**changes):
    from dataclasses import replace

    return replace(_statistics(_tetrahedron()), **changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"topology_indicators": ()},  # point-cloud style statistics: no mesh topology
        {"connected_component_count": None},
        {"connected_component_count": True},
        {"topology_indicators": (("boundary_edge_count", 0.0), ("nonmanifold_edge_count", 0))},
        {"topology_indicators": (("boundary_edge_count", False), ("nonmanifold_edge_count", 0))},
        {"topology_indicators": (("boundary_edge_count", -1), ("nonmanifold_edge_count", 0))},
    ],
)
def test_missing_or_malformed_topology_is_incomplete_not_clean(changes) -> None:
    # Review F-2: these used to return NO_RULE_TRIGGERED_DIAGNOSTIC_ONLY.
    report = detect_reconstruction_anomalies(_replace_stats(**changes), _confidence())
    assert report.status == "REVIEW_REQUIRED"
    assert "mesh_topology_evidence_incomplete" in {item.code for item in report.findings}


def test_nonmanifold_and_unresolved_hole_rules_each_fire() -> None:
    nonmanifold = _replace_stats(
        topology_indicators=(
            ("unique_edge_count", 6),
            ("boundary_edge_count", 0),
            ("nonmanifold_edge_count", 2),
        )
    )
    report = detect_reconstruction_anomalies(nonmanifold, _confidence())
    assert {item.code for item in report.findings} == {"mesh_nonmanifold_edges_present"}
    holes = _replace_stats(hole_report_linkage=("hole-report-1", "a" * 64, 3, 1))
    report = detect_reconstruction_anomalies(holes, _confidence())
    assert {item.code for item in report.findings} == {"mesh_hole_report_unresolved_components"}


def test_not_evaluated_confidence_threshold_is_incomplete() -> None:
    report = detect_reconstruction_anomalies(
        _statistics(_tetrahedron()), _confidence(threshold="not_evaluated")
    )
    assert report.status == "REVIEW_REQUIRED"
    finding = next(
        item for item in report.findings if item.code == "confidence_evidence_incomplete"
    )
    assert finding.as_dict()["evidence"] == {"threshold_status": "not_evaluated"}
