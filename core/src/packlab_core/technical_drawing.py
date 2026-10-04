"""Backend-neutral vector-ready orthographic views derived from exact CAD BREP."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .cad_adapter import (
    CadAdapterError,
    CadProjectedCurveData,
    cad_shape_bounds,
    project_visible_cad_edges,
)
from .cad_brep import CadBrepRepresentationRevision
from .cad_feature_map import map_design_model_features_to_brep
from .cad_validation import validate_cad_brep
from .design_model import DesignModelRevision

DRAWING_VIEW_MODEL_CONTRACT = "packlab.technical-drawing-view-model.v1"
_ROUND_DIGITS = 12
_UP: tuple[float, float, float] = (0.0, 0.0, 1.0)
_CANONICAL_FRONT: tuple[float, float, float] = (0.0, 1.0, 0.0)


class TechnicalDrawingError(ValueError):
    """Raised when exact Design Model/BREP inputs cannot produce orthographic views."""


@dataclass(frozen=True, slots=True)
class DrawingCurve:
    curve_id: str
    curve_type: str
    points: tuple[tuple[float, float], ...]
    visibility: str = "VISIBLE"
    feature_lineage_status: str = "UNRESOLVED_EDGE_TO_FEATURE_ASSOCIATION"

    def as_dict(self) -> dict[str, object]:
        return {
            "curve_id": self.curve_id,
            "curve_type": self.curve_type,
            "points": [list(point) for point in self.points],
            "visibility": self.visibility,
            "feature_lineage_status": self.feature_lineage_status,
            "native_topology_id_used_as_authority": False,
        }


@dataclass(frozen=True, slots=True)
class OrthographicView:
    view_id: str
    camera_side: tuple[float, float, float]
    projection_direction: tuple[float, float, float]
    screen_right: tuple[float, float, float]
    screen_up: tuple[float, float, float]
    bounds: tuple[float, float, float, float]
    curves: tuple[DrawingCurve, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "view_id": self.view_id,
            "projection_kind": "ORTHOGRAPHIC",
            "camera_side_canonical_xyz": list(self.camera_side),
            "projection_direction_canonical_xyz": list(self.projection_direction),
            "screen_right_canonical_xyz": list(self.screen_right),
            "screen_up_canonical_xyz": list(self.screen_up),
            "bounds": list(self.bounds),
            "curves": [curve.as_dict() for curve in self.curves],
            "curve_count": len(self.curves),
            "hidden_edges_included": False,
            "raster_source_of_truth": False,
        }


@dataclass(frozen=True, slots=True)
class TechnicalDrawingViewModel:
    revision_id: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    parent_kind: str
    parent_authority_revision_id: str
    scale_state: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    front_direction: tuple[float, float, float]
    front_direction_source: str
    front_direction_revision_id: str | None
    feature_mapping_revision_id: str
    feature_references: tuple[dict[str, object], ...]
    views: tuple[OrthographicView, ...]
    vector_source_authority: str = "EXACT_CAD_BREP_HLR"
    edge_visibility_policy: str = "OCCT_EXACT_HLR_VISIBLE_EDGES_ONLY"
    hidden_edges_included: bool = False
    coordinate_scale: float = 1.0
    contract: str = DRAWING_VIEW_MODEL_CONTRACT

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "DERIVED_TECHNICAL_DRAWING_VIEW_MODEL",
            "revision_id": self.revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_brep_geometry_sha256": self.source_brep_geometry_sha256,
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "coordinate_scale": self.coordinate_scale,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
            "front_direction_canonical_xyz": list(self.front_direction),
            "front_direction_source": self.front_direction_source,
            "front_direction_revision_id": self.front_direction_revision_id,
            "feature_mapping_revision_id": self.feature_mapping_revision_id,
            "feature_references": list(self.feature_references),
            "vector_source_authority": self.vector_source_authority,
            "raster_source_of_truth": False,
            "edge_visibility_policy": self.edge_visibility_policy,
            "hidden_edges_included": self.hidden_edges_included,
            "limitations": [
                "nonlinear projected BREP edges are sampled into deterministic vector polylines",
                "OCCT HLR may retain coincident or superimposed lines",
                "edge-to-feature association is unresolved unless separately supported by feature lineage",
                "numerical drawing values are software geometry, not physical metrology",
            ],
            "views": [view.as_dict() for view in self.views],
            "scan_master_promoted": False,
            "design_model_replaced": False,
            "cad_brep_replaced": False,
        }


def generate_orthographic_views(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    *,
    front_direction: tuple[float, float, float] | None = None,
    front_direction_revision_id: str | None = None,
) -> TechnicalDrawingViewModel:
    """Generate front/side/top vector linework without changing its CAD source."""
    if not isinstance(model, DesignModelRevision):
        raise TechnicalDrawingError("design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise TechnicalDrawingError("cad_brep_representation_required")
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
        raise TechnicalDrawingError("drawing_source_authority_mismatch")
    if (
        model.scale_state.value == "RELATIVE" and model.coordinate_unit != "reconstruction_units"
    ) or (
        model.scale_state.value == "METRIC_UNVERIFIED" and model.coordinate_unit != "mm_unverified"
    ):
        raise TechnicalDrawingError("drawing_source_unit_mismatch")
    if front_direction_revision_id is not None and (
        not isinstance(front_direction_revision_id, str) or not front_direction_revision_id.strip()
    ):
        raise TechnicalDrawingError("drawing_front_direction_revision_invalid")
    normalized_front = _front_direction(front_direction)

    try:
        validation = validate_cad_brep(representation)
        if not validation.valid_closed_solid:
            raise TechnicalDrawingError("drawing_valid_closed_solid_required")
        feature_mapping = map_design_model_features_to_brep(model, representation)
        grouped_bounds = cad_shape_bounds(representation.shape_handle)
    except TechnicalDrawingError:
        raise
    except Exception as error:
        raise TechnicalDrawingError("drawing_source_validation_failed") from error

    front_projection = _cross(normalized_front, _UP)
    side_out = front_projection
    view_specs = (
        (
            "FRONT",
            normalized_front,
            _negate(normalized_front),
            front_projection,
            _UP,
        ),
        (
            "SIDE",
            side_out,
            _negate(side_out),
            _cross(_UP, _negate(side_out)),
            _UP,
        ),
        (
            "TOP",
            _UP,
            _negate(_UP),
            _cross(normalized_front, _negate(_UP)),
            normalized_front,
        ),
    )
    corners = _aabb_corners(grouped_bounds)
    views: list[OrthographicView] = []
    try:
        for view_id, camera_side, direction, screen_right, screen_up in view_specs:
            raw_curves = project_visible_cad_edges(
                representation.shape_handle,
                screen_right=screen_right,
                screen_up=screen_up,
            )
            curves = _canonical_curves(raw_curves)
            projected_corners = tuple(
                (_dot(point, screen_right), _dot(point, screen_up)) for point in corners
            )
            bounds = (
                _rounded(min(point[0] for point in projected_corners)),
                _rounded(min(point[1] for point in projected_corners)),
                _rounded(max(point[0] for point in projected_corners)),
                _rounded(max(point[1] for point in projected_corners)),
            )
            views.append(
                OrthographicView(
                    view_id,
                    _rounded_vector(camera_side),
                    _rounded_vector(direction),
                    _rounded_vector(screen_right),
                    _rounded_vector(screen_up),
                    bounds,
                    curves,
                )
            )
    except CadAdapterError as error:
        raise TechnicalDrawingError(str(error)) from error
    except Exception as error:
        raise TechnicalDrawingError("drawing_projection_failed") from error

    reference_documents = tuple(item.as_dict() for item in feature_mapping.references)
    identity = {
        "source_design_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "source_brep_geometry_sha256": representation.geometry_sha256,
        "parent_kind": model.parent_kind.value,
        "parent_authority_revision_id": parent_revision,
        "scale_state": model.scale_state.value,
        "coordinate_unit": model.coordinate_unit,
        "front_direction": _rounded_vector(normalized_front),
        "front_direction_source": "CANONICAL_DEFAULT"
        if front_direction is None
        else "EXPLICIT_INPUT",
        "front_direction_revision_id": front_direction_revision_id,
        "feature_mapping_revision_id": feature_mapping.revision_id,
        "views": [view.as_dict() for view in views],
    }
    revision_id = (
        "technical-drawing-view-model:"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )
    return TechnicalDrawingViewModel(
        revision_id=revision_id,
        source_design_model_revision_id=model.revision_id,
        source_brep_revision_id=representation.revision_id,
        source_brep_geometry_sha256=representation.geometry_sha256,
        parent_kind=model.parent_kind.value,
        parent_authority_revision_id=parent_revision,
        scale_state=model.scale_state.value,
        coordinate_unit=model.coordinate_unit,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
        front_direction=_rounded_vector(normalized_front),
        front_direction_source="CANONICAL_DEFAULT" if front_direction is None else "EXPLICIT_INPUT",
        front_direction_revision_id=front_direction_revision_id,
        feature_mapping_revision_id=feature_mapping.revision_id,
        feature_references=reference_documents,
        views=tuple(views),
    )


def _canonical_curves(curves: tuple[CadProjectedCurveData, ...]) -> tuple[DrawingCurve, ...]:
    records: dict[bytes, DrawingCurve] = {}
    for curve in curves:
        points = tuple((_rounded(x), _rounded(y)) for x, y in curve.points)
        if len(points) < 2:
            continue
        forward = points
        backward = tuple(reversed(points))
        canonical_points = min(forward, backward)
        payload = json.dumps(
            {"curve_type": curve.curve_type, "points": canonical_points},
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
        identity = hashlib.sha256(payload).hexdigest()
        records[payload] = DrawingCurve(
            f"drawing-curve:{identity}", curve.curve_type, canonical_points
        )
    return tuple(records[key] for key in sorted(records))


def _front_direction(
    direction: tuple[float, float, float] | None,
) -> tuple[float, float, float]:
    if direction is None:
        return _CANONICAL_FRONT
    if (
        not isinstance(direction, tuple)
        or len(direction) != 3
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in direction
        )
    ):
        raise TechnicalDrawingError("drawing_front_direction_invalid")
    if abs(float(direction[2])) > 1e-9:
        raise TechnicalDrawingError("drawing_front_direction_must_be_horizontal")
    magnitude = math.hypot(float(direction[0]), float(direction[1]))
    if magnitude <= 1e-12:
        raise TechnicalDrawingError("drawing_front_direction_degenerate")
    return (float(direction[0]) / magnitude, float(direction[1]) / magnitude, 0.0)


def _aabb_corners(
    bounds: tuple[float, float, float, float, float, float],
) -> tuple[tuple[float, float, float], ...]:
    return tuple(
        (x, y, z)
        for x in (bounds[0], bounds[3])
        for y in (bounds[1], bounds[4])
        for z in (bounds[2], bounds[5])
    )


def _dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _cross(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _negate(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(-value for value in vector)  # type: ignore[return-value]


def _rounded(value: float) -> float:
    rounded = round(value, _ROUND_DIGITS)
    return 0.0 if rounded == 0.0 else rounded


def _rounded_vector(
    vector: tuple[float, float, float],
) -> tuple[float, float, float]:
    return tuple(_rounded(value) for value in vector)  # type: ignore[return-value]


__all__ = [
    "DRAWING_VIEW_MODEL_CONTRACT",
    "DrawingCurve",
    "OrthographicView",
    "TechnicalDrawingError",
    "TechnicalDrawingViewModel",
    "generate_orthographic_views",
]
