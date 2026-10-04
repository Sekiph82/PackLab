"""Simplified standalone sachet/pouch design geometry and preview proxy."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_standalone_design_model_revision,
    revise_design_model_revision,
    stable_feature_id,
)
from .design_model_binding import StandaloneDesignGeometryRoot
from .design_preview import PREVIEW_AUTHORITY, PREVIEW_CONTRACT, DesignPreview
from .flexible_pack_authority import flexible_pack_authority_handoff
from .geometry_adapter import TriangleMeshData

_MAX_DIMENSION = 1e7
_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_SURFACE_GRID_CELLS = 16


class PouchFamilyError(ValueError):
    """Raised when pouch design parameters cannot form a valid model."""


@dataclass(frozen=True, slots=True)
class PouchFamilyDimensions:
    """Nominal overall dimensions and seal widths in the standalone root's units."""

    overall_width: float
    overall_height: float
    thickness: float
    top_seal_width: float
    bottom_seal_width: float
    left_seal_width: float
    right_seal_width: float

    def __post_init__(self) -> None:
        values = (
            self.overall_width,
            self.overall_height,
            self.thickness,
            self.top_seal_width,
            self.bottom_seal_width,
            self.left_seal_width,
            self.right_seal_width,
        )
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0.0
            or value > _MAX_DIMENSION
            for value in values
        ):
            raise PouchFamilyError("pouch_dimension_must_be_finite_positive_and_bounded")
        if (
            self.thickness >= min(self.overall_width, self.overall_height)
            or self.left_seal_width + self.right_seal_width >= self.overall_width
            or self.top_seal_width + self.bottom_seal_width >= self.overall_height
            or max(
                self.top_seal_width,
                self.bottom_seal_width,
                self.left_seal_width,
                self.right_seal_width,
            )
            >= min(self.overall_width, self.overall_height) / 2.0
        ):
            raise PouchFamilyError("pouch_seal_or_dimension_relationship_impossible")

    def as_dict(self, coordinate_unit: str) -> dict[str, object]:
        return {
            "overall_width": self.overall_width,
            "overall_height": self.overall_height,
            "thickness": self.thickness,
            "seal_zones": {
                "top": self.top_seal_width,
                "bottom": self.bottom_seal_width,
                "left": self.left_seal_width,
                "right": self.right_seal_width,
            },
            "coordinate_unit": coordinate_unit,
            "scale_state": "relative"
            if coordinate_unit == "reconstruction_units"
            else "metric-unverified",
            "physical_accuracy_validation_status": _DEFERRED,
        }


@dataclass(frozen=True, slots=True)
class PouchArtworkAnchor:
    """Stable normalized artwork coordinate pinned to a semantic pouch surface."""

    anchor_id: str
    surface_feature_id: str
    u: float
    v: float

    def __post_init__(self) -> None:
        _identifier(self.anchor_id, "artwork_anchor_id")
        if not isinstance(self.surface_feature_id, str) or not self.surface_feature_id.startswith(
            "packlab-feature:"
        ):
            raise PouchFamilyError("artwork_surface_feature_invalid")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0.0 <= value <= 1.0
            for value in (self.u, self.v)
        ):
            raise PouchFamilyError("artwork_coordinate_out_of_bounds")

    def as_dict(self) -> dict[str, object]:
        return {
            "anchor_id": self.anchor_id,
            "surface_feature_id": self.surface_feature_id,
            "u": self.u,
            "v": self.v,
            "coordinate_space": "normalized_surface_uv",
        }


@dataclass(frozen=True, slots=True)
class PouchFamilyRevision:
    """Standalone pouch Design Model plus explicit artwork references and preview proxy."""

    model: DesignModelRevision
    dimensions: PouchFamilyDimensions
    preview: DesignPreview
    component_id: str
    front_artwork_feature_id: str
    back_artwork_feature_id: str
    front_bulge: float
    back_bulge: float
    artwork_anchors: tuple[PouchArtworkAnchor, ...]

    def as_dict(self) -> dict[str, object]:
        if self.model.standalone_root is None:
            raise PouchFamilyError("pouch_standalone_parent_missing")
        return {
            "contract": "packlab.sachet-pouch-family.v1",
            "authority_class": "DESIGN_MODEL_WITH_PREVIEW_PROXY",
            "parent_authority": {
                "kind": "STANDALONE_DESIGN_GEOMETRY",
                "root_revision_id": self.model.standalone_root.revision_id,
            },
            "model": self.model.as_dict(),
            "authority_and_limitations": flexible_pack_authority_handoff(self.model),
            "component_id": self.component_id,
            "dimensions": self.dimensions.as_dict(self.model.coordinate_unit),
            "artwork_surfaces": {
                "front_feature_id": self.front_artwork_feature_id,
                "back_feature_id": self.back_artwork_feature_id,
                "coordinate_system": "normalized_surface_uv",
                "anchors": [anchor.as_dict() for anchor in self.artwork_anchors],
            },
            "flexible_surface_design": {
                "representation": "bounded_simplified_bulge",
                "front_bulge": self.front_bulge,
                "back_bulge": self.back_bulge,
                "bulge_is_measured_film_deformation": False,
                "seal_zones_remain_flat": True,
            },
            "preview": self.preview.as_dict(),
            "visualization_only": True,
            "captured_surface_claimed": False,
            "physical_accuracy_validation_status": _DEFERRED,
            "mold_use_authorized": False,
            "manufacturing_authority": False,
            "scan_master_promoted": False,
            "cad_or_brep_generated": False,
        }


def build_pouch_family(
    root: StandaloneDesignGeometryRoot,
    dimensions: PouchFamilyDimensions,
    *,
    component_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    front_bulge: float = 0.0,
    back_bulge: float = 0.0,
    artwork_anchors: tuple[PouchArtworkAnchor, ...] | None = None,
) -> PouchFamilyRevision:
    """Create a standalone model-only pouch with stable front/back artwork surfaces."""
    if not isinstance(root, StandaloneDesignGeometryRoot):
        raise PouchFamilyError("standalone_design_geometry_root_required")
    if not isinstance(dimensions, PouchFamilyDimensions):
        raise PouchFamilyError("pouch_dimensions_required")
    _identifier(component_id, "component_id")
    _validate_bulge(front_bulge, dimensions)
    _validate_bulge(back_bulge, dimensions)
    front = _feature(component_id, "front-artwork-surface")
    back = _feature(component_id, "back-artwork-surface")
    seal_keys = (
        "top-seal-zone",
        "bottom-seal-zone",
        "left-seal-zone",
        "right-seal-zone",
    )
    seals = tuple(_feature(component_id, key) for key in seal_keys)
    feature_tuple = (front, back, *seals)
    anchors = _anchors(artwork_anchors, front.feature_id, back.feature_id)
    parameters = _parameters(dimensions, front_bulge, back_bulge, anchors, root.coordinate_unit)
    model = create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.FLEXIBLE_PACK,
        parameters=parameters,
        features=feature_tuple,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    preview = _preview(model, dimensions, front_bulge, back_bulge)
    return PouchFamilyRevision(
        model,
        dimensions,
        preview,
        component_id,
        front.feature_id,
        back.feature_id,
        front_bulge,
        back_bulge,
        anchors,
    )


def edit_pouch_family(
    current: PouchFamilyRevision,
    *,
    dimensions: PouchFamilyDimensions | None = None,
    front_bulge: float | None = None,
    back_bulge: float | None = None,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> PouchFamilyRevision:
    """Create an immutable flexible-surface edit preserving root and artwork UVs."""
    if not isinstance(current, PouchFamilyRevision):
        raise PouchFamilyError("current_pouch_family_revision_required")
    root = current.model.standalone_root
    if root is None:
        raise PouchFamilyError("pouch_standalone_parent_missing")
    next_dimensions = current.dimensions if dimensions is None else dimensions
    if not isinstance(next_dimensions, PouchFamilyDimensions):
        raise PouchFamilyError("pouch_dimensions_required")
    next_front = current.front_bulge if front_bulge is None else front_bulge
    next_back = current.back_bulge if back_bulge is None else back_bulge
    _validate_bulge(next_front, next_dimensions)
    _validate_bulge(next_back, next_dimensions)
    parameters = _parameters(
        next_dimensions,
        next_front,
        next_back,
        current.artwork_anchors,
        current.model.coordinate_unit,
    )
    model = revise_design_model_revision(
        current.model,
        parameters=parameters,
        features=current.model.features,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    if model.standalone_root != root or model.parent_kind is not current.model.parent_kind:
        raise PouchFamilyError("pouch_parent_authority_changed")
    preview = _preview(model, next_dimensions, next_front, next_back)
    return PouchFamilyRevision(
        model,
        next_dimensions,
        preview,
        current.component_id,
        current.front_artwork_feature_id,
        current.back_artwork_feature_id,
        next_front,
        next_back,
        current.artwork_anchors,
    )


def _feature(component_id: str, semantic_key: str) -> DesignModelFeatureReference:
    return DesignModelFeatureReference(
        stable_feature_id(component_id, FeatureKind.BODY, f"sachet-pouch:{semantic_key}:v1"),
        component_id,
        FeatureKind.BODY,
        f"sachet-pouch:{semantic_key}:v1",
    )


def _preview(
    model: DesignModelRevision,
    dimensions: PouchFamilyDimensions,
    front_bulge: float,
    back_bulge: float,
) -> DesignPreview:
    """Build bounded front/back surface grids and perimeter strips as preview geometry."""
    width, height = dimensions.overall_width, dimensions.overall_height
    x0, y0, half_thickness = -width / 2, -height / 2, dimensions.thickness / 2
    cells = _SURFACE_GRID_CELLS
    side = cells + 1
    vertices_list: list[tuple[float, float, float]] = []
    for is_front, bulge in ((False, back_bulge), (True, front_bulge)):
        for row in range(side):
            v = row / cells
            y = y0 + v * height
            for column in range(side):
                u = column / cells
                x = x0 + u * width
                in_artwork_area = (
                    dimensions.left_seal_width < u * width < width - dimensions.right_seal_width
                    and dimensions.bottom_seal_width
                    < v * height
                    < height - dimensions.top_seal_width
                )
                dome = 16.0 * u * (1.0 - u) * v * (1.0 - v) if in_artwork_area else 0.0
                z = half_thickness + bulge * dome if is_front else -half_thickness - bulge * dome
                vertices_list.append((x, y, z))
    front_offset = side * side
    triangles_list: list[tuple[int, int, int]] = []
    for base, is_front in ((0, False), (front_offset, True)):
        for row in range(cells):
            for column in range(cells):
                lower_left = base + row * side + column
                lower_right = lower_left + 1
                upper_left = lower_left + side
                upper_right = upper_left + 1
                if is_front:
                    triangles_list.extend(
                        (
                            (lower_left, lower_right, upper_right),
                            (lower_left, upper_right, upper_left),
                        )
                    )
                else:
                    triangles_list.extend(
                        (
                            (lower_left, upper_right, lower_right),
                            (lower_left, upper_left, upper_right),
                        )
                    )
    boundary: list[int] = list(range(side))
    boundary.extend(row * side + cells for row in range(1, side))
    boundary.extend(cells * side + column for column in range(cells - 1, -1, -1))
    boundary.extend(row * side for row in range(cells - 1, 0, -1))
    for first, second in zip(boundary, (*boundary[1:], boundary[0]), strict=True):
        opposite_first, opposite_second = first + front_offset, second + front_offset
        triangles_list.extend(
            ((first, second, opposite_second), (first, opposite_second, opposite_first))
        )
    vertices, triangles = tuple(vertices_list), tuple(triangles_list)
    front, back = model.features[:2]
    root = model.standalone_root
    if root is None:
        raise PouchFamilyError("pouch_standalone_parent_missing")
    return DesignPreview(
        mesh=TriangleMeshData(vertices, triangles),
        model_revision_id=model.revision_id,
        scan_master_revision_id=None,
        scan_master_geometry_sha256=None,
        parent_binding_revision_id=None,
        scale_state=model.scale_state,
        coordinate_unit=model.coordinate_unit,
        physical_accuracy_validation_status=_DEFERRED,
        mold_use_authorized=False,
        feature_vertex_indices=(
            (front.feature_id, tuple(range(front_offset, len(vertices)))),
            (back.feature_id, tuple(range(front_offset))),
        ),
        authority_class=PREVIEW_AUTHORITY,
        contract=PREVIEW_CONTRACT,
        standalone_root_revision_id=root.revision_id,
        flexible_pack_design_only=True,
    )


def _identifier(value: object, field: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or not value[0].isalpha()
        or not all(character.isalnum() or character in "_.:-" for character in value)
    ):
        raise PouchFamilyError(f"{field}_invalid")


def _validate_bulge(value: object, dimensions: PouchFamilyDimensions) -> None:
    bound = min(dimensions.overall_width, dimensions.overall_height) * 0.1
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0.0
        or value > bound
    ):
        raise PouchFamilyError("pouch_bulge_out_of_bounds")


def _anchors(
    supplied: tuple[PouchArtworkAnchor, ...] | None,
    front_feature_id: str,
    back_feature_id: str,
) -> tuple[PouchArtworkAnchor, ...]:
    anchors = (
        (
            PouchArtworkAnchor("front-center", front_feature_id, 0.5, 0.5),
            PouchArtworkAnchor("back-center", back_feature_id, 0.5, 0.5),
        )
        if supplied is None
        else supplied
    )
    if (
        not isinstance(anchors, tuple)
        or not anchors
        or any(not isinstance(item, PouchArtworkAnchor) for item in anchors)
        or len({item.anchor_id for item in anchors}) != len(anchors)
        or any(
            item.surface_feature_id not in {front_feature_id, back_feature_id} for item in anchors
        )
    ):
        raise PouchFamilyError("pouch_artwork_anchors_invalid")
    return tuple(sorted(anchors, key=lambda item: item.anchor_id))


def _parameters(
    dimensions: PouchFamilyDimensions,
    front_bulge: float,
    back_bulge: float,
    anchors: tuple[PouchArtworkAnchor, ...],
    unit: str,
) -> tuple[DesignModelParameter, ...]:
    values: list[tuple[str, float]] = [
        ("pouch_overall_width", dimensions.overall_width),
        ("pouch_overall_height", dimensions.overall_height),
        ("pouch_thickness", dimensions.thickness),
        ("pouch_top_seal_width", dimensions.top_seal_width),
        ("pouch_bottom_seal_width", dimensions.bottom_seal_width),
        ("pouch_left_seal_width", dimensions.left_seal_width),
        ("pouch_right_seal_width", dimensions.right_seal_width),
        ("pouch_front_bulge", front_bulge),
        ("pouch_back_bulge", back_bulge),
    ]
    for anchor in anchors:
        values.extend(
            (
                (f"pouch_artwork:{anchor.anchor_id}:u", anchor.u),
                (f"pouch_artwork:{anchor.anchor_id}:v", anchor.v),
            )
        )
    return tuple(
        DesignModelParameter(key, value, ParameterType.NUMBER, unit) for key, value in values
    )


__all__ = [
    "PouchArtworkAnchor",
    "PouchFamilyDimensions",
    "PouchFamilyError",
    "PouchFamilyRevision",
    "build_pouch_family",
    "edit_pouch_family",
]
