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
    FeatureKind,
    resolve_design_model_feature,
)
from .geometry_adapter import (
    GeometryAdapterError,
    MeshSurfaceDistanceOutput,
    Open3DGeometryAdapter,
    PointCloudData,
)
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
MAX_FEATURE_REGION_SAMPLES = 50_000
MAX_FEATURE_COVERAGE_GRID = 32
_LOCAL_COVERAGE_THRESHOLD = 0.75
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
class FeatureDeviationTarget:
    """Explicit local bounds and feature-scoped Design Model mesh for one M12 feature."""

    feature_id: str
    region_id: str
    bounds_xyz: tuple[float, float, float, float, float, float]
    geometry: DesignModelGeometryReference
    coverage_axes: tuple[int, int] = (0, 2)
    coverage_grid_resolution: int = 4

    def __post_init__(self) -> None:
        if not isinstance(self.feature_id, str) or not _IDENTIFIER.fullmatch(self.feature_id):
            raise DeviationReportError("feature_region_feature_id_invalid")
        if not isinstance(self.region_id, str) or not _IDENTIFIER.fullmatch(self.region_id):
            raise DeviationReportError("feature_region_id_invalid")
        bounds = _region_bounds(self.bounds_xyz)
        object.__setattr__(self, "bounds_xyz", bounds)
        if (
            not isinstance(self.coverage_axes, tuple)
            or len(self.coverage_axes) != 2
            or any(
                isinstance(axis, bool) or not isinstance(axis, int) for axis in self.coverage_axes
            )
            or any(not 0 <= axis <= 2 for axis in self.coverage_axes)
            or self.coverage_axes[0] == self.coverage_axes[1]
        ):
            raise DeviationReportError("feature_region_coverage_axes_invalid")
        if (
            isinstance(self.coverage_grid_resolution, bool)
            or not isinstance(self.coverage_grid_resolution, int)
            or not 2 <= self.coverage_grid_resolution <= MAX_FEATURE_COVERAGE_GRID
        ):
            raise DeviationReportError("feature_region_coverage_grid_invalid")
        if not isinstance(self.geometry, DesignModelGeometryReference):
            raise DeviationReportError("feature_geometry_reference_required")


@dataclass(frozen=True, slots=True)
class FeatureDeviationRegion:
    rank: int
    feature_id: str
    feature_semantic_key: str
    region_id: str
    bounds_xyz: tuple[float, float, float, float, float, float]
    feature_geometry_sha256: str
    scan_master_region_vertex_count: int
    scan_to_design_sample_count: int
    scan_to_design_mean: float | None
    scan_to_design_maximum: float | None
    coverage_grid_resolution: int
    observed_coverage_cell_count: int
    coverage_ratio: float
    coverage_status: str
    coverage_metadata_known: bool
    declared_coverage_gaps: tuple[str, ...]
    units: str

    @property
    def deviation_present(self) -> bool:
        return self.scan_to_design_maximum is not None and self.scan_to_design_maximum > 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "feature_id": self.feature_id,
            "feature_semantic_key": self.feature_semantic_key,
            "region_id": self.region_id,
            "bounds_xyz": list(self.bounds_xyz),
            "feature_geometry_sha256": self.feature_geometry_sha256,
            "scan_support": {
                "source": "SCAN_MASTER_VERTICES_ONLY",
                "region_vertex_count": self.scan_master_region_vertex_count,
                "distance_sample_count": self.scan_to_design_sample_count,
                "observed_coverage_cell_count": self.observed_coverage_cell_count,
                "coverage_grid_resolution": self.coverage_grid_resolution,
                "coverage_ratio": self.coverage_ratio,
                "coverage_status": self.coverage_status,
                "coverage_metadata_known": self.coverage_metadata_known,
                "declared_coverage_gaps": list(self.declared_coverage_gaps),
                "parametric_model_filled_missing_scan_coverage": False,
            },
            "scan_to_design": {
                "sample_count": self.scan_to_design_sample_count,
                "mean": self.scan_to_design_mean,
                "maximum": self.scan_to_design_maximum,
                "direction": "OBSERVED_SCAN_MASTER_REGION_VERTICES_TO_FEATURE_DESIGN_SURFACE",
            },
            "units": self.units,
            "deviation_present": self.deviation_present,
            "is_manufacturing_tolerance": False,
        }


@dataclass(frozen=True, slots=True)
class FeatureDeviationReport:
    report_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    design_model_revision_id: str
    design_model_geometry_sha256: str
    global_heatmap_id: str
    scale_state: ScaleState
    units: str
    regions: tuple[FeatureDeviationRegion, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.feature-deviation-report.v1",
            "report_id": self.report_id,
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "design_model_revision_id": self.design_model_revision_id,
                "design_model_geometry_sha256": self.design_model_geometry_sha256,
            },
            "global_heatmap_id": self.global_heatmap_id,
            "scale": {
                "state": self.scale_state.value,
                "units": self.units,
                "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
                "mold_use_authorized": False,
            },
            "regions": [item.as_dict() for item in self.regions],
            "region_ranking": "descending_observed_scan_to_design_maximum_then_feature_and_region_id",
            "tolerance_interpretation": _TOLERANCE_TEXT,
            "is_manufacturing_tolerance": False,
            "authority_class": "DERIVED_SCAN_DESIGN_FEATURE_REGION_DIAGNOSTIC",
            "scan_master_changed": False,
            "parametric_model_filled_missing_scan_coverage": False,
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


def calculate_feature_deviation_report(
    scan_master: ScanMasterRevision,
    design_model: DesignModelRevision,
    full_geometry: DesignModelGeometryReference,
    regions: tuple[FeatureDeviationTarget, ...],
    *,
    expected_scan_master_revision_id: str,
    expected_scan_master_geometry_sha256: str,
    heatmap_policy: HeatmapPolicy = HeatmapPolicy(),
    adapter: Open3DGeometryAdapter | None = None,
) -> FeatureDeviationReport:
    """Report observed local Scan Master support against feature-scoped Design Model meshes.

    Region vertices and coverage are selected from the exact Scan Master only. The full
    parametric model and feature meshes are distance targets and never fill scan support.
    """

    if not isinstance(scan_master, ScanMasterRevision):
        raise DeviationReportError("scan_master_revision_required")
    if not isinstance(design_model, DesignModelRevision):
        raise DeviationReportError("design_model_revision_required")
    if not isinstance(full_geometry, DesignModelGeometryReference):
        raise DeviationReportError("design_model_geometry_reference_required")
    scan_digest = mesh_sha256(scan_master.mesh)
    if (
        expected_scan_master_revision_id != scan_master.revision_id
        or expected_scan_master_geometry_sha256 != scan_digest
        or design_model.fitted_to_scan_master_revision_id != scan_master.revision_id
        or design_model.scan_master_geometry_sha256 != scan_digest
    ):
        raise DeviationReportError("scan_master_parent_binding_mismatch")
    if (
        full_geometry.revision_id != design_model.revision_id
        or full_geometry.project_id != design_model.project_id
        or full_geometry.fitted_to_scan_master_revision_id != scan_master.revision_id
        or full_geometry.scale_state is not design_model.scale_state
        or full_geometry.scale_provenance_id != design_model.scale_provenance_id
        or full_geometry.physical_accuracy_validation_status
        != design_model.physical_accuracy_validation_status
        or full_geometry.mold_use_authorized is not False
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
        or any(not isinstance(item, FeatureDeviationTarget) for item in regions)
    ):
        raise DeviationReportError("feature_deviation_regions_invalid_or_unbounded")
    keys = tuple((item.feature_id, item.region_id) for item in regions)
    if len(keys) != len(set(keys)):
        raise DeviationReportError("feature_deviation_region_duplicate")

    try:
        heatmap = compute_scan_design_heatmap(
            scan_master, full_geometry, policy=heatmap_policy, adapter=adapter
        )
    except HeatmapError as error:
        raise DeviationReportError(f"heatmap_comparison_failed:{error}") from error
    if (
        heatmap.scan_master_revision_id != scan_master.revision_id
        or heatmap.scan_master_geometry_sha256 != scan_digest
        or heatmap.design_model_revision_id != design_model.revision_id
        or heatmap.design_model_geometry_sha256 != full_geometry.geometry_sha256
        or heatmap.scale_state is not design_model.scale_state
    ):
        raise DeviationReportError("heatmap_parent_binding_mismatch")

    backend = Open3DGeometryAdapter() if adapter is None else adapter
    manifest_gaps = scan_master.manifest.get("coverage_gaps")
    if isinstance(manifest_gaps, (tuple, list)) and any(
        not isinstance(item, str) or not item.strip() for item in manifest_gaps
    ):
        raise DeviationReportError("scan_master_coverage_gaps_invalid")
    coverage_metadata_known = isinstance(manifest_gaps, (tuple, list))
    declared_gaps = (
        tuple(item for item in manifest_gaps if isinstance(item, str))
        if isinstance(manifest_gaps, (tuple, list))
        else ()
    )
    region_rows: list[FeatureDeviationRegion] = []
    for target in regions:
        try:
            feature = resolve_design_model_feature(design_model, target.feature_id)
        except DesignModelError as error:
            raise DeviationReportError("feature_deviation_feature_stale_or_missing") from error
        if feature.feature_kind not in {FeatureKind.HANDLE_OPENING, FeatureKind.GRIP_INDENT}:
            raise DeviationReportError("feature_deviation_feature_kind_unsupported")
        geometry = target.geometry
        if (
            geometry.revision_id != design_model.revision_id
            or geometry.project_id != design_model.project_id
            or geometry.fitted_to_scan_master_revision_id != scan_master.revision_id
            or geometry.scale_state is not design_model.scale_state
            or geometry.scale_provenance_id != design_model.scale_provenance_id
            or geometry.physical_accuracy_validation_status
            != design_model.physical_accuracy_validation_status
            or geometry.mold_use_authorized is not False
            or not geometry.mesh.vertices
            or not geometry.mesh.triangles
        ):
            raise DeviationReportError("feature_geometry_binding_mismatch")
        local_vertices = tuple(
            point for point in scan_master.mesh.vertices if _in_bounds(point, target.bounds_xyz)
        )
        if len(local_vertices) > MAX_FEATURE_REGION_SAMPLES:
            raise DeviationReportError("feature_region_sample_bound_exceeded")
        observed_cells = _coverage_cells(local_vertices, target)
        resolution = target.coverage_grid_resolution
        coverage_ratio = len(observed_cells) / (resolution * resolution)
        distances: tuple[float, ...] = ()
        if local_vertices:
            try:
                result: MeshSurfaceDistanceOutput = backend.compute_mesh_surface_distances(
                    geometry.mesh,
                    PointCloudData(local_vertices),
                    signed=False,
                    maximum_query_points=MAX_FEATURE_REGION_SAMPLES,
                )
            except (GeometryAdapterError, RuntimeError, ValueError) as error:
                raise DeviationReportError("feature_region_distance_comparison_failed") from error
            if (
                result.signed
                or len(result.distances) != len(local_vertices)
                or any(not math.isfinite(value) or value < 0.0 for value in result.distances)
            ):
                raise DeviationReportError("feature_region_distance_result_invalid")
            distances = result.distances
        if not local_vertices:
            coverage_status = "MISSING_SCAN_COVERAGE"
        elif not coverage_metadata_known:
            coverage_status = "COVERAGE_METADATA_UNKNOWN"
        elif declared_gaps:
            coverage_status = "DECLARED_COVERAGE_GAPS_PRESENT"
        elif coverage_ratio < _LOCAL_COVERAGE_THRESHOLD:
            coverage_status = "PARTIAL_LOCAL_SCAN_SUPPORT"
        else:
            coverage_status = "OBSERVED_LOCAL_SCAN_SUPPORT"
        region_rows.append(
            FeatureDeviationRegion(
                0,
                feature.feature_id,
                feature.semantic_key,
                target.region_id,
                target.bounds_xyz,
                geometry.geometry_sha256,
                len(local_vertices),
                len(distances),
                float(sum(distances) / len(distances)) if distances else None,
                float(max(distances)) if distances else None,
                resolution,
                len(observed_cells),
                coverage_ratio,
                coverage_status,
                coverage_metadata_known,
                declared_gaps,
                heatmap.distance_units,
            )
        )
    ranked = sorted(
        region_rows,
        key=lambda item: (
            -(item.scan_to_design_maximum if item.scan_to_design_maximum is not None else -1.0),
            item.feature_id,
            item.region_id,
        ),
    )
    summaries = tuple(
        FeatureDeviationRegion(
            index,
            item.feature_id,
            item.feature_semantic_key,
            item.region_id,
            item.bounds_xyz,
            item.feature_geometry_sha256,
            item.scan_master_region_vertex_count,
            item.scan_to_design_sample_count,
            item.scan_to_design_mean,
            item.scan_to_design_maximum,
            item.coverage_grid_resolution,
            item.observed_coverage_cell_count,
            item.coverage_ratio,
            item.coverage_status,
            item.coverage_metadata_known,
            item.declared_coverage_gaps,
            item.units,
        )
        for index, item in enumerate(ranked, start=1)
    )
    units = (
        "reconstruction_units"
        if design_model.scale_state is ScaleState.RELATIVE
        else "mm_unverified"
    )
    report_body = {
        "contract": "packlab.feature-deviation-report.v1",
        "scan_master_revision_id": scan_master.revision_id,
        "scan_master_geometry_sha256": scan_digest,
        "design_model_revision_id": design_model.revision_id,
        "design_model_geometry_sha256": full_geometry.geometry_sha256,
        "global_heatmap_id": heatmap.heatmap_id,
        "scale_state": design_model.scale_state.value,
        "units": units,
        "regions": [item.as_dict() for item in summaries],
    }
    report_id = (
        "feature-deviation-report:"
        + hashlib.sha256(
            json.dumps(report_body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    return FeatureDeviationReport(
        report_id,
        scan_master.revision_id,
        scan_digest,
        design_model.revision_id,
        full_geometry.geometry_sha256,
        heatmap.heatmap_id,
        design_model.scale_state,
        units,
        summaries,
    )


def _region_bounds(value: object) -> tuple[float, float, float, float, float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 6:
        raise DeviationReportError("feature_region_bounds_invalid")
    numbers = tuple(
        _finite_deviation_value(item, "feature_region_bounds_invalid") for item in value
    )
    if any(numbers[axis * 2] >= numbers[axis * 2 + 1] for axis in range(3)):
        raise DeviationReportError("feature_region_bounds_invalid")
    return (numbers[0], numbers[1], numbers[2], numbers[3], numbers[4], numbers[5])


def _finite_deviation_value(value: object, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DeviationReportError(code)
    return float(value)


def _in_bounds(
    point: tuple[float, float, float], bounds: tuple[float, float, float, float, float, float]
) -> bool:
    return all(bounds[axis * 2] <= point[axis] <= bounds[axis * 2 + 1] for axis in range(3))


def _coverage_cells(
    points: tuple[tuple[float, float, float], ...], target: FeatureDeviationTarget
) -> set[tuple[int, int]]:
    axes = target.coverage_axes
    resolution = target.coverage_grid_resolution
    extents = tuple(target.bounds_xyz[axis * 2 + 1] - target.bounds_xyz[axis * 2] for axis in axes)
    cells: set[tuple[int, int]] = set()
    for point in points:
        indices = []
        for index, axis in enumerate(axes):
            normalized = (point[axis] - target.bounds_xyz[axis * 2]) / extents[index]
            indices.append(min(resolution - 1, max(0, int(normalized * resolution))))
        cells.add((indices[0], indices[1]))
    return cells


__all__ = [
    "MAX_FEATURE_COVERAGE_GRID",
    "MAX_FEATURE_REGION_SAMPLES",
    "MAX_DEVIATION_REGIONS",
    "DeviationRegion",
    "DeviationReportError",
    "DesignDeviationReport",
    "FeatureDeviationRegion",
    "FeatureDeviationReport",
    "FeatureDeviationTarget",
    "SectionDeviationTarget",
    "calculate_design_deviation_report",
    "calculate_feature_deviation_report",
]
