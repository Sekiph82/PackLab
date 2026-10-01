from __future__ import annotations

import hashlib
import json

import pytest

from packlab_core.reconstruction import ReconstructionStageResult, RunStatus, StageStatus
from packlab_core.sparse_connectivity import (
    SPARSE_CONNECTIVITY_CONTRACT,
    SparseConnectivityError,
    SparseConnectivityPolicy,
    build_sparse_connectivity_report,
)
from packlab_core.sparse_mapping import (
    STAGE_SUMMARY_CONTRACT,
    SparseMappingRequest,
    SparseMappingRun,
    normalize_sparse_mapping_result,
)

_SOURCE_DIGEST = hashlib.sha256(b"synthetic packscan").hexdigest()
_MATCHER_DIGEST = hashlib.sha256(b"synthetic matcher").hexdigest()


def _run(registered: int, *, total: int = 5):
    request = SparseMappingRequest(
        tuple(f"working/images/{index:03}.jpg" for index in range(total)),
        "revision-1",
        _SOURCE_DIGEST,
        _MATCHER_DIGEST,
    )
    summary = {
        "contract": STAGE_SUMMARY_CONTRACT,
        "total_images": total,
        "registered_images": registered,
        "unregistered_images": total - registered,
        "registration_ratio": registered / total,
        "sparse_model_asset_id": "working/reconstruction/sparse",
    }
    stage = ReconstructionStageResult(
        "sparse-mapping",
        StageStatus.SUCCEEDED,
        0,
        0.125,
        stdout="PACKLAB_SPARSE_MAPPING_SUMMARY_V1 " + json.dumps(summary, sort_keys=True),
    )
    return normalize_sparse_mapping_result(request, stage)


def _node_ids(count: int) -> list[str]:
    return [f"working/images/{index:03}.jpg" for index in range(count)]


def test_empty_and_single_component_graphs_are_deterministic_observations() -> None:
    empty = build_sparse_connectivity_report(_run(0), [], [])
    connected = build_sparse_connectivity_report(_run(3), _node_ids(3), [(0, 1), (1, 2)])

    assert empty.as_dict()["observation_status"] == "observed"
    assert empty.as_dict()["graph"]["connectivity_status"] == "empty"  # type: ignore[index]
    assert empty.as_dict()["threshold_status"] == "not_evaluated"
    assert connected.as_dict()["contract"] == SPARSE_CONNECTIVITY_CONTRACT
    assert connected.as_dict()["graph"]["connectivity_status"] == "connected"  # type: ignore[index]
    assert connected.as_dict()["graph"]["component_count"] == 1  # type: ignore[index]
    assert connected.as_dict()["threshold_status"] == "meets_threshold"
    assert connected.as_dict()["acceptance_status"] == "not_evaluated"


def test_disconnected_graph_reports_components_and_provenance() -> None:
    run = _run(4)
    report = build_sparse_connectivity_report(
        run,
        _node_ids(4),
        [(0, 1), (2, 3)],
    )
    payload = report.as_dict()

    assert payload["observation_status"] == "observed"
    assert payload["threshold_status"] == "below_threshold"
    assert payload["graph"]["connectivity_status"] == "fragmented"  # type: ignore[index]
    assert payload["graph"]["component_count"] == 2  # type: ignore[index]
    assert payload["graph"]["component_sizes_largest_first"] == [2, 2]  # type: ignore[index]
    assert payload["source_evidence"]["request_sha256"]  # type: ignore[index]
    assert payload["source_evidence"]["stage_evidence_sha256"]  # type: ignore[index]
    assert payload["authority"] == "diagnostic_only_no_geometry_promotion"


@pytest.mark.parametrize(
    "edges",
    [
        [(0, 1), (1, 0)],
        [(0, 1), (0, 1)],
    ],
)
def test_duplicate_undirected_edges_fail_closed(edges: list[tuple[int, int]]) -> None:
    payload = build_sparse_connectivity_report(_run(3), _node_ids(3), edges).as_dict()
    assert payload["observation_status"] == "invalid"
    assert payload["graph"] is None
    assert payload["diagnostics"][0]["code"] == "connectivity_edge_invalid"  # type: ignore[index]


@pytest.mark.parametrize("edge", [(-1, 1), (0, 3), (True, 1), (1, 1), (1,)])
def test_invalid_edge_indexes_and_self_edges_fail_closed(edge: tuple[object, ...]) -> None:
    payload = build_sparse_connectivity_report(_run(3), _node_ids(3), [edge]).as_dict()
    assert payload["observation_status"] == "invalid"
    assert payload["graph"] is None


def test_threshold_boundaries_are_inclusive_and_just_below_is_flagged() -> None:
    boundary_policy = SparseConnectivityPolicy(0.9, 0.1)
    boundary = build_sparse_connectivity_report(
        _run(10, total=10),
        _node_ids(10),
        [(index, index + 1) for index in range(8)],
        policy=boundary_policy,
    )
    below = build_sparse_connectivity_report(
        _run(10, total=10),
        _node_ids(10),
        [(index, index + 1) for index in range(7)],
        policy=boundary_policy,
    )

    assert boundary.as_dict()["graph"]["largest_component_ratio"] == pytest.approx(0.9)  # type: ignore[index]
    assert boundary.as_dict()["threshold_status"] == "meets_threshold"
    assert below.as_dict()["graph"]["largest_component_ratio"] == pytest.approx(0.8)  # type: ignore[index]
    assert below.as_dict()["threshold_status"] == "below_threshold"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"minimum_largest_component_ratio": float("nan")},
        {"minimum_largest_component_ratio": 1.01},
        {"maximum_isolated_node_ratio": -0.01},
        {"maximum_isolated_node_ratio": True},
    ],
)
def test_policy_rejects_invalid_thresholds(kwargs: dict[str, object]) -> None:
    with pytest.raises(SparseConnectivityError):
        SparseConnectivityPolicy(**kwargs)  # type: ignore[arg-type]


def test_identity_mismatch_duplicate_nodes_and_unavailable_stage_fail_closed() -> None:
    duplicate_ids = ["working/images/000.jpg", "working/images/000.jpg", "working/images/002.jpg"]
    invalid_nodes = build_sparse_connectivity_report(_run(3), duplicate_ids, [(0, 1)]).as_dict()
    wrong_count = build_sparse_connectivity_report(_run(2), _node_ids(3), [(0, 1)]).as_dict()
    unavailable = build_sparse_connectivity_report(None, [], []).as_dict()

    assert invalid_nodes["observation_status"] == "invalid"
    assert wrong_count["observation_status"] == "invalid"
    assert unavailable["observation_status"] == "invalid"


def test_failed_stage_has_no_graph_observation_or_acceptance_claim() -> None:
    request = _run(3).request
    failed_stage = ReconstructionStageResult("sparse-mapping", StageStatus.FAILED, 9, 0.2)
    report = build_sparse_connectivity_report(
        SparseMappingRun(request, RunStatus.FAILED, failed_stage), [], []
    )
    payload = report.as_dict()

    assert payload["observation_status"] == "unavailable"
    assert payload["threshold_status"] == "not_evaluated"
    assert payload["acceptance_status"] == "not_evaluated"
    assert payload["graph"] is None


def test_component_summary_is_bounded_and_graph_report_is_deterministic() -> None:
    run = _run(18, total=18)
    ids = _node_ids(18)
    edges: list[tuple[int, int]] = []
    before_run = run.as_dict()
    first = build_sparse_connectivity_report(run, ids, edges)
    second = build_sparse_connectivity_report(run, ids, edges)

    assert first.serialize() == second.serialize()
    assert first.digest() == second.digest()
    assert first.as_dict()["graph"]["component_sizes_largest_first"] == [1] * 16  # type: ignore[index]
    assert first.as_dict()["graph"]["additional_component_count"] == 2  # type: ignore[index]
    assert run.as_dict() == before_run
    assert ids == _node_ids(18)
    assert edges == []


def test_raw_stage_output_and_graph_identities_are_not_copied_to_report() -> None:
    run = _run(3)
    object.__setattr__(run.stage_result, "stderr", "C:/private/capture SECRET")
    ids = _node_ids(3)
    edges = [(0, 1), (1, 2)]
    before_ids = list(ids)
    before_edges = list(edges)
    report = build_sparse_connectivity_report(run, ids, edges)
    serialized = report.serialize()

    assert "SECRET" not in serialized
    assert "private" not in serialized.lower()
    assert '"stdout":' not in serialized and '"stderr":' not in serialized
    assert all(image_id not in serialized for image_id in ids)
    assert ids == before_ids and edges == before_edges


def test_graph_identity_changes_when_an_edge_changes() -> None:
    ids = _node_ids(3)
    first = build_sparse_connectivity_report(_run(3), ids, [(0, 1)])
    second = build_sparse_connectivity_report(_run(3), ids, [(1, 2)])
    assert first.as_dict()["graph"]["sha256"] != second.as_dict()["graph"]["sha256"]  # type: ignore[index]
