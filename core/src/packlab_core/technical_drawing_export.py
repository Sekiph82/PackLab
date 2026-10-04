"""Deterministic SVG and DXF exports of PackLab's shared drawing records."""

from __future__ import annotations

import hashlib
import html
import json
import math
from collections.abc import Iterable
from dataclasses import dataclass

from .technical_drawing import DrawingCurve, TechnicalDrawingViewModel
from .technical_drawing_dimensions import TechnicalDrawingDimensions
from .technical_drawing_sections import DrawingSectionCurve, DrawingSectionViewModel
from .technical_drawing_title_block import TechnicalDrawingTitleBlock

DRAWING_EXPORT_CONTRACT = "packlab.technical-drawing-vector-export.v1"
DXF_VERSION = "AC1015"
DXF_SUBSET = "R2000 ASCII: LINE, CIRCLE and TEXT entities; explicit layers; no blocks, splines, or raster entities"
_GAP = 20.0
_MARGIN = 10.0
_TEXT_HEIGHT = 2.5
_MAX_VIEWS = 32
_MAX_CURVES = 32768


class DrawingExportError(ValueError):
    """Raised when drawing records cannot be exported without losing authority."""


@dataclass(frozen=True, slots=True)
class TechnicalDrawingVectorExport:
    contract: str
    drawing_revision_id: str
    source_design_model_revision_id: str
    source_brep_revision_id: str
    parent_kind: str
    parent_authority_revision_id: str
    scale_state: str
    coordinate_unit: str
    svg_bytes: bytes
    dxf_bytes: bytes
    manifest: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "drawing_revision_id": self.drawing_revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "svg_sha256": hashlib.sha256(self.svg_bytes).hexdigest(),
            "dxf_sha256": hashlib.sha256(self.dxf_bytes).hexdigest(),
            "manifest": self.manifest,
            "raster_source_of_truth": False,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
        }


@dataclass(frozen=True, slots=True)
class _Panel:
    panel_id: str
    label: str
    bounds: tuple[float, float, float, float]
    curves: tuple[DrawingCurve | DrawingSectionCurve, ...]
    offset: tuple[float, float]
    layer: str


def export_technical_drawing_vectors(
    views: TechnicalDrawingViewModel,
    sections: tuple[DrawingSectionViewModel, ...],
    dimensions: TechnicalDrawingDimensions,
    title_block: TechnicalDrawingTitleBlock,
) -> TechnicalDrawingVectorExport:
    """Serialize exact shared view/section/dimension/title records as SVG and DXF."""
    _validate_sources(views, sections, dimensions, title_block)
    panels = _layout_panels(views, sections)
    if len(panels) > _MAX_VIEWS:
        raise DrawingExportError("drawing_export_view_limit_exceeded")
    curve_count = sum(len(panel.curves) for panel in panels)
    if curve_count > _MAX_CURVES:
        raise DrawingExportError("drawing_export_curve_limit_exceeded")

    min_x = min(panel.offset[0] + panel.bounds[0] for panel in panels)
    min_y = min(panel.offset[1] + panel.bounds[1] for panel in panels)
    max_x = max(panel.offset[0] + panel.bounds[2] for panel in panels)
    max_y = max(panel.offset[1] + panel.bounds[3] for panel in panels)
    unit = views.coordinate_unit
    unit_label = "mm (UNVERIFIED)" if unit == "mm_unverified" else "reconstruction_units"
    title_lines = (
        f"{title_block.project_id} — {title_block.package_family}",
        f"Drawing {title_block.drawing_revision_id}",
        f"Design {views.source_design_model_revision_id}",
        f"CAD {views.source_brep_revision_id}",
        f"Parent {views.parent_kind}: {views.parent_authority_revision_id}",
        f"Units: {unit_label}",
        title_block.disclaimer,
    )
    title_width = max((_text_width(line) for line in title_lines), default=0.0)
    drawing_width = max_x - min_x
    drawing_height = max_y - min_y
    canvas_width = max(drawing_width, title_width) + 2 * _MARGIN
    canvas_height = drawing_height + 2 * _MARGIN + len(title_lines) * (_TEXT_HEIGHT + 1.5)
    # SVG uses a top-left origin. This translation preserves all source coordinates and units.
    sheet_x = _MARGIN - min_x
    sheet_y = _MARGIN + max_y

    manifest: dict[str, object] = {
        "contract": DRAWING_EXPORT_CONTRACT,
        "drawing_revision_id": title_block.drawing_revision_id,
        "view_model_revision_id": views.revision_id,
        "section_revision_ids": [section.revision_id for section in sections],
        "dimension_revision_id": dimensions.revision_id,
        "title_block_revision_id": title_block.revision_id,
        "source_design_model_revision_id": views.source_design_model_revision_id,
        "source_brep_revision_id": views.source_brep_revision_id,
        "source_brep_geometry_sha256": views.source_brep_geometry_sha256,
        "parent_authority": {
            "kind": views.parent_kind,
            "revision_id": views.parent_authority_revision_id,
        },
        "scale_state": views.scale_state,
        "coordinate_unit": unit,
        "svg_coordinate_units": unit,
        "dxf_version": "R2000 / AC1015",
        "dxf_subset": DXF_SUBSET,
        "layers": ["GEOMETRY", "SECTIONS", "DIMENSIONS", "ANNOTATIONS", "TITLE_BLOCK"],
        "raster_entities": 0,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "physical_accuracy_inferred": False,
        "manufacturing_suitability_inferred": False,
    }
    svg = _render_svg(
        panels,
        dimensions,
        title_lines,
        manifest,
        canvas_width,
        canvas_height,
        sheet_x,
        sheet_y,
    )
    dxf = _render_dxf(
        panels,
        dimensions,
        title_lines,
        title_block,
        views,
        sections,
        unit,
        canvas_width,
        canvas_height,
        sheet_x,
        sheet_y,
    )
    manifest["artifacts"] = {
        "svg": {"media_type": "image/svg+xml", "sha256": hashlib.sha256(svg).hexdigest()},
        "dxf": {"media_type": "image/vnd.dxf", "sha256": hashlib.sha256(dxf).hexdigest()},
    }
    return TechnicalDrawingVectorExport(
        contract=DRAWING_EXPORT_CONTRACT,
        drawing_revision_id=title_block.drawing_revision_id,
        source_design_model_revision_id=views.source_design_model_revision_id,
        source_brep_revision_id=views.source_brep_revision_id,
        parent_kind=views.parent_kind,
        parent_authority_revision_id=views.parent_authority_revision_id,
        scale_state=views.scale_state,
        coordinate_unit=unit,
        svg_bytes=svg,
        dxf_bytes=dxf,
        manifest=manifest,
    )


def _validate_sources(
    views: TechnicalDrawingViewModel,
    sections: tuple[DrawingSectionViewModel, ...],
    dimensions: TechnicalDrawingDimensions,
    title_block: TechnicalDrawingTitleBlock,
) -> None:
    if not isinstance(views, TechnicalDrawingViewModel):
        raise DrawingExportError("drawing_view_model_required")
    if (
        not isinstance(sections, tuple)
        or len(sections) > 16
        or any(not isinstance(item, DrawingSectionViewModel) for item in sections)
    ):
        raise DrawingExportError("drawing_sections_invalid")
    if not isinstance(dimensions, TechnicalDrawingDimensions):
        raise DrawingExportError("drawing_dimensions_required")
    if not isinstance(title_block, TechnicalDrawingTitleBlock):
        raise DrawingExportError("drawing_title_block_required")
    source = (
        views.source_design_model_revision_id,
        views.source_brep_revision_id,
        views.source_brep_geometry_sha256,
        views.parent_kind,
        views.parent_authority_revision_id,
        views.scale_state,
        views.coordinate_unit,
    )
    if source != (
        dimensions.source_design_model_revision_id,
        dimensions.source_brep_revision_id,
        dimensions.source_brep_geometry_sha256,
        dimensions.parent_kind,
        dimensions.parent_authority_revision_id,
        dimensions.scale_state,
        dimensions.coordinate_unit,
    ):
        raise DrawingExportError("drawing_dimension_source_mismatch")
    if source != (
        title_block.design_model_revision_id,
        title_block.cad_representation_revision_id,
        title_block.cad_geometry_sha256,
        title_block.parent_kind,
        title_block.parent_authority_revision_id,
        title_block.scale_state,
        title_block.coordinate_unit,
    ):
        raise DrawingExportError("drawing_title_block_source_mismatch")
    if (
        views.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or dimensions.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or title_block.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or views.mold_use_authorized
        or dimensions.mold_use_authorized
        or title_block.mold_use_authorized
        or views.scale_state not in {"relative", "metric-unverified"}
        or (views.scale_state == "relative" and views.coordinate_unit != "reconstruction_units")
        or (views.scale_state == "metric-unverified" and views.coordinate_unit != "mm_unverified")
    ):
        raise DrawingExportError("drawing_export_authority_or_unit_invalid")
    view_ids = {view.view_id for view in views.views}
    if (
        not views.views
        or len(views.views) > 8
        or not view_ids.issubset(set(title_block.generated_view_ids))
    ):
        raise DrawingExportError("drawing_export_views_invalid")
    if any(
        section.scale_state != views.scale_state
        or section.coordinate_unit != views.coordinate_unit
        or section.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or section.mold_use_authorized
        or any(
            component.source_design_model_revision_id != views.source_design_model_revision_id
            or component.source_brep_revision_id != views.source_brep_revision_id
            or component.source_brep_geometry_sha256 != views.source_brep_geometry_sha256
            or component.parent_kind != views.parent_kind
            or component.parent_authority_revision_id != views.parent_authority_revision_id
            for component in section.components
        )
        for section in sections
    ):
        raise DrawingExportError("drawing_section_source_mismatch")


def _layout_panels(
    views: TechnicalDrawingViewModel, sections: tuple[DrawingSectionViewModel, ...]
) -> tuple[_Panel, ...]:
    raw: list[
        tuple[
            str,
            str,
            tuple[float, float, float, float],
            tuple[DrawingCurve | DrawingSectionCurve, ...],
            str,
        ]
    ] = []
    for view in views.views:
        raw.append((view.view_id, view.view_id, view.bounds, tuple(view.curves), "GEOMETRY"))
    for index, section in enumerate(sections):
        label = f"SECTION_{section.plane_axis}_{_number(section.plane_offset)}"
        if section.bounds is not None and section.curves:
            raw.append(
                (f"SECTION_{index}", label, section.bounds, tuple(section.curves), "SECTIONS")
            )
        else:
            raw.append((f"SECTION_{index}", label, (0.0, 0.0, 0.0, 0.0), (), "SECTIONS"))
    if not raw or len(raw) > _MAX_VIEWS:
        raise DrawingExportError("drawing_export_view_limit_exceeded")
    row_y = 0.0
    row_x = 0.0
    panels: list[_Panel] = []
    max_row_height = 0.0
    for index, (panel_id, label, bounds, curves, layer) in enumerate(raw):
        _validate_bounds(bounds)
        width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        if index == len(views.views):
            row_y = max_row_height + _GAP
            row_x = 0.0
        offset = (row_x - bounds[0], row_y - bounds[1])
        panels.append(_Panel(panel_id, label, bounds, curves, offset, layer))
        row_x += width + _GAP
        max_row_height = max(max_row_height, row_y + height)
    return tuple(panels)


def _render_svg(
    panels: tuple[_Panel, ...],
    dimensions: TechnicalDrawingDimensions,
    title_lines: tuple[str, ...],
    manifest: dict[str, object],
    width: float,
    height: float,
    sheet_x: float,
    sheet_y: float,
) -> bytes:
    unit = str(manifest["svg_coordinate_units"])
    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 {_number(width)} {_number(height)}" width="{_number(width)}" height="{_number(height)}" data-coordinate-unit="{html.escape(unit, quote=True)}">',
        f"<metadata>{html.escape(json.dumps(manifest, sort_keys=True, separators=(',', ':')))}</metadata>",
        '<g fill="none" stroke="#111" stroke-width="0.25" vector-effect="non-scaling-stroke">',
    ]
    panel_lookup = {panel.panel_id: panel for panel in panels}
    for panel in panels:
        chunks.append(
            f'<g id="{html.escape(panel.panel_id)}" data-layer="{panel.layer}" transform="translate({_number(sheet_x + panel.offset[0])} {_number(sheet_y - panel.offset[1])}) scale(1 -1)">'
        )
        for curve in panel.curves:
            points = getattr(curve, "points", ())
            _validate_points(points)
            serialized = " ".join(f"{_number(point[0])},{_number(point[1])}" for point in points)
            chunks.append(
                f'<polyline points="{serialized}" data-curve-id="{html.escape(str(curve.curve_id))}"/>'
            )
        chunks.append("</g>")
        label_y = sheet_y - panel.offset[1] + 4.0
        chunks.append(
            f'<text x="{_number(sheet_x + panel.offset[0])}" y="{_number(label_y)}" font-size="{_number(_TEXT_HEIGHT)}" data-layer="ANNOTATIONS">{html.escape(panel.label)}</text>'
        )
    for dimension in dimensions.dimensions:
        dimension_panel = panel_lookup.get(dimension.view_id)
        if dimension_panel is None:
            continue
        tx, ty = sheet_x + dimension_panel.offset[0], sheet_y - dimension_panel.offset[1]
        for start, end in dimension.extension_lines + (dimension.dimension_line,):
            chunks.append(
                _svg_line(tx + start[0], ty - start[1], tx + end[0], ty - end[1], "DIMENSIONS")
            )
        for anchor in dimension.arrow_anchors:
            chunks.append(
                f'<circle cx="{_number(tx + anchor[0])}" cy="{_number(ty - anchor[1])}" r="0.8" data-layer="DIMENSIONS"/>'
            )
        chunks.append(
            f'<text x="{_number(tx + dimension.text_anchor[0])}" y="{_number(ty - dimension.text_anchor[1])}" font-size="{_number(_TEXT_HEIGHT)}" data-layer="DIMENSIONS">{html.escape(_dimension_label(dimension))}</text>'
        )
    title_start = height - _MARGIN - _TEXT_HEIGHT
    for index, line in enumerate(title_lines):
        chunks.append(
            f'<text x="{_number(_MARGIN)}" y="{_number(title_start - index * (_TEXT_HEIGHT + 1.5))}" font-size="{_number(_TEXT_HEIGHT)}" data-layer="TITLE_BLOCK">{html.escape(line)}</text>'
        )
    chunks.extend(["</g>", "</svg>"])
    return ("\n".join(chunks) + "\n").encode("utf-8")


def _render_dxf(
    panels: tuple[_Panel, ...],
    dimensions: TechnicalDrawingDimensions,
    title_lines: tuple[str, ...],
    title: TechnicalDrawingTitleBlock,
    views: TechnicalDrawingViewModel,
    sections: tuple[DrawingSectionViewModel, ...],
    unit: str,
    width: float,
    height: float,
    sheet_x: float,
    sheet_y: float,
) -> bytes:
    pairs: list[tuple[int, str]] = [
        (0, "SECTION"),
        (2, "HEADER"),
        (9, "$ACADVER"),
        (1, DXF_VERSION),
    ]
    pairs.extend([(9, "$INSUNITS"), (70, "4" if unit == "mm_unverified" else "0")])
    pairs.extend([(9, "$EXTMIN"), (10, "0"), (20, "0"), (30, "0")])
    pairs.extend([(9, "$EXTMAX"), (10, _number(width)), (20, _number(height)), (30, "0")])
    pairs.extend([(0, "ENDSEC"), (0, "SECTION"), (2, "TABLES")])
    layers = ("0", "GEOMETRY", "SECTIONS", "DIMENSIONS", "ANNOTATIONS", "TITLE_BLOCK")
    pairs.extend([(0, "TABLE"), (2, "LAYER"), (70, str(len(layers)))])
    for layer in layers:
        pairs.extend([(0, "LAYER"), (2, layer), (70, "0"), (62, "7"), (6, "CONTINUOUS")])
    pairs.extend([(0, "ENDTAB"), (0, "ENDSEC"), (0, "SECTION"), (2, "ENTITIES")])
    pairs.extend(
        [
            (999, f"PackLab drawing revision {title.drawing_revision_id}"),
            (999, f"Design Model revision {views.source_design_model_revision_id}"),
            (999, f"CAD BREP revision {views.source_brep_revision_id}"),
            (999, f"Parent authority {views.parent_kind}:{views.parent_authority_revision_id}"),
            (999, f"Coordinate unit {unit}"),
            (999, f"DXF subset: {DXF_SUBSET}"),
        ]
    )
    for panel in panels:
        ox, oy = sheet_x + panel.offset[0], sheet_y - panel.offset[1]
        for curve in panel.curves:
            points = getattr(curve, "points", ())
            _validate_points(points)
            for start, end in zip(points, points[1:]):
                _dxf_line(
                    pairs, (ox + start[0], oy - start[1]), (ox + end[0], oy - end[1]), panel.layer
                )
        _dxf_text(pairs, (ox, oy + 4.0), panel.label, "ANNOTATIONS", _TEXT_HEIGHT)
    lookup = {panel.panel_id: panel for panel in panels}
    for dimension in dimensions.dimensions:
        dimension_panel = lookup.get(dimension.view_id)
        if dimension_panel is None:
            continue
        ox, oy = sheet_x + dimension_panel.offset[0], sheet_y - dimension_panel.offset[1]
        for start, end in dimension.extension_lines + (dimension.dimension_line,):
            _dxf_line(
                pairs, (ox + start[0], oy - start[1]), (ox + end[0], oy - end[1]), "DIMENSIONS"
            )
        for anchor in dimension.arrow_anchors:
            _dxf_circle(pairs, (ox + anchor[0], oy - anchor[1]), 0.8, "DIMENSIONS")
        _dxf_text(
            pairs,
            (ox + dimension.text_anchor[0], oy - dimension.text_anchor[1]),
            _dimension_label(dimension),
            "DIMENSIONS",
            _TEXT_HEIGHT,
        )
    for index, line in enumerate(title_lines):
        _dxf_text(
            pairs,
            (_MARGIN, _MARGIN + (len(title_lines) - index - 1) * (_TEXT_HEIGHT + 1.5)),
            line,
            "TITLE_BLOCK",
            _TEXT_HEIGHT,
        )
    pairs.extend([(0, "ENDSEC"), (0, "EOF")])
    return ("\n".join(str(value) for pair in pairs for value in pair) + "\n").encode("ascii")


def _svg_line(x1: float, y1: float, x2: float, y2: float, layer: str) -> str:
    return f'<line x1="{_number(x1)}" y1="{_number(y1)}" x2="{_number(x2)}" y2="{_number(y2)}" data-layer="{layer}"/>'


def _dxf_line(
    pairs: list[tuple[int, str]], start: tuple[float, float], end: tuple[float, float], layer: str
) -> None:
    pairs.extend(
        [
            (0, "LINE"),
            (8, layer),
            (10, _number(start[0])),
            (20, _number(start[1])),
            (30, "0"),
            (11, _number(end[0])),
            (21, _number(end[1])),
            (31, "0"),
        ]
    )


def _dxf_circle(
    pairs: list[tuple[int, str]], center: tuple[float, float], radius: float, layer: str
) -> None:
    pairs.extend(
        [
            (0, "CIRCLE"),
            (8, layer),
            (10, _number(center[0])),
            (20, _number(center[1])),
            (30, "0"),
            (40, _number(radius)),
        ]
    )


def _dxf_text(
    pairs: list[tuple[int, str]], point: tuple[float, float], text: str, layer: str, height: float
) -> None:
    pairs.extend(
        [
            (0, "TEXT"),
            (8, layer),
            (10, _number(point[0])),
            (20, _number(point[1])),
            (30, "0"),
            (40, _number(height)),
            (1, _dxf_escape(text)),
        ]
    )


def _dxf_escape(value: str) -> str:
    escaped: list[str] = []
    for character in value:
        code = ord(character)
        if character in "\r\n":
            escaped.append(" ")
        elif code < 32 or code > 126:
            escaped.append(f"\\U+{code:04X}")
        elif character == "\\":
            escaped.append("\\\\")
        else:
            escaped.append(character)
    return "".join(escaped)


def _dimension_label(dimension: object) -> str:
    value = getattr(dimension, "value")
    unit = getattr(dimension, "unit_label")
    return f"{_number(value)} {unit}"


def _text_width(text: str) -> float:
    # Reserve one full text-height per code point so fonts/Qt versions cannot clip the title block.
    return max(1.0, len(text) * _TEXT_HEIGHT)


def _number(value: float) -> str:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise DrawingExportError("drawing_export_non_finite_number")
    normalized = 0.0 if value == 0 else float(value)
    return format(normalized, ".12g")


def _validate_bounds(bounds: tuple[float, float, float, float]) -> None:
    if (
        not isinstance(bounds, tuple)
        or len(bounds) != 4
        or any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in bounds
        )
        or bounds[2] < bounds[0]
        or bounds[3] < bounds[1]
    ):
        raise DrawingExportError("drawing_export_bounds_invalid")


def _validate_points(points: Iterable[tuple[float, float]]) -> None:
    materialized = tuple(points)
    if len(materialized) < 2 or any(
        not isinstance(point, tuple)
        or len(point) != 2
        or any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in point
        )
        for point in materialized
    ):
        raise DrawingExportError("drawing_export_curve_invalid")


__all__ = [
    "DRAWING_EXPORT_CONTRACT",
    "DXF_SUBSET",
    "DXF_VERSION",
    "DrawingExportError",
    "TechnicalDrawingVectorExport",
    "export_technical_drawing_vectors",
]
