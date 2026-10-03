"""Feature and section summaries built on the accepted M10 comparison services."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass

from .cross_section_overlay import (
    CanonicalAxis,
    CanonicalPlaneSelection,
    CrossSectionOverlay,
    CrossSectionOverlayError,
    compare_scan_design_cross_sections,
)
from .design_model import (
    DesignModelError,
    DesignModelRevision,
    resolve_design_model_feature,
)
from .geometry_adapter import Open3DGeometryAdapter
from .reconstruction import ScaleState
from .scan_design_heatmap import (
    DesignModelGeometryReference,
    DistanceSignPolicy,
    HeatmapError,
    HeatmapPolicy,
    ScanDesignHeatmap,
    compute_scan_design_heatmap,
)
from .scan_master import ScanMasterRevision, mesh_sha256

MAX_DEVIATION_REGIONS = 64
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}$")
_TOLERANCE_TEXT = "GEOMETRY_DEVIATION_ONLY_NOT_MANUFACTURING_TOLERANCE"


class DeviationReportError(ValueError):
    """Raised when a pinned comparison report is stale, ambiguous or unbounded."""


@dataclass(frozen=True, slots=True)
class SectionDeviationTarget:
    feature_id: str
    section_id: str
    height: float
    geometry: DesignModelGeometryReference

    def __post_init__(self) -> None:
        for value, field in ((self.feature_id, "feature_id"), (self.section_id, "section_id")):
            if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
                raise DeviationReportError(f"{field}_invalid")
        if (
            isinstance(self.height, bool)
            or not isinstance(self.height, (int, float))
            or not math.isfinite(self.height)
        ):
            raise DeviationReportError("section_height_invalid")
        if not isinstance(self.geometry, DesignModelGeometryReference):
            raise DeviationReportError("feature_geometry_reference_required")
        object.__setattr__(self, "height", float(self.height))


@dataclass(frozen=True, slots=True)
class DeviationRegion:
    rank: int
    feature_id: str
    feature_semantic_key: str
    section_id: str
    height: float
    feature_geometry_sha256: str
    overlay_id: str
    scan_to_design_sample_count: int
    scan_to_design_mean: float
    scan_to_design_maximum: float
    design_to_scan_sample_count: int
    design_to_scan_mean: float
    design_to_scan_maximum: float
    peak_deviation: float
    units: str

    @property
    def deviation_present(self) -> bool:
        return self.peak_deviation > 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "feature_id": self.feature_id,
            "feature_semantic_key": self.feature_semantic_key,
            "section_id": self.section_id,
            "height": self.height,
            "feature_geometry_sha256": self.feature_geometry_sha256,
            "overlay_id": self.overlay_id,
            "scan_to_design": {
                "sample_count": self.scan_to_design_sample_count,
                "mean": self.scan_to_design_mean,
                "maximum": self.scan_to_design_maximum,
            },
            "design_to_scan": {
                "sample_count": self.design_to_scan_sample_count,
                "mean": self.design_to_scan_mean,
                "maximum": self.design_to_scan_maximum,
            },
            "peak_deviation": self.peak_deviation,
            "units": self.units,
            "deviation_present": self.deviation_present,
            "is_manufacturing_tolerance": False,
        }


@dataclass(frozen=True, slots=True)
class DesignDeviationReport:
    report_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    design_model_revision_id: str
    design_model_geometry_sha256: str
    scale_state: ScaleState
    units: str
    heatmap: ScanDesignHeatmap
    regions: tuple[DeviationRegion, ...]
    design_surface_watertight: bool
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.design-deviation-report.v1",
            "report_id": self.report_id,
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "design_model_revision_id": self.design_model_revision_id,
                "design_model_geometry_sha256": self.design_model_geometry_sha256,
                "design_model_fitted_to_scan_master_revision_id": self.scan_master_revision_id,
            },
            "scale": {
                "state": self.scale_state.value,
                "units": self.units,
                "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
                "mold_use_authorized": self.mold_use_authorized,
            },
            "surface_comparison": {
                "heatmap_id": self.heatmap.heatmap_id,
                "sample_count": len(self.heatmap.signed_distances),
                "maximum_unsigned_deviation": max(self.heatmap.signed_distances, default=0.0),
                "distance_sign_policy": self.heatmap.policy.sign_policy.value,
                "signed_distance_available": False,
                "design_surface_watertight": self.design_surface_watertight,
                "inside_outside_direction_available": False,
                "open_surface_direction_limited": not self.design_surface_watertight,
            },
            "regions": [region.as_dict() for region in self.regions],
            "region_ranking": "descending_peak_deviation_then_height_feature_and_section_id",
            "tolerance_interpretation": _TOLERANCE_TEXT,
            "is_manufacturing_tolerance": False,
            "authority_class": "DERIVED_SCAN_DESIGN_DEVIATION_DIAGNOSTIC",
            "scan_master_changed": False,
            "preview_or_deviation_is_parametric_truth": False,
        }


def calculate_design_deviation_report(
    scan_master: ScanMasterRevision,
    design_model: DesignModelRevision,
    geometry: DesignModelGeometryReference,
    regions: tuple[SectionDeviationTarget, ...],
    *,
    expected_scan_master_revision_id: str,
    expected_scan_master_geometry_sha256: str,
    heatmap_policy: HeatmapPolicy = HeatmapPolicy(),
    adapter: Open3DGeometryAdapter | None = None,
) -> DesignDeviationReport:
    """Summarize unsigned M10 surface and section comparisons for one exact parent."""
    if not isinstance(scan_master, ScanMasterRevision):
        raise DeviationReportError("scan_master_revision_required")
    if not isinstance(design_model, DesignModelRevision):
        raise DeviationReportError("design_model_revision_required")
    if not isinstance(geometry, DesignModelGeometryReference):
        raise DeviationReportError("design_model_geometry_reference_required")
    if (
        not isinstance(expected_scan_master_revision_id, str)
        or expected_scan_master_revision_id != scan_master.revision_id
        or not isinstance(expected_scan_master_geometry_sha256, str)
        or not _SHA256.fullmatch(expected_scan_master_geometry_sha256)
        or expected_scan_master_geometry_sha256 != mesh_sha256(scan_master.mesh)
        or design_model.fitted_to_scan_master_revision_id != expected_scan_master_revision_id
        or design_model.scan_master_geometry_sha256 != expected_scan_master_geometry_sha256
    ):
        raise DeviationReportError("scan_master_parent_binding_mismatch")
    if (
        design_model.revision_id != geometry.revision_id
        or design_model.project_id != geometry.project_id
        or geometry.fitted_to_scan_master_revision_id != expected_scan_master_revision_id
        or design_model.scale_state is not geometry.scale_state
        or design_model.scale_provenance_id != geometry.scale_provenance_id
        or design_model.physical_accuracy_validation_status
        != geometry.physical_accuracy_validation_status
        or design_model.mold_use_authorized is not False
        or geometry.mold_use_authorized is not False
    ):
        raise DeviationReportError("design_model_geometry_binding_mismatch")
    if not isinstance(heatmap_policy, HeatmapPolicy):
        raise DeviationReportError("heatmap_policy_required")
    if heatmap_policy.sign_policy is not DistanceSignPolicy.UNSIGNED:
        raise DeviationReportError("signed_deviation_report_not_supported")
    if (
        not isinstance(regions, tuple)
        or not regions
        or len(regions) > MAX_DEVIATION_REGIONS
        or any(not isinstance(item, SectionDeviationTarget) for item in regions)
    ):
        raise DeviationReportError("deviation_regions_invalid_or_unbounded")
    identities = tuple((item.feature_id, item.section_id, item.height) for item in regions)
    if len(set(identities)) != len(identities):
        raise DeviationReportError("deviation_region_duplicate")

    resolved: dict[str, str] = {}
    for target in regions:
        feature_geometry = target.geometry
        if (
            feature_geometry.revision_id != design_model.revision_id
            or feature_geometry.project_id != design_model.project_id
            or feature_geometry.fitted_to_scan_master_revision_id
            != expected_scan_master_revision_id
            or feature_geometry.scale_state is not design_model.scale_state
            or feature_geometry.scale_provenance_id != design_model.scale_provenance_id
            or feature_geometry.physical_accuracy_validation_status
            != design_model.physical_accuracy_validation_status
            or feature_geometry.mold_use_authorized is not False
        ):
            raise DeviationReportError("feature_geometry_binding_mismatch")
        try:
            feature = resolve_design_model_feature(design_model, target.feature_id)
        except DesignModelError as error:
            raise DeviationReportError("deviation_region_feature_stale_or_missing") from error
        resolved[target.feature_id] = feature.semantic_key

    try:
        heatmap = compute_scan_design_heatmap(
            scan_master, geometry, policy=heatmap_policy, adapter=adapter
        )
    except HeatmapError as error:
        raise DeviationReportError(f"heatmap_comparison_failed:{error}") from error
    if (
        heatmap.scan_master_revision_id != expected_scan_master_revision_id
        or heatmap.scan_master_geometry_sha256 != expected_scan_master_geometry_sha256
        or heatmap.design_model_revision_id != design_model.revision_id
        or heatmap.design_model_geometry_sha256 != geometry.geometry_sha256
        or heatmap.scale_state is not design_model.scale_state
    ):
        raise DeviationReportError("heatmap_parent_binding_mismatch")

    overlays: list[tuple[SectionDeviationTarget, str, CrossSectionOverlay]] = []
    for target in regions:
        plane = CanonicalPlaneSelection(CanonicalAxis.Z, target.height)
        try:
            overlay = compare_scan_design_cross_sections(scan_master, target.geometry, plane)
        except CrossSectionOverlayError as error:
            raise DeviationReportError(f"section_overlay_failed:{error}") from error
        if (
            overlay.scan_master_revision_id != expected_scan_master_revision_id
            or overlay.scan_master_geometry_sha256 != expected_scan_master_geometry_sha256
            or overlay.design_model_revision_id != design_model.revision_id
            or overlay.design_model_geometry_sha256 != target.geometry.geometry_sha256
            or overlay.scale_state is not design_model.scale_state
            or overlay.mold_use_authorized is not False
        ):
            raise DeviationReportError("section_overlay_parent_binding_mismatch")
        overlays.append((target, resolved[target.feature_id], overlay))

    ranked = sorted(
        overlays,
        key=lambda item: (
            -max(item[2].scan_to_design.maximum, item[2].design_to_scan.maximum),
            item[0].height,
            item[0].feature_id,
            item[0].section_id,
        ),
    )
    summaries = tuple(
        DeviationRegion(
            index,
            target.feature_id,
            semantic_key,
            target.section_id,
            target.height,
            target.geometry.geometry_sha256,
            overlay.overlay_id,
            overlay.scan_to_design.sample_count,
            overlay.scan_to_design.mean,
            overlay.scan_to_design.maximum,
            overlay.design_to_scan.sample_count,
            overlay.design_to_scan.mean,
            overlay.design_to_scan.maximum,
            max(overlay.scan_to_design.maximum, overlay.design_to_scan.maximum),
            overlay.coordinate_unit,
        )
        for index, (target, semantic_key, overlay) in enumerate(ranked, start=1)
    )
    report_body = {
        "scan_master_revision_id": scan_master.revision_id,
        "scan_master_geometry_sha256": expected_scan_master_geometry_sha256,
        "design_model_revision_id": design_model.revision_id,
        "design_model_geometry_sha256": geometry.geometry_sha256,
        "heatmap_id": heatmap.heatmap_id,
        "regions": [region.as_dict() for region in summaries],
        "distance_sign_policy": DistanceSignPolicy.UNSIGNED.value,
    }
    report_id = (
        "design-deviation-report:"
        + hashlib.sha256(
            json.dumps(report_body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    if design_model.scale_state is ScaleState.RELATIVE:
        units = "reconstruction_units"
    elif design_model.scale_state is ScaleState.METRIC_UNVERIFIED:
        units = "mm_unverified"
    else:
        raise DeviationReportError("metric_verified_deviation_forbidden_while_validation_deferred")
    return DesignDeviationReport(
        report_id,
        scan_master.revision_id,
        expected_scan_master_geometry_sha256,
        design_model.revision_id,
        geometry.geometry_sha256,
        design_model.scale_state,
        units,
        heatmap,
        summaries,
        heatmap.target_watertight,
    )


__all__ = [
    "MAX_DEVIATION_REGIONS",
    "DeviationRegion",
    "DeviationReportError",
    "DesignDeviationReport",
    "SectionDeviationTarget",
    "calculate_design_deviation_report",
]
