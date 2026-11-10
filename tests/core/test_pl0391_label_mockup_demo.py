"""PL-0391: label dieline + artwork + rendered product mockup share one authority chain.

The lineage test runs wherever the OCP CAD kernel is available (hosted CI included). The
rendered mockup needs the approved Blender 5.2.2 executable and runs only with
PACKLAB_REAL_BLENDER_SMOKE=1. All inputs are synthetic test fixtures; nothing here is a
print-fit, colour, physical or manufacturing validation.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from tests.core.test_blender_real_scene_smoke import _hybrid_scene

from packlab_core.blender_render import (
    BlenderRenderRequest,
    build_blender_render_runner,
    run_blender_render,
)
from packlab_core.blender_render_preset import create_blender_render_preset
from packlab_core.label_dieline_svg import export_label_dieline_svg
from packlab_core.label_metric_surface_binding import (
    create_label_dieline,
    create_label_dieline_print_intent,
)

BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")


def _chain(root: Path):
    package, model, brep, bindings = _hybrid_scene(root)
    overlays = package.manifest()["body"]["scene"]["overlays"]
    exports = []
    for binding in bindings:
        dieline = create_label_dieline(binding.metric_binding, binding.placement)
        intent = create_label_dieline_print_intent(
            dieline, safe_margin_mm_unverified=2.0, bleed_mm_unverified=1.5
        )
        exports.append((binding, intent, export_label_dieline_svg(intent, binding.placement)))
    return package, model, brep, overlays, exports


def test_svg_dieline_and_scene_overlay_share_the_exact_authority_chain(tmp_path: Path) -> None:
    package, model, brep, overlays, exports = _chain(tmp_path)
    by_placement = {item["placement_revision_id"]: item for item in overlays}
    assert len(exports) == len(overlays) == 3
    for binding, intent, svg in exports:
        overlay = by_placement[binding.placement.revision_id]
        record = svg.as_dict()
        text = svg.svg_bytes.decode("utf-8")
        # Criterion 1: the SVG is bound to the exact model/BREP/zone/placement revisions.
        assert intent.binding.source_design_model_revision_id == model.revision_id
        assert intent.binding.source_brep_revision_id == brep.revision_id
        assert intent.zone_id == binding.placement.zone_id == overlay["zone_id"]
        for revision in (model.revision_id, binding.placement.revision_id, intent.zone_id):
            assert revision in text
        # Criterion 2: artwork, mapping, assignment and overlay share the same parents.
        assert overlay["source_design_model_revision_id"] == model.revision_id
        assert overlay["source_brep_revision_id"] == brep.revision_id
        assert overlay["metric_surface_binding_revision_id"] == intent.binding.revision_id
        assert overlay["artwork_revision_id"] == binding.artwork.revision_id
        assert overlay["mapping_revision_id"] == binding.mapping.revision_id
        assert overlay["assignment_revision_id"] == binding.assignment.revision_id
        # Criterion 4: unverified units and no-manufacturing declarations stay visible.
        assert overlay["coordinate_unit"] == record["coordinate_unit"] == "mm_unverified"
        assert record["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
        assert record["print_fit_verified"] is False and record["print_ready"] is False
        assert record["manufacturing_authorized"] is False
        assert overlay["manufacturing_authorized"] is False
        assert overlay["physical_fit_verified"] is False


@pytest.mark.skipif(
    os.environ.get("PACKLAB_REAL_BLENDER_SMOKE") != "1",
    reason="set PACKLAB_REAL_BLENDER_SMOKE=1 to render the mockup through approved Blender 5.2.2",
)
def test_rendered_mockup_runs_through_the_blender_scene_pipeline(tmp_path: Path) -> None:
    if not BLENDER.is_file():
        pytest.fail("approved_blender_5_2_2_executable_missing")
    package, _model, _brep, overlays, exports = _chain(tmp_path)
    source = package.manifest()["body"]["source"]
    revisions = tuple(
        sorted(
            (key.removesuffix("_revision_id"), value)
            for key, value in source.items()
            if key.endswith("_revision_id")
        )
    )
    preset = create_blender_render_preset(
        (0.0, -0.06, 0.0), (0.1, 0.0, 0.06), "THREE_QUARTER", revisions
    )
    request = BlenderRenderRequest(width=512, height=512, samples=16)
    script = tmp_path / "blender_render_runner.py"
    script.write_bytes(build_blender_render_runner(package, preset, request))
    completed = run_blender_render(BLENDER, script, tmp_path)
    assert "PACKLAB_BLENDER_RENDER_VALID" in completed.stdout, completed.stderr[-2000:]

    image = (tmp_path / request.output_relative_path).read_bytes()
    evidence = json.loads((tmp_path / request.evidence_relative_path).read_bytes())
    assert image[:8] == b"\x89PNG\r\n\x1a\n"
    assert evidence["output"]["sha256"] == hashlib.sha256(image).hexdigest()
    assert evidence["output"]["visible_pixel_count"] > 0
    assert evidence["scene_package_revision_id"] == package.revision_id
    assert evidence["authority_limits"]["physical_accuracy_inferred"] is False
    assert evidence["network_access"] == "NONE"
    # Pixel content (regression for the factory-cube / overexposure / axis bugs): the
    # mockup must not be blown out and must show the saturated synthetic label colours.
    from PySide6.QtGui import QImage

    rendered = QImage.fromData(image)
    visible = white = saturated = 0
    for y in range(0, rendered.height(), 2):
        for x in range(0, rendered.width(), 2):
            pixel = rendered.pixelColor(x, y)
            if pixel.alpha() == 0:
                continue
            visible += 1
            channels = (pixel.red(), pixel.green(), pixel.blue())
            white += min(channels) >= 250
            saturated += max(channels) - min(channels) >= 120
    assert visible > 0
    assert white / visible < 0.2, white / visible
    assert saturated / visible > 0.02, saturated / visible
    summary = {
        "blender": "5.2.2 LTS",
        "scene_package_revision_id": package.revision_id,
        "render_preset_revision_id": preset.revision_id,
        "png_sha256": evidence["output"]["sha256"],
        "png_size": [evidence["output"]["width"], evidence["output"]["height"]],
        "visible_pixel_count": evidence["output"]["visible_pixel_count"],
        "overlay_revision_ids": sorted(item["revision_id"] for item in overlays),
        "svg_dieline_sha256": sorted(svg.svg_sha256 for _b, _i, svg in exports),
    }
    print("PL0391_MOCKUP_EVIDENCE " + json.dumps(summary, sort_keys=True))
