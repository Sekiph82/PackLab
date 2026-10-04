from __future__ import annotations

from test_technical_drawing_export import _export

from packlab_core.reconstruction import ScaleState
from packlab_core.technical_drawing_export import export_technical_drawing_vectors
from packlab_core.technical_drawing_pdf import (
    DrawingPdfExportError,
    export_technical_drawing_pdf,
    probe_vector_pdf_capability,
)


def test_existing_qt_vector_pdf_capabilities_are_available_offline() -> None:
    capability = probe_vector_pdf_capability()
    assert capability.available is True
    assert capability.writer_available is True
    assert capability.svg_renderer_available is True
    assert capability.pdf_parser_available is True
    assert "QSvgRenderer" in capability.route
    assert "QPdfWriter" in capability.route


def test_one_page_pdf_preserves_svg_vector_path_and_verifies_render() -> None:
    vector = export_technical_drawing_vectors(*_export())
    pdf = export_technical_drawing_pdf(vector)
    record = pdf.as_dict()

    assert pdf.pdf_bytes.startswith(b"%PDF-")
    assert pdf.manifest["page_count"] == 1
    assert pdf.manifest["page_size"] == "A4"
    assert pdf.manifest["orientation"] == "LANDSCAPE"
    assert pdf.manifest["vector_source_format"] == "SVG"
    assert pdf.manifest["svg_source_sha256"] == vector.as_dict()["svg_sha256"]
    assert pdf.manifest["parsed_by_qtpdf"] is True
    assert (
        "unverified against the physical benchmark" in pdf.manifest["visible_authority_disclaimer"]
    )
    assert pdf.manifest["render_smoke"]["status"] == "PASS"
    assert pdf.manifest["render_smoke"]["clipping_detected"] is False
    assert pdf.manifest["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert pdf.manifest["mold_use_authorized"] is False
    assert pdf.manifest["rasterized_pdf_source"] is False
    assert record["pdf_sha256"] == pdf.manifest["pdf_sha256"]
    assert b"/Subtype /Image" not in pdf.pdf_bytes
    assert b"not mold or manufacturing approval" in vector.svg_bytes


def test_relative_pdf_keeps_reconstruction_units_and_disclaimer() -> None:
    vector = export_technical_drawing_vectors(*_export(ScaleState.RELATIVE))
    pdf = export_technical_drawing_pdf(vector)

    assert pdf.manifest["coordinate_unit"] == "reconstruction_units"
    assert "reconstruction-relative" in pdf.manifest["visible_authority_disclaimer"]
    assert b"mm_unverified" not in vector.dxf_bytes
    assert b"reconstruction-relative" in vector.svg_bytes
    assert pdf.manifest["render_smoke"]["status"] == "PASS"


def test_invalid_svg_source_rejected() -> None:
    vector = export_technical_drawing_vectors(*_export())
    invalid = type(vector)(
        vector.contract,
        vector.drawing_revision_id,
        vector.source_design_model_revision_id,
        vector.source_brep_revision_id,
        vector.parent_kind,
        vector.parent_authority_revision_id,
        vector.scale_state,
        vector.coordinate_unit,
        b"not svg",
        vector.dxf_bytes,
        vector.manifest,
    )

    try:
        export_technical_drawing_pdf(invalid)
    except DrawingPdfExportError as error:
        assert "svg" in str(error)
    else:
        raise AssertionError("invalid SVG source must fail closed")
