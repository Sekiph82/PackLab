from __future__ import annotations

import struct
import zlib
from dataclasses import replace

import pytest
from tests.core.test_label_metric_surface_binding import _cylinder
from tests.core.test_label_zone import BODY_ID, COMPONENT_ID, _model, _representation

from packlab_core.blender_label_render_overlay import (
    RENDERER_ONLY_OFFSET_MM_UNVERIFIED,
    LabelRenderOverlayError,
    create_label_render_overlay_binding,
)
from packlab_core.cad_label_surface_analysis import (
    CadLabelSurfacePolicy,
    analyze_cad_label_surfaces,
)
from packlab_core.label_artwork import (
    create_label_artwork_assignment,
    ingest_label_artwork,
    map_label_artwork_to_zone,
)
from packlab_core.label_metric_surface_binding import create_label_metric_surface_binding
from packlab_core.label_zone import LabelZoneBoundary, LabelZoneKind, create_label_zone
from packlab_core.label_zone_placement import create_label_zone_placement_revision


def _chunk(name: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + name
        + payload
        + struct.pack(">I", zlib.crc32(name + payload) & 0xFFFFFFFF)
    )


_PNG = (
    b"\x89PNG\r\n\x1a\n"
    + _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    + _chunk(b"IDAT", zlib.compress(b"\x00\xff\x20\x10\xff"))
    + _chunk(b"IEND", b"")
)
_POLICY = CadLabelSurfacePolicy((0.0, 1.0, 0.0), 90.0, 1_000_000.0)


def _make_binding(kind: LabelZoneKind, *, seam: float | None = None):
    if kind is LabelZoneKind.WRAP:
        model, brep = _cylinder()
        boundary = LabelZoneBoundary(0.1, 0.2, 0.7, 0.8)
    else:
        model = _model(label=f"scene-overlay-{kind.value}")
        brep = _representation(model)
        boundary = LabelZoneBoundary(0.1, 0.2, 0.7, 0.8)
    zone = create_label_zone(
        model,
        brep,
        zone_kind=kind,
        component_id=COMPONENT_ID,
        feature_id=BODY_ID,
        boundary=boundary,
    )
    placement = create_label_zone_placement_revision(
        zone,
        boundary,
        actor_id="operator-1",
        reason="Bind a deterministic render overlay to exact surface authority.",
        created_at_utc="2026-10-05T10:00:00Z",
    )
    analysis = analyze_cad_label_surfaces(model, brep, _POLICY)
    if kind is LabelZoneKind.FRONT:
        candidate = next(
            item
            for item in analysis.candidates
            if item.surface_type == "GeomAbs_Plane" and item.center[1] == pytest.approx(60.0)
        )
    elif kind is LabelZoneKind.BACK:
        candidate = next(
            item
            for item in analysis.candidates
            if item.surface_type == "GeomAbs_Plane" and item.center[1] == pytest.approx(0.0)
        )
    else:
        candidate = next(
            item for item in analysis.candidates if item.surface_type == "GeomAbs_Cylinder"
        )
    metric = create_label_metric_surface_binding(
        model, brep, placement, analysis, candidate.analysis_region_id
    )
    artwork = ingest_label_artwork(_PNG)
    mapping = map_label_artwork_to_zone(artwork, placement)
    assignment = create_label_artwork_assignment(
        mapping,
        placement,
        variant_id=f"{kind.value}-primary",
        wrap_seam_u_normalized=seam if kind is LabelZoneKind.WRAP else None,
    )
    overlay = create_label_render_overlay_binding(
        model, brep, analysis, metric, placement, mapping, assignment, artwork
    )
    return model, brep, analysis, metric, placement, mapping, assignment, artwork, overlay


@pytest.mark.parametrize(
    ("kind", "expected_first_x", "expected_y"),
    [
        (LabelZoneKind.FRONT, 10.0, 60.0 + RENDERER_ONLY_OFFSET_MM_UNVERIFIED),
        (LabelZoneKind.BACK, 90.0, -RENDERER_ONLY_OFFSET_MM_UNVERIFIED),
    ],
)
def test_planar_overlay_persists_exact_front_back_zone_frame(
    kind: LabelZoneKind, expected_first_x: float, expected_y: float
) -> None:
    *_, overlay = _make_binding(kind)
    geometry = dict(overlay.geometry)
    assert overlay.mapping_mode == "PLANAR_RECTANGULAR"
    assert geometry["zone_corners_mm_unverified"][0] == pytest.approx(
        [expected_first_x, expected_y, 8.0]
    )
    assert geometry["source_face_identity_persisted"] is False
    assert overlay.source_to_glb_viewer_transform[0][0] == "inverse_scale"
    assert overlay.renderer_only_offset_mm_unverified == RENDERER_ONLY_OFFSET_MM_UNVERIFIED
    assert overlay.revision_id.startswith("label-render-overlay:")


def test_cylindrical_overlay_persists_exact_seam_angles_and_axial_zone() -> None:
    *_, overlay = _make_binding(LabelZoneKind.WRAP, seam=0.1)
    geometry = dict(overlay.geometry)
    assert overlay.mapping_mode == "CYLINDRICAL_WRAP"
    assert geometry["center_mm_unverified"] == pytest.approx([0.0, 0.0, 0.0])
    assert geometry["radius_mm_unverified"] == pytest.approx(5.0)
    assert geometry["angular_start_radians"] == pytest.approx(0.0)
    assert geometry["angular_end_radians"] == pytest.approx(2.0 * 3.141592653589793 * 0.6)
    assert geometry["axial_start_mm_unverified"] == pytest.approx(4.0)
    assert geometry["axial_end_mm_unverified"] == pytest.approx(16.0)
    assert geometry["source_face_identity_persisted"] is False


def test_overlay_binding_rejects_stale_metric_and_svg_media() -> None:
    values = _make_binding(LabelZoneKind.FRONT)
    model, brep, analysis, metric, placement, mapping, assignment, artwork, _overlay = values
    wrong_analysis = replace(analysis, revision_id="cad-label-surface-analysis:stale")
    with pytest.raises(LabelRenderOverlayError, match="provenance_or_png_invalid"):
        create_label_render_overlay_binding(
            model, brep, wrong_analysis, metric, placement, mapping, assignment, artwork
        )
    svg = ingest_label_artwork(
        b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"><rect width="1" height="1"/></svg>'
    )
    svg_mapping = map_label_artwork_to_zone(svg, placement)
    svg_assignment = create_label_artwork_assignment(svg_mapping, placement, variant_id="front-svg")
    with pytest.raises(LabelRenderOverlayError, match="svg_scene_texturing_unsupported"):
        create_label_render_overlay_binding(
            model, brep, analysis, metric, placement, svg_mapping, svg_assignment, svg
        )
