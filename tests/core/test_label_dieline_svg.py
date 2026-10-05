from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET

import pytest
from tests.core.test_label_dieline_print_intent import _dieline
from tests.core.test_label_metric_surface_binding import _model, _placement, _representation

from packlab_core.label_dieline_svg import (
    PRINT_DISCLAIMER,
    SCALE_MARK_LENGTH_MM_UNVERIFIED,
    LabelDielineSvgExportError,
    export_label_dieline_svg,
)
from packlab_core.label_metric_surface_binding import create_label_dieline_print_intent
from packlab_core.label_zone import LabelZoneKind
from packlab_core.reconstruction import ScaleState

_SVG = "{http://www.w3.org/2000/svg}"


def _export():
    model, brep, placement, source = _dieline()
    intent = create_label_dieline_print_intent(
        source, safe_margin_mm_unverified=2.0, bleed_mm_unverified=1.5
    )
    return model, brep, placement, intent, export_label_dieline_svg(intent, placement)


def test_svg_export_is_deterministic_vector_only_and_pins_source_provenance() -> None:
    model, brep, placement, dieline, first = _export()
    second = export_label_dieline_svg(dieline, placement)
    root = ET.fromstring(first.svg_bytes)

    assert first == second
    assert first.svg_sha256 == hashlib.sha256(first.svg_bytes).hexdigest()
    assert first.source_dieline_revision_id == dieline.revision_id
    assert root.attrib["data-coordinate-unit"] == "mm_unverified"
    assert root.attrib["data-scale-state"] == "METRIC_UNVERIFIED"
    assert root.attrib["data-source-dieline"] == dieline.source_dieline_revision_id
    assert root.attrib["data-current-dieline"] == dieline.revision_id
    assert root.attrib["data-source-zone"] == placement.zone_id
    assert root.attrib["data-source-placement"] == placement.revision_id
    assert root.attrib["data-source-design-model"] == model.revision_id
    assert root.attrib["data-source-brep"] == brep.revision_id
    assert root.attrib["data-source-brep-sha256"] == brep.geometry_sha256
    assert root.attrib["data-source-analysis"] == dieline.binding.analysis_revision_id
    assert root.attrib["data-source-analysis-region"] == dieline.binding.analysis_region_id
    assert root.attrib["data-source-metric-binding"] == dieline.binding.revision_id
    drawable = [
        node for node in root.iter() if node.tag in {_SVG + "path", _SVG + "rect", _SVG + "image"}
    ]
    assert len(drawable) == 4
    assert all(node.tag == _SVG + "path" for node in drawable)
    assert not any(node.tag in {_SVG + "image", _SVG + "use"} for node in root.iter())
    assert PRINT_DISCLAIMER in "".join(root.itertext())
    assert first.as_dict()["print_ready"] is False
    assert first.as_dict()["print_fit_verified"] is False
    assert "Do not treat this file as print-ready." in first.svg_bytes.decode("utf-8")


def test_svg_dimensions_viewbox_and_path_boundaries_use_explicit_mm_values() -> None:
    _, _, _, dieline, exported = _export()
    root = ET.fromstring(exported.svg_bytes)
    view_box = tuple(float(value) for value in root.attrib["viewBox"].split())

    assert root.attrib["width"] == f"{exported.width_mm_unverified:g}mm"
    assert root.attrib["height"] == f"{exported.height_mm_unverified:g}mm"
    assert view_box[2] == exported.width_mm_unverified
    assert view_box[3] == exported.height_mm_unverified
    safe_layer = root.find(".//" + _SVG + "g[@id='safe-boundary-layer']")
    bleed_layer = root.find(".//" + _SVG + "g[@id='bleed-boundary-layer']")
    assert safe_layer is not None and safe_layer.attrib["data-margin-mm-unverified"] == "2"
    assert bleed_layer is not None and bleed_layer.attrib["data-bleed-mm-unverified"] == "1.5"
    assert safe_layer.find(_SVG + "path") is not None
    assert bleed_layer.find(_SVG + "path") is not None
    assert dieline.source_dieline_revision_id is not None


def test_svg_has_a_known_ten_mm_verification_bar_and_ticks() -> None:
    _, _, _, _, exported = _export()
    root = ET.fromstring(exported.svg_bytes)
    layer = root.find(".//" + _SVG + "g[@id='scale-verification-layer']")
    assert layer is not None
    assert layer.attrib["data-coordinate-unit"] == "mm_unverified"
    assert (
        float(layer.attrib["data-known-spacing-mm-unverified"]) == SCALE_MARK_LENGTH_MM_UNVERIFIED
    )
    mark = layer.find(_SVG + "path")
    assert mark is not None
    tokens = mark.attrib["d"].split()
    # The central horizontal vector segment spans exactly the declared 10 mm.
    x_start = float(tokens[7])
    x_end = float(tokens[10])
    assert x_end - x_start == SCALE_MARK_LENGTH_MM_UNVERIFIED


def test_svg_export_rejects_relative_zone_and_missing_print_intent() -> None:
    _, _, _, metric_dieline = _dieline()
    relative_model = _model(ScaleState.RELATIVE, label="svg-relative-zone")
    relative_brep = _representation(relative_model)
    relative_placement = _placement(relative_model, relative_brep, LabelZoneKind.FRONT)
    with pytest.raises(LabelDielineSvgExportError, match="scale_must_be_mm_unverified"):
        export_label_dieline_svg(metric_dieline, relative_placement)

    model, brep, placement, source = _dieline()
    with pytest.raises(LabelDielineSvgExportError, match="print_intent_required"):
        export_label_dieline_svg(source, placement)


def test_svg_export_rejects_stale_placement_or_source_binding() -> None:
    _, _, _, dieline, _ = _export()
    relative_model = _model(label="svg-stale-zone")
    other_brep = _representation(relative_model)
    other_placement = _placement(relative_model, other_brep, LabelZoneKind.BACK)

    with pytest.raises(LabelDielineSvgExportError, match="source_binding_mismatch"):
        export_label_dieline_svg(dieline, other_placement)
