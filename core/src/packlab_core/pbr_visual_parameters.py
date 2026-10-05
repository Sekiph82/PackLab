"""Bounded, digest-stable PBR render parameters with visual-only authority."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass

from .component_visual_assignments import GeometryMaterialAssignmentRevision

PBR_VISUAL_PARAMETERS_CONTRACT = "packlab.pbr-visual-parameters.v1"
NORMAL_DETAIL_CONTRACT = "packlab.pbr-normal-detail-reference.v1"
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,255}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PbrVisualParametersError(ValueError):
    """Raised when render-only PBR values or normal reference metadata are invalid."""


@dataclass(frozen=True, slots=True)
class NormalDetailReference:
    revision_id: str
    texture_asset_revision_id: str
    texture_sha256: str
    strength_factor: float
    coordinate_frame: str = "TANGENT_SPACE"
    contract: str = NORMAL_DETAIL_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != NORMAL_DETAIL_CONTRACT
            or not _valid_id(self.texture_asset_revision_id)
            or not isinstance(self.texture_sha256, str)
            or not _SHA256.fullmatch(self.texture_sha256)
            or not isinstance(self.coordinate_frame, str)
            or self.coordinate_frame not in {"TANGENT_SPACE", "OBJECT_SPACE"}
            or not _finite_range(self.strength_factor, 0.0, 2.0)
            or self.revision_id != "pbr-normal-detail:" + _digest(_normal_detail_identity(self))
        ):
            raise PbrVisualParametersError("normal_detail_reference_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "revision_id": self.revision_id,
            "texture_asset_revision_id": self.texture_asset_revision_id,
            "texture_sha256": self.texture_sha256,
            "strength_factor": self.strength_factor,
            "coordinate_frame": self.coordinate_frame,
            "authority_semantics": "RENDER_APPEARANCE_METADATA_ONLY",
            "changes_geometry": False,
            "measured_surface_normal_inferred": False,
        }


@dataclass(frozen=True, slots=True)
class PbrVisualParameterRevision:
    revision_id: str
    source_design_model_revision_id: str
    component_id: str
    source_geometry_material_assignment_revision_id: str
    source_material_library_revision_id: str
    source_material_id: str
    base_color_rgb: tuple[float, float, float]
    roughness_factor: float
    transmission_factor: float
    opacity_factor: float
    ior: float
    normal_detail: NormalDetailReference | None
    contract: str = PBR_VISUAL_PARAMETERS_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != PBR_VISUAL_PARAMETERS_CONTRACT
            or not _valid_id(self.source_design_model_revision_id)
            or not _valid_id(self.component_id)
            or not _valid_id(self.source_geometry_material_assignment_revision_id)
            or not _valid_id(self.source_material_library_revision_id)
            or not _valid_id(self.source_material_id)
        ):
            raise PbrVisualParametersError("pbr_visual_source_binding_invalid")
        if not isinstance(self.base_color_rgb, tuple) or len(self.base_color_rgb) != 3:
            raise PbrVisualParametersError("pbr_base_color_invalid")
        color = (
            _normalized_range(self.base_color_rgb[0], 0.0, 1.0, "pbr_base_color_invalid"),
            _normalized_range(self.base_color_rgb[1], 0.0, 1.0, "pbr_base_color_invalid"),
            _normalized_range(self.base_color_rgb[2], 0.0, 1.0, "pbr_base_color_invalid"),
        )
        object.__setattr__(self, "base_color_rgb", color)
        roughness = _normalized_range(self.roughness_factor, 0.0, 1.0, "pbr_roughness_invalid")
        transmission = _normalized_range(
            self.transmission_factor, 0.0, 1.0, "pbr_transmission_invalid"
        )
        opacity = _normalized_range(self.opacity_factor, 0.0, 1.0, "pbr_opacity_invalid")
        ior = _normalized_range(self.ior, 1.0, 3.0, "pbr_ior_out_of_bounds")
        object.__setattr__(self, "roughness_factor", roughness)
        object.__setattr__(self, "transmission_factor", transmission)
        object.__setattr__(self, "opacity_factor", opacity)
        object.__setattr__(self, "ior", ior)
        if opacity < 1.0 and transmission > 0.0:
            raise PbrVisualParametersError("pbr_opacity_transmission_policy_conflict")
        if self.normal_detail is not None and not isinstance(
            self.normal_detail, NormalDetailReference
        ):
            raise PbrVisualParametersError("normal_detail_reference_required")
        if self.revision_id != "pbr-visual-parameters:" + _digest(_pbr_identity(self)):
            raise PbrVisualParametersError("pbr_visual_parameters_identity_mismatch")

    @property
    def alpha_mode(self) -> str:
        return "BLEND" if self.opacity_factor < 1.0 else "OPAQUE"

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "RENDER_APPEARANCE_PARAMETERS_ONLY",
            "revision_id": self.revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "component_id": self.component_id,
            "source_geometry_material_assignment_revision_id": (
                self.source_geometry_material_assignment_revision_id
            ),
            "source_material_library_revision_id": self.source_material_library_revision_id,
            "source_material_id": self.source_material_id,
            "base_color_rgb": list(self.base_color_rgb),
            "base_color_unit": "unitless_srgb_display_reference",
            "roughness_factor": self.roughness_factor,
            "transmission_factor": self.transmission_factor,
            "opacity_factor": self.opacity_factor,
            "alpha_mode": self.alpha_mode,
            "ior": self.ior,
            "ior_semantics": "RENDER_PARAMETER_NOT_MEASURED_REFRACTIVE_INDEX",
            "normal_detail": self.normal_detail.as_dict() if self.normal_detail else None,
            "authority_semantics": "NON_CERTIFIED_VISUAL_REFERENCE",
            "values_are_measured_material_properties": False,
            "optical_properties_verified": False,
            "material_certified": False,
            "regulatory_approval": False,
            "changes_design_model": False,
            "changes_geometry": False,
        }


def create_normal_detail_reference(
    texture_asset_revision_id: str,
    texture_sha256: str,
    *,
    strength_factor: float = 1.0,
    coordinate_frame: str = "TANGENT_SPACE",
) -> NormalDetailReference:
    strength = _normalized_range(strength_factor, 0.0, 2.0, "normal_detail_strength_invalid")
    values: dict[str, object] = {
        "contract": NORMAL_DETAIL_CONTRACT,
        "texture_asset_revision_id": texture_asset_revision_id,
        "texture_sha256": texture_sha256,
        "strength_factor": strength,
        "coordinate_frame": coordinate_frame,
    }
    return NormalDetailReference(
        revision_id="pbr-normal-detail:" + _digest(values),
        texture_asset_revision_id=texture_asset_revision_id,
        texture_sha256=texture_sha256,
        strength_factor=strength,
        coordinate_frame=coordinate_frame,
    )


def create_pbr_visual_parameter_revision(
    geometry_material_assignment: GeometryMaterialAssignmentRevision,
    *,
    base_color_rgb: tuple[float, float, float],
    roughness_factor: float,
    transmission_factor: float,
    opacity_factor: float,
    ior: float,
    normal_detail: NormalDetailReference | None = None,
) -> PbrVisualParameterRevision:
    if (
        not isinstance(geometry_material_assignment, GeometryMaterialAssignmentRevision)
        or geometry_material_assignment.status != "ASSIGNED"
    ):
        raise PbrVisualParametersError("active_geometry_material_assignment_required")
    material_library_revision_id = geometry_material_assignment.material_library_revision_id
    material_id = geometry_material_assignment.material_id
    if (
        not isinstance(material_library_revision_id, str)
        or not _valid_id(material_library_revision_id)
        or not isinstance(material_id, str)
        or not _valid_id(material_id)
    ):
        raise PbrVisualParametersError("pbr_visual_source_binding_invalid")
    if not isinstance(base_color_rgb, tuple) or len(base_color_rgb) != 3:
        raise PbrVisualParametersError("pbr_base_color_invalid")
    color = (
        _normalized_range(base_color_rgb[0], 0.0, 1.0, "pbr_base_color_invalid"),
        _normalized_range(base_color_rgb[1], 0.0, 1.0, "pbr_base_color_invalid"),
        _normalized_range(base_color_rgb[2], 0.0, 1.0, "pbr_base_color_invalid"),
    )
    roughness = _normalized_range(roughness_factor, 0.0, 1.0, "pbr_roughness_invalid")
    transmission = _normalized_range(transmission_factor, 0.0, 1.0, "pbr_transmission_invalid")
    opacity = _normalized_range(opacity_factor, 0.0, 1.0, "pbr_opacity_invalid")
    normalized_ior = _normalized_range(ior, 1.0, 3.0, "pbr_ior_out_of_bounds")
    if opacity < 1.0 and transmission > 0.0:
        raise PbrVisualParametersError("pbr_opacity_transmission_policy_conflict")
    if normal_detail is not None and not isinstance(normal_detail, NormalDetailReference):
        raise PbrVisualParametersError("normal_detail_reference_required")
    values: dict[str, object] = {
        "contract": PBR_VISUAL_PARAMETERS_CONTRACT,
        "source_design_model_revision_id": geometry_material_assignment.source_design_model_revision_id,
        "component_id": geometry_material_assignment.component_id,
        "source_geometry_material_assignment_revision_id": geometry_material_assignment.revision_id,
        "source_material_library_revision_id": material_library_revision_id,
        "source_material_id": material_id,
        "base_color_rgb": list(color),
        "roughness_factor": roughness,
        "transmission_factor": transmission,
        "opacity_factor": opacity,
        "ior": normalized_ior,
        "normal_detail_revision_id": normal_detail.revision_id if normal_detail else None,
    }
    return PbrVisualParameterRevision(
        revision_id="pbr-visual-parameters:" + _digest(values),
        source_design_model_revision_id=geometry_material_assignment.source_design_model_revision_id,
        component_id=geometry_material_assignment.component_id,
        source_geometry_material_assignment_revision_id=geometry_material_assignment.revision_id,
        source_material_library_revision_id=material_library_revision_id,
        source_material_id=material_id,
        base_color_rgb=color,
        roughness_factor=roughness,
        transmission_factor=transmission,
        opacity_factor=opacity,
        ior=normalized_ior,
        normal_detail=normal_detail,
    )


def _pbr_identity(parameters: PbrVisualParameterRevision) -> dict[str, object]:
    return {
        "contract": parameters.contract,
        "source_design_model_revision_id": parameters.source_design_model_revision_id,
        "component_id": parameters.component_id,
        "source_geometry_material_assignment_revision_id": (
            parameters.source_geometry_material_assignment_revision_id
        ),
        "source_material_library_revision_id": parameters.source_material_library_revision_id,
        "source_material_id": parameters.source_material_id,
        "base_color_rgb": list(parameters.base_color_rgb),
        "roughness_factor": parameters.roughness_factor,
        "transmission_factor": parameters.transmission_factor,
        "opacity_factor": parameters.opacity_factor,
        "ior": parameters.ior,
        "normal_detail_revision_id": (
            parameters.normal_detail.revision_id if parameters.normal_detail else None
        ),
    }


def _normal_detail_identity(reference: NormalDetailReference) -> dict[str, object]:
    return {
        "contract": reference.contract,
        "texture_asset_revision_id": reference.texture_asset_revision_id,
        "texture_sha256": reference.texture_sha256,
        "strength_factor": reference.strength_factor,
        "coordinate_frame": reference.coordinate_frame,
    }


def _valid_id(value: object) -> bool:
    return isinstance(value, str) and _IDENTIFIER.fullmatch(value) is not None


def _finite_range(value: object, minimum: float, maximum: float) -> bool:
    try:
        _normalized_range(value, minimum, maximum, "pbr_value_invalid")
    except PbrVisualParametersError:
        return False
    return True


def _normalized_range(value: object, minimum: float, maximum: float, error_code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PbrVisualParametersError(error_code)
    try:
        normalized = float(value)
    except OverflowError as error:
        raise PbrVisualParametersError(error_code) from error
    if not math.isfinite(normalized) or not minimum <= normalized <= maximum:
        raise PbrVisualParametersError(error_code)
    return 0.0 if normalized == 0.0 else normalized


def _digest(value: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


__all__ = [
    "NORMAL_DETAIL_CONTRACT",
    "PBR_VISUAL_PARAMETERS_CONTRACT",
    "NormalDetailReference",
    "PbrVisualParameterRevision",
    "PbrVisualParametersError",
    "create_normal_detail_reference",
    "create_pbr_visual_parameter_revision",
]
