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
from packlab_core.label_dieline_svg import export_label_dieline_svg
from packlab_core.label_metric_surface_binding import (
    create_label_dieline,
    create_label_dieline_print_intent,
    create_label_metric_surface_binding,
    map_label_artwork_to_metric_surface,
)
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


def _make_binding(kind: LabelZoneKind, *, seam: float | None = None, fit: str = "STRETCH"):
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
    mapping = map_label_artwork_to_metric_surface(artwork, placement, metric, fit_mode=fit)
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


def test_overlay_requires_metric_aspect_for_contain_and_cover() -> None:
    # O-1: the zone UV spans the host face in millimetres, so a CONTAIN/COVER fit made in
    # normalized units would render distorted on this non-square face.
    values = _make_binding(LabelZoneKind.FRONT)
    model, brep, analysis, metric, placement, _mapping, _assignment, artwork, _overlay = values
    assert metric.host_width_mm_unverified != metric.host_height_mm_unverified

    def overlay_for(mapping):
        assignment = create_label_artwork_assignment(mapping, placement, variant_id="front-o1")
        return create_label_render_overlay_binding(
            model, brep, analysis, metric, placement, mapping, assignment, artwork
        )

    for fit in ("CONTAIN", "COVER"):
        with pytest.raises(LabelRenderOverlayError, match="metric_aspect_mapping_required"):
            overlay_for(map_label_artwork_to_zone(artwork, placement, fit_mode=fit))
        wrong_host = map_label_artwork_to_zone(
            artwork,
            placement,
            fit_mode=fit,
            host_size_mm_unverified=(
                metric.host_width_mm_unverified,
                metric.host_height_mm_unverified + 1.0,
            ),
        )
        with pytest.raises(LabelRenderOverlayError, match="mapping_host_size_mismatch"):
            overlay_for(wrong_host)
    # STRETCH is an explicit, recorded distortion and stays allowed in either basis.
    overlay_for(map_label_artwork_to_zone(artwork, placement, fit_mode="STRETCH"))
    overlay_for(map_label_artwork_to_metric_surface(artwork, placement, metric, fit_mode="STRETCH"))


@pytest.mark.parametrize("kind", [LabelZoneKind.FRONT, LabelZoneKind.WRAP])
def test_rendered_contain_artwork_keeps_its_aspect_in_millimetres(kind: LabelZoneKind) -> None:
    *_, metric, placement, mapping, _assignment, artwork, overlay = _make_binding(
        kind, seam=0.1 if kind is LabelZoneKind.WRAP else None, fit="CONTAIN"
    )
    geometry = dict(overlay.geometry)
    assert geometry["artwork_mapping"]["host_size_mm_unverified"] == [
        metric.host_width_mm_unverified,
        metric.host_height_mm_unverified,
    ]
    u0, v0, u1, v1 = mapping.target_rect_normalized_uv
    drawn_width_mm = (u1 - u0) * metric.host_width_mm_unverified
    drawn_height_mm = (v1 - v0) * metric.host_height_mm_unverified
    assert drawn_width_mm / drawn_height_mm == pytest.approx(artwork.width / artwork.height)
    boundary = placement.boundary
    zone_width_mm = (boundary.u_max - boundary.u_min) * metric.host_width_mm_unverified
    zone_height_mm = (boundary.v_max - boundary.v_min) * metric.host_height_mm_unverified
    assert drawn_width_mm <= zone_width_mm + 1e-9 and drawn_height_mm <= zone_height_mm + 1e-9
    assert max(drawn_width_mm / zone_width_mm, drawn_height_mm / zone_height_mm) == pytest.approx(
        1.0
    )
    # The renderer quad covers exactly the drawn rect, not the letterboxed remainder.
    assert geometry["drawn_rect_normalized_uv"] == list(mapping.target_rect_normalized_uv)
    if kind is LabelZoneKind.FRONT:
        corners = geometry["zone_corners_mm_unverified"]
        quad_width = abs(corners[1][0] - corners[0][0])
        quad_height = abs(corners[2][2] - corners[1][2])
        assert quad_width == pytest.approx(drawn_width_mm)
        assert quad_height == pytest.approx(drawn_height_mm)
    else:
        arc = abs(geometry["angular_end_radians"] - geometry["angular_start_radians"])
        assert arc * geometry["radius_mm_unverified"] == pytest.approx(drawn_width_mm)
        axial = geometry["axial_end_mm_unverified"] - geometry["axial_start_mm_unverified"]
        assert axial == pytest.approx(drawn_height_mm)


def test_metric_surface_helper_rejects_a_binding_for_another_placement() -> None:
    from packlab_core.label_metric_surface_binding import LabelMetricSurfaceBindingError

    front = _make_binding(LabelZoneKind.FRONT)
    back = _make_binding(LabelZoneKind.BACK)
    with pytest.raises(LabelMetricSurfaceBindingError, match="binding_placement_mismatch"):
        map_label_artwork_to_metric_surface(front[7], back[4], front[3])


def test_dieline_artwork_and_product_mockup_binding_share_authority() -> None:
    model, brep, analysis, metric, placement, mapping, assignment, artwork, overlay = _make_binding(
        LabelZoneKind.FRONT
    )
    source_dieline = create_label_dieline(metric, placement)
    print_intent = create_label_dieline_print_intent(
        source_dieline, safe_margin_mm_unverified=2.0, bleed_mm_unverified=1.5
    )
    exported = export_label_dieline_svg(print_intent, placement)

    assert exported.as_dict()["source_dieline_revision_id"] == print_intent.revision_id
    assert print_intent.source_dieline_revision_id == source_dieline.revision_id
    assert exported.as_dict()["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert exported.as_dict()["manufacturing_authorized"] is False
    assert overlay.source_design_model_revision_id == model.revision_id
    assert overlay.source_brep_revision_id == brep.revision_id
    assert overlay.analysis_revision_id == analysis.revision_id
    assert overlay.metric_surface_binding_revision_id == metric.revision_id
    assert overlay.mapping_revision_id == mapping.revision_id
    assert overlay.assignment_revision_id == assignment.revision_id
    assert overlay.artwork_revision_id == artwork.revision_id
    assert overlay.as_dict()["physical_fit_verified"] is False
    assert overlay.as_dict()["manufacturing_authorized"] is False


def test_overlay_refuses_a_hand_built_mapping_with_a_self_computed_id() -> None:
    # Review O-1 V03 P2-1: the mapping sets the rendered quad, so a forged record that is
    # internally consistent (valid id) but not what the fit produces must be refused.
    from packlab_core.label_artwork import LabelArtworkMappingRevision, _mapping_digest

    model, brep, analysis, metric, placement, mapping, _assignment, artwork, _overlay = (
        _make_binding(LabelZoneKind.FRONT, fit="CONTAIN")
    )
    boundary = placement.boundary
    stretched_rect = (boundary.u_min, boundary.v_min, boundary.u_max, boundary.v_max)
    values = {
        "revision_id": mapping.revision_id,
        "source_artwork_revision_id": mapping.source_artwork_revision_id,
        "source_artwork_sha256": mapping.source_artwork_sha256,
        "zone_id": mapping.zone_id,
        "placement_revision_id": mapping.placement_revision_id,
        "fit_mode": "CONTAIN",
        "target_rect_normalized_uv": stretched_rect,
        "source_crop_rect": mapping.source_crop_rect,
        "scale_u": (boundary.u_max - boundary.u_min) / artwork.width,
        "scale_v": (boundary.v_max - boundary.v_min) / artwork.height,
        "translate_u": boundary.u_min,
        "translate_v": boundary.v_min,
        "aspect_basis": mapping.aspect_basis,
        "host_size_mm_unverified": mapping.host_size_mm_unverified,
    }
    shell = object.__new__(LabelArtworkMappingRevision)
    for name, value in values.items():
        object.__setattr__(shell, name, value)
    object.__setattr__(shell, "contract", mapping.contract)
    values["revision_id"] = "label-artwork-mapping:" + _mapping_digest(shell)
    forged = LabelArtworkMappingRevision(**values)  # valid id, stretched numbers
    assignment = create_label_artwork_assignment(forged, placement, variant_id="front-forged")
    with pytest.raises(LabelRenderOverlayError, match="mapping_not_reproducible"):
        create_label_render_overlay_binding(
            model, brep, analysis, metric, placement, forged, assignment, artwork
        )
