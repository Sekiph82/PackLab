"""PL-0487: flat disc/annulus TOP label zone (closure top), core chain end to end.

Synthetic nominal closure (15 mm tall, 90 mm diameter, mm_unverified); not a measurement.
"""

from __future__ import annotations

import math
import re

import numpy as np
import pytest
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QColor, QImage

from packlab_core.blender_label_render_overlay import create_label_render_overlay_binding
from packlab_core.label_artwork import create_label_artwork_assignment, ingest_label_artwork
from packlab_core.label_dieline_svg import export_label_dieline_svg
from packlab_core.label_metric_surface_binding import (
    LabelMetricSurfaceBindingError,
    create_label_dieline,
    create_label_dieline_print_intent,
    create_label_metric_surface_binding,
    disc_radii,
    map_label_artwork_to_metric_surface,
)
from packlab_core.label_zone import LabelZoneBoundary, LabelZoneKind
from packlab_studio.app import create_application
from packlab_studio.design_workbench import (
    DesignWorkbench,
    DesignWorkbenchError,
    label_preview_points,
    nominal_jar_design_document,
)

RADIUS = 45.0


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    return create_application(["packlab-top-disc"])


@pytest.fixture
def closure(app) -> DesignWorkbench:
    workbench = DesignWorkbench()
    workbench.open_document(
        nominal_jar_design_document(
            height_mm=15.0, diameter_mm=2 * RADIUS, created_at_utc="2026-11-22T00:00:00Z"
        ),
        part_name="closure",
    )
    return workbench


def _png(width: int, height: int) -> bytes:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("#d22"))
    for x in range(width // 2):  # left half blue: shows orientation
        for y in range(height):
            image.setPixelColor(x, y, QColor("#22d"))
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")  # type: ignore[call-overload]
    return bytes(buffer.data().data())


def test_top_disc_geometry_radii_and_limits(closure) -> None:
    suggestion = closure.suggest_label_zone(LabelZoneKind.TOP)
    assert suggestion.candidate.center[2] == pytest.approx(15.0)
    entry = closure.add_label_zone(suggestion, disc_outer_radius_mm=40.0, disc_inner_radius_mm=10.0)
    binding = entry.metric_binding
    parameters = dict(binding.mapping_parameters)
    assert binding.mapping_mode == "PLANAR_DISC"
    assert binding.host_width_mm_unverified == pytest.approx(2 * RADIUS)
    assert parameters["host_outer_radius_mm_unverified"] == pytest.approx(RADIUS)
    assert parameters["plane_z_mm_unverified"] == pytest.approx(15.0)
    assert disc_radii(binding) == pytest.approx((40.0, 10.0))
    assert entry.size_mm == pytest.approx((80.0, 80.0))
    area = math.pi * (40.0**2 - 10.0**2)  # printed annulus area, mm^2 (mm_unverified)
    assert area == pytest.approx(4712.39, abs=0.01)
    b = entry.placement.boundary
    assert (b.u_min + b.u_max, b.u_max - b.u_min) == pytest.approx((1.0, 80.0 / 90.0))

    whole = closure.add_label_zone(suggestion, variant_id="whole")
    assert disc_radii(whole.metric_binding) == pytest.approx((RADIUS, 0.0))

    for options, match in (
        ({"disc_outer_radius_mm": 46.0}, "at most the top face radius"),
        ({"disc_outer_radius_mm": 20.0, "disc_inner_radius_mm": 20.0}, "radius_out_of_range"),
        ({"disc_inner_radius_mm": -1.0}, "radius_out_of_range"),
        ({"disc_rotation_degrees": math.nan}, "rotation_invalid"),
    ):
        with pytest.raises((DesignWorkbenchError, LabelMetricSurfaceBindingError), match=match):
            closure.add_label_zone(suggestion, variant_id="bad", **options)
    with pytest.raises(LabelMetricSurfaceBindingError, match="centred_square"):
        closure.add_label_zone(
            suggestion, boundary=LabelZoneBoundary(0.0, 0.0, 0.5, 0.5), variant_id="off"
        )
    wrap = closure.suggest_label_zone(LabelZoneKind.WRAP)
    with pytest.raises(LabelMetricSurfaceBindingError, match="wrong_zone_kind"):
        create_label_metric_surface_binding(
            closure.session.model,
            closure.session.label_representation,
            closure.add_label_zone(wrap, variant_id="skirt").placement,
            wrap.analysis,
            wrap.candidate.analysis_region_id,
            disc_rotation_degrees=10.0,
        )


def test_top_artwork_keeps_print_scale_in_mm(closure) -> None:
    entry = closure.add_label_zone(
        closure.suggest_label_zone(LabelZoneKind.TOP), disc_outer_radius_mm=30.0
    )
    artwork = closure.import_artwork(entry, _png(400, 200), fit_mode="CONTAIN")
    rect = artwork.mapping.target_rect_normalized_uv
    width_mm = (rect[2] - rect[0]) * 2 * RADIUS
    height_mm = (rect[3] - rect[1]) * 2 * RADIUS
    assert width_mm == pytest.approx(60.0)  # spans the 60 mm label square
    assert height_mm == pytest.approx(30.0)  # same mm per pixel both ways (no stretch)
    assert width_mm / 400 == pytest.approx(height_mm / 200)


def test_top_dieline_is_circle_or_annulus_with_safe_and_bleed(closure, tmp_path) -> None:
    entry = closure.add_label_zone(
        closure.suggest_label_zone(LabelZoneKind.TOP),
        disc_outer_radius_mm=40.0,
        disc_inner_radius_mm=10.0,
    )
    dieline = create_label_dieline(entry.metric_binding, entry.placement)
    assert (dieline.width, dieline.height) == pytest.approx((80.0, 80.0))
    with pytest.raises(LabelMetricSurfaceBindingError, match="safe_margin"):
        create_label_dieline_print_intent(
            dieline, safe_margin_mm_unverified=15.0, bleed_mm_unverified=1.0
        )
    intent = create_label_dieline_print_intent(
        dieline, safe_margin_mm_unverified=2.0, bleed_mm_unverified=1.5
    )
    svg = export_label_dieline_svg(intent, entry.placement).svg_bytes.decode("utf-8")
    radii = {
        layer: (float(outer), float(inner))
        for layer, outer, inner in re.findall(
            r'id="([a-z-]+)" data-outer-radius-mm-unverified="([0-9.]+)" '
            r'data-inner-radius-mm-unverified="([0-9.]+)"',
            svg,
        )
    }
    assert radii == {
        "source-outline": (40.0, 10.0),
        "safe-boundary": (38.0, 12.0),
        "bleed-boundary": (41.5, 8.5),
    }
    assert " A 40 40 0 1 0 -40 0 " in svg and 'fill-rule="evenodd"' in svg
    assert 'data-known-spacing-mm-unverified="10"' in svg

    path, _export = closure.export_dieline_svg(entry, tmp_path)
    assert path.name == "closure-top-dieline.svg"
    assert 'id="source-outline" data-outer-radius-mm-unverified="40"' in path.read_text("utf-8")


def test_top_overlay_rotation_preview_and_mockup_package(closure, tmp_path, monkeypatch) -> None:
    entry = closure.add_label_zone(
        closure.suggest_label_zone(LabelZoneKind.TOP),
        disc_outer_radius_mm=40.0,
        disc_rotation_degrees=90.0,
    )
    closure.import_artwork(entry, _png(200, 200), fit_mode="CONTAIN")
    png = entry.artwork.content
    asset = ingest_label_artwork(png)
    mapping = map_label_artwork_to_metric_surface(
        asset, entry.placement, entry.metric_binding, fit_mode="CONTAIN"
    )
    assignment = create_label_artwork_assignment(mapping, entry.placement, variant_id="top")
    session = closure.session
    overlay = create_label_render_overlay_binding(
        session.model,
        session.label_representation,
        entry.analysis,
        entry.metric_binding,
        entry.placement,
        mapping,
        assignment,
        asset,
    )
    geometry = dict(overlay.geometry)
    assert overlay.mapping_mode == "PLANAR_DISC"
    # canonical artwork right = -X, up = -Y; turned 90 deg about +Z: right = -Y, up = +X
    assert geometry["u_axis"] == pytest.approx([0.0, -1.0, 0.0])
    assert geometry["v_axis"] == pytest.approx([1.0, 0.0, 0.0])

    points, colors = label_preview_points(session, entry)
    assert np.allclose(points[:, 2], 15.2)  # on the top face, lifted 0.2 mm
    assert np.hypot(points[:, 0], points[:, 1]).max() <= 40.0 + 1e-6
    left = colors[points[:, 1] > 5.0]  # artwork left half (blue) lies at +Y after 90 deg
    assert (left[:, 2] > left[:, 0]).mean() > 0.95

    monkeypatch.setenv("PACKLAB_BUILD_REVISION", "a" * 40)
    fake = tmp_path / "blender.exe"
    fake.write_bytes(b"not run")
    out = tmp_path / "out"
    out.mkdir()
    job = closure.prepare_mockup(out, executable=fake)
    overlays = job.package.manifest()["body"]["scene"]["overlays"]
    assert [item["mapping_mode"] for item in overlays] == ["PLANAR_DISC"]
    assert overlays[0]["geometry"]["outer_radius_mm_unverified"] == pytest.approx(40.0)
