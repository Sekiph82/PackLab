"""Evidence-only detection of candidate handle voids in jerrycan sections."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict, deque
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from .cross_section_overlay import (
    CanonicalPlaneSelection,
    CrossSectionOverlay,
    CrossSectionOverlayError,
    compare_scan_design_cross_sections,
)
from .design_model import DesignModelRevision, FeatureKind, PackageFamily
from .design_preview import DesignPreview
from .reconstruction import ScaleState
from .scan_design_heatmap import DesignModelGeometryReference
from .scan_master import ScanMasterRevision, mesh_sha256

MAX_CANDIDATE_LOOPS = 64
MAX_CONTAINMENT_WORK = 1_000_000


class HandleVoidDetectionError(ValueError):
    """Raised when the selected evidence cannot support a bounded candidate report."""


class HandleVoidStatus(StrEnum):
    NO_CANDIDATE = "NO_CANDIDATE"
    CANDIDATE = "CANDIDATE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class HandleVoidCandidate:
    candidate_id: str
    region_bounds: tuple[float, float, float, float]
    region_area: float
    contour_sha256: str
    support_segment_count: int
    support_vertex_count: int
    confidence: str
    ambiguity: str
    parent_feature_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "region": {
                "kind": "bounded_2d_section_region",
                "bounds": list(self.region_bounds),
                "area": self.region_area,
                "contour_sha256": self.contour_sha256,
            },
            "support": {
                "segment_count": self.support_segment_count,
                "unique_vertex_count": self.support_vertex_count,
                "source": "closed_scan_master_section_loop_inside_design_model_silhouette",
            },
            "confidence": self.confidence,
            "ambiguity": self.ambiguity,
            "parent_feature_ids": list(self.parent_feature_ids),
            "geometry_subtracted": False,
            "handle_opening_created": False,
            "hidden_extent_inferred": False,
        }


@dataclass(frozen=True, slots=True)
class HandleVoidDetection:
    status: HandleVoidStatus
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    design_model_revision_id: str
    design_model_geometry_sha256: str
    parent_binding_revision_id: str
    coordinate_unit: str
    plane: CanonicalPlaneSelection
    candidates: tuple[HandleVoidCandidate, ...]
    scan_closed_loop_count: int
    scan_open_component_count: int
    design_closed_loop_count: int
    coverage_gaps: tuple[str, ...]
    selected_plane_coverage_complete: bool
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.jerrycan-handle-void-candidates.v1",
            "status": self.status.value,
            "authority_class": "EVIDENCE_BOUND_DIAGNOSTIC",
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "design_model_revision_id": self.design_model_revision_id,
                "design_model_geometry_sha256": self.design_model_geometry_sha256,
                "parent_binding_revision_id": self.parent_binding_revision_id,
            },
            "plane": self.plane.as_dict(self.coordinate_unit),
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "support": {
                "scan_closed_loop_count": self.scan_closed_loop_count,
                "scan_open_component_count": self.scan_open_component_count,
                "design_closed_loop_count": self.design_closed_loop_count,
                "coverage_gaps": list(self.coverage_gaps),
                "selected_plane_coverage_complete": self.selected_plane_coverage_complete,
            },
            "limitations": list(self.limitations),
            "geometry_subtracted": False,
            "handle_opening_created": False,
            "scan_master_replaced": False,
            "hidden_extent_inferred": False,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }


Point2 = tuple[float, float]
Segment2 = tuple[Point2, Point2]


def detect_jerrycan_handle_void_candidates(
    scan_master: ScanMasterRevision,
    design_model: DesignModelRevision,
    design_preview: DesignPreview,
    plane: CanonicalPlaneSelection,
    *,
    expected_scan_master_revision_id: str,
    expected_design_model_revision_id: str,
) -> HandleVoidDetection:
    """Find enclosed Scan Master section loops inside an explicit jerrycan silhouette."""
    reference = _design_reference(
        scan_master,
        design_model,
        design_preview,
        expected_scan_master_revision_id=expected_scan_master_revision_id,
        expected_design_model_revision_id=expected_design_model_revision_id,
    )
    parent_binding_revision_id = design_model.parent_binding_revision_id
    if parent_binding_revision_id is None:
        raise HandleVoidDetectionError("jerrycan_captured_parent_required")
    if not isinstance(plane, CanonicalPlaneSelection):
        raise HandleVoidDetectionError("explicit_canonical_plane_required")
    try:
        overlay = compare_scan_design_cross_sections(scan_master, reference, plane)
    except CrossSectionOverlayError as error:
        raise HandleVoidDetectionError("selected_section_evidence_invalid") from error

    scan_loops, open_count = _closed_loops(overlay.scan_master_section.segments)
    design_loops, design_open_count = _closed_loops(overlay.design_model_section.segments)
    if len(scan_loops) > MAX_CANDIDATE_LOOPS or len(design_loops) > MAX_CANDIDATE_LOOPS:
        raise HandleVoidDetectionError("section_loop_limit_exceeded")
    if not design_loops:
        raise HandleVoidDetectionError("design_model_silhouette_not_closed")

    silhouette = max(design_loops, key=lambda loop: (_area(loop), tuple(loop)))
    scan_outer = max(scan_loops, key=lambda loop: (_area(loop), tuple(loop))) if scan_loops else ()
    containment_work = 2 * sum(len(loop) for loop in scan_loops) * len(silhouette)
    if containment_work > MAX_CONTAINMENT_WORK:
        raise HandleVoidDetectionError("section_containment_work_bound_exceeded")
    nested = tuple(
        loop
        for loop in scan_loops
        if loop is not scan_outer
        and _area(loop) < _area(scan_outer)
        and all(_inside(point, silhouette) for point in loop)
        and all(_inside(point, scan_outer) for point in loop)
    )
    feature_ids = tuple(
        sorted(
            feature.feature_id
            for feature in design_model.features
            if feature.feature_kind is FeatureKind.BODY
        )
    )
    if not feature_ids:
        raise HandleVoidDetectionError("jerrycan_body_feature_references_missing")

    coverage_raw = scan_master.manifest.get("coverage_gaps")
    if isinstance(coverage_raw, (tuple, list)):
        if any(not isinstance(item, str) or not item.strip() for item in coverage_raw):
            raise HandleVoidDetectionError("scan_master_coverage_gaps_invalid")
        coverage_gaps: tuple[str, ...] = tuple(
            item for item in coverage_raw if isinstance(item, str)
        )
        coverage_known = True
    else:
        coverage_gaps = ()
        coverage_known = False
    selected_plane_coverage_complete = (
        coverage_known and not coverage_gaps and open_count == 0 and design_open_count == 0
    )
    limitations = [
        "candidate_is_diagnostic_only_and_requires_review",
        "one_selected_plane_does_not_establish_full_three_dimensional_void_extent",
        "hidden_or_unobserved_void_extent_remains_unknown",
        "no_boolean_subtraction_or_handle_opening_is_performed",
    ]
    if design_open_count:
        limitations.append("design_silhouette_has_open_section_components")
    if open_count:
        limitations.append("scan_section_has_open_components_and_incomplete_contour_support")
    if not coverage_known:
        limitations.append("scan_master_coverage_metadata_missing")
    limitations.extend(f"scan_master_coverage_gap:{gap}" for gap in coverage_gaps)

    confidence = (
        "HIGH_SECTION_SUPPORT" if selected_plane_coverage_complete else "LIMITED_SECTION_SUPPORT"
    )
    candidates = tuple(
        _candidate(
            loop,
            overlay,
            plane,
            feature_ids,
            confidence=confidence,
            ambiguity=(
                "multiple_enclosed_regions_require_review"
                if len(nested) > 1
                else "single_enclosed_region_candidate_only"
            ),
        )
        for loop in sorted(nested, key=lambda item: (_bounds(item), _area(item)))
    )
    review_required = (
        len(candidates) > 1
        or open_count > 0
        or design_open_count > 0
        or bool(coverage_gaps)
        or not coverage_known
    )
    status = (
        HandleVoidStatus.REVIEW_REQUIRED
        if review_required
        else HandleVoidStatus.CANDIDATE
        if candidates
        else HandleVoidStatus.NO_CANDIDATE
    )
    return HandleVoidDetection(
        status,
        scan_master.revision_id,
        overlay.scan_master_geometry_sha256,
        design_model.revision_id,
        overlay.design_model_geometry_sha256,
        parent_binding_revision_id,
        overlay.coordinate_unit,
        plane,
        candidates,
        len(scan_loops),
        open_count,
        len(design_loops),
        coverage_gaps,
        selected_plane_coverage_complete,
        tuple(limitations),
    )


def _design_reference(
    scan_master: ScanMasterRevision,
    design_model: DesignModelRevision,
    preview: DesignPreview,
    *,
    expected_scan_master_revision_id: str,
    expected_design_model_revision_id: str,
) -> DesignModelGeometryReference:
    if not isinstance(scan_master, ScanMasterRevision):
        raise HandleVoidDetectionError("scan_master_revision_required")
    if not isinstance(design_model, DesignModelRevision) or not isinstance(preview, DesignPreview):
        raise HandleVoidDetectionError("jerrycan_design_model_and_preview_required")
    if (
        scan_master.revision_id != expected_scan_master_revision_id
        or design_model.revision_id != expected_design_model_revision_id
        or design_model.package_family is not PackageFamily.JERRYCAN
    ):
        raise HandleVoidDetectionError("selected_parent_revision_stale_or_wrong_family")
    scan_digest = mesh_sha256(scan_master.mesh)
    manifest = scan_master.manifest
    if (
        manifest.get("scan_master_revision_id") != scan_master.revision_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != scan_digest
        or manifest.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
        or manifest.get("mold_use_authorized") is not False
    ):
        raise HandleVoidDetectionError("scan_master_authority_or_digest_invalid")
    try:
        scale_state = ScaleState(str(manifest.get("scale_state")))
    except ValueError as error:
        raise HandleVoidDetectionError("scan_master_scale_state_invalid") from error
    if scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
        raise HandleVoidDetectionError("scan_master_scale_state_unauthorized")
    scale_provenance_id = manifest.get("scale_provenance_id")
    alignment = manifest.get("alignment_transform")
    transform = alignment.get("transform") if isinstance(alignment, Mapping) else None
    frame = transform.get("target_frame") if isinstance(transform, Mapping) else None
    if not isinstance(scale_provenance_id, str) or not scale_provenance_id:
        raise HandleVoidDetectionError("scan_master_scale_provenance_missing")
    if not isinstance(frame, str) or not frame:
        raise HandleVoidDetectionError("scan_master_coordinate_frame_missing")
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    if (
        design_model.project_id != scan_master.project_id
        or design_model.fitted_to_scan_master_revision_id != scan_master.revision_id
        or design_model.scan_master_geometry_sha256 != scan_digest
        or design_model.scale_state is not scale_state
        or design_model.scale_provenance_id != scale_provenance_id
        or design_model.coordinate_unit != unit
        or design_model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or design_model.mold_use_authorized is not False
        or preview.authority_class != "PREVIEW_PROXY"
        or preview.model_revision_id != design_model.revision_id
        or preview.scan_master_revision_id != scan_master.revision_id
        or preview.scan_master_geometry_sha256 != scan_digest
        or preview.parent_binding_revision_id != design_model.parent_binding_revision_id
        or preview.scale_state is not scale_state
        or preview.coordinate_unit != unit
    ):
        raise HandleVoidDetectionError("jerrycan_design_model_parent_or_authority_mismatch")
    model_feature_ids = {feature.feature_id for feature in design_model.features}
    preview_feature_ids = tuple(feature_id for feature_id, _ in preview.feature_vertex_indices)
    if (
        not preview_feature_ids
        or len(preview_feature_ids) != len(set(preview_feature_ids))
        or any(feature_id not in model_feature_ids for feature_id in preview_feature_ids)
        or any(
            isinstance(index, bool)
            or not isinstance(index, int)
            or not 0 <= index < len(preview.mesh.vertices)
            for _, indices in preview.feature_vertex_indices
            for index in indices
        )
    ):
        raise HandleVoidDetectionError("jerrycan_preview_feature_provenance_invalid")
    try:
        return DesignModelGeometryReference(
            design_model.revision_id,
            design_model.project_id,
            design_model.fitted_to_scan_master_revision_id,
            preview.mesh,
            mesh_sha256(preview.mesh),
            frame,
            scale_state,
            scale_provenance_id,
        )
    except (TypeError, ValueError) as error:
        raise HandleVoidDetectionError("jerrycan_design_model_preview_invalid") from error


def _closed_loops(segments: tuple[Segment2, ...]) -> tuple[tuple[tuple[Point2, ...], ...], int]:
    adjacency: dict[Point2, set[Point2]] = defaultdict(set)
    for start, end in segments:
        adjacency[start].add(end)
        adjacency[end].add(start)
    remaining = set(adjacency)
    loops: list[tuple[Point2, ...]] = []
    open_count = 0
    while remaining:
        seed = min(remaining)
        queue = deque((seed,))
        component: set[Point2] = set()
        while queue:
            point = queue.popleft()
            if point in component:
                continue
            component.add(point)
            queue.extend(adjacency[point] - component)
        remaining.difference_update(component)
        if len(component) < 3 or any(len(adjacency[point]) != 2 for point in component):
            open_count += 1
            continue
        ordered = [seed]
        previous: Point2 | None = None
        current = seed
        while True:
            following = min(point for point in adjacency[current] if point != previous)
            if following == seed:
                break
            if following in ordered:
                open_count += 1
                ordered = []
                break
            ordered.append(following)
            previous, current = current, following
        if len(ordered) >= 3:
            loops.append(tuple(ordered))
    return tuple(loops), open_count


def _area(loop: tuple[Point2, ...]) -> float:
    return (
        abs(
            math.fsum(
                first[0] * second[1] - second[0] * first[1]
                for first, second in zip(loop, (*loop[1:], loop[0]), strict=True)
            )
        )
        / 2.0
    )


def _bounds(loop: tuple[Point2, ...]) -> tuple[float, float, float, float]:
    return (
        min(point[0] for point in loop),
        min(point[1] for point in loop),
        max(point[0] for point in loop),
        max(point[1] for point in loop),
    )


def _inside(point: Point2, loop: tuple[Point2, ...]) -> bool:
    inside = False
    x, y = point
    for (x1, y1), (x2, y2) in zip(loop, (*loop[1:], loop[0]), strict=True):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _candidate(
    loop: tuple[Point2, ...],
    overlay: CrossSectionOverlay,
    plane: CanonicalPlaneSelection,
    feature_ids: tuple[str, ...],
    *,
    confidence: str,
    ambiguity: str,
) -> HandleVoidCandidate:
    contour_hash = hashlib.sha256(
        json.dumps(loop, separators=(",", ":"), allow_nan=False).encode("ascii")
    ).hexdigest()
    identity = {
        "contract": "packlab.jerrycan-handle-void-candidate.v1",
        "scan_master_revision_id": overlay.scan_master_revision_id,
        "scan_master_geometry_sha256": overlay.scan_master_geometry_sha256,
        "design_model_revision_id": overlay.design_model_revision_id,
        "design_model_geometry_sha256": overlay.design_model_geometry_sha256,
        "plane": plane.as_dict(overlay.coordinate_unit),
        "parent_feature_ids": feature_ids,
        "contour_sha256": contour_hash,
    }
    candidate_id = (
        "jerrycan-handle-void-candidate:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    return HandleVoidCandidate(
        candidate_id,
        _bounds(loop),
        _area(loop),
        contour_hash,
        len(loop),
        len(set(loop)),
        confidence,
        ambiguity,
        feature_ids,
    )


__all__ = [
    "HandleVoidCandidate",
    "HandleVoidDetection",
    "HandleVoidDetectionError",
    "HandleVoidStatus",
    "detect_jerrycan_handle_void_candidates",
]
