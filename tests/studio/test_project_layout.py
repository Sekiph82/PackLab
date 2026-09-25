from __future__ import annotations

import json

import pytest

from packlab_studio.project_layout import ProjectLayout, ProjectLayoutError, safe_relative_path


def test_create_validate_and_reuse_layout(tmp_path) -> None:
    root = tmp_path / "project"
    layout = ProjectLayout.create(root)
    assert ProjectLayout.open(root) == layout
    assert layout.path("working", "state.json") == root / "working" / "state.json"
    with pytest.raises(ProjectLayoutError):
        ProjectLayout.create(root)


def test_traversal_absolute_and_unknown_area_are_rejected(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    for value in ("..\\secret", "C:\\secret", "\\\\server\\secret"):
        with pytest.raises(ProjectLayoutError):
            safe_relative_path(value)
    with pytest.raises(ProjectLayoutError):
        layout.path("working", "..\\raw\\secret")
    with pytest.raises(ProjectLayoutError):
        layout.path("unknown")


def test_corrupt_or_incompatible_marker_is_rejected(tmp_path) -> None:
    root = tmp_path / "project"
    layout = ProjectLayout.create(root)
    layout.marker_path.write_text(json.dumps({"schema_version": "99"}), encoding="utf-8")
    with pytest.raises(ProjectLayoutError):
        ProjectLayout.open(root)

