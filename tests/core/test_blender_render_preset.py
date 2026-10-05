from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from packlab_core.blender_render_preset import (
    BlenderRenderPresetError,
    build_blender_render_preset_runner,
    create_blender_render_preset,
)

_BOUNDS = ((-50.0, -30.0, 0.0), (50.0, 30.0, 80.0))
_SOURCES = (("cad_export", "cad-export:rev-1"), ("model", "design-model:rev-1"))
_RESULT = "PACKLAB_RENDER_PRESET_RESULT:"


def _preset(view: str = "FRONT", *, transparent: bool = True):
    return create_blender_render_preset(
        _BOUNDS[0],
        _BOUNDS[1],
        view,  # type: ignore[arg-type]
        _SOURCES,
        transparent_background=transparent,
    )


def test_named_versions_and_source_revisions_are_deterministic() -> None:
    front = _preset()
    assert front.contract == "packlab.blender-render-preset.v1"
    assert front.schema_version == 1
    assert front.revision_id == _preset().revision_id
    assert front.view == "FRONT"
    assert dict(front.source_revisions) == dict(_SOURCES)
    assert front.as_dict()["authority"] == "DERIVED_PRESENTATION_ONLY"
    assert front.as_dict()["physical_measurement_inference"] is False
    assert "C:\\" not in json.dumps(front.as_dict())


@pytest.mark.parametrize(
    ("view", "expected_signs"),
    (("FRONT", (0, -1)), ("THREE_QUARTER", (1, -1)), ("BACK", (0, 1))),
)
def test_camera_view_transforms_are_bounds_centered(view: str, expected_signs) -> None:
    preset = _preset(view)
    center = tuple((a + b) / 2 for a, b in zip(*_BOUNDS, strict=True))
    offset = tuple(a - b for a, b in zip(preset.camera_location, center, strict=True))
    assert preset.camera_target == center
    assert (0 if abs(offset[0]) < 1e-8 else (1 if offset[0] > 0 else -1)) == expected_signs[0]
    assert (1 if offset[1] > 0 else -1) == expected_signs[1]
    assert preset.camera_location != center


def test_bounds_change_framing_and_all_lighting_values_are_bounded() -> None:
    small = create_blender_render_preset((0.0, 0.0, 0.0), (10.0, 20.0, 30.0), "FRONT", _SOURCES)
    large = create_blender_render_preset((0.0, 0.0, 0.0), (20.0, 40.0, 60.0), "FRONT", _SOURCES)
    assert large.camera_location[1] < small.camera_location[1]
    assert len(small.lights) == 3
    assert {light["name"] for light in small.lights} == {"KEY", "FILL", "RIM"}
    for light in small.lights:
        assert 0 < light["energy_watts"] <= 2000
        assert 0 < light["size"] <= 100
        assert all(abs(value) <= 1_000_000 for value in light["location"])


def test_transparency_and_background_compatibility_are_in_identity() -> None:
    transparent = _preset(transparent=True)
    opaque = _preset(transparent=False)
    assert transparent.as_dict()["background"]["transparent"] is True
    assert opaque.as_dict()["background"]["transparent"] is False
    assert transparent.revision_id != opaque.revision_id
    assert opaque.as_dict()["background"]["rgba"] == [0.08, 0.08, 0.08, 1.0]


@pytest.mark.parametrize(
    ("low", "high", "view", "sources", "message"),
    [
        ((0.0, 0.0, 0.0), (0.0, 1.0, 1.0), "FRONT", _SOURCES, "render_bounds_extent_invalid"),
        (
            (0.0, 0.0, 0.0),
            (float("nan"), 1.0, 1.0),
            "FRONT",
            _SOURCES,
            "render_bounds_max_out_of_range",
        ),
        ((0.0, 0.0, 0.0), (1e9, 1.0, 1.0), "FRONT", _SOURCES, "render_bounds_max_out_of_range"),
        ((*_BOUNDS[0],), _BOUNDS[1], "SIDE", _SOURCES, "render_view_unsupported"),
        (
            _BOUNDS[0],
            _BOUNDS[1],
            "FRONT",
            (("model", "x"), ("model", "y")),
            "render_source_revision_key_duplicate",
        ),
    ],
)
def test_invalid_or_unbounded_inputs_fail_closed(low, high, view, sources, message) -> None:
    with pytest.raises(BlenderRenderPresetError, match=message):
        create_blender_render_preset(low, high, view, sources)  # type: ignore[arg-type]


@pytest.mark.parametrize("rgba", [(-0.1, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.1)])
def test_background_channels_must_be_normalized(rgba) -> None:
    with pytest.raises(BlenderRenderPresetError, match="render_background_channel_out_of_range"):
        create_blender_render_preset(*_BOUNDS, "FRONT", _SOURCES, background_rgba=rgba)


def test_runner_is_fixed_data_only_and_has_no_ambient_path() -> None:
    script = build_blender_render_preset_runner(_preset())
    assert script == build_blender_render_preset_runner(_preset())
    assert b"exec(" not in script
    assert b"requests" not in script
    assert b"urllib" not in script
    assert b"subprocess" not in script
    assert re.search(rb"blender-render-preset:[0-9a-f]{64}", script)


@pytest.mark.skipif(
    os.environ.get("PACKLAB_REAL_BLENDER_SMOKE") != "1",
    reason="set PACKLAB_REAL_BLENDER_SMOKE=1 to run the approved Blender smoke",
)
def test_real_blender_applies_camera_lighting_and_background(tmp_path: Path) -> None:
    executable = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
    if not executable.is_file():
        pytest.fail("approved_blender_5_2_2_executable_missing")
    script_path = tmp_path / "render_preset_runner.py"
    script_path.write_bytes(build_blender_render_preset_runner(_preset("THREE_QUARTER")))
    completed = subprocess.run(
        [
            str(executable),
            "--background",
            "--factory-startup",
            "--disable-autoexec",
            "--python",
            str(script_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert completed.returncode == 0, completed.stderr[-4000:]
    line = next((item for item in completed.stdout.splitlines() if _RESULT in item), None)
    assert line is not None, completed.stdout[-4000:]
    result = json.loads(line.split(_RESULT, 1)[1])
    assert result["view"] == "THREE_QUARTER"
    assert result["light_count"] == 3
    assert result["light_objects"] == [
        "PackLab Studio FILL",
        "PackLab Studio KEY",
        "PackLab Studio RIM",
    ]
    assert result["transparent_background"] is True
    assert result["resolution_px"] == [1024, 1024]
    assert result["source_revisions"] == dict(_SOURCES)
    assert result["physical_measurement_inference"] is False
    assert "C:\\" not in line
