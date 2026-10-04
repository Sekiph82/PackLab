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
    stable_feature_id,
)
from .design_model_binding import StandaloneDesignGeometryRoot
from .design_preview import PREVIEW_AUTHORITY, PREVIEW_CONTRACT, DesignPreview
from .geometry_adapter import TriangleMeshData

_MAX_DIMENSION = 1e7
_DEFERRED = "DEFERRED_OWNER_VALIDATION"


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
class PouchFamilyRevision:
    """Standalone pouch Design Model plus explicit artwork references and preview proxy."""

    model: DesignModelRevision
    dimensions: PouchFamilyDimensions
    preview: DesignPreview
    component_id: str
    front_artwork_feature_id: str
    back_artwork_feature_id: str

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
            "component_id": self.component_id,
            "dimensions": self.dimensions.as_dict(self.model.coordinate_unit),
            "artwork_surfaces": {
                "front_feature_id": self.front_artwork_feature_id,
                "back_feature_id": self.back_artwork_feature_id,
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
) -> PouchFamilyRevision:
    """Create a standalone model-only pouch with stable front/back artwork surfaces."""
    if not isinstance(root, StandaloneDesignGeometryRoot):
        raise PouchFamilyError("standalone_design_geometry_root_required")
    if not isinstance(dimensions, PouchFamilyDimensions):
        raise PouchFamilyError("pouch_dimensions_required")
    _identifier(component_id, "component_id")
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
    values = (
        ("pouch_overall_width", dimensions.overall_width),
        ("pouch_overall_height", dimensions.overall_height),
        ("pouch_thickness", dimensions.thickness),
        ("pouch_top_seal_width", dimensions.top_seal_width),
        ("pouch_bottom_seal_width", dimensions.bottom_seal_width),
        ("pouch_left_seal_width", dimensions.left_seal_width),
        ("pouch_right_seal_width", dimensions.right_seal_width),
    )
    parameters = tuple(
        DesignModelParameter(key, value, ParameterType.NUMBER, root.coordinate_unit)
        for key, value in values
    )
    model = create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.OTHER,
        parameters=parameters,
        features=feature_tuple,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    preview = _preview(model, dimensions)
    return PouchFamilyRevision(
        model, dimensions, preview, component_id, front.feature_id, back.feature_id
    )


def _feature(component_id: str, semantic_key: str) -> DesignModelFeatureReference:
    return DesignModelFeatureReference(
        stable_feature_id(component_id, FeatureKind.BODY, f"sachet-pouch:{semantic_key}:v1"),
        component_id,
        FeatureKind.BODY,
        f"sachet-pouch:{semantic_key}:v1",
    )


def _preview(model: DesignModelRevision, dimensions: PouchFamilyDimensions) -> DesignPreview:
    """Build a deterministic thin rectangular prism proxy, never captured geometry."""
    x, y, z = dimensions.overall_width / 2, dimensions.overall_height / 2, dimensions.thickness / 2
    vertices = (
        (-x, -y, -z),
        (x, -y, -z),
        (x, y, -z),
        (-x, y, -z),
        (-x, -y, z),
        (x, -y, z),
        (x, y, z),
        (-x, y, z),
    )
    triangles = (
        (0, 2, 1),
        (0, 3, 2),
        (4, 5, 6),
        (4, 6, 7),
        (0, 1, 5),
        (0, 5, 4),
        (1, 2, 6),
        (1, 6, 5),
        (2, 3, 7),
        (2, 7, 6),
        (3, 0, 4),
        (3, 4, 7),
    )
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
            (front.feature_id, (4, 5, 6, 7)),
            (back.feature_id, (0, 1, 2, 3)),
        ),
        authority_class=PREVIEW_AUTHORITY,
        contract=PREVIEW_CONTRACT,
        standalone_root_revision_id=root.revision_id,
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


__all__ = ["PouchFamilyDimensions", "PouchFamilyError", "PouchFamilyRevision", "build_pouch_family"]
