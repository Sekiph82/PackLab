from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import pytest
from tests.core.test_blender_real_scene_smoke import _hybrid_sources

from packlab_core.blender_render import (
    BlenderRenderError,
    render_standard_views,
)


def _fixture(tmp_path: Path):
    package = _hybrid_sources(tmp_path)
    body_source = package.manifest()["body"]["source"]
    source_revisions = tuple(
        sorted(
            (key.removesuffix("_revision_id"), value)
            for key, value in body_source.items()
            if key.endswith("_revision_id")
        )
    )
    return package, source_revisions


def _job(script_path: Path) -> dict[str, object]:
    source = script_path.read_text("utf-8")
    match = re.search(r"^_job=json.loads\((.+)\)$", source, re.MULTILINE)
    assert match is not None
    return json.loads(ast.literal_eval(match.group(1)))


def _write_fake_render(job: dict[str, object], root: Path, *, index: int) -> None:
    settings = job["settings"]
    preset = job["preset"]
    output_path = root / settings["output_relative_path"]
    evidence_path = root / settings["evidence_relative_path"]
    scene_path = root / f"renders/standard_views/{preset['view'].lower()}.scene.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene_path.write_text("{}", encoding="utf-8")
    image = f"fixture-png-{index}".encode()
    output_path.write_bytes(image)
    body_source = {
        key: value
        for key, value in job["scene_source"].items()
        if key.endswith("_revision_id") or key.endswith("_sha256")
    }
    evidence = {
        "scene_package_revision_id": job["scene_package_revision_id"],
        "scene_package_sha256": job["scene_package_sha256"],
        "render_preset_revision_id": preset["revision_id"],
        "source_revisions_and_digests": body_source,
        "blender": {
            "version": [5, 2, 2],
            "version_string": "5.2.2 LTS",
            "build_hash": "fixture-build",
            "build_branch": "fixture-branch",
            "build_date": "2026-09-15",
        },
        "settings": {
            "engine": "BLENDER_EEVEE",
            "device": "EEVEE_DEFAULT",
            "width": settings["width"],
            "height": settings["height"],
            "samples": settings["samples"],
            "image_format": "PNG",
            "color_mode": "RGBA",
            "color_depth": "8",
            "transparent_background": True,
            "resolution_percentage": 100,
            "view_transform": "Standard",
            "camera_view": preset["view"],
            "camera_location": preset["camera"]["location"],
            "camera_target": preset["camera"]["target"],
            "camera_lens_mm": 50.0,
            "light_facts": preset["lights"],
        },
        "output": {
            "sha256": hashlib.sha256(image).hexdigest(),
            "byte_length": len(image),
            "width": settings["width"],
            "height": settings["height"],
            "alpha_channel": True,
            "visible_pixel_count": 1,
            "transparent_pixel_count": 1,
            "all_mesh_bounds_inside_camera": True,
        },
    }
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")


def test_three_view_batch_is_ordered_shared_and_digest_bound(tmp_path: Path) -> None:
    package, source_revisions = _fixture(tmp_path)
    calls = []

    def fake_executor(_exe, script_path, root, **_kwargs):
        job = _job(script_path)
        calls.append(job["preset"]["view"])
        job["scene_source"] = package.manifest()["body"]["source"]
        _write_fake_render(job, root, index=len(calls))
        return subprocess.CompletedProcess(["blender"], 0, "PACKLAB_BLENDER_RENDER_VALID", "")

    result = render_standard_views(
        "blender",
        package,
        (0.0, -0.06, 0.0),
        (0.1, 0.0, 0.06),
        source_revisions,
        tmp_path,
        packlab_commit="a" * 40,
        packlab_version="0.1.0",
        blender_executable_sha256="b" * 64,
        width=128,
        height=128,
        samples=4,
        render_executor=fake_executor,
    )
    assert calls == ["FRONT", "THREE_QUARTER", "BACK"]
    assert result["view_order"] == calls
    assert result["scene_package_revision_id"] == package.revision_id
    assert result["scene_package_sha256"] == package.manifest()["content_sha256"]
    provenance = result["m14_render_provenance"]
    assert provenance["identity"].startswith("m14-render-provenance:")
    assert provenance["identity_payload"]["packlab"] == {
        "commit": "a" * 40,
        "version": "0.1.0",
    }
    assert len(provenance["outputs"]) == 3
    assert provenance["limitations"]["cross_hardware_pixel_identity_guaranteed"] is False
    records = result["views"]
    assert [record["order"] for record in records] == [1, 2, 3]
    assert len({record["camera_id"] for record in records}) == 3
    assert len({tuple(record["camera_location"]) for record in records}) == 3
    assert all(record["width"] == record["height"] == 128 for record in records)
    assert all(record["alpha_channel"] for record in records)
    assert len(set(result["output_sha256_by_view"].values())) == 3
    manifest_path = tmp_path / "renders/standard_views_manifest.json"
    assert json.loads(manifest_path.read_bytes()) == result
    assert str(tmp_path) not in manifest_path.read_text("utf-8")
    for view in ("front", "three_quarter", "back"):
        evidence = json.loads((tmp_path / f"renders/standard_views/{view}.render.json").read_text())
        assert evidence["m14_render_provenance"] == provenance
    assert not list((tmp_path / "renders/standard_views").glob("*.scene.json"))


def test_partial_failure_removes_only_created_batch_outputs(tmp_path: Path) -> None:
    package, source_revisions = _fixture(tmp_path)
    calls = 0

    def fail_second(_exe, script_path, root, **_kwargs):
        nonlocal calls
        calls += 1
        job = _job(script_path)
        if calls == 2:
            raise BlenderRenderError("simulated_second_view_failure")
        job["scene_source"] = package.manifest()["body"]["source"]
        _write_fake_render(job, root, index=calls)
        return subprocess.CompletedProcess(["blender"], 0, "PACKLAB_BLENDER_RENDER_VALID", "")

    with pytest.raises(BlenderRenderError, match="simulated_second_view_failure"):
        render_standard_views(
            "blender",
            package,
            (0.0, -0.06, 0.0),
            (0.1, 0.0, 0.06),
            source_revisions,
            tmp_path,
            packlab_commit="a" * 40,
            packlab_version="0.1.0",
            blender_executable_sha256="b" * 64,
            width=128,
            height=128,
            render_executor=fail_second,
        )
    assert not (tmp_path / "renders/standard_views/front.png").exists()
    assert not (tmp_path / "renders/standard_views/front.render.json").exists()
    assert not (tmp_path / "renders/standard_views/front.scene.json").exists()
    assert not (tmp_path / "renders/standard_views_manifest.json").exists()


@pytest.mark.skipif(
    os.environ.get("PACKLAB_REAL_BLENDER_SMOKE") != "1",
    reason="set PACKLAB_REAL_BLENDER_SMOKE=1 to render all views with approved Blender 5.2.2",
)
def test_real_blender_renders_all_three_ordered_views(tmp_path: Path) -> None:
    executable = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
    if not executable.is_file():
        pytest.fail("approved_blender_5_2_2_executable_missing")
    package, source_revisions = _fixture(tmp_path)
    result = render_standard_views(
        executable,
        package,
        (0.0, -0.06, 0.0),
        (0.1, 0.0, 0.06),
        source_revisions,
        tmp_path,
        packlab_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).parents[2], text=True
        ).strip(),
        packlab_version="0.1.0",
        width=256,
        height=256,
        samples=8,
        timeout_seconds=180,
    )
    assert result["view_order"] == ["FRONT", "THREE_QUARTER", "BACK"]
    records = result["views"]
    assert len(records) == 3
    assert len({item["camera_id"] for item in records}) == 3
    assert len({tuple(item["camera_location"]) for item in records}) == 3
    assert len({item["output_sha256"] for item in records}) == 3
    for item in records:
        image = tmp_path / item["output_relative_path"]
        assert hashlib.sha256(image.read_bytes()).hexdigest() == item["output_sha256"]
        assert item["width"] == item["height"] == 256
        assert item["visible_pixel_count"] > 0
        assert item["transparent_pixel_count"] > 0
        assert item["alpha_channel"] is True
    assert result["authority_limits"]["physical_accuracy_inferred"] is False
    assert str(tmp_path) not in (tmp_path / "renders/standard_views_manifest.json").read_text(
        "utf-8"
    )
