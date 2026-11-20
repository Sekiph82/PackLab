"""PL-0444 pinned engine bundle: hash verification, safe extraction, staging, inventory."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from tools.packaging import engine_bundle
from tools.packaging import windows_redistribution_inventory as inventory

ROOT = Path(__file__).resolve().parents[2]


def _zip(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return buffer.getvalue()


def _fake_manifest(seed: Path) -> dict[str, object]:
    colmap = _zip({"bin/colmap.exe": b"colmap", "bin/x.pdb": b"pdb", "COLMAP.bat": b"bat"})
    openmvs = _zip({"vc17/x64/Release/DensifyPointCloud.exe": b"dpc", "README": b"skip"})
    (seed / "colmap.zip").write_bytes(colmap)
    (seed / "openmvs.zip").write_bytes(openmvs)
    real = engine_bundle.load_manifest()["engines"]
    return {
        "schema_version": 1,
        "engines": [
            {
                **real[0],
                "archive_name": "colmap.zip",
                "archive_sha256": hashlib.sha256(colmap).hexdigest(),
            },
            {
                **real[1],
                "archive_name": "openmvs.zip",
                "archive_sha256": hashlib.sha256(openmvs).hexdigest(),
                "executables": {"densify_point_cloud": "DensifyPointCloud.exe"},
            },
        ],
    }


def test_pinned_manifest_matches_task_hashes_and_license_texts() -> None:
    engines = {e["id"]: e for e in engine_bundle.load_manifest()["engines"]}
    assert engines["colmap"]["archive_sha256"] == (
        "c493d88cb4a43f21afba42cb55bf786e5434a0420e73db0ba1454c5d8b3686ae"
    )
    assert engines["openmvs"]["archive_sha256"] == (
        "0c31660c15c9ebc4c106873cf67564d9570d404aef7a6403451da1b6178b2167"
    )
    assert engines["openmvs"]["license_identifier"] == "AGPL-3.0-only"
    for engine in engines.values():
        for license_file in engine["license_files"]:
            assert engine_bundle.sha256_file(ROOT / license_file["path"]) == license_file["sha256"]


def test_stage_bundle_extracts_excludes_and_records_hashes(tmp_path: Path) -> None:
    seed = tmp_path / "seed"
    seed.mkdir()
    manifest = _fake_manifest(seed)
    dest = tmp_path / "engines"
    status = engine_bundle.stage_bundle(tmp_path / "cache", dest, [seed], manifest)
    assert status == "STAGED"
    assert (dest / "colmap" / "bin" / "colmap.exe").read_bytes() == b"colmap"
    assert not (dest / "colmap" / "bin" / "x.pdb").exists()
    assert (dest / "openmvs" / "DensifyPointCloud.exe").read_bytes() == b"dpc"
    assert (dest / "openmvs" / "LICENSES" / "SOURCE_OFFER.txt").is_file()
    record = json.loads((dest / engine_bundle.RECORD_NAME).read_text(encoding="utf-8"))
    paths = {item["relative_path"]: item for item in record["files"]}
    assert paths["openmvs/DensifyPointCloud.exe"]["component_id"] == "openmvs-2.4.0"
    assert engine_bundle.stage_bundle(tmp_path / "cache", dest, [seed], manifest) == "UP_TO_DATE"
    (dest / "colmap" / "bin" / "colmap.exe").write_bytes(b"tampered")
    assert engine_bundle.stage_bundle(tmp_path / "cache", dest, [seed], manifest) == "STAGED"


def test_tampered_archive_is_rejected_and_not_cached(tmp_path: Path) -> None:
    seed = tmp_path / "seed"
    seed.mkdir()
    manifest = _fake_manifest(seed)
    (seed / "colmap.zip").write_bytes(_zip({"bin/colmap.exe": b"evil"}))
    with pytest.raises(ValueError, match="does not match pinned"):
        engine_bundle.stage_bundle(tmp_path / "cache", tmp_path / "engines", [seed], manifest)
    assert not (tmp_path / "cache" / "archives" / "colmap.zip").exists()
    assert not (tmp_path / "engines").exists()


def test_tampered_cached_archive_is_rejected(tmp_path: Path) -> None:
    seed = tmp_path / "seed"
    seed.mkdir()
    manifest = _fake_manifest(seed)
    cached = tmp_path / "cache" / "archives" / "colmap.zip"
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"not the pinned archive")
    with pytest.raises(ValueError, match="does not match pinned"):
        engine_bundle.stage_bundle(tmp_path / "cache", tmp_path / "engines", [seed], manifest)


def test_unsafe_archive_member_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "evil.zip"
    archive.write_bytes(_zip({"../escape.exe": b"x"}))
    engine = {"id": "colmap", "archive_subdir": "", "exclude_globs": []}
    with pytest.raises(ValueError, match="unsafe"):
        engine_bundle.extract_archive(archive, engine, tmp_path / "out")
    assert not (tmp_path / "escape.exe").exists()


def test_metered_hotspot_blocks_download(monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        stdout = "IPv4 Address. . . : 172.20.10.4"

    monkeypatch.setattr(engine_bundle.os, "name", "nt")
    monkeypatch.setattr(engine_bundle.subprocess, "run", lambda *a, **k: Result())
    with pytest.raises(RuntimeError, match="metered"):
        engine_bundle.assert_unmetered_network()


def test_license_inventory_maps_staged_engines_and_keeps_them_blocked(tmp_path: Path) -> None:
    seed = tmp_path / "seed"
    seed.mkdir()
    manifest = _fake_manifest(seed)
    stage = tmp_path / "PackLabStudio"
    engine_bundle.stage_bundle(tmp_path / "cache", stage / "engines", [seed], manifest)
    # The inventory trusts the repository manifest; bind the fake archives to it.
    project = tmp_path / "project"
    (project / "tools" / "packaging").mkdir(parents=True)
    (project / "tools" / "packaging" / "engine_bundle_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    mapped = inventory.engine_bundle_files(stage, project)
    assert mapped["engines/colmap/bin/colmap.exe"]["component_id"] == "colmap-4.2.1"
    assert mapped["engines/openmvs/licenses/license.txt"]["component_id"] == "openmvs-2.4.0"
    # Against the real pinned manifest the fake archives do not match: nothing maps.
    assert inventory.engine_bundle_files(stage, ROOT) == {}

    registry = json.loads(
        (ROOT / "tools/packaging/windows_component_license_registry.json").read_text("utf-8")
    )
    components, notices, unresolved = inventory.license_rows(
        {"colmap-4.2.1", "openmvs-2.4.0"}, {}, registry, tmp_path / "evidence"
    )
    by_id = {row["component_id"]: row for row in components}
    assert by_id["colmap-4.2.1"]["license_identifier"] == "BSD-3-Clause"
    assert by_id["openmvs-2.4.0"]["license_identifier"] == "AGPL-3.0-only"
    assert any(n["path"].endswith("SOURCE_OFFER.txt") for n in notices)
    assert "legal" in by_id["openmvs-2.4.0"]["unresolved_reason"]
    # Pending legal review keeps redistribution clearance blocked.
    assert unresolved == {"component:colmap-4.2.1", "component:openmvs-2.4.0"}
