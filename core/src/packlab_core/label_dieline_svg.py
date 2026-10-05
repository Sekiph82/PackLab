"""Deterministic vector SVG export for explicitly unverified label dielines."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from xml.sax.saxutils import escape

from .label_metric_surface_binding import LabelDielineRevision
from .label_zone_placement import LabelZonePlacementRevision
from .reconstruction import ScaleState

LABEL_DIELINE_SVG_CONTRACT = "packlab.label-dieline-svg-export.v1"
SCALE_MARK_LENGTH_MM_UNVERIFIED = 10.0
PRINT_DISCLAIMER = (
    "DESIGN OUTPUT ONLY — dimensions are mm_unverified. Physical accuracy, print fit, "
    "printer requirements, certification, manufacturing, and regulatory suitability "
    "are not verified. Do not treat this file as print-ready."
)


class LabelDielineSvgExportError(ValueError):
    """Raised when a dieline cannot be exported with truthful units and provenance."""


@dataclass(frozen=True, slots=True)
class LabelDielineSvgExport:
    revision_id: str
    source_dieline_revision_id: str
    svg_sha256: str
    svg_bytes: bytes
    width_mm_unverified: float
    height_mm_unverified: float
    contract: str = LABEL_DIELINE_SVG_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != LABEL_DIELINE_SVG_CONTRACT
            or not self.source_dieline_revision_id
            or hashlib.sha256(self.svg_bytes).hexdigest() != self.svg_sha256
            or not math.isfinite(self.width_mm_unverified)
            or not math.isfinite(self.height_mm_unverified)
            or self.width_mm_unverified <= 0.0
            or self.height_mm_unverified <= 0.0
            or self.revision_id
            != "label-dieline-svg:"
            + _digest(
                {
                    "contract": self.contract,
                    "source_dieline_revision_id": self.source_dieline_revision_id,
                    "svg_sha256": self.svg_sha256,
                    "width_mm_unverified": self.width_mm_unverified,
                    "height_mm_unverified": self.height_mm_unverified,
                }
            )
        ):
            raise LabelDielineSvgExportError("label_dieline_svg_export_identity_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "DERIVED_LABEL_DIELINE_SVG",
            "revision_id": self.revision_id,
            "source_dieline_revision_id": self.source_dieline_revision_id,
            "svg_sha256": self.svg_sha256,
            "media_type": "image/svg+xml",
            "coordinate_unit": "mm_unverified",
            "width": self.width_mm_unverified,
            "height": self.height_mm_unverified,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "print_fit_verified": False,
            "printer_certified": False,
            "manufacturing_authorized": False,
            "print_ready": False,
        }


def export_label_dieline_svg(
    dieline: LabelDielineRevision,
    placement: LabelZonePlacementRevision,
) -> LabelDielineSvgExport:
    """Export exact print-intent boundaries as deterministic vector-only SVG paths."""
    if not isinstance(dieline, LabelDielineRevision):
        raise LabelDielineSvgExportError("label_dieline_required")
    if not isinstance(placement, LabelZonePlacementRevision):
        raise LabelDielineSvgExportError("label_dieline_placement_required")
    zone = placement.label_zone
    if (
        zone.scale_state is not ScaleState.METRIC_UNVERIFIED
        or zone.coordinate_unit != "mm_unverified"
    ):
        raise LabelDielineSvgExportError("label_dieline_scale_must_be_mm_unverified")
    if (
        dieline.coordinate_unit != "mm_unverified"
        or dieline.zone_id != placement.zone_id
        or dieline.placement_revision_id != placement.revision_id
        or dieline.binding.zone_id != placement.zone_id
        or dieline.binding.placement_revision_id != placement.revision_id
        or dieline.binding.source_design_model_revision_id != zone.source_design_model_revision_id
        or dieline.binding.source_brep_revision_id != zone.source_brep_revision_id
        or dieline.binding.source_brep_geometry_sha256 != zone.source_brep_geometry_sha256
        or dieline.binding.parent_kind != zone.parent_kind.value
        or dieline.binding.parent_authority_revision_id != zone.parent_authority_revision_id
    ):
        raise LabelDielineSvgExportError("label_dieline_source_binding_mismatch")
    if (
        dieline.source_dieline_revision_id is None
        or len(dieline.safe_boundary_vertices) != 4
        or len(dieline.bleed_boundary_vertices) != 4
    ):
        raise LabelDielineSvgExportError("label_dieline_print_intent_required")

    source_points = dieline.boundary_vertices
    safe_points = dieline.safe_boundary_vertices
    bleed_points = dieline.bleed_boundary_vertices
    all_points = (*source_points, *safe_points, *bleed_points)
    if not all(math.isfinite(value) for point in all_points for value in point):
        raise LabelDielineSvgExportError("label_dieline_svg_coordinates_non_finite")
    bleed_xs = tuple(point[0] for point in bleed_points)
    bleed_ys = tuple(point[1] for point in bleed_points)
    bleed_x_min, bleed_x_max = min(bleed_xs), max(bleed_xs)
    bleed_y_min, bleed_y_max = min(bleed_ys), max(bleed_ys)

    # Keep a separate verification strip below the bleed boundary. Its vector bar is
    # exactly 10 mm in the same unverified design coordinate system.
    view_x_min = bleed_x_min - 2.0
    view_x_max = max(bleed_x_max + 2.0, view_x_min + SCALE_MARK_LENGTH_MM_UNVERIFIED + 4.0)
    view_y_min = bleed_y_min - 2.0
    mark_y = bleed_y_max + 7.0
    view_y_max = mark_y + 2.0
    view_width, view_height = view_x_max - view_x_min, view_y_max - view_y_min
    provenance = {
        "current-dieline": dieline.revision_id,
        "source-dieline": dieline.source_dieline_revision_id,
        "source-zone": dieline.zone_id,
        "source-placement": dieline.placement_revision_id,
        "source-design-model": dieline.binding.source_design_model_revision_id,
        "source-brep": dieline.binding.source_brep_revision_id,
        "source-brep-sha256": dieline.binding.source_brep_geometry_sha256,
        "source-analysis": dieline.binding.analysis_revision_id,
        "source-analysis-region": dieline.binding.analysis_region_id,
        "source-metric-binding": dieline.binding.revision_id,
    }
    attrs = " ".join(
        f'data-{key}="{escape(value, {chr(34): "&quot;"})}"' for key, value in provenance.items()
    )
    paths = [
        _path("source-outline", source_points),
        _path("safe-boundary", safe_points),
        _path("bleed-boundary", bleed_points),
        _scale_mark(view_x_min, mark_y),
    ]
    svg_text = "\n".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="{_n(view_x_min)} {_n(view_y_min)} {_n(view_width)} {_n(view_height)}" width="{_n(view_width)}mm" height="{_n(view_height)}mm" data-coordinate-unit="mm_unverified" data-scale-state="METRIC_UNVERIFIED" {attrs}>',
            f"  <metadata>{escape(PRINT_DISCLAIMER)} Physical accuracy validation status: DEFERRED_OWNER_VALIDATION.</metadata>",
            '  <g id="label-dieline-layers" fill="none" stroke="black" stroke-width="0.2">',
            f'    <g id="source-outline-layer" data-layer="SOURCE_OUTLINE">{paths[0]}</g>',
            f'    <g id="safe-boundary-layer" data-layer="SAFE_MARGIN" data-margin-mm-unverified="{_n(dieline.safe_margin_mm_unverified)}">{paths[1]}</g>',
            f'    <g id="bleed-boundary-layer" data-layer="BLEED" data-bleed-mm-unverified="{_n(dieline.bleed_mm_unverified)}">{paths[2]}</g>',
            f'    <g id="scale-verification-layer" data-layer="SCALE_VERIFICATION" data-coordinate-unit="mm_unverified" data-known-spacing-mm-unverified="{_n(SCALE_MARK_LENGTH_MM_UNVERIFIED)}">{paths[3]}</g>',
            "  </g>",
            "</svg>",
            "",
        )
    )
    svg_bytes = svg_text.encode("utf-8")
    svg_sha256 = hashlib.sha256(svg_bytes).hexdigest()
    identity = {
        "contract": LABEL_DIELINE_SVG_CONTRACT,
        "source_dieline_revision_id": dieline.revision_id,
        "svg_sha256": svg_sha256,
        "width_mm_unverified": view_width,
        "height_mm_unverified": view_height,
    }
    return LabelDielineSvgExport(
        revision_id="label-dieline-svg:" + _digest(identity),
        source_dieline_revision_id=dieline.revision_id,
        svg_sha256=svg_sha256,
        svg_bytes=svg_bytes,
        width_mm_unverified=view_width,
        height_mm_unverified=view_height,
    )


def _path(layer: str, points: tuple[tuple[float, float], ...]) -> str:
    coordinates = " ".join(
        f"{'M' if index == 0 else 'L'} {_n(x)} {_n(y)}" for index, (x, y) in enumerate(points)
    )
    return f'<path id="{layer}" d="{coordinates} Z" />'


def _scale_mark(x: float, y: float) -> str:
    x_end = x + SCALE_MARK_LENGTH_MM_UNVERIFIED
    return (
        f'<path id="known-10mm-scale-mark" d="M {_n(x)} {_n(y - 1)} L {_n(x)} {_n(y + 1)} '
        f"M {_n(x)} {_n(y)} L {_n(x_end)} {_n(y)} "
        f'M {_n(x_end)} {_n(y - 1)} L {_n(x_end)} {_n(y + 1)}" />'
    )


def _n(value: float) -> str:
    if not math.isfinite(value):
        raise LabelDielineSvgExportError("label_dieline_svg_number_non_finite")
    return format(value, ".15g")


def _digest(value: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


__all__ = [
    "LABEL_DIELINE_SVG_CONTRACT",
    "PRINT_DISCLAIMER",
    "SCALE_MARK_LENGTH_MM_UNVERIFIED",
    "LabelDielineSvgExport",
    "LabelDielineSvgExportError",
    "export_label_dieline_svg",
]
