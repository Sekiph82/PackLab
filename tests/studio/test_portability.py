from __future__ import annotations

import hashlib
import json

import pytest

from packlab_studio.portability import PortabilityClassification, scan_project_portability
from packlab_studio.project import ProjectError, ProjectManager


def _project(tmp_path):
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Portable")
    return manager, tmp_path / "project"


def test_fully_portable_project_report_is_redacted_and_preserves_raw(tmp_path) -> None:
    manager, root = _project(tmp_path)
    raw = root / "raw" / "capture.packscan"
    raw.write_bytes(b"accepted-source")
    before = hashlib.sha256(raw.read_bytes()).hexdigest()
    report = manager.portability_report()
    assert report.portable
    assert report.raw_digest
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == before
    encoded = json.dumps(report.to_dict())
    assert str(root) not in encoded
    assert "accepted-source" not in encoded


def test_missing_and_present_external_assets_are_classified_without_copying(tmp_path) -> None:
    manager, root = _project(tmp_path)
    present = tmp_path / "supplier" / "mesh.obj"
    present.parent.mkdir()
    present.write_text("v 0 0 0\n", encoding="utf-8")
    state = {
        "asset_references": [
            {"path": str(present), "required": True},
            {"path": str(tmp_path / "supplier" / "missing.ply"), "required": True},
        ]
    }
    (root / "working" / "state.json").write_text(json.dumps(state), encoding="utf-8")
    report = manager.portability_report()
    assert report.classifications(PortabilityClassification.EXTERNAL_PRESENT)
    assert report.classifications(PortabilityClassification.REQUIRED_MISSING)
    assert not (root / "supplier").exists()
    assert str(tmp_path) not in json.dumps(report.to_dict())


def test_derived_cache_is_regenerable_and_path_traversal_is_unsafe(tmp_path) -> None:
    manager, root = _project(tmp_path)
    (root / "derived" / "preview.bin").write_bytes(b"derived")
    state = {"asset_references": [{"path": "..\\outside.obj", "required": True}]}
    (root / "working" / "state.json").write_text(json.dumps(state), encoding="utf-8")
    report = scan_project_portability(root)
    assert report.classifications(PortabilityClassification.REGENERABLE_DERIVED)
    assert report.classifications(PortabilityClassification.UNSAFE_LINK)
    assert not report.portable


def test_project_manager_portability_entry_point_requires_open_project(tmp_path) -> None:
    manager = ProjectManager()
    with pytest.raises(ProjectError, match="no project"):
        manager.portability_report()
