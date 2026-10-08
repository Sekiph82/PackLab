from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from tools.packaging.validate_controlled_ocp_manifest import (
    load_and_validate_manifest,
    validate_staged_tree,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LOCK = ROOT / "tools" / "packaging" / "windows_native_source_lock.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def controlled_manifest(tmp_path: Path) -> tuple[Path, dict[str, object], dict[str, bytes]]:
    source_lock = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    records = {row["id"]: row for row in source_lock["records"]}
    files = {
        "OCP/OCP.cp312-win_amd64.pyd": b"binding",
        "OCP/TKBRep.dll": b"occt-runtime",
    }
    manifest = {
        "schema_version": 1,
        "status": "PASS",
        "input_lock_sha256": digest(SOURCE_LOCK.read_bytes()),
        "files": [],
    }
    for relative, content in files.items():
        source_id = "ocp-source-7.9.3.1.1" if relative.endswith(".pyd") else "occt-source-7.9.3"
        record = records[source_id]
        manifest["files"].append(
            {
                "relative_path": relative,
                "sha256": digest(content),
                "owning_component": record["component"],
                "source_package_id": source_id,
                "version": record["version"],
                "build_revision": record["revision"],
                "license_identifier": record["license_identifier"],
                "license_notice_source": record["license_notice_source"],
                "production_purpose": "test fixture",
            }
        )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, manifest, files


def test_controlled_ocp_manifest_binds_exact_lock_and_stage(
    tmp_path: Path, controlled_manifest: tuple[Path, dict[str, object], dict[str, bytes]]
) -> None:
    manifest_path, _, files = controlled_manifest
    manifest = load_and_validate_manifest(manifest_path, SOURCE_LOCK)
    stage = tmp_path / "PackLabStudio"
    for relative, content in files.items():
        destination = stage / "_internal" / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    validate_staged_tree(stage, manifest)


def test_controlled_ocp_manifest_rejects_unmanifested_extension(
    tmp_path: Path, controlled_manifest: tuple[Path, dict[str, object], dict[str, bytes]]
) -> None:
    manifest_path, _, files = controlled_manifest
    manifest = load_and_validate_manifest(manifest_path, SOURCE_LOCK)
    stage = tmp_path / "PackLabStudio"
    for relative, content in files.items():
        destination = stage / "_internal" / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    (stage / "_internal" / "OCP" / "Opaque.pyd").write_bytes(b"unmapped")
    with pytest.raises(ValueError, match="without controlled provenance"):
        validate_staged_tree(stage, manifest)


def test_controlled_ocp_manifest_rejects_missing_native_file(
    tmp_path: Path, controlled_manifest: tuple[Path, dict[str, object], dict[str, bytes]]
) -> None:
    manifest_path, _, files = controlled_manifest
    manifest = load_and_validate_manifest(manifest_path, SOURCE_LOCK)
    stage = tmp_path / "PackLabStudio"
    relative, content = next(iter(files.items()))
    destination = stage / "_internal" / Path(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    with pytest.raises(ValueError, match="manifest and staged native files differ"):
        validate_staged_tree(stage, manifest)
