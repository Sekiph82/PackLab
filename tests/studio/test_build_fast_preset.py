"""Fast build preset: capture-order photos, neighbour pair list, no RefineMesh (fake runners)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from packlab_core.reconstruction import ReconstructionStageResult, StageStatus
from packlab_studio import build_model, i18n, navigation
from packlab_studio.app import create_application
from packlab_studio.build_model import (
    BUILD_QUALITIES,
    ColmapOpenMvsBackend,
    capture_sequence,
    determinism,
    fast_match_pairs,
)

ASSET = "working/reconstruction/r1"
TOOLS = (
    "interface_colmap",
    "densify_point_cloud",
    "reconstruct_mesh",
    "refine_mesh",
    "texture_mesh",
)


def _context(names: list[str]):
    inputs = type(
        "Inputs", (), {"image_asset_ids": tuple(f"{ASSET}/inputs/images/{n}" for n in names)}
    )
    return type("Context", (), {"cancel": None, "job": type("Job", (), {"inputs": inputs})})


def _plan(monkeypatch, tmp_path: Path, quality: str, facts: dict[str, object]):
    backend = ColmapOpenMvsBackend(
        tmp_path / "colmap.exe", {key: tmp_path / f"{key}.exe" for key in TOOLS}, quality=quality
    )
    commands: dict[str, list[tuple[str, ...]]] = {}

    def record(stage_id, planned, cancel):
        commands[stage_id] = [tuple(args) for args, _cwd in planned]
        return ReconstructionStageResult(stage_id, StageStatus.FAILED, 1, 0.0, "", "")

    monkeypatch.setattr(build_model, "_run_commands", record)
    monkeypatch.setattr(build_model.shutil, "copyfile", lambda s, d: Path(d).write_bytes(b"x"))
    stages = {stage.stage_id: stage for stage in backend.stages(tmp_path, ASSET, facts)}
    return stages, commands


def test_pair_list_covers_neighbours_rings_and_is_far_below_exhaustive() -> None:
    pairs = fast_match_pairs(81)
    assert pairs == sorted(set(pairs)) and all(0 <= i < j < 81 for i, j in pairs)
    assert {(0, 1), (0, 12), (0, 16), (0, 32), (0, 64), (64, 80)} <= set(pairs)
    assert (0, 13) not in pairs  # beyond the overlap only quadratic / ring pairs
    assert {(0, 15), (0, 14), (1, 15), (16, 31), (64, 79)} <= set(pairs)  # ring closure
    assert {(16, 31), (16, 32), (16, 33)} <= set(pairs)  # same wedge, adjacent ring
    assert len(pairs) < 81 * 80 // 2 // 2
    assert fast_match_pairs(1) == [] and fast_match_pairs(2) == [(0, 1)]


def test_capture_sequence_reads_photos_json_and_falls_back(tmp_path) -> None:
    package = tmp_path / "scan.packscan"
    photos = [
        {"image_path": "images/B.heic", "sequence": 0},
        {"image_path": "images/A.heic", "sequence": 1},
        {"image_path": "images/C.heic", "sequence": "2"},  # not an int: ignored
    ]
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("metadata/photos.json", json.dumps({"photos": photos}))
    assert capture_sequence(package) == {"images/B.heic": 0, "images/A.heic": 1}
    with zipfile.ZipFile(tmp_path / "empty.packscan", "w") as archive:
        archive.writestr("metadata/photos.json", "{}")
    assert capture_sequence(tmp_path / "empty.packscan") == {}
    assert capture_sequence(tmp_path / "missing.packscan") == {}


@pytest.mark.parametrize("quality", ["fast", "high"])
def test_photos_follow_capture_sequence_not_file_name(monkeypatch, tmp_path, quality) -> None:
    facts: dict[str, object] = {
        "capture_sequence": {"images/c.jpg": 0, "images/a.jpg": 1, "images/b.jpg": 2}
    }
    stages, _commands = _plan(monkeypatch, tmp_path, quality, facts)
    stages["feature-extraction"].execute(_context(["a.jpg", "b.jpg", "c.jpg", "d.jpg"]))
    images = tmp_path / "outputs/colmap/images"
    # Sorted working names (COLMAP's canonical image ids) are the capture order; a photo
    # without a sequence goes last.
    assert sorted(path.name for path in images.iterdir()) == [
        "0000_c.jpg",
        "0001_a.jpg",
        "0002_b.jpg",
        "0003_d.jpg",
    ]


def test_fast_plan_matches_pair_list_densifies_lower_and_skips_refine(monkeypatch, tmp_path):
    stages, commands = _plan(monkeypatch, tmp_path, "fast", {})
    stages["feature-extraction"].execute(_context([f"{n:02d}.jpg" for n in range(20)]))
    stages["matching"].execute(_context([]))
    args = commands["matching"][0]
    assert args[1] == "matches_importer" and args[args.index("--match_type") + 1] == "pairs"
    assert args[args.index("--TwoViewGeometry.random_seed") + 1] == "0"
    lines = Path(args[args.index("--match_list_path") + 1]).read_text("utf-8").splitlines()
    assert lines[0] == "0000_00.jpg 0001_01.jpg"
    assert len(lines) == len(fast_match_pairs(20))

    stages["dense-point-cloud"].execute(_context([]))
    densify = commands["dense-point-cloud"][0]
    assert densify[densify.index("--max-resolution") + 1] == "750"

    stages["mesh-reconstruction"].execute(_context([]))
    mesh = commands["mesh-reconstruction"][0]
    assert mesh[mesh.index("--target-face-num") + 1] == str(build_model.FAST_MESH_FACES)

    mvs = tmp_path / "outputs/mvs"
    mvs.mkdir(parents=True)
    (mvs / "scene_dense_mesh.ply").write_text("ply\n", encoding="ascii")
    refine = stages["mesh-refinement"].execute(_context([]))
    assert "mesh-refinement" not in commands  # RefineMesh never started
    assert (
        refine.stage_result.status is StageStatus.SUCCEEDED
        and "skipped" in refine.stage_result.stdout
    )
    assert refine.output_asset_ids["mesh"] == f"{ASSET}/outputs/mvs/scene_dense_mesh.ply"

    stages["texture-mesh"].execute(_context([]))
    texture = commands["texture-mesh"][0]
    assert texture[texture.index("-m") + 1] == "scene_dense_mesh.ply"
    configuration = stages["matching"].configuration
    assert configuration["preset"] == BUILD_QUALITIES["fast"]
    assert configuration["build_quality"] == "fast"
    assert configuration["image_order"] == "capture_sequence"


def test_high_quality_plan_is_the_original_pipeline(monkeypatch, tmp_path) -> None:
    stages, commands = _plan(monkeypatch, tmp_path, "high", {})
    (tmp_path / "outputs/mvs").mkdir(parents=True)
    (tmp_path / "outputs/mvs/scene_refined.ply").write_text("ply\n", encoding="ascii")
    for stage_id in ("matching", "dense-point-cloud", "mesh-refinement", "texture-mesh"):
        stages[stage_id].execute(_context([]))
    assert commands["matching"][0][1] == "exhaustive_matcher"
    densify = commands["dense-point-cloud"][0]
    assert densify[densify.index("--resolution-level") + 1] == "1"
    assert "--max-resolution" not in densify
    assert commands["mesh-refinement"][0][0].endswith("refine_mesh.exe")
    stages["mesh-reconstruction"].execute(_context([]))
    assert "--target-face-num" not in commands["mesh-reconstruction"][0]
    texture = commands["texture-mesh"][0]
    assert texture[texture.index("-m") + 1] == "scene_refined.ply"
    assert stages["matching"].configuration["preset"] == "studio-cpu-v1"
    assert determinism(2, "high")["mesh_refinement"] == "RefineMesh"


def test_settings_quality_defaults_to_fast_and_translates(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    create_application(["packlab-quality-test"])
    monkeypatch.setattr(navigation, "engine_rows", lambda: [])
    view = navigation.SettingsView()
    assert view.build_quality.currentData() == "fast"
    assert [view.build_quality.itemData(i) for i in range(view.build_quality.count())] == [
        "fast",
        "high",
    ]
    i18n.set_language("tr")
    try:
        assert i18n.tr("Fast (default)") == "Hızlı (varsayılan)"
        assert i18n.tr("High quality") == "Yüksek kalite"
        assert i18n.tr("Build quality") == "Model kalitesi"
    finally:
        i18n.set_language("en")
