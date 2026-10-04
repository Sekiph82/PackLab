from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import replace

import pytest
from test_cad_brep import _inputs

from packlab_core.cad_adapter import probe_cad_runtime
from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.reconstruction import ScaleState
from packlab_core.technical_drawing import generate_orthographic_views
from packlab_core.technical_drawing_dimensions import build_drawing_dimensions
from packlab_core.technical_drawing_export import (
    DrawingExportError,
    export_technical_drawing_vectors,
)
from packlab_core.technical_drawing_sections import (
    DrawingSectionSource,
    generate_section_view,
)
from packlab_core.technical_drawing_title_block import build_technical_drawing_title_block

FRAME = "vector-export-frame-v1"
IDENTITY = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


def _export(scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED):
    model, profile, operation = _inputs(scale_state)
    representation = revolve_design_model_to_brep(model, profile, operation)
    views = generate_orthographic_views(model, representation)
    dimensions = build_drawing_dimensions(model, representation, coordinate_frame_id=FRAME)
    sections = (
        generate_section_view(
            (
                DrawingSectionSource(
                    "body-instance",
                    FRAME,
                    "placement:body-instance:v1",
                    IDENTITY,
                    model,
                    representation,
                ),
            ),
            plane_axis="Z",
            plane_offset=50.0,
        ),
    )
    title = build_technical_drawing_title_block(
        model,
        representation,
        probe_cad_runtime(),
        generated_view_ids=("FRONT", "SIDE", "TOP"),
    )
    return views, sections, dimensions, title


def test_svg_and_dxf_are_deterministic_vector_exports_with_source_digests() -> None:
    inputs = _export()
    first = export_technical_drawing_vectors(*inputs)
    second = export_technical_drawing_vectors(*inputs)

    assert first.svg_bytes == second.svg_bytes
    assert first.dxf_bytes == second.dxf_bytes
    assert first.as_dict() == second.as_dict()
    assert first.as_dict()["svg_sha256"] == hashlib.sha256(first.svg_bytes).hexdigest()
    assert first.as_dict()["dxf_sha256"] == hashlib.sha256(first.dxf_bytes).hexdigest()
    assert (
        first.manifest["source_design_model_revision_id"]
        == inputs[0].source_design_model_revision_id
    )
    assert first.manifest["source_brep_revision_id"] == inputs[0].source_brep_revision_id
    assert first.manifest["drawing_revision_id"] == inputs[3].drawing_revision_id
    assert first.manifest["coordinate_unit"] == "mm_unverified"
    assert first.manifest["dxf_version"] == "R2000 / AC1015"
    assert first.manifest["raster_entities"] == 0
    assert b"<polyline" in first.svg_bytes
    assert b"<image" not in first.svg_bytes
    assert b"GEOMETRY" in first.svg_bytes and b"SECTIONS" in first.svg_bytes
    assert b"DIMENSIONS" in first.svg_bytes and b"TITLE_BLOCK" in first.svg_bytes
    assert b"mm (UNVERIFIED)" in first.svg_bytes
    assert b"AC1015" in first.dxf_bytes
    assert b"GEOMETRY" in first.dxf_bytes and b"SECTIONS" in first.dxf_bytes
    assert b"DIMENSIONS" in first.dxf_bytes and b"TITLE_BLOCK" in first.dxf_bytes
    assert b"mm_unverified" in first.dxf_bytes
    assert b"not mold or manufacturing approval" in first.svg_bytes


def test_svg_is_parseable_and_contains_view_section_dimension_title_primitives() -> None:
    export = export_technical_drawing_vectors(*_export())
    root = ET.fromstring(export.svg_bytes)
    namespace = {"svg": "http://www.w3.org/2000/svg"}

    assert root.attrib["viewBox"].startswith("0 0 ")
    assert root.attrib["data-coordinate-unit"] == "mm_unverified"
    assert root.find("svg:metadata", namespace) is not None
    assert root.findall(".//svg:polyline", namespace)
    layers = {
        element.attrib["data-layer"] for element in root.iter() if "data-layer" in element.attrib
    }
    assert {"GEOMETRY", "SECTIONS", "DIMENSIONS", "TITLE_BLOCK", "ANNOTATIONS"} <= layers
    metadata = json.loads(root.findtext("svg:metadata", namespaces=namespace) or "{}")
    assert metadata["source_brep_geometry_sha256"] == export.manifest["source_brep_geometry_sha256"]


def test_dxf_subset_has_valid_group_pairs_entities_layers_and_escaped_text() -> None:
    views, sections, dimensions, title = _export(ScaleState.RELATIVE)
    escaped_title = replace(title, project_id='Pack & <Lab> "µ"')
    export = export_technical_drawing_vectors(views, sections, dimensions, escaped_title)
    assert b"Pack &amp; &lt;Lab&gt; &quot;" in export.svg_bytes
    lines = export.dxf_bytes.decode("ascii").splitlines()
    assert len(lines) % 2 == 0
    pairs = list(zip(lines[::2], lines[1::2]))
    entity_types = [value for code, value in pairs if code == "0"]
    layer_names = {
        value
        for code, value in pairs
        if code == "2" and value not in {"HEADER", "TABLES", "ENTITIES", "LAYER"}
    }
    assert entity_types.count("LINE") > 0
    assert entity_types.count("TEXT") > 0
    assert "GEOMETRY" in layer_names and "SECTIONS" in layer_names
    assert "DIMENSIONS" in layer_names and "TITLE_BLOCK" in layer_names
    assert any(
        "Pack & <Lab>" in value and "\\U+00B5" in value for code, value in pairs if code == "1"
    )
    assert export.coordinate_unit == "reconstruction_units"
    assert b"mm_unverified" not in export.dxf_bytes
    assert b"reconstruction_units" in export.dxf_bytes


def test_stale_sources_and_relative_to_metric_unit_promotion_fail_closed() -> None:
    views, sections, dimensions, title = _export(ScaleState.RELATIVE)
    with pytest.raises(DrawingExportError, match="drawing_dimension_source_mismatch"):
        export_technical_drawing_vectors(
            views, sections, replace(dimensions, coordinate_unit="mm_unverified"), title
        )
    with pytest.raises(DrawingExportError, match="drawing_title_block_source_mismatch"):
        export_technical_drawing_vectors(
            views, sections, dimensions, replace(title, coordinate_unit="mm_unverified")
        )
