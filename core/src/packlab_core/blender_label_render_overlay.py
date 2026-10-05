"""Exact BREP-derived renderer overlays for Label Zone artwork."""

from __future__ import annotations

import hashlib
import importlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .cad_adapter import CadAdapterError, cad_shape_geometry_digest, sample_cad_surface_regions
from .cad_brep import CadBrepRepresentationRevision
from .cad_label_surface_analysis import CadLabelSurfaceAnalysis
from .design_model import DesignModelRevision
from .label_artwork import (
    LabelArtworkAssetRevision,
    LabelArtworkAssignmentRevision,
    LabelArtworkMappingRevision,
)
from .label_metric_surface_binding import (
    LabelMetricSurfaceBinding,
    LabelMetricSurfaceBindingError,
    create_label_metric_surface_binding,
)
from .label_zone_placement import LabelZonePlacementRevision

LABEL_RENDER_OVERLAY_CONTRACT = "packlab.label-render-overlay-binding.v1"
RENDERER_ONLY_OFFSET_MM_UNVERIFIED = 0.001
_TOLERANCE = 1e-7


class LabelRenderOverlayError(ValueError):
    """Raised when exact source-surface overlay coordinates cannot be resolved."""


@dataclass(frozen=True, slots=True)
class LabelRenderOverlayBinding:
    revision_id: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    analysis_revision_id: str
    analysis_region_id: str
    metric_surface_binding_revision_id: str
    zone_id: str
    placement_revision_id: str
    mapping_revision_id: str
    assignment_revision_id: str
    artwork_revision_id: str
    artwork_sha256: str
    mapping_mode: str
    coordinate_unit: str
    geometry: tuple[tuple[str, object], ...]
    source_to_glb_viewer_transform: tuple[tuple[str, object], ...]
    renderer_only_offset_mm_unverified: float
    contract: str = LABEL_RENDER_OVERLAY_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != LABEL_RENDER_OVERLAY_CONTRACT
            or self.mapping_mode not in {"PLANAR_RECTANGULAR", "CYLINDRICAL_WRAP"}
            or self.coordinate_unit != "mm_unverified"
            or self.renderer_only_offset_mm_unverified != RENDERER_ONLY_OFFSET_MM_UNVERIFIED
            or self.revision_id != "label-render-overlay:" + _digest(self._identity())
        ):
            raise LabelRenderOverlayError("label_render_overlay_identity_invalid")

    def _identity(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_brep_geometry_sha256": self.source_brep_geometry_sha256,
            "analysis_revision_id": self.analysis_revision_id,
            "analysis_region_id": self.analysis_region_id,
            "metric_surface_binding_revision_id": self.metric_surface_binding_revision_id,
            "zone_id": self.zone_id,
            "placement_revision_id": self.placement_revision_id,
            "mapping_revision_id": self.mapping_revision_id,
            "assignment_revision_id": self.assignment_revision_id,
            "artwork_revision_id": self.artwork_revision_id,
            "artwork_sha256": self.artwork_sha256,
            "mapping_mode": self.mapping_mode,
            "coordinate_unit": self.coordinate_unit,
            "geometry": dict(self.geometry),
            "source_to_glb_viewer_transform": dict(self.source_to_glb_viewer_transform),
            "renderer_only_offset_mm_unverified": self.renderer_only_offset_mm_unverified,
            "geometry_authority_created": False,
            "physical_fit_verified": False,
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "DERIVED_RENDER_PRESENTATION_ONLY",
            "revision_id": self.revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_brep_geometry_sha256": self.source_brep_geometry_sha256,
            "analysis_revision_id": self.analysis_revision_id,
            "analysis_region_id": self.analysis_region_id,
            "metric_surface_binding_revision_id": self.metric_surface_binding_revision_id,
            "zone_id": self.zone_id,
            "placement_revision_id": self.placement_revision_id,
            "mapping_revision_id": self.mapping_revision_id,
            "assignment_revision_id": self.assignment_revision_id,
            "artwork_revision_id": self.artwork_revision_id,
            "artwork_sha256": self.artwork_sha256,
            "mapping_mode": self.mapping_mode,
            "coordinate_unit": self.coordinate_unit,
            "geometry": dict(self.geometry),
            "source_to_glb_viewer_transform": dict(self.source_to_glb_viewer_transform),
            "renderer_only_offset_mm_unverified": self.renderer_only_offset_mm_unverified,
            "geometry_authority_created": False,
            "physical_fit_verified": False,
            "manufacturing_authorized": False,
        }


def create_label_render_overlay_binding(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    analysis: CadLabelSurfaceAnalysis,
    metric_binding: LabelMetricSurfaceBinding,
    placement: LabelZonePlacementRevision,
    mapping: LabelArtworkMappingRevision,
    assignment: LabelArtworkAssignmentRevision,
    artwork: LabelArtworkAssetRevision,
) -> LabelRenderOverlayBinding:
    """Resolve exact host geometry again and persist only stable renderer coordinates."""
    zone = placement.label_zone
    if (
        not isinstance(model, DesignModelRevision)
        or not isinstance(representation, CadBrepRepresentationRevision)
        or not isinstance(analysis, CadLabelSurfaceAnalysis)
        or not isinstance(metric_binding, LabelMetricSurfaceBinding)
        or assignment.status != "ASSIGNED"
        or assignment.zone_id != zone.zone_id
        or assignment.placement_revision_id != placement.revision_id
        or assignment.mapping_revision_id != mapping.revision_id
        or assignment.artwork_revision_id != artwork.revision_id
        or mapping.zone_id != zone.zone_id
        or mapping.placement_revision_id != placement.revision_id
        or mapping.source_artwork_revision_id != artwork.revision_id
        or mapping.source_artwork_sha256 != artwork.content_sha256
        or zone.source_design_model_revision_id != model.revision_id
        or zone.source_brep_revision_id != representation.revision_id
        or zone.source_brep_geometry_sha256 != representation.geometry_sha256
        or metric_binding.zone_id != zone.zone_id
        or metric_binding.placement_revision_id != placement.revision_id
        or metric_binding.source_design_model_revision_id != model.revision_id
        or metric_binding.source_brep_revision_id != representation.revision_id
        or metric_binding.source_brep_geometry_sha256 != representation.geometry_sha256
        or metric_binding.analysis_revision_id != analysis.revision_id
        or metric_binding.analysis_region_id
        not in {item.analysis_region_id for item in analysis.candidates}
    ):
        raise LabelRenderOverlayError("label_render_overlay_provenance_or_png_invalid")
    if artwork.media_type == "image/svg+xml":
        raise LabelRenderOverlayError("label_render_overlay_svg_scene_texturing_unsupported")
    if artwork.media_type != "image/png":
        raise LabelRenderOverlayError("label_render_overlay_media_type_unsupported")
    try:
        verified = create_label_metric_surface_binding(
            model, representation, placement, analysis, metric_binding.analysis_region_id
        )
    except (CadAdapterError, LabelMetricSurfaceBindingError, TypeError, ValueError) as error:
        raise LabelRenderOverlayError("label_render_overlay_host_resolution_failed") from error
    if verified != metric_binding:
        raise LabelRenderOverlayError("label_render_overlay_metric_binding_stale")
    if cad_shape_geometry_digest(representation.shape_handle) != representation.geometry_sha256:
        raise LabelRenderOverlayError("label_render_overlay_brep_digest_mismatch")
    face = _resolve_face(representation, analysis, metric_binding.analysis_region_id)
    if metric_binding.mapping_mode == "PLANAR_RECTANGULAR":
        geometry = _planar_geometry(face, placement)
    elif metric_binding.mapping_mode == "CYLINDRICAL_WRAP":
        geometry = _cylindrical_geometry(face, placement, assignment)
    else:
        raise LabelRenderOverlayError("label_render_overlay_mapping_unsupported")
    scale = 0.001 if model.coordinate_unit == "mm_unverified" else 1.0
    if model.scale_state.value != "metric-unverified" or model.coordinate_unit != "mm_unverified":
        raise LabelRenderOverlayError("label_render_overlay_scale_must_be_mm_unverified")
    geometry["uv_orientation"] = assignment.orientation
    geometry["artwork_mapping"] = mapping.as_dict()
    geometry["artwork_width"] = artwork.width
    geometry["artwork_height"] = artwork.height
    geometry["artwork_pixel_origin"] = "TOP_LEFT"
    geometry["placement_boundary_normalized_uv"] = [
        placement.boundary.u_min,
        placement.boundary.v_min,
        placement.boundary.u_max,
        placement.boundary.v_max,
    ]
    geometry["artwork_media_type"] = artwork.media_type
    geometry["overlay_id"] = (
        "label-render-overlay:"
        + hashlib.sha256((zone.zone_id + ":" + assignment.variant_id).encode("utf-8")).hexdigest()
    )
    transform = {
        "kind": "uniform_scale",
        "source_unit": "mm_unverified",
        "target_unit": "meters",
        "scale": [scale, scale, scale],
        "inverse_scale": [1.0 / scale] * 3,
        "reversible": True,
        "source_coordinates_preserved_in_buffer": True,
        "matches_cad_export_viewer_transform": True,
        "physical_authority_upgraded": False,
    }
    values = {
        "contract": LABEL_RENDER_OVERLAY_CONTRACT,
        "source_design_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "source_brep_geometry_sha256": representation.geometry_sha256,
        "analysis_revision_id": analysis.revision_id,
        "analysis_region_id": metric_binding.analysis_region_id,
        "metric_surface_binding_revision_id": metric_binding.revision_id,
        "zone_id": zone.zone_id,
        "placement_revision_id": placement.revision_id,
        "mapping_revision_id": mapping.revision_id,
        "assignment_revision_id": assignment.revision_id,
        "artwork_revision_id": artwork.revision_id,
        "artwork_sha256": artwork.content_sha256,
        "mapping_mode": metric_binding.mapping_mode,
        "coordinate_unit": "mm_unverified",
        "geometry": geometry,
        "source_to_glb_viewer_transform": transform,
        "renderer_only_offset_mm_unverified": RENDERER_ONLY_OFFSET_MM_UNVERIFIED,
        "geometry_authority_created": False,
        "physical_fit_verified": False,
    }
    return LabelRenderOverlayBinding(
        "label-render-overlay:" + _digest(values),
        model.revision_id,
        representation.revision_id,
        representation.geometry_sha256,
        analysis.revision_id,
        metric_binding.analysis_region_id,
        metric_binding.revision_id,
        zone.zone_id,
        placement.revision_id,
        mapping.revision_id,
        assignment.revision_id,
        artwork.revision_id,
        artwork.content_sha256,
        metric_binding.mapping_mode,
        "mm_unverified",
        tuple(sorted(geometry.items())),
        tuple(sorted(transform.items())),
        RENDERER_ONLY_OFFSET_MM_UNVERIFIED,
    )


def _resolve_face(
    representation: CadBrepRepresentationRevision,
    analysis: CadLabelSurfaceAnalysis,
    region_id: str,
) -> Any:
    candidate = next(
        (item for item in analysis.candidates if item.analysis_region_id == region_id), None
    )
    if candidate is None:
        raise LabelRenderOverlayError("label_render_overlay_analysis_region_missing")
    try:
        regions = sample_cad_surface_regions(
            representation.shape_handle,
            samples_per_axis=analysis.policy.samples_per_axis,
            maximum_faces=analysis.policy.maximum_faces,
            maximum_regions=analysis.policy.maximum_regions,
            maximum_differential_samples=analysis.policy.maximum_differential_samples,
        )
    except CadAdapterError as error:
        raise LabelRenderOverlayError("label_render_overlay_brep_sampling_failed") from error
    expected = tuple(
        sorted({tuple(round(value, 9) for value in point) for point in candidate.support_points})
    )
    matches: list[Any] = []
    for region in regions:
        observed = tuple(
            sorted(
                {
                    tuple(round(value, 9) for value in sample.point)
                    for sample in region.support_points
                }
            )
        )
        if observed == expected and region._runtime_face is not None:
            if not any(region._runtime_face.IsSame(face) for face in matches):
                matches.append(region._runtime_face)
    if len(matches) != 1:
        raise LabelRenderOverlayError("label_render_overlay_host_resolution_not_unique")
    return matches[0]


def _planar_geometry(face: Any, placement: LabelZonePlacementRevision) -> dict[str, object]:
    modules = _ocp_modules()
    surface = modules["adaptor"].BRepAdaptor_Surface(face, True)
    bounds = modules["tools"].BRepTools.UVBounds_s(face)
    u0, u1, v0, v1 = (float(value) for value in bounds)
    points = [surface.Value(u, v) for u, v in ((u0, v0), (u0, v1), (u1, v0), (u1, v1))]
    coords = [(float(point.X()), float(point.Y()), float(point.Z())) for point in points]
    xs, zs = [point[0] for point in coords], [point[2] for point in coords]
    y_values = [point[1] for point in coords]
    if max(y_values) - min(y_values) > _TOLERANCE:
        raise LabelRenderOverlayError("label_render_overlay_planar_frame_invalid")
    zone = placement.label_zone
    plane = surface.Plane()
    direction = plane.Axis().Direction()
    normal_y = float(direction.Y())
    if face.Orientation() == modules["topabs"].TopAbs_REVERSED:
        normal_y *= -1.0
    expected_normal = 1.0 if zone.zone_kind.value == "front" else -1.0
    if (
        abs(float(direction.X())) > _TOLERANCE
        or abs(float(direction.Z())) > _TOLERANCE
        or abs(normal_y - expected_normal) > _TOLERANCE
    ):
        raise LabelRenderOverlayError("label_render_overlay_planar_orientation_invalid")
    boundary = placement.boundary
    u_sign = 1.0 if zone.zone_kind.value == "front" else -1.0
    u_origin = min(xs) if u_sign > 0 else max(xs)
    x0 = u_origin + u_sign * (max(xs) - min(xs)) * boundary.u_min
    x1 = u_origin + u_sign * (max(xs) - min(xs)) * boundary.u_max
    z0 = min(zs) + (max(zs) - min(zs)) * boundary.v_min
    z1 = min(zs) + (max(zs) - min(zs)) * boundary.v_max
    y = sum(y_values) / len(y_values) + normal_y * RENDERER_ONLY_OFFSET_MM_UNVERIFIED
    corners = ((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1))
    return {
        "mode": "PLANAR_RECTANGULAR",
        "host_frame": "PACKLAB_FRONT_BACK",
        "origin_mm_unverified": [u_origin, sum(y_values) / len(y_values), min(zs)],
        "u_axis": [u_sign, 0.0, 0.0],
        "v_axis": [0.0, 0.0, 1.0],
        "surface_normal": [0.0, normal_y, 0.0],
        "zone_corners_mm_unverified": [list(item) for item in corners],
        "placement_boundary_normalized_uv": [
            boundary.u_min,
            boundary.v_min,
            boundary.u_max,
            boundary.v_max,
        ],
        "overlay_kind": "DETERMINISTIC_QUAD",
        "uv_domain": [0.0, 1.0],
        "source_face_identity_persisted": False,
    }


def _cylindrical_geometry(
    face: Any, placement: LabelZonePlacementRevision, assignment: LabelArtworkAssignmentRevision
) -> dict[str, object]:
    modules = _ocp_modules()
    surface = modules["adaptor"].BRepAdaptor_Surface(face, True)
    cylinder = surface.Cylinder()
    position = cylinder.Position()
    center = position.Location()
    axis = position.Direction()
    seam = position.YDirection()
    ax, ay, az = float(axis.X()), float(axis.Y()), float(axis.Z())
    radius = float(cylinder.Radius())
    if (
        abs(ax) > _TOLERANCE
        or abs(ay) > _TOLERANCE
        or abs(az - 1.0) > _TOLERANCE
        or abs(float(seam.X())) > _TOLERANCE
        or abs(float(seam.Y()) - 1.0) > _TOLERANCE
        or radius <= _TOLERANCE
    ):
        raise LabelRenderOverlayError("label_render_overlay_cylinder_frame_invalid")
    cx, cy, cz = float(center.X()), float(center.Y()), float(center.Z())
    _, _, z_min, _, _, z_max = _bounds(face)
    zone = placement.label_zone
    boundary = placement.boundary
    seam_u = float(assignment.wrap_seam_u_normalized or 0.0)
    u0 = boundary.u_min - seam_u
    u1 = boundary.u_max - seam_u
    theta0, theta1 = 2.0 * math.pi * u0, 2.0 * math.pi * u1
    z0 = z_min + (z_max - z_min) * boundary.v_min
    z1 = z_min + (z_max - z_min) * boundary.v_max
    return {
        "mode": "CYLINDRICAL_WRAP",
        "center_mm_unverified": [cx, cy, cz],
        "axis": [ax, ay, az],
        "radius_mm_unverified": radius,
        "seam_direction": [0.0, 1.0, 0.0],
        "azimuth_direction": "+Y_TO_PLUS_X",
        "angular_start_radians": theta0,
        "angular_end_radians": theta1,
        "axial_start_mm_unverified": z0,
        "axial_end_mm_unverified": z1,
        "placement_boundary_normalized_uv": [
            boundary.u_min,
            boundary.v_min,
            boundary.u_max,
            boundary.v_max,
        ],
        "overlay_kind": "BOUNDED_SEGMENTED_CYLINDRICAL_PATCH",
        "uv_domain": [0.0, 1.0],
        "source_face_identity_persisted": False,
        "source_zone_kind": zone.zone_kind.value,
    }


def _bounds(face: Any) -> tuple[float, float, float, float, float, float]:
    modules = _ocp_modules()
    shape = modules["bndlib"].Bnd_Box()
    modules["brepbnd"].BRepBndLib.Add_s(face, shape)
    values = tuple(float(value) for value in shape.Get())
    if len(values) != 6:
        raise LabelRenderOverlayError("label_render_overlay_surface_bounds_invalid")
    return (values[0], values[1], values[2], values[3], values[4], values[5])


def _ocp_modules() -> dict[str, Any]:
    return {
        "adaptor": importlib.import_module("OCP.BRepAdaptor"),
        "tools": importlib.import_module("OCP.BRepTools"),
        "topabs": importlib.import_module("OCP.TopAbs"),
        "bndlib": importlib.import_module("OCP.Bnd"),
        "brepbnd": importlib.import_module("OCP.BRepBndLib"),
    }


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


__all__ = [
    "LABEL_RENDER_OVERLAY_CONTRACT",
    "LabelRenderOverlayBinding",
    "LabelRenderOverlayError",
    "create_label_render_overlay_binding",
]
