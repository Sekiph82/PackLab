"""Bounded, provenance-linked sparse image-graph connectivity diagnostics."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from .registered_photo_ratio import build_registered_photo_ratio_report
from .sparse_mapping import SparseMappingRun

SPARSE_CONNECTIVITY_CONTRACT: Final = "packlab.sparse-connectivity.v1"
SPARSE_CONNECTIVITY_POLICY_VERSION: Final = "packlab.sparse-connectivity-policy.v1"
DEFAULT_MINIMUM_LARGEST_COMPONENT_RATIO: Final = 0.9
DEFAULT_MAXIMUM_ISOLATED_NODE_RATIO: Final = 0.05
MAX_CONNECTIVITY_NODES: Final = 100_000
MAX_CONNECTIVITY_EDGES: Final = 1_000_000
MAX_REPORTED_COMPONENT_SIZES: Final = 16


class SparseConnectivityError(ValueError):
    """Raised for invalid policy configuration, not malformed graph evidence."""


@dataclass(frozen=True, slots=True)
class SparseConnectivityPolicy:
    """Versioned inclusive thresholds for describing graph fragmentation."""

    minimum_largest_component_ratio: float = DEFAULT_MINIMUM_LARGEST_COMPONENT_RATIO
    maximum_isolated_node_ratio: float = DEFAULT_MAXIMUM_ISOLATED_NODE_RATIO

    def __post_init__(self) -> None:
        for field_name in (
            "minimum_largest_component_ratio",
            "maximum_isolated_node_ratio",
        ):
            value = getattr(self, field_name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
                or value > 1
                or not math.isfinite(float(value))
            ):
                raise SparseConnectivityError(f"{field_name} must be finite and within 0..1")
            object.__setattr__(self, field_name, float(value))

    def as_dict(self) -> dict[str, object]:
        return {
            "version": SPARSE_CONNECTIVITY_POLICY_VERSION,
            "minimum_largest_component_ratio": self.minimum_largest_component_ratio,
            "maximum_isolated_node_ratio": self.maximum_isolated_node_ratio,
            "boundaries_inclusive": True,
        }


@dataclass(frozen=True, slots=True)
class SparseConnectivityReport:
    """Canonical graph observations that do not promote sparse geometry authority."""

    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return json.loads(json.dumps(self.payload, sort_keys=True, allow_nan=False))

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _invalid_report(code: str) -> SparseConnectivityReport:
    return SparseConnectivityReport(
        {
            "contract": SPARSE_CONNECTIVITY_CONTRACT,
            "authority": "diagnostic_only_no_geometry_promotion",
            "observation_status": "invalid",
            "threshold_status": "not_evaluated",
            "source_evidence": None,
            "graph": None,
            "policy": SparseConnectivityPolicy().as_dict(),
            "diagnostics": [{"code": code}],
        }
    )


def _normalize_edges(edges: object, node_count: int) -> tuple[tuple[int, int], ...] | None:
    if not isinstance(edges, Sequence) or isinstance(edges, (str, bytes, bytearray)):
        return None
    if len(edges) > MAX_CONNECTIVITY_EDGES:
        return None
    normalized: set[tuple[int, int]] = set()
    for edge in edges:
        if (
            not isinstance(edge, Sequence)
            or isinstance(edge, (str, bytes, bytearray))
            or len(edge) != 2
        ):
            return None
        left, right = edge
        if (
            isinstance(left, bool)
            or not isinstance(left, int)
            or isinstance(right, bool)
            or not isinstance(right, int)
            or not 0 <= left < node_count
            or not 0 <= right < node_count
            or left == right
        ):
            return None
        identity = (min(left, right), max(left, right))
        if identity in normalized:
            return None
        normalized.add(identity)
    return tuple(sorted(normalized))


def _components(node_count: int, edges: tuple[tuple[int, int], ...]) -> tuple[list[int], int]:
    adjacency: list[set[int]] = [set() for _ in range(node_count)]
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    seen: set[int] = set()
    sizes: list[int] = []
    isolated = 0
    for start in range(node_count):
        if start in seen:
            continue
        pending = [start]
        seen.add(start)
        size = 0
        while pending:
            node = pending.pop()
            size += 1
            for neighbor in sorted(adjacency[node], reverse=True):
                if neighbor not in seen:
                    seen.add(neighbor)
                    pending.append(neighbor)
        sizes.append(size)
        if size == 1:
            isolated += 1
    sizes.sort(reverse=True)
    return sizes, isolated


def build_sparse_connectivity_report(
    run: object,
    registered_image_ids: object,
    edges: object,
    *,
    policy: SparseConnectivityPolicy = SparseConnectivityPolicy(),
) -> SparseConnectivityReport:
    """Describe connected components for a stage-bound registered-image graph.

    ``registered_image_ids`` must be the complete, input-ordered identity list
    represented by graph nodes. Edges are undirected pairs of zero-based node
    indexes derived from the same COLMAP sparse-stage evidence. Raw graph inputs
    are never changed or copied into report output.
    """
    if not isinstance(policy, SparseConnectivityPolicy):
        raise SparseConnectivityError("an explicit SparseConnectivityPolicy is required")
    ratio_payload = build_registered_photo_ratio_report(run).as_dict()
    ratio_status = ratio_payload.get("observation_status")
    if ratio_status != "observed":
        if ratio_status == "unavailable":
            return SparseConnectivityReport(
                {
                    "contract": SPARSE_CONNECTIVITY_CONTRACT,
                    "authority": "diagnostic_only_no_geometry_promotion",
                    "observation_status": "unavailable",
                    "threshold_status": "not_evaluated",
                    "acceptance_status": "not_evaluated",
                    "source_evidence": ratio_payload.get("source_evidence"),
                    "graph": None,
                    "policy": policy.as_dict(),
                    "diagnostics": [{"code": "registered_photo_stage_evidence_unavailable"}],
                }
            )
        return _invalid_report("registered_photo_stage_evidence_invalid")
    if not isinstance(run, SparseMappingRun):
        return _invalid_report("registered_photo_stage_evidence_invalid")
    request = run.request
    if not isinstance(request.image_asset_ids, tuple):
        return _invalid_report("registered_photo_stage_evidence_invalid")
    registered_count = ratio_payload.get("statistics")
    if not isinstance(registered_count, dict):
        return _invalid_report("registered_photo_stage_evidence_invalid")
    expected_registered = registered_count.get("registered_photos")
    if (
        isinstance(expected_registered, bool)
        or not isinstance(expected_registered, int)
        or not isinstance(registered_image_ids, Sequence)
        or isinstance(registered_image_ids, (str, bytes, bytearray))
    ):
        return _invalid_report("registered_image_identity_invalid")
    input_ids = request.image_asset_ids
    node_ids = tuple(registered_image_ids)
    node_id_set = set(node_ids) if all(isinstance(value, str) for value in node_ids) else set()
    if (
        len(input_ids) > MAX_CONNECTIVITY_NODES
        or len(node_ids) != expected_registered
        or len(node_ids) > MAX_CONNECTIVITY_NODES
        or any(not isinstance(value, str) for value in node_ids)
        or len(set(node_ids)) != len(node_ids)
        or len({value.casefold() for value in node_ids}) != len(node_ids)
        or any(value not in input_ids for value in node_ids)
        or node_ids != tuple(value for value in input_ids if value in node_id_set)
    ):
        return _invalid_report("registered_image_identity_invalid")
    normalized_edges = _normalize_edges(edges, len(node_ids))
    if normalized_edges is None:
        return _invalid_report("connectivity_edge_invalid")

    stage_evidence = ratio_payload.get("source_evidence")
    if not isinstance(stage_evidence, dict):
        return _invalid_report("registered_photo_stage_evidence_invalid")
    graph_identity = {
        "contract": SPARSE_CONNECTIVITY_CONTRACT,
        "request_sha256": stage_evidence.get("request_sha256"),
        "stage_evidence_sha256": stage_evidence.get("stage_evidence_sha256"),
        "registered_image_ids": list(node_ids),
        "edges": [list(edge) for edge in normalized_edges],
    }
    graph_sha256 = _canonical_digest(graph_identity)
    node_count = len(node_ids)
    edge_count = len(normalized_edges)
    if node_count == 0:
        component_sizes: list[int] = []
        isolated_count = 0
        largest_ratio = None
        isolated_ratio = None
        connectivity_status = "empty"
        threshold_status = "not_evaluated"
        diagnostics = [{"code": "connectivity_graph_empty", "severity": "info"}]
    else:
        component_sizes, isolated_count = _components(node_count, normalized_edges)
        largest_ratio = component_sizes[0] / node_count
        isolated_ratio = isolated_count / node_count
        connectivity_status = "connected" if len(component_sizes) == 1 else "fragmented"
        threshold_met = (
            largest_ratio >= policy.minimum_largest_component_ratio
            and isolated_ratio <= policy.maximum_isolated_node_ratio
        )
        threshold_status = "meets_threshold" if threshold_met else "below_threshold"
        severity = "info" if threshold_met else "warning"
        diagnostics = [
            {
                "code": "connectivity_fragmentation_observed"
                if connectivity_status == "fragmented"
                else "connectivity_single_component",
                "severity": severity,
            }
        ]

    graph = {
        "sha256": graph_sha256,
        "identity_algorithm": "sha256_canonical_json_stage_bound_index_edges_v1",
        "node_count": node_count,
        "edge_count": edge_count,
        "component_count": len(component_sizes),
        "largest_component_size": component_sizes[0] if component_sizes else 0,
        "largest_component_ratio": largest_ratio,
        "isolated_node_count": isolated_count,
        "isolated_node_ratio": isolated_ratio,
        "component_sizes_largest_first": component_sizes[:MAX_REPORTED_COMPONENT_SIZES],
        "additional_component_count": max(0, len(component_sizes) - MAX_REPORTED_COMPONENT_SIZES),
        "mean_degree": None if node_count == 0 else (2 * edge_count) / node_count,
        "connectivity_status": connectivity_status,
    }
    return SparseConnectivityReport(
        {
            "contract": SPARSE_CONNECTIVITY_CONTRACT,
            "authority": "diagnostic_only_no_geometry_promotion",
            "observation_status": "observed",
            "threshold_status": threshold_status,
            "acceptance_status": "not_evaluated",
            "source_evidence": {
                "request_sha256": stage_evidence.get("request_sha256"),
                "stage_evidence_sha256": stage_evidence.get("stage_evidence_sha256"),
                "ordered_input_photo_count": stage_evidence.get("ordered_input_photo_count"),
                "registered_photo_count": expected_registered,
                "graph_node_ids_sha256": _canonical_digest(list(node_ids)),
            },
            "policy": policy.as_dict(),
            "graph": graph,
            "diagnostics": diagnostics,
        }
    )
