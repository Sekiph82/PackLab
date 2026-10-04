"""Parametric collapsible-tube Design Models with captured or standalone roots."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .cross_section import CrossSection, CrossSectionSymmetry, SectionPoint, create_cross_section
from .design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_design_model_revision,
    create_standalone_design_model_revision,
    stable_feature_id,
)
from .design_model_binding import (
    DesignModelParentBindingRevision,
    StandaloneDesignGeometryRoot,
)
from .design_operations import DesignOperation, LoftSectionInput, create_loft_operation
from .design_preview import DesignPreview, tessellate_design_preview
from .flexible_pack_authority import flexible_pack_authority_handoff
from .reconstruction import ScaleState

_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_MAX_DIMENSION = 1e7
_SECTION_POINTS = 32


class TubeFamilyError(ValueError):
    """Raised when tube parameters cannot form a bounded, explicit Design Model."""


@dataclass(frozen=True, slots=True)
class TubeFamilyDimensions:
    """Explicit nominal design dimensions; values inherit the selected parent's unit."""

    body_length: float
    body_diameter: float
    shoulder_length: float
    shoulder_diameter: float
    neck_length: float
    neck_diameter: float
    cap_height: float
    cap_diameter: float
    crimp_length: float
    crimp_thickness: float

    def __post_init__(self) -> None:
        values = (
            self.body_length,
            self.body_diameter,
            self.shoulder_length,
            self.shoulder_diameter,
            self.neck_length,
            self.neck_diameter,
            self.cap_height,
            self.cap_diameter,
            self.crimp_length,
            self.crimp_thickness,
        )
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0.0
            or value > _MAX_DIMENSION
            for value in values
        ):
            raise TubeFamilyError("tube_dimension_must_be_finite_positive_and_bounded")
        if (
            self.body_diameter <= self.shoulder_diameter
            or self.shoulder_diameter <= self.neck_diameter
            or self.cap_diameter < self.neck_diameter
            or self.crimp_thickness >= self.body_diameter
            or self.crimp_length >= self.body_length
        ):
            raise TubeFamilyError("tube_dimension_relationship_impossible")
        total_height = (
            self.crimp_length
            + self.body_length
            + self.shoulder_length
            + self.neck_length
            + self.cap_height
        )
        if not math.isfinite(total_height) or total_height > _MAX_DIMENSION:
            raise TubeFamilyError("tube_total_height_exceeds_bound")

    def as_dict(self, coordinate_unit: str) -> dict[str, object]:
        return {
            "body_length": self.body_length,
            "body_diameter": self.body_diameter,
            "shoulder_length": self.shoulder_length,
            "shoulder_diameter": self.shoulder_diameter,
            "neck_length": self.neck_length,
            "neck_diameter": self.neck_diameter,
            "cap_height": self.cap_height,
            "cap_diameter": self.cap_diameter,
            "crimp_length": self.crimp_length,
            "crimp_thickness": self.crimp_thickness,
            "coordinate_unit": coordinate_unit,
            "scale_state": (
                "relative" if coordinate_unit == "reconstruction_units" else "metric-unverified"
            ),
            "physical_accuracy_validation_status": _DEFERRED,
        }


@dataclass(frozen=True, slots=True)
class TubeFamilyRevision:
    model: DesignModelRevision
    dimensions: TubeFamilyDimensions
    sections: tuple[CrossSection, ...]
    operation: DesignOperation
    preview: DesignPreview
    component_id: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.tube-family.v1",
            "authority_class": "DESIGN_MODEL_WITH_PREVIEW_PROXY",
            "model": self.model.as_dict(),
            "authority_and_limitations": flexible_pack_authority_handoff(self.model),
            "component_id": self.component_id,
            "dimensions": self.dimensions.as_dict(self.model.coordinate_unit),
            "sections": [section.as_dict() for section in self.sections],
            "operation": self.operation.as_dict(),
            "preview": self.preview.as_dict(),
            "flexible_wall_deformation_claimed": False,
            "physical_accuracy_validation_status": _DEFERRED,
            "mold_use_authorized": False,
            "cad_or_brep_generated": False,
            "scan_master_mutated": False,
        }


def build_tube_family(
    parent: DesignModelParentBindingRevision | StandaloneDesignGeometryRoot,
    dimensions: TubeFamilyDimensions,
    *,
    component_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    chord_tolerance: float = 0.25,
    maximum_angular_segments: int = 128,
) -> TubeFamilyRevision:
    """Build editable tube parameters and a disposable bounded loft preview."""
    if not isinstance(dimensions, TubeFamilyDimensions):
        raise TubeFamilyError("tube_dimensions_required")
    if not isinstance(parent, (DesignModelParentBindingRevision, StandaloneDesignGeometryRoot)):
        raise TubeFamilyError("explicit_tube_parent_authority_required")
    _identifier(component_id, "component_id")
    scale_state = parent.scale_state
    coordinate_unit = (
        "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    )
    feature_specs = (
        ("crimp", FeatureKind.CRIMP, "tube:crimp:v1"),
        ("body", FeatureKind.BODY, "tube:body:v1"),
        ("body_end", FeatureKind.BODY, "tube:body-end:v1"),
        ("shoulder", FeatureKind.SHOULDER, "tube:shoulder:v1"),
        ("neck", FeatureKind.NECK, "tube:neck:v1"),
        ("cap", FeatureKind.CAP, "tube:cap:v1"),
    )
    features = tuple(
        DesignModelFeatureReference(
            stable_feature_id(component_id, kind, semantic_key),
            component_id,
            kind,
            semantic_key,
        )
        for _name, kind, semantic_key in feature_specs
    )
    feature_by_name = {
        name: feature for (name, _kind, _key), feature in zip(feature_specs, features, strict=True)
    }
    parameter_values = (
        ("tube_body_length", dimensions.body_length),
        ("tube_body_diameter", dimensions.body_diameter),
        ("tube_shoulder_length", dimensions.shoulder_length),
        ("tube_shoulder_diameter", dimensions.shoulder_diameter),
        ("tube_neck_length", dimensions.neck_length),
        ("tube_neck_diameter", dimensions.neck_diameter),
        ("tube_cap_height", dimensions.cap_height),
        ("tube_cap_diameter", dimensions.cap_diameter),
        ("tube_crimp_length", dimensions.crimp_length),
        ("tube_crimp_thickness", dimensions.crimp_thickness),
    )
    parameters = tuple(
        DesignModelParameter(parameter_id, value, ParameterType.NUMBER, coordinate_unit)
        for parameter_id, value in parameter_values
    )
    if isinstance(parent, DesignModelParentBindingRevision):
        model = create_design_model_revision(
            parent,
            package_family=PackageFamily.TUBE,
            parameters=parameters,
            features=features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    else:
        model = create_standalone_design_model_revision(
            parent,
            package_family=PackageFamily.TUBE,
            parameters=parameters,
            features=features,
            actor_id=actor_id,
            reason=reason,
            created_at_utc=created_at_utc,
        )
    body_start = dimensions.crimp_length
    body_end = body_start + dimensions.body_length
    shoulder_end = body_end + dimensions.shoulder_length
    neck_end = shoulder_end + dimensions.neck_length
    cap_end = neck_end + dimensions.cap_height
    section_values = (
        ("crimp", 0.0, dimensions.body_diameter / 2.0, dimensions.crimp_thickness / 2.0),
        ("body", body_start, dimensions.body_diameter / 2.0, dimensions.body_diameter / 2.0),
        ("body_end", body_end, dimensions.body_diameter / 2.0, dimensions.body_diameter / 2.0),
        (
            "shoulder",
            shoulder_end,
            dimensions.shoulder_diameter / 2.0,
            dimensions.shoulder_diameter / 2.0,
        ),
        ("neck", neck_end, dimensions.neck_diameter / 2.0, dimensions.neck_diameter / 2.0),
        ("cap", cap_end, dimensions.cap_diameter / 2.0, dimensions.cap_diameter / 2.0),
    )
    section_list: list[CrossSection] = []
    for _name, _position, width_radius, depth_radius in section_values:
        section_list.append(
            _ellipse_section(
                component_id,
                width_radius,
                depth_radius,
                scale_state,
                previous_section_id=(section_list[-1].section_id if section_list else None),
            )
        )
    sections = tuple(section_list)
    loft_inputs = tuple(
        LoftSectionInput(feature_by_name[name].feature_id, section, position)
        for (name, position, _width_radius, _depth_radius), section in zip(
            section_values, sections, strict=True
        )
    )
    operation = create_loft_operation(model, loft_inputs)
    previews = tessellate_design_preview(
        model,
        cross_sections=sections,
        operations=(operation,),
        chord_tolerance=chord_tolerance,
        maximum_angular_segments=maximum_angular_segments,
    )
    if len(previews) != 1:
        raise TubeFamilyError("tube_preview_result_invalid")
    return TubeFamilyRevision(model, dimensions, sections, operation, previews[0], component_id)


def _ellipse_section(
    component_id: str,
    radius_x: float,
    radius_y: float,
    scale_state: ScaleState,
    *,
    previous_section_id: str | None,
) -> CrossSection:
    points = tuple(
        SectionPoint(
            radius_x * math.cos(math.tau * index / _SECTION_POINTS),
            radius_y * math.sin(math.tau * index / _SECTION_POINTS),
        )
        for index in range(_SECTION_POINTS)
    )
    return create_cross_section(
        component_id,
        points,
        symmetry=CrossSectionSymmetry.BOTH,
        scale_state=scale_state,
        previous_section_id=previous_section_id,
    )


def _identifier(value: object, field: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or not value[0].isalpha()
        or not all(character.isalnum() or character in "_.:-" for character in value)
    ):
        raise TubeFamilyError(f"{field}_invalid")


__all__ = [
    "TubeFamilyDimensions",
    "TubeFamilyError",
    "TubeFamilyRevision",
    "build_tube_family",
]
