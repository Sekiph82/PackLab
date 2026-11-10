from __future__ import annotations

from dataclasses import replace

import pytest

from packlab_core.scan_station_layout import (
    IPHONE_16_MAIN_LANDSCAPE,
    IPHONE_16_MAIN_PORTRAIT,
    camera_position,
    layout_issues,
    panel,
    pl0397_v01_layout,
    pl0397_v02_layout,
    view_angles_deg,
)

FOVS = (IPHONE_16_MAIN_PORTRAIT, IPHONE_16_MAIN_LANDSCAPE)


def test_iphone_16_main_fov_matches_26mm_equivalent_4_3_frame() -> None:
    assert IPHONE_16_MAIN_LANDSCAPE.horizontal_deg == pytest.approx(67.3, abs=0.1)
    assert IPHONE_16_MAIN_LANDSCAPE.vertical_deg == pytest.approx(53.1, abs=0.1)
    assert IPHONE_16_MAIN_PORTRAIT.horizontal_deg == IPHONE_16_MAIN_LANDSCAPE.vertical_deg


def test_view_angles_on_axis_and_behind_camera() -> None:
    cam, target = (0.0, 800.0, 200.0), (0.0, 0.0, 200.0)
    h, v, depth = view_angles_deg(cam, target, (0.0, -100.0, 200.0))
    assert (h, v) == pytest.approx((0.0, 0.0)) and depth == pytest.approx(900.0)
    assert view_angles_deg(cam, target, (0.0, 1000.0, 200.0))[2] < 0


@pytest.mark.parametrize("fov", FOVS, ids=lambda f: f.name)
def test_original_pl0397_layout_puts_lights_in_frame_and_too_close(fov) -> None:
    issues = layout_issues(pl0397_v01_layout(), fov)
    assert any("emitting surface in frame" in issue for issue in issues)
    assert any("stand foot" in issue for issue in issues)


@pytest.mark.parametrize("fov", FOVS, ids=lambda f: f.name)
def test_revised_layout_frames_envelope_without_lights_in_view(fov) -> None:
    assert layout_issues(pl0397_v02_layout(), fov) == []


def test_revised_layout_keeps_margin_for_larger_panels() -> None:
    layout = pl0397_v02_layout()
    bigger = tuple(panel(light.name, light.emitting_points[0], 500.0, light.stand_foot_xy) for light in layout.lights)
    for fov in FOVS:
        assert layout_issues(replace(layout, lights=bigger), fov) == []


def test_oversized_envelope_and_close_camera_are_reported() -> None:
    layout = replace(pl0397_v02_layout(), camera_distance_mm=450.0)
    issues = layout_issues(layout, IPHONE_16_MAIN_LANDSCAPE)
    assert any("envelope fills" in issue for issue in issues)
    assert camera_position(layout, 90.0, 200.0) == pytest.approx((450.0, 0.0, 200.0))
