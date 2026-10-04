"""Deterministic canonical-plane sections derived from exact CAD BREP inputs."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .cad_adapter import (
    CadAdapterError,
    CadProjectedCurveData,
    CadSectionResultData,
    section_cad_shape,
)
from .cad_brep import CadBrepRepresentationRevision
from .cad_feature_map import map_design_model_features_to_brep
from .cad_validation import validate_cad_brep
from .design_model import DesignModelRevision
from .reconstruction import ScaleState

SECTION_VIEW_MODEL_CONTRACT = "packlab.technical-drawing-section-view.v1"
_MAX_COMPONENTS = 16
_MAX_EDGES_PER_COMPONENT = 4096
_ROUND_DIGITS = 12
_SECTION_FRAMES: dict[
    str,
    tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ],
] = {
    "X": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "Y": ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "Z": ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
}


class DrawingSectionError(ValueError):
    """Raised when section inputs or CAD intersections are invalid."""


@dataclass(frozen=True, slots=True)
class DrawingSectionSource:
    """One explicitly supplied source component and its exact model/BREP revisions."""

    component_reference_id: str
    coordinate_frame_id: str
    placement_revision_id: str
    placement_matrix: tuple[float, ...]
    model: DesignModelRevision
    representation: CadBrepRepresentationRevision


@dataclass(frozen=True, slots=True)
class DrawingSectionCurve:
    curve_id: str
    component_reference_id: str
    curve_type: str
    points: tuple[tuple[float, float], ...]
    feature_lineage_status: str = "UNRESOLVED_EDGE_TO_FEATURE_ASSOCIATION"

    def as_dict(self) -> dict[str, object]:
        return {
            "curve_id": self.curve_id,
            "component_reference_id": self.component_reference_id,
            "curve_type": self.curve_type,
            "points": [list(point) for point in self.points],
            "feature_lineage_status": self.feature_lineage_status,
            "native_topology_id_used_as_authority": False,
        }


@dataclass(frozen=True, slots=True)
class DrawingSectionComponent:
    component_reference_id: str
    coordinate_frame_id: str
    placement_revision_id: str
    placement_matrix: tuple[float, ...]
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    parent_kind: str
    parent_authority_revision_id: str
    feature_mapping_revision_id: str
    feature_references: tuple[dict[str, object], ...]
    intersected: bool
    bounds: tuple[float, float, float, float] | None
    curves: tuple[DrawingSectionCurve, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "component_reference_id": self.component_reference_id,
            "coordinate_frame_id": self.coordinate_frame_id,
            "placement_revision_id": self.placement_revision_id,
            "placement_matrix_row_major_4x4": list(self.placement_matrix),
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_brep_geometry_sha256": self.source_brep_geometry_sha256,
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "feature_mapping_revision_id": self.feature_mapping_revision_id,
            "feature_references": list(self.feature_references),
            "intersected": self.intersected,
            "bounds": list(self.bounds) if self.bounds is not None else None,
            "curves": [curve.as_dict() for curve in self.curves],
        }


@dataclass(frozen=True, slots=True)
class DrawingSectionViewModel:
    revision_id: str
    plane_axis: str
    plane_offset: float
    plane_origin: tuple[float, float, float]
    plane_normal: tuple[float, float, float]
    screen_right: tuple[float, float, float]
    screen_up: tuple[float, float, float]
    scale_state: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    bounds: tuple[float, float, float, float] | None
    components: tuple[DrawingSectionComponent, ...]
    curves: tuple[DrawingSectionCurve, ...]
    hatching_status: str = "NOT_DERIVED_CLOSED_LOOP_CLASSIFICATION_UNAVAILABLE"
    hatching_regions: tuple[dict[str, object], ...] = ()
    placement_policy: str = "EXPLICIT_RIGID_COMPONENT_TRANSFORMS"
    contract: str = SECTION_VIEW_MODEL_CONTRACT

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "DERIVED_TECHNICAL_DRAWING_SECTION_VIEW",
            "revision_id": self.revision_id,
            "plane": {
                "definition": "CANONICAL_AXIS_ALIGNED",
                "axis": self.plane_axis,
                "offset": self.plane_offset,
                "origin_canonical_xyz": list(self.plane_origin),
                "normal_canonical_xyz": list(self.plane_normal),
            },
            "screen_right_canonical_xyz": list(self.screen_right),
            "screen_up_canonical_xyz": list(self.screen_up),
            "bounds": list(self.bounds) if self.bounds is not None else None,
            "empty_section": not self.curves,
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "coordinate_frame_id": self.components[0].coordinate_frame_id,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
            "raster_source_of_truth": False,
            "placement_policy": self.placement_policy,
            "component_count": len(self.components),
            "components": [item.as_dict() for item in self.components],
            "curves": [curve.as_dict() for curve in self.curves],
            "hatching": {
                "status": self.hatching_status,
                "regions": list(self.hatching_regions),
            },
            "limitations": [
                "component placements are explicit inputs pinned by caller reference and matrix",
                "placement references are not independently accepted as assembly authority",
                "component transforms are explicit inputs; no assembly BREP is persisted or inferred",
                "section curves are sampled vector polylines rather than analytic curves",
                "edge-to-feature association is unresolved unless separately supported by feature lineage",
                "hatching is omitted because closed-loop classification is not established",
                "numerical section geometry is software evidence, not physical metrology",
            ],
            "scan_master_promoted": False,
            "design_model_replaced": False,
            "cad_brep_replaced": False,
        }


def generate_section_view(
    sources: tuple[DrawingSectionSource, ...], *, plane_axis: str, plane_offset: float
) -> DrawingSectionViewModel:
    """Cut one canonical plane through one or more exact, co-framed BREP sources."""
    if not isinstance(sources, tuple) or not 1 <= len(sources) <= _MAX_COMPONENTS:
        raise DrawingSectionError("drawing_section_component_count_invalid")
    if any(not isinstance(source, DrawingSectionSource) for source in sources):
        raise DrawingSectionError("drawing_section_source_required")
    if not isinstance(plane_axis, str) or plane_axis not in _SECTION_FRAMES:
        raise DrawingSectionError("drawing_section_plane_axis_invalid")
    if (
        isinstance(plane_offset, bool)
        or not isinstance(plane_offset, (int, float))
        or not math.isfinite(plane_offset)
        or abs(float(plane_offset)) > 1e9
    ):
        raise DrawingSectionError("drawing_section_plane_offset_invalid")
    if any(
        not isinstance(source.component_reference_id, str)
        or not source.component_reference_id.strip()
        or len(source.component_reference_id) > 128
        or not isinstance(source.coordinate_frame_id, str)
        or not source.coordinate_frame_id.strip()
        or len(source.coordinate_frame_id) > 128
        or not isinstance(source.placement_revision_id, str)
        or not source.placement_revision_id.strip()
        or len(source.placement_revision_id) > 128
        for source in sources
    ) or len({source.component_reference_id for source in sources}) != len(sources):
        raise DrawingSectionError("drawing_section_component_reference_invalid")

    checked = tuple(sorted(sources, key=lambda source: source.component_reference_id))
    prepared: list[
        tuple[
            DrawingSectionSource,
            str,
            str,
            tuple[dict[str, object], ...],
            CadSectionResultData,
        ]
    ] = []
    common_scale: ScaleState | None = None
    common_unit: str | None = None
    common_frame: str | None = None
    for source in checked:
        model = source.model
        representation = source.representation
        if not isinstance(model, DesignModelRevision):
            raise DrawingSectionError("drawing_section_design_model_required")
        if not isinstance(representation, CadBrepRepresentationRevision):
            raise DrawingSectionError("drawing_section_cad_brep_required")
        parent_revision = (
            model.standalone_root.revision_id
            if model.standalone_root is not None
            else model.parent_binding_revision_id
        )
        if (
            representation.source_design_model_revision_id != model.revision_id
            or representation.parent_kind is not model.parent_kind
            or representation.parent_authority_revision_id != parent_revision
            or representation.scale_state is not model.scale_state
            or representation.coordinate_unit != model.coordinate_unit
            or representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
            or representation.mold_use_authorized is not False
            or model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
            or model.mold_use_authorized is not False
        ):
            raise DrawingSectionError("drawing_section_source_authority_mismatch")
        if common_scale is None:
            common_scale = model.scale_state
            common_unit = model.coordinate_unit
            common_frame = source.coordinate_frame_id
        elif model.scale_state is not common_scale or model.coordinate_unit != common_unit:
            raise DrawingSectionError("drawing_section_component_units_mismatch")
        elif source.coordinate_frame_id != common_frame:
            raise DrawingSectionError("drawing_section_component_coordinate_frame_mismatch")
        try:
            validation = validate_cad_brep(representation)
            if not validation.valid_closed_solid:
                raise DrawingSectionError("drawing_section_valid_closed_solid_required")
            mapping = map_design_model_features_to_brep(model, representation)
            section_result = section_cad_shape(
                representation.shape_handle,
                plane_origin=_plane_origin(plane_axis, float(plane_offset)),
                plane_normal=_SECTION_FRAMES[plane_axis][0],
                screen_right=_SECTION_FRAMES[plane_axis][1],
                screen_up=_SECTION_FRAMES[plane_axis][2],
                placement_matrix=source.placement_matrix,
                maximum_edges=_MAX_EDGES_PER_COMPONENT,
            )
        except DrawingSectionError:
            raise
        except CadAdapterError as error:
            raise DrawingSectionError(str(error)) from error
        except Exception as error:
            raise DrawingSectionError("drawing_section_source_processing_failed") from error
        prepared.append(
            (
                source,
                mapping.revision_id,
                parent_revision,
                tuple(item.as_dict() for item in mapping.references),
                section_result,
            )
        )

    component_results: list[DrawingSectionComponent] = []
    all_curves: list[DrawingSectionCurve] = []
    for source, mapping_id, parent_revision, feature_refs, section_result in prepared:
        canonical_curves = _section_curves(source.component_reference_id, section_result.curves)
        component = DrawingSectionComponent(
            component_reference_id=source.component_reference_id,
            coordinate_frame_id=source.coordinate_frame_id,
            placement_revision_id=source.placement_revision_id,
            placement_matrix=source.placement_matrix,
            source_design_model_revision_id=source.model.revision_id,
            source_brep_revision_id=source.representation.revision_id,
            source_brep_geometry_sha256=source.representation.geometry_sha256,
            parent_kind=source.model.parent_kind.value,
            parent_authority_revision_id=parent_revision,
            feature_mapping_revision_id=mapping_id,
            feature_references=feature_refs,
            intersected=bool(canonical_curves),
            bounds=section_result.bounds,
            curves=canonical_curves,
        )
        component_results.append(component)
        all_curves.extend(canonical_curves)
    curves_sorted = tuple(sorted(all_curves, key=lambda curve: curve.curve_id))
    component_bounds = tuple(
        component.bounds for component in component_results if component.bounds is not None
    )
    bounds = (
        (
            _round(min(item[0] for item in component_bounds)),
            _round(min(item[1] for item in component_bounds)),
            _round(max(item[2] for item in component_bounds)),
            _round(max(item[3] for item in component_bounds)),
        )
        if component_bounds
        else None
    )
    normal, right, up = _SECTION_FRAMES[plane_axis]
    origin = _plane_origin(plane_axis, float(plane_offset))
    identity = {
        "plane_axis": plane_axis,
        "plane_offset": _round(float(plane_offset)),
        "plane_origin": origin,
        "plane_normal": normal,
        "screen_right": right,
        "screen_up": up,
        "scale_state": common_scale.value if common_scale is not None else None,
        "coordinate_unit": common_unit,
        "coordinate_frame_id": common_frame,
        "components": [item.as_dict() for item in component_results],
        "curves": [curve.as_dict() for curve in curves_sorted],
        "hatching_status": "NOT_DERIVED_CLOSED_LOOP_CLASSIFICATION_UNAVAILABLE",
    }
    revision_id = (
        "technical-drawing-section:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    return DrawingSectionViewModel(
        revision_id=revision_id,
        plane_axis=plane_axis,
        plane_offset=_round(float(plane_offset)),
        plane_origin=origin,
        plane_normal=normal,
        screen_right=right,
        screen_up=up,
        scale_state=common_scale.value if common_scale is not None else "",
        coordinate_unit=common_unit or "",
        physical_accuracy_validation_status="DEFERRED_OWNER_VALIDATION",
        mold_use_authorized=False,
        bounds=bounds,
        components=tuple(component_results),
        curves=curves_sorted,
    )


def _section_curves(
    component_reference_id: str, curves: tuple[CadProjectedCurveData, ...]
) -> tuple[DrawingSectionCurve, ...]:
    records: dict[bytes, DrawingSectionCurve] = {}
    for curve in curves:
        points = tuple((_round(x), _round(y)) for x, y in curve.points)
        if len(points) < 2:
            continue
        canonical = min(points, tuple(reversed(points)))
        payload = json.dumps(
            {
                "component_reference_id": component_reference_id,
                "curve_type": curve.curve_type,
                "points": canonical,
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
        digest = hashlib.sha256(payload).hexdigest()
        records[payload] = DrawingSectionCurve(
            curve_id=f"drawing-section-curve:{digest}",
            component_reference_id=component_reference_id,
            curve_type=curve.curve_type,
            points=canonical,
        )
    return tuple(records[key] for key in sorted(records))


def _plane_origin(axis: str, offset: float) -> tuple[float, float, float]:
    coordinates = {"X": (offset, 0.0, 0.0), "Y": (0.0, offset, 0.0), "Z": (0.0, 0.0, offset)}
    return tuple(_round(value) for value in coordinates[axis])  # type: ignore[return-value]


def _round(value: float) -> float:
    rounded = round(value, _ROUND_DIGITS)
    return 0.0 if rounded == 0.0 else rounded


__all__ = [
    "DrawingSectionComponent",
    "DrawingSectionCurve",
    "DrawingSectionError",
    "DrawingSectionSource",
    "DrawingSectionViewModel",
    "SECTION_VIEW_MODEL_CONTRACT",
    "generate_section_view",
]
