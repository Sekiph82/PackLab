from __future__ import annotations

import hashlib
import json
from pathlib import Path

from packlab_core.packscan import write_packscan
from packlab_studio.ingest import DeterministicFilePicker, ImportService, IngestController


def _package(path: Path, repo_root: Path) -> Path:
    manifest = json.loads((repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8"))
    manifest["capture_id"] = "ingest-capture"
    manifest["payloads"][0]["size_bytes"] = 3
    manifest["payloads"][0]["sha256"] = hashlib.sha256(b"IMG").hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return write_packscan(path, manifest, {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"})


def test_drop_and_picker_use_one_validating_service(tmp_path: Path, repo_root: Path) -> None:
    package = _package(tmp_path / "capture.packscan", repo_root)
    controller = IngestController(ImportService())
    dropped = controller.ingest_dropped([package])
    selected = controller.ingest_from_picker(DeterministicFilePicker(package))
    assert dropped[0].state == selected.state == "validated"
    assert dropped[0].capture_id == selected.capture_id == "ingest-capture"
    assert dropped[0].source_channel == "drop"
    assert selected.source_channel == "picker"


def test_drop_order_duplicates_extensions_directories_and_missing_paths_are_structured(tmp_path: Path, repo_root: Path) -> None:
    package = _package(tmp_path / "capture.packscan", repo_root)
    text = tmp_path / "capture.txt"
    text.write_text("not a package", encoding="utf-8")
    directory = tmp_path / "folder.packscan"
    directory.mkdir()
    controller = IngestController(ImportService())
    results = controller.ingest_dropped([package, package, text, directory, tmp_path / "missing.packscan"])
    assert [result.error_code for result in results] == [None, "duplicate_selection", "unsupported_extension", "directory_not_file", "missing_path"]
    assert controller.ingest_from_picker(DeterministicFilePicker(None)).error_code == "picker_cancelled"


def test_invalid_package_is_not_imported(tmp_path: Path) -> None:
    bad = tmp_path / "bad.packscan"
    bad.write_bytes(b"not zip")
    result = ImportService().import_path(bad, source_channel="drop")
    assert result.state == "rejected"
    assert result.error_code == "corrupt_zip"
