"""Evidence-bound, backend-neutral parametric local jerrycan grip/indent features."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from statistics import median

from .design_history import DesignEditCommand, EditTargetKind, create_edit_command
from .design_model import (
    DesignModelError,
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    ParameterType,
    revise_design_model_revision,
    stable_feature_id,
)
from .scan_master import ScanMasterRevision, mesh_sha256

MAX_INDENT_PROFILE_VERTICES = 64
MIN_RING_SUPPORT_POINTS = 8
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,95}$")

Point2 = tuple[float, float]
RegionBounds = tuple[float, float, float, float]


class GripIndentError(ValueError):
    """Raised when local indent evidence or a parametric feature is invalid."""


class GripIndentStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NO_INDENT = "NO_INDENT"


class GripIndentSide(StrEnum):
    FRONT = "front"
    BACK = "back"


@dataclass(frozen=True, slots=True)
class GripIndentEvidence:
    status: GripIndentStatus
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    design_model_revision_id: str
    parent_binding_revision_id: str
    body_feature_id: str
    region_id: str
    region_bounds: RegionBounds
    ring_width: float
    grid_resolution: int
    side: GripIndentSide
    support_point_count: int
    ring_support_point_count: int
    coverage_ratio: float
    observed_depth: float | None
    depth_envelope: tuple[float, float] | None
    evidence_sha256: str
    uncertainty_codes: tuple[str, ...]
    coordinate_unit: str
    physical_accuracy_validation_status: str = "DEFERRED_OWNER_VALIDATION"
    mold_use_authorized: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.jerrycan-grip-indent-evidence.v1",
            "status": self.status.value,
            "authority_class": "SCAN_MASTER_DERIVED_DESIGN_EVIDENCE",
            "parents": {
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "design_model_revision_id": self.design_model_revision_id,
                "parent_binding_revision_id": self.parent_binding_revision_id,
                "body_feature_id": self.body_feature_id,
            },
            "region_id": self.region_id,
            "region_bounds_xz": list(self.region_bounds),
            "ring_width": self.ring_width,
            "grid_resolution": self.grid_resolution,
            "side": self.side.value,
            "support": {
                "region_point_count": self.support_point_count,
                "ring_point_count": self.ring_support_point_count,
                "region_grid_coverage_ratio": self.coverage_ratio,
            },
            "observed_depth": self.observed_depth,
            "depth_envelope": list(self.depth_envelope) if self.depth_envelope else None,
            "evidence_sha256": self.evidence_sha256,
            "uncertainty_codes": list(self.uncertainty_codes),
            "coordinate_unit": self.coordinate_unit,
            "raw_scan_points_retained": False,
            "scan_master_replaced": False,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
        }


@dataclass(frozen=True, slots=True)
class JerrycanGripIndent:
    feature: DesignModelFeatureReference
    body_feature_id: str
    region_id: str
    region_bounds: RegionBounds
    profile: tuple[Point2, ...]
    depth: float
    depth_envelope: tuple[float, float]
    side: GripIndentSide
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    evidence_sha256: str
    coordinate_unit: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.jerrycan-grip-indent.v1",
            "authority_class": "DESIGN_MODEL_FEATURE",
            "feature": self.feature.as_dict(),
            "body_feature_id": self.body_feature_id,
            "region_id": self.region_id,
            "region_bounds_xz": list(self.region_bounds),
            "profile_xz": [list(point) for point in self.profile],
            "depth": self.depth,
            "depth_envelope": list(self.depth_envelope),
            "side": self.side.value,
            "scan_master_revision_id": self.scan_master_revision_id,
            "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
            "evidence_sha256": self.evidence_sha256,
            "coordinate_unit": self.coordinate_unit,
            "geometry_backend": None,
            "scan_master_mutated": False,
            "raw_scan_points_retained": False,
            "uncertainty_codes": [
                "localized_parametric_representation_only",
                "no_mold_ready_surface_detail_or_physical_accuracy_claim",
            ],
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        }


def measure_jerrycan_grip_indent_evidence(
    scan_master: ScanMasterRevision,
    model: DesignModelRevision,
    *,
    body_feature_id: str,
    region_id: str,
    region_bounds: RegionBounds,
    ring_width: float,
    side: GripIndentSide,
    grid_resolution: int = 4,
) -> GripIndentEvidence:
    """Measure bounded indentation support from captured surface vertices only."""

    region = _validate_region(region_bounds)
    ring = _positive(ring_width, "grip_indent_ring_width_invalid")
    if not isinstance(side, GripIndentSide):
        raise GripIndentError("grip_indent_side_invalid")
    if (
        isinstance(grid_resolution, bool)
        or not isinstance(grid_resolution, int)
        or not 3 <= grid_resolution <= 16
    ):
        raise GripIndentError("grip_indent_grid_resolution_invalid")
    if not isinstance(scan_master, ScanMasterRevision):
        raise GripIndentError("scan_master_revision_required")
    if (
        not isinstance(model, DesignModelRevision)
        or model.package_family is not PackageFamily.JERRYCAN
    ):
        raise GripIndentError("jerrycan_design_model_required")
    if not isinstance(region_id, str) or not _IDENTIFIER.fullmatch(region_id):
        raise GripIndentError("grip_indent_region_id_invalid")
    body = _resolve_body(model, body_feature_id)
    scan_digest = mesh_sha256(scan_master.mesh)
    _validate_scan_parent(scan_master, model, scan_digest)
    parent_binding_revision_id = model.parent_binding_revision_id
    if parent_binding_revision_id is None:
        raise GripIndentError("grip_indent_captured_parent_required")
    front_sign = _front_sign(model)
    side_sign = front_sign if side is GripIndentSide.FRONT else -front_sign

    manifest_gaps = scan_master.manifest.get("coverage_gaps")
    if isinstance(manifest_gaps, (tuple, list)) and any(
        not isinstance(item, str) or not item.strip() for item in manifest_gaps
    ):
        raise GripIndentError("scan_master_coverage_gaps_invalid")
    gaps_known = isinstance(manifest_gaps, (tuple, list))
    coverage_gaps: tuple[str, ...] = ()
    if isinstance(manifest_gaps, (tuple, list)):
        coverage_gaps = tuple(item for item in manifest_gaps if isinstance(item, str))

    x0, z0, x1, z1 = region
    outer_bounds = (x0 - ring, z0 - ring, x1 + ring, z1 + ring)
    vertices: tuple[tuple[float, float, float], ...] = tuple(
        (float(point[0]), float(point[1]), float(point[2]))
        for point in scan_master.mesh.vertices
        if side_sign * float(point[1]) > 0
        and outer_bounds[0] <= point[0] <= outer_bounds[2]
        and outer_bounds[1] <= point[2] <= outer_bounds[3]
    )
    inside = tuple(point for point in vertices if x0 <= point[0] <= x1 and z0 <= point[2] <= z1)
    outside = tuple(
        point for point in vertices if not (x0 <= point[0] <= x1 and z0 <= point[2] <= z1)
    )
    region_cells = _frontmost_cells(inside, region, side_sign, grid_resolution)
    ring_cells = _frontmost_cells(outside, outer_bounds, side_sign, grid_resolution + 2)
    coverage_ratio = len(region_cells) / (grid_resolution * grid_resolution)
    uncertainties: list[str] = []
    if not gaps_known:
        uncertainties.append("scan_master_coverage_metadata_missing")
    if coverage_gaps:
        uncertainties.append("scan_master_has_declared_coverage_gaps")
    if coverage_ratio < 0.75:
        uncertainties.append("local_region_surface_coverage_incomplete")
    if len(ring_cells) < MIN_RING_SUPPORT_POINTS:
        uncertainties.append("surrounding_surface_support_insufficient")

    observed_depth: float | None = None
    depth_envelope: tuple[float, float] | None = None
    if region_cells and ring_cells:
        reference = median(value for _cell, value in ring_cells)
        depths = tuple(reference - value for _cell, value in region_cells)
        if all(math.isfinite(value) for value in depths):
            observed_depth = float(median(depths))
            depth_envelope = (float(min(depths)), float(max(depths)))
            if depth_envelope[0] <= 0 < depth_envelope[1]:
                uncertainties.append("local_indent_depth_not_distinct_from_surface_support")
    if observed_depth is None or depth_envelope is None:
        status = GripIndentStatus.REVIEW_REQUIRED
        uncertainties.append("local_surface_depth_unavailable")
    elif depth_envelope[1] <= 0 and not uncertainties:
        status = GripIndentStatus.NO_INDENT
        uncertainties.append("no_positive_local_indent_observed")
    elif uncertainties:
        status = GripIndentStatus.REVIEW_REQUIRED
    elif depth_envelope[0] <= 0:
        status = GripIndentStatus.REVIEW_REQUIRED
        uncertainties.append("local_indent_depth_not_distinct_from_surface_support")
    else:
        status = GripIndentStatus.SUPPORTED

    point_digest = _support_digest(inside, outside, side_sign)
    evidence_sha256 = _evidence_digest(
        scan_master.revision_id,
        scan_digest,
        model.revision_id,
        body_feature_id,
        region_id,
        region,
        ring,
        grid_resolution,
        side,
        len(inside),
        len(outside),
        coverage_ratio,
        observed_depth,
        depth_envelope,
        point_digest,
        model.coordinate_unit,
    )
    return GripIndentEvidence(
        status,
        scan_master.revision_id,
        scan_digest,
        model.revision_id,
        parent_binding_revision_id,
        body.feature_id,
        region_id,
        region,
        ring,
        grid_resolution,
        side,
        len(inside),
        len(outside),
        coverage_ratio,
        observed_depth,
        depth_envelope,
        evidence_sha256,
        tuple(sorted(set(uncertainties))),
        model.coordinate_unit,
    )


def create_jerrycan_grip_indent(
    scan_master: ScanMasterRevision,
    model: DesignModelRevision,
    evidence: GripIndentEvidence,
    *,
    profile: Sequence[Sequence[float]],
    depth: float | None = None,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignModelRevision:
    """Add a parametric local indent only from reproducible supported Scan Master evidence."""

    if not isinstance(evidence, GripIndentEvidence):
        raise GripIndentError("grip_indent_evidence_required")
    if evidence.status is not GripIndentStatus.SUPPORTED or evidence.depth_envelope is None:
        raise GripIndentError("grip_indent_evidence_requires_review")
    reproduced = measure_jerrycan_grip_indent_evidence(
        scan_master,
        model,
        body_feature_id=evidence.body_feature_id,
        region_id=evidence.region_id,
        region_bounds=evidence.region_bounds,
        ring_width=evidence.ring_width,
        side=evidence.side,
        grid_resolution=evidence.grid_resolution,
    )
    if reproduced != evidence:
        raise GripIndentError("grip_indent_evidence_stale_or_mismatched")

    requested_depth = (
        evidence.observed_depth if depth is None else _finite(depth, "grip_indent_depth_invalid")
    )
    if requested_depth is None:
        raise GripIndentError("grip_indent_depth_unavailable")
    lower, upper = evidence.depth_envelope
    if requested_depth < lower or requested_depth > upper:
        raise GripIndentError("grip_indent_depth_outside_evidence_envelope")
    profile_points = _profile(profile, evidence.region_bounds)
    body = _resolve_body(model, evidence.body_feature_id)
    semantic_key = f"jerrycan-grip-indent:{evidence.region_id}"
    feature = DesignModelFeatureReference(
        stable_feature_id(body.component_id, FeatureKind.GRIP_INDENT, semantic_key),
        body.component_id,
        FeatureKind.GRIP_INDENT,
        semantic_key,
    )
    if any(item.feature_id == feature.feature_id for item in model.features):
        raise GripIndentError("grip_indent_feature_already_exists")
    parameters = _feature_parameters(
        evidence, profile_points, requested_depth, feature, model.coordinate_unit
    )
    try:
        return revise_design_model_revision(
            model,
            parameters=(*model.parameters, *parameters),
            features=(*model.features, feature),
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    except DesignModelError as error:
        raise GripIndentError("grip_indent_design_model_invalid") from error


def create_grip_indent_depth_edit(
    model: DesignModelRevision,
    feature_id: str,
    depth: float,
) -> DesignEditCommand:
    """Create a history command for a depth change inside the observed envelope."""

    definition, parameter_prefix = _resolve_feature(model, feature_id)
    value = _finite(depth, "grip_indent_depth_invalid")
    envelope = definition.get("depth_envelope")
    if not isinstance(envelope, list) or len(envelope) != 2:
        raise GripIndentError("grip_indent_definition_invalid")
    lower = _finite(envelope[0], "grip_indent_definition_invalid")
    upper = _finite(envelope[1], "grip_indent_definition_invalid")
    if lower > upper:
        raise GripIndentError("grip_indent_definition_invalid")
    if value < lower or value > upper:
        raise GripIndentError("grip_indent_depth_outside_evidence_envelope")
    parameter_id = f"{parameter_prefix}:depth"
    before = _parameter(model, parameter_id)
    after = DesignModelParameter(
        parameter_id,
        value,
        ParameterType.NUMBER,
        model.coordinate_unit,
    )
    return create_edit_command(
        model.revision_id,
        EditTargetKind.PARAMETER,
        parameter_id,
        before,
        after,
    )


def _feature_parameters(
    evidence: GripIndentEvidence,
    profile: tuple[Point2, ...],
    depth: float,
    feature: DesignModelFeatureReference,
    coordinate_unit: str,
) -> tuple[DesignModelParameter, ...]:
    prefix = _parameter_prefix(feature)
    definition = {
        "contract": "packlab.jerrycan-grip-indent-definition.v1",
        "feature_id": feature.feature_id,
        "body_feature_id": evidence.body_feature_id,
        "region_id": evidence.region_id,
        "region_bounds_xz": list(evidence.region_bounds),
        "ring_width": evidence.ring_width,
        "grid_resolution": evidence.grid_resolution,
        "side": evidence.side.value,
        "scan_master_revision_id": evidence.scan_master_revision_id,
        "scan_master_geometry_sha256": evidence.scan_master_geometry_sha256,
        "parent_binding_revision_id": evidence.parent_binding_revision_id,
        "evidence_sha256": evidence.evidence_sha256,
        "support_point_count": evidence.support_point_count,
        "ring_support_point_count": evidence.ring_support_point_count,
        "coverage_ratio": evidence.coverage_ratio,
        "observed_depth": evidence.observed_depth,
        "depth_envelope": list(evidence.depth_envelope or ()),
        "uncertainty_codes": list(evidence.uncertainty_codes),
        "authority_class": "DESIGN_MODEL_FEATURE_FROM_SCAN_MASTER_EVIDENCE",
        "raw_scan_points_retained": False,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "coordinate_unit": coordinate_unit,
    }
    return (
        DesignModelParameter(f"{prefix}:definition", definition, ParameterType.OBJECT),
        DesignModelParameter(
            f"{prefix}:region", list(evidence.region_bounds), ParameterType.ARRAY, coordinate_unit
        ),
        DesignModelParameter(
            f"{prefix}:profile",
            [list(point) for point in profile],
            ParameterType.ARRAY,
            coordinate_unit,
        ),
        DesignModelParameter(
            f"{prefix}:depth",
            depth,
            ParameterType.NUMBER,
            coordinate_unit,
        ),
        DesignModelParameter(
            f"{prefix}:depth_envelope",
            list(evidence.depth_envelope or ()),
            ParameterType.ARRAY,
            coordinate_unit,
        ),
    )


def _resolve_feature(model: DesignModelRevision, feature_id: str) -> tuple[dict[str, object], str]:
    if (
        not isinstance(model, DesignModelRevision)
        or model.package_family is not PackageFamily.JERRYCAN
    ):
        raise GripIndentError("jerrycan_design_model_required")
    feature = next(
        (
            item
            for item in model.features
            if item.feature_id == feature_id and item.feature_kind is FeatureKind.GRIP_INDENT
        ),
        None,
    )
    if feature is None:
        raise GripIndentError("grip_indent_feature_missing_or_stale")
    prefix = _parameter_prefix(feature)
    definition_parameter = _parameter(model, f"{prefix}:definition")
    definition_value = definition_parameter.as_dict()["value"]
    if not isinstance(definition_value, dict):
        raise GripIndentError("grip_indent_definition_invalid")
    body_feature_id = definition_value.get("body_feature_id")
    bodies = tuple(
        item
        for item in model.features
        if item.feature_id == body_feature_id and item.feature_kind is FeatureKind.BODY
    )
    if (
        definition_value.get("scan_master_revision_id") != model.fitted_to_scan_master_revision_id
        or definition_value.get("scan_master_geometry_sha256") != model.scan_master_geometry_sha256
        or definition_value.get("parent_binding_revision_id") != model.parent_binding_revision_id
        or definition_value.get("coordinate_unit") != model.coordinate_unit
        or len(bodies) != 1
        or bodies[0].component_id != feature.component_id
    ):
        raise GripIndentError("grip_indent_parent_binding_invalid")
    envelope = definition_value.get("depth_envelope")
    if not isinstance(envelope, list) or len(envelope) != 2:
        raise GripIndentError("grip_indent_definition_invalid")
    lower = _finite(envelope[0], "grip_indent_definition_invalid")
    upper = _finite(envelope[1], "grip_indent_definition_invalid")
    if lower > upper:
        raise GripIndentError("grip_indent_definition_invalid")
    for name in ("region", "profile", "depth", "depth_envelope"):
        parameter = _parameter(model, f"{prefix}:{name}")
        if parameter.unit != model.coordinate_unit:
            raise GripIndentError("grip_indent_unit_mismatch")
    return definition_value, prefix


def _parameter_prefix(feature: DesignModelFeatureReference) -> str:
    return f"grip-indent:{feature.feature_id.rsplit(':', 1)[-1]}"


def _parameter(model: DesignModelRevision, parameter_id: str) -> DesignModelParameter:
    matches = tuple(item for item in model.parameters if item.parameter_id == parameter_id)
    if len(matches) != 1:
        raise GripIndentError("grip_indent_parameter_missing_or_ambiguous")
    return matches[0]


def _resolve_body(model: DesignModelRevision, feature_id: str) -> DesignModelFeatureReference:
    matches = tuple(
        item
        for item in model.features
        if item.feature_id == feature_id and item.feature_kind is FeatureKind.BODY
    )
    if len(matches) != 1:
        raise GripIndentError("grip_indent_body_feature_missing_or_ambiguous")
    return matches[0]


def _validate_scan_parent(
    scan: ScanMasterRevision, model: DesignModelRevision, digest: str
) -> None:
    manifest = scan.manifest
    if (
        model.fitted_to_scan_master_revision_id != scan.revision_id
        or model.scan_master_geometry_sha256 != digest
        or manifest.get("scan_master_revision_id") != scan.revision_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != digest
        or manifest.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
        or manifest.get("mold_use_authorized") is not False
    ):
        raise GripIndentError("grip_indent_scan_master_parent_invalid")


def _front_sign(model: DesignModelRevision) -> float:
    matches = tuple(
        item for item in model.parameters if item.parameter_id == "jerrycan_section_frame"
    )
    if len(matches) != 1:
        raise GripIndentError("jerrycan_front_direction_missing_or_ambiguous")
    frame = matches[0].as_dict()["value"]
    if not isinstance(frame, dict):
        raise GripIndentError("jerrycan_section_frame_invalid")
    direction = frame.get("front_direction")
    if direction == "+y":
        return 1.0
    if direction == "-y":
        return -1.0
    raise GripIndentError("jerrycan_front_direction_invalid")


def _frontmost_cells(
    points: tuple[tuple[float, float, float], ...],
    bounds: RegionBounds,
    side_sign: float,
    resolution: int,
) -> tuple[tuple[tuple[int, int], float], ...]:
    x0, z0, x1, z1 = bounds
    cells: dict[tuple[int, int], float] = {}
    for x, y, z in points:
        ix = min(resolution - 1, max(0, int((x - x0) / (x1 - x0) * resolution)))
        iz = min(resolution - 1, max(0, int((z - z0) / (z1 - z0) * resolution)))
        cell = (ix, iz)
        surface = side_sign * y
        cells[cell] = max(cells.get(cell, -math.inf), surface)
    return tuple(sorted(cells.items()))


def _support_digest(
    inside: tuple[tuple[float, float, float], ...],
    outside: tuple[tuple[float, float, float], ...],
    side_sign: float,
) -> str:
    payload = {
        "contract": "packlab.grip-indent-support.v1",
        "region_samples": sorted(inside),
        "ring_samples": sorted(outside),
        "surface_sign": side_sign,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    ).hexdigest()


def _evidence_digest(
    scan_id: str,
    scan_digest: str,
    model_id: str,
    body_feature_id: str,
    region_id: str,
    region: RegionBounds,
    ring_width: float,
    grid_resolution: int,
    side: GripIndentSide,
    support_count: int,
    ring_count: int,
    coverage_ratio: float,
    observed_depth: float | None,
    depth_envelope: tuple[float, float] | None,
    support_digest: str,
    coordinate_unit: str,
) -> str:
    payload = {
        "contract": "packlab.jerrycan-grip-indent-evidence.v1",
        "scan_master_revision_id": scan_id,
        "scan_master_geometry_sha256": scan_digest,
        "design_model_revision_id": model_id,
        "body_feature_id": body_feature_id,
        "region_id": region_id,
        "region_bounds_xz": list(region),
        "ring_width": ring_width,
        "grid_resolution": grid_resolution,
        "side": side.value,
        "support_point_count": support_count,
        "ring_support_point_count": ring_count,
        "coverage_ratio": coverage_ratio,
        "observed_depth": observed_depth,
        "depth_envelope": list(depth_envelope) if depth_envelope else None,
        "support_digest": support_digest,
        "coordinate_unit": coordinate_unit,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    ).hexdigest()


def _validate_region(value: RegionBounds) -> RegionBounds:
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        raise GripIndentError("grip_indent_region_bounds_invalid")
    bounds = tuple(_finite(item, "grip_indent_region_bounds_invalid") for item in value)
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise GripIndentError("grip_indent_region_bounds_invalid")
    return bounds  # type: ignore[return-value]


def _profile(value: Sequence[Sequence[float]], bounds: RegionBounds) -> tuple[Point2, ...]:
    if not isinstance(value, (tuple, list)) or not 3 <= len(value) <= MAX_INDENT_PROFILE_VERTICES:
        raise GripIndentError("grip_indent_profile_vertex_count_invalid")
    points: list[Point2] = []
    for point in value:
        if not isinstance(point, (tuple, list)) or len(point) != 2:
            raise GripIndentError("grip_indent_profile_point_invalid")
        points.append(
            (
                _finite(point[0], "grip_indent_profile_point_invalid"),
                _finite(point[1], "grip_indent_profile_point_invalid"),
            )
        )
    profile = tuple(points)
    if len(set(profile)) != len(profile):
        raise GripIndentError("grip_indent_profile_duplicate_point")
    x0, z0, x1, z1 = bounds
    if any(x < x0 or x > x1 or z < z0 or z > z1 for x, z in profile):
        raise GripIndentError("grip_indent_profile_outside_region")
    twice_area = sum(
        x0_ * z1_ - x1_ * z0_
        for (x0_, z0_), (x1_, z1_) in zip(profile, (*profile[1:], profile[0]), strict=True)
    )
    if abs(twice_area) <= 1e-12 or _self_intersects(profile):
        raise GripIndentError("grip_indent_profile_invalid_or_self_intersecting")
    return profile


def _self_intersects(points: tuple[Point2, ...]) -> bool:
    edges = tuple(zip(points, (*points[1:], points[0]), strict=True))
    for first in range(len(edges)):
        for second in range(first + 1, len(edges)):
            if second == first + 1 or (first == 0 and second == len(edges) - 1):
                continue
            if _segments_intersect(*edges[first], *edges[second]):
                return True
    return False


def _segments_intersect(a: Point2, b: Point2, c: Point2, d: Point2) -> bool:
    def orientation(p: Point2, q: Point2, r: Point2) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def on_segment(p: Point2, q: Point2, r: Point2) -> bool:
        return min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and min(p[1], r[1]) <= q[1] <= max(
            p[1], r[1]
        )

    values = (
        orientation(a, b, c),
        orientation(a, b, d),
        orientation(c, d, a),
        orientation(c, d, b),
    )
    ab_c, ab_d, cd_a, cd_b = values
    if ab_c * ab_d < 0 and cd_a * cd_b < 0:
        return True
    epsilon = 1e-12
    return (
        abs(ab_c) <= epsilon
        and on_segment(a, c, b)
        or abs(ab_d) <= epsilon
        and on_segment(a, d, b)
        or abs(cd_a) <= epsilon
        and on_segment(c, a, d)
        or abs(cd_b) <= epsilon
        and on_segment(c, b, d)
    )


def _finite(value: object, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GripIndentError(code)
    result = float(value)
    if not math.isfinite(result):
        raise GripIndentError(code)
    return result


def _positive(value: object, code: str) -> float:
    result = _finite(value, code)
    if result <= 0:
        raise GripIndentError(code)
    return result


__all__ = [
    "GripIndentEvidence",
    "GripIndentError",
    "GripIndentSide",
    "GripIndentStatus",
    "JerrycanGripIndent",
    "create_grip_indent_depth_edit",
    "create_jerrycan_grip_indent",
    "measure_jerrycan_grip_indent_evidence",
]
