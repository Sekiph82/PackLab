"""Bounded PREVIEW_PROXY AABB diagnostics for exact parametric assemblies."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum

from .assembly_graph import (
    AssemblyComponentInput,
    AssemblyComponentReference,
    AssemblyComponentRole,
    AssemblyGraphError,
    ParametricAssemblyGraph,
    validate_parametric_assembly_graph,
)
from .design_model import DesignModelRevision, FeatureKind, resolve_design_model_feature
from .design_preview import MAX_PREVIEW_VERTICES, PREVIEW_AUTHORITY, DesignPreview
from .dip_tube import DipTubeComponentRevision
from .reconstruction import ScaleState

_EPSILON = 1e-8
_MAX_COORDINATE = 1e9
_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_ROLES = tuple(sorted(AssemblyComponentRole, key=lambda role: role.value))


class AssemblyClearanceError(ValueError):
    """Raised when assembly inputs, placement pins, or proxies are invalid."""


class PairDiagnosticStatus(StrEnum):
    CANDIDATE_OVERLAP = "CANDIDATE_OVERLAP"
    NEAR_CLEARANCE = "NEAR_CLEARANCE"
    CLEARANCE = "CLEARANCE"
    UNKNOWN_PROXY_UNSUPPORTED = "UNKNOWN_PROXY_UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class AssemblyComponentPlacement:
    """Explicit rigid transform pinned to one current assembly graph component."""

    role: AssemblyComponentRole
    model_revision_id: str
    feature_id: str
    placement_revision_id: str
    transform: tuple[float, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.role, AssemblyComponentRole):
            raise AssemblyClearanceError("assembly_placement_role_invalid")
        for value, field in (
            (self.model_revision_id, "model_revision_id"),
            (self.feature_id, "feature_id"),
            (self.placement_revision_id, "placement_revision_id"),
        ):
            if not isinstance(value, str) or not _ID.fullmatch(value):
                raise AssemblyClearanceError(f"assembly_placement_{field}_invalid")
        _validate_rigid_transform(self.transform)

    def as_dict(self) -> dict[str, object]:
        return {
            "role": self.role.value,
            "model_revision_id": self.model_revision_id,
            "feature_id": self.feature_id,
            "placement_revision_id": self.placement_revision_id,
            "transform_convention": "row_major_4x4_column_vectors_v1",
            "matrix": list(self.transform),
        }


@dataclass(frozen=True, slots=True)
class AssemblyComponentProxy:
    """One exact feature AABB derived from a PREVIEW_PROXY mesh or explicitly unsupported."""

    role: AssemblyComponentRole
    model_revision_id: str
    feature_id: str
    parent_binding_revision_id: str
    scan_master_revision_id: str
    scan_master_geometry_sha256: str
    scale_state: ScaleState
    coordinate_unit: str
    bounds_min: tuple[float, float, float] | None
    bounds_max: tuple[float, float, float] | None
    unsupported_reason: str | None = None
    authority_class: str = PREVIEW_AUTHORITY

    def __post_init__(self) -> None:
        if not isinstance(self.role, AssemblyComponentRole):
            raise AssemblyClearanceError("assembly_proxy_role_invalid")
        if self.authority_class != PREVIEW_AUTHORITY:
            raise AssemblyClearanceError("assembly_proxy_authority_invalid")
        for value, field in (
            (self.model_revision_id, "model_revision_id"),
            (self.feature_id, "feature_id"),
            (self.parent_binding_revision_id, "parent_binding_revision_id"),
            (self.scan_master_revision_id, "scan_master_revision_id"),
        ):
            if not isinstance(value, str) or not _ID.fullmatch(value):
                raise AssemblyClearanceError(f"assembly_proxy_{field}_invalid")
        if not re.fullmatch(r"[0-9a-f]{64}", self.scan_master_geometry_sha256):
            raise AssemblyClearanceError("assembly_proxy_scan_master_digest_invalid")
        if self.scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}:
            raise AssemblyClearanceError("assembly_proxy_scale_state_invalid")
        expected_unit = (
            "reconstruction_units" if self.scale_state is ScaleState.RELATIVE else "mm_unverified"
        )
        if self.coordinate_unit != expected_unit:
            raise AssemblyClearanceError("assembly_proxy_unit_mismatch")
        if self.bounds_min is None or self.bounds_max is None:
            if (
                self.bounds_min is not None
                or self.bounds_max is not None
                or not isinstance(self.unsupported_reason, str)
                or not self.unsupported_reason.strip()
                or len(self.unsupported_reason) > 200
            ):
                raise AssemblyClearanceError("assembly_proxy_unsupported_reason_required")
        else:
            minimum = _point(self.bounds_min, "proxy_bounds_min")
            maximum = _point(self.bounds_max, "proxy_bounds_max")
            if any(minimum[index] > maximum[index] for index in range(3)):
                raise AssemblyClearanceError("assembly_proxy_bounds_invalid")
            object.__setattr__(self, "bounds_min", minimum)
            object.__setattr__(self, "bounds_max", maximum)
            if self.unsupported_reason is not None:
                raise AssemblyClearanceError("assembly_proxy_supported_reason_conflict")

    @classmethod
    def from_preview(
        cls,
        role: AssemblyComponentRole,
        model: DesignModelRevision,
        feature_id: str,
        preview: DesignPreview,
    ) -> AssemblyComponentProxy:
        if not isinstance(role, AssemblyComponentRole):
            raise AssemblyClearanceError("assembly_proxy_role_invalid")
        if not isinstance(model, DesignModelRevision):
            raise AssemblyClearanceError("assembly_proxy_design_model_required")
        if not isinstance(preview, DesignPreview) or preview.authority_class != PREVIEW_AUTHORITY:
            raise AssemblyClearanceError("assembly_preview_proxy_required")
        if (
            preview.model_revision_id != model.revision_id
            or preview.scan_master_revision_id != model.fitted_to_scan_master_revision_id
            or preview.scan_master_geometry_sha256 != model.scan_master_geometry_sha256
            or preview.parent_binding_revision_id != model.parent_binding_revision_id
            or preview.scale_state is not model.scale_state
            or preview.coordinate_unit != model.coordinate_unit
            or preview.physical_accuracy_validation_status != _DEFERRED
            or preview.mold_use_authorized is not False
        ):
            raise AssemblyClearanceError("assembly_preview_parent_or_authority_mismatch")
        try:
            feature = resolve_design_model_feature(model, feature_id)
        except ValueError as error:
            raise AssemblyClearanceError("assembly_proxy_feature_stale") from error
        if feature.feature_kind is not _ROLE_FEATURE_KIND[role]:
            raise AssemblyClearanceError("assembly_proxy_feature_kind_mismatch")
        feature_map = preview.feature_vertex_indices
        feature_ids = tuple(item[0] for item in feature_map)
        if len(feature_ids) != len(set(feature_ids)):
            raise AssemblyClearanceError("assembly_preview_feature_mapping_ambiguous")
        indices = dict(feature_map).get(feature_id)
        if (
            not indices
            or not isinstance(indices, tuple)
            or len(indices) > MAX_PREVIEW_VERTICES
            or len(preview.mesh.vertices) > MAX_PREVIEW_VERTICES
            or any(isinstance(index, bool) or not isinstance(index, int) for index in indices)
            or len(set(indices)) != len(indices)
        ):
            raise AssemblyClearanceError("assembly_preview_feature_proxy_missing")
        if any(
            isinstance(index, bool) or index < 0 or index >= len(preview.mesh.vertices)
            for index in indices
        ):
            raise AssemblyClearanceError("assembly_preview_feature_indices_invalid")
        vertices = tuple(preview.mesh.vertices[index] for index in indices)
        minimum = _point(
            tuple(min(point[axis] for point in vertices) for axis in range(3)),
            "proxy_bounds_min",
        )
        maximum = _point(
            tuple(max(point[axis] for point in vertices) for axis in range(3)),
            "proxy_bounds_max",
        )
        return cls(
            role,
            model.revision_id,
            feature_id,
            model.parent_binding_revision_id,
            model.fitted_to_scan_master_revision_id,
            model.scan_master_geometry_sha256,
            model.scale_state,
            model.coordinate_unit,
            minimum,
            maximum,
        )

    @classmethod
    def unsupported(
        cls,
        role: AssemblyComponentRole,
        model: DesignModelRevision,
        feature_id: str,
        reason: str,
    ) -> AssemblyComponentProxy:
        if not isinstance(role, AssemblyComponentRole):
            raise AssemblyClearanceError("assembly_proxy_role_invalid")
        if not isinstance(model, DesignModelRevision):
            raise AssemblyClearanceError("assembly_proxy_design_model_required")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 200:
            raise AssemblyClearanceError("assembly_proxy_unsupported_reason_invalid")
        try:
            feature = resolve_design_model_feature(model, feature_id)
        except ValueError as error:
            raise AssemblyClearanceError("assembly_proxy_feature_stale") from error
        if feature.feature_kind is not _ROLE_FEATURE_KIND[role]:
            raise AssemblyClearanceError("assembly_proxy_feature_kind_mismatch")
        return cls(
            role,
            model.revision_id,
            feature_id,
            model.parent_binding_revision_id,
            model.fitted_to_scan_master_revision_id,
            model.scan_master_geometry_sha256,
            model.scale_state,
            model.coordinate_unit,
            None,
            None,
            reason.strip(),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "role": self.role.value,
            "model_revision_id": self.model_revision_id,
            "feature_id": self.feature_id,
            "parent_binding_revision_id": self.parent_binding_revision_id,
            "scan_master_revision_id": self.scan_master_revision_id,
            "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "authority_class": self.authority_class,
            "bounds_min": list(self.bounds_min) if self.bounds_min is not None else None,
            "bounds_max": list(self.bounds_max) if self.bounds_max is not None else None,
            "unsupported_reason": self.unsupported_reason,
        }


@dataclass(frozen=True, slots=True)
class PairClearanceDiagnostic:
    first_role: AssemblyComponentRole
    second_role: AssemblyComponentRole
    status: str
    clearance_estimate: float | None
    overlap_depth_estimate: float | None
    estimate_kind: str
    unsupported_roles: tuple[AssemblyComponentRole, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "pair": [self.first_role.value, self.second_role.value],
            "status": self.status,
            "clearance_estimate": self.clearance_estimate,
            "overlap_depth_estimate": self.overlap_depth_estimate,
            "estimate_kind": self.estimate_kind,
            "unsupported_roles": [role.value for role in self.unsupported_roles],
            "certified_fit_claimed": False,
            "manufacturing_interference_claimed": False,
        }


@dataclass(frozen=True, slots=True)
class AssemblyClearanceDiagnosticRevision:
    revision_id: str
    assembly_graph_revision_id: str
    component_revision_ids: tuple[tuple[AssemblyComponentRole, str], ...]
    placements: tuple[AssemblyComponentPlacement, ...]
    proxies: tuple[AssemblyComponentProxy, ...]
    pair_diagnostics: tuple[PairClearanceDiagnostic, ...]
    clearance_tolerance: float
    scale_state: ScaleState
    coordinate_unit: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.assembly-clearance-diagnostic.v1",
            "revision_id": self.revision_id,
            "assembly_graph_revision_id": self.assembly_graph_revision_id,
            "component_revision_ids": [
                {"role": role.value, "model_revision_id": revision}
                for role, revision in self.component_revision_ids
            ],
            "placements": [item.as_dict() for item in self.placements],
            "proxies": [item.as_dict() for item in self.proxies],
            "pairs": [item.as_dict() for item in self.pair_diagnostics],
            "clearance_tolerance": self.clearance_tolerance,
            "coordinate_unit": self.coordinate_unit,
            "scale_state": self.scale_state.value,
            "physical_accuracy_validation_status": _DEFERRED,
            "mold_use_authorized": False,
            "authority_class": "ASSEMBLY_DIAGNOSTIC_PREVIEW_ONLY",
            "certified_fit_claimed": False,
            "manufacturing_interference_claimed": False,
            "collision_result_is_candidate_only": True,
        }


_ROLE_FEATURE_KIND = {
    AssemblyComponentRole.BODY: FeatureKind.BODY,
    AssemblyComponentRole.CLOSURE: FeatureKind.CAP,
    AssemblyComponentRole.TRIGGER_PUMP: FeatureKind.TRIGGER_PUMP,
    AssemblyComponentRole.DIP_TUBE: FeatureKind.DIP_TUBE,
}


def diagnose_assembly_clearance(
    graph: ParametricAssemblyGraph,
    current_components: tuple[AssemblyComponentInput, ...],
    dip_tube: DipTubeComponentRevision,
    placements: tuple[AssemblyComponentPlacement, ...],
    proxies: tuple[AssemblyComponentProxy, ...],
    *,
    clearance_tolerance: float,
) -> AssemblyClearanceDiagnosticRevision:
    """Return conservative AABB candidates without changing placements or component geometry."""
    try:
        validate_parametric_assembly_graph(graph, current_components)
    except AssemblyGraphError as error:
        raise AssemblyClearanceError(str(error)) from error
    if not isinstance(dip_tube, DipTubeComponentRevision):
        raise AssemblyClearanceError("dip_tube_component_required")
    if (
        isinstance(clearance_tolerance, bool)
        or not isinstance(clearance_tolerance, (int, float))
        or not math.isfinite(clearance_tolerance)
        or clearance_tolerance > _MAX_COORDINATE
        or clearance_tolerance < 0.0
    ):
        raise AssemblyClearanceError("clearance_tolerance_invalid")
    graph_refs = {item.role: item for item in graph.components}
    current = {item.role: item for item in current_components}
    if (
        dip_tube.revision_id != graph_refs[AssemblyComponentRole.DIP_TUBE].model_revision_id
        or dip_tube.feature_id != graph_refs[AssemblyComponentRole.DIP_TUBE].feature_id
        or dip_tube.attachment.trigger_pump_model_revision_id
        != graph_refs[AssemblyComponentRole.TRIGGER_PUMP].model_revision_id
        or dip_tube.attachment.trigger_pump_feature_id
        != graph_refs[AssemblyComponentRole.TRIGGER_PUMP].feature_id
        or current[AssemblyComponentRole.DIP_TUBE].model.revision_id != dip_tube.revision_id
    ):
        raise AssemblyClearanceError("dip_tube_assembly_reference_stale")
    if (
        not isinstance(placements, tuple)
        or len(placements) != len(_ROLES)
        or any(not isinstance(item, AssemblyComponentPlacement) for item in placements)
        or {item.role for item in placements} != set(_ROLES)
    ):
        raise AssemblyClearanceError("assembly_placements_must_pin_each_role_once")
    ordered_placements = tuple(sorted(placements, key=lambda item: item.role.value))
    for placement in ordered_placements:
        reference = graph_refs[placement.role]
        if (
            placement.model_revision_id != reference.model_revision_id
            or placement.feature_id != reference.feature_id
        ):
            raise AssemblyClearanceError("assembly_placement_component_pin_stale")
    if (
        not isinstance(proxies, tuple)
        or any(not isinstance(item, AssemblyComponentProxy) for item in proxies)
        or len({item.role for item in proxies}) != len(proxies)
        or AssemblyComponentRole.DIP_TUBE in {item.role for item in proxies}
        or {item.role for item in proxies}
        != {
            AssemblyComponentRole.BODY,
            AssemblyComponentRole.CLOSURE,
            AssemblyComponentRole.TRIGGER_PUMP,
        }
    ):
        raise AssemblyClearanceError("assembly_component_proxies_must_pin_non_tube_roles")
    ordered_proxies = tuple(sorted(proxies, key=lambda item: item.role.value))
    for proxy in ordered_proxies:
        reference = graph_refs[proxy.role]
        if (
            proxy.model_revision_id != reference.model_revision_id
            or proxy.feature_id != reference.feature_id
            or proxy.parent_binding_revision_id != reference.parent_binding_revision_id
            or proxy.scan_master_revision_id != reference.scan_master_revision_id
            or proxy.scan_master_geometry_sha256 != reference.scan_master_geometry_sha256
            or proxy.scale_state is not reference.scale_state
            or proxy.coordinate_unit != reference.coordinate_unit
        ):
            raise AssemblyClearanceError("assembly_proxy_component_pin_stale_or_incompatible")

    placement_by_role = {item.role: item for item in ordered_placements}
    proxy_bounds: dict[
        AssemblyComponentRole, tuple[tuple[float, float, float], tuple[float, float, float]] | None
    ] = {}
    for proxy in ordered_proxies:
        if proxy.bounds_min is None or proxy.bounds_max is None:
            proxy_bounds[proxy.role] = None
            continue
        proxy_bounds[proxy.role] = _transform_bounds(
            proxy.bounds_min, proxy.bounds_max, placement_by_role[proxy.role].transform
        )
    tube_local_bounds = _dip_tube_local_bounds(dip_tube)
    proxy_bounds[AssemblyComponentRole.DIP_TUBE] = _transform_bounds(
        tube_local_bounds[0],
        tube_local_bounds[1],
        placement_by_role[AssemblyComponentRole.DIP_TUBE].transform,
    )
    all_proxies = tuple(
        sorted(
            (
                *ordered_proxies,
                _dip_tube_proxy_reference(
                    graph_refs[AssemblyComponentRole.DIP_TUBE], tube_local_bounds
                ),
            ),
            key=lambda item: item.role.value,
        )
    )
    pairs: list[PairClearanceDiagnostic] = []
    for first_role, second_role in itertools.combinations(_ROLES, 2):
        first = proxy_bounds[first_role]
        second = proxy_bounds[second_role]
        unsupported = tuple(
            role for role, bounds in ((first_role, first), (second_role, second)) if bounds is None
        )
        if unsupported:
            pairs.append(
                PairClearanceDiagnostic(
                    first_role,
                    second_role,
                    PairDiagnosticStatus.UNKNOWN_PROXY_UNSUPPORTED,
                    None,
                    None,
                    "UNSUPPORTED_PREVIEW_PROXY",
                    unsupported,
                )
            )
            continue
        assert first is not None and second is not None
        clearance, overlap = _box_distance(first, second)
        if overlap > 0.0:
            status = PairDiagnosticStatus.CANDIDATE_OVERLAP
        elif clearance <= float(clearance_tolerance):
            status = PairDiagnosticStatus.NEAR_CLEARANCE
        else:
            status = PairDiagnosticStatus.CLEARANCE
        pairs.append(
            PairClearanceDiagnostic(
                first_role,
                second_role,
                status,
                clearance,
                overlap if overlap > 0.0 else None,
                "PREVIEW_AABB_DISTANCE_ESTIMATE",
                (),
            )
        )
    component_ids = tuple((role, graph_refs[role].model_revision_id) for role in _ROLES)
    identity = {
        "contract": "packlab.assembly-clearance-diagnostic.v1",
        "assembly_graph_revision_id": graph.revision_id,
        "component_revision_ids": [(role.value, revision) for role, revision in component_ids],
        "placements": [item.as_dict() for item in ordered_placements],
        "proxies": [item.as_dict() for item in all_proxies],
        "pair_diagnostics": [item.as_dict() for item in pairs],
        "clearance_tolerance": float(clearance_tolerance),
        "scale_state": graph.scale_state.value,
        "coordinate_unit": graph.coordinate_unit,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return AssemblyClearanceDiagnosticRevision(
        "assembly-clearance:" + digest,
        graph.revision_id,
        component_ids,
        ordered_placements,
        all_proxies,
        tuple(pairs),
        float(clearance_tolerance),
        graph.scale_state,
        graph.coordinate_unit,
    )


def _dip_tube_proxy_reference(
    reference: AssemblyComponentReference,
    bounds: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> AssemblyComponentProxy:
    return AssemblyComponentProxy(
        reference.role,
        reference.model_revision_id,
        reference.feature_id,
        reference.parent_binding_revision_id,
        reference.scan_master_revision_id,
        reference.scan_master_geometry_sha256,
        reference.scale_state,
        reference.coordinate_unit,
        bounds[0],
        bounds[1],
    )


def _dip_tube_local_bounds(
    tube: DipTubeComponentRevision,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    # Every Bezier curve lies in its control hull; these expanded bounds enclose the tube proxy.
    control_points = tuple(
        point for segment in tube.path.segments for point in segment.control_points
    )
    radius = float(tube.diameter) / 2.0
    return (
        _point(
            tuple(min(point[axis] for point in control_points) - radius for axis in range(3)),
            "dip_tube_proxy_bounds_min",
        ),
        _point(
            tuple(max(point[axis] for point in control_points) + radius for axis in range(3)),
            "dip_tube_proxy_bounds_max",
        ),
    )


def _transform_bounds(
    minimum: tuple[float, float, float],
    maximum: tuple[float, float, float],
    transform: tuple[float, ...],
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    corners = tuple(
        _transform_point((x, y, z), transform)
        for x in (minimum[0], maximum[0])
        for y in (minimum[1], maximum[1])
        for z in (minimum[2], maximum[2])
    )
    return (
        _point(
            tuple(min(point[axis] for point in corners) for axis in range(3)),
            "proxy_world_bounds_min",
        ),
        _point(
            tuple(max(point[axis] for point in corners) for axis in range(3)),
            "proxy_world_bounds_max",
        ),
    )


def _transform_point(
    point: tuple[float, float, float], transform: tuple[float, ...]
) -> tuple[float, float, float]:
    return tuple(
        math.fsum(transform[row * 4 + column] * point[column] for column in range(3))
        + transform[row * 4 + 3]
        for row in range(3)
    )  # type: ignore[return-value]


def _box_distance(
    first: tuple[tuple[float, float, float], tuple[float, float, float]],
    second: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> tuple[float, float]:
    gaps = tuple(
        max(first[0][axis] - second[1][axis], second[0][axis] - first[1][axis], 0.0)
        for axis in range(3)
    )
    overlaps = tuple(
        min(first[1][axis], second[1][axis]) - max(first[0][axis], second[0][axis])
        for axis in range(3)
    )
    if all(value >= 0.0 for value in overlaps):
        return 0.0, min(overlaps)
    return math.sqrt(math.fsum(value * value for value in gaps)), 0.0


def _point(point: object, field: str) -> tuple[float, float, float]:
    if (
        not isinstance(point, tuple)
        or len(point) != 3
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or abs(value) > _MAX_COORDINATE
            for value in point
        )
    ):
        raise AssemblyClearanceError(f"{field}_invalid")
    return tuple(float(value) for value in point)  # type: ignore[return-value]


def _validate_rigid_transform(transform: tuple[float, ...]) -> None:
    if (
        not isinstance(transform, tuple)
        or len(transform) != 16
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or abs(value) > _MAX_COORDINATE
            for value in transform
        )
    ):
        raise AssemblyClearanceError("assembly_placement_transform_invalid")
    if any(
        abs(transform[index] - expected) > _EPSILON
        for index, expected in ((12, 0.0), (13, 0.0), (14, 0.0), (15, 1.0))
    ):
        raise AssemblyClearanceError("assembly_placement_transform_not_affine")
    axes = tuple(
        tuple(float(transform[row * 4 + column]) for row in range(3)) for column in range(3)
    )
    for first, second in itertools.combinations(axes, 2):
        if abs(math.fsum(first[index] * second[index] for index in range(3))) > _EPSILON:
            raise AssemblyClearanceError("assembly_placement_transform_not_rigid")
    if any(
        abs(math.sqrt(math.fsum(value * value for value in axis)) - 1.0) > _EPSILON for axis in axes
    ):
        raise AssemblyClearanceError("assembly_placement_transform_not_rigid")
    determinant = (
        transform[0] * (transform[5] * transform[10] - transform[6] * transform[9])
        - transform[1] * (transform[4] * transform[10] - transform[6] * transform[8])
        + transform[2] * (transform[4] * transform[9] - transform[5] * transform[8])
    )
    if abs(determinant - 1.0) > _EPSILON:
        raise AssemblyClearanceError("assembly_placement_transform_not_proper_rotation")


__all__ = [
    "AssemblyClearanceDiagnosticRevision",
    "AssemblyClearanceError",
    "AssemblyComponentPlacement",
    "AssemblyComponentProxy",
    "PairClearanceDiagnostic",
    "PairDiagnosticStatus",
    "diagnose_assembly_clearance",
]
