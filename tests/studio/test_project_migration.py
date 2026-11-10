"""PL-0384: projects written before the authority file migrate deterministically."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import packlab_studio.project as project_module
from packlab_studio.project import AUTHORITY_SCHEMA_VERSION, ProjectError, ProjectManager

FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "studio" / "legacy_pre_authority_project_v1"
)
LEGACY_ID = "71254b4a-5917-453f-a2c1-b09e0e2f7fbc"


def _legacy_copy(tmp_path: Path) -> Path:
    root = tmp_path / "legacy-project"
    shutil.copytree(FIXTURE, root, ignore=shutil.ignore_patterns("README.md"))
    layout = json.loads((root / ".packlab-layout.json").read_text(encoding="utf-8"))
    for name in layout["directories"]:
        (root / name).mkdir(exist_ok=True)
    return root


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes() for p in sorted((root / "working").iterdir())
    }


def test_legacy_project_opens_read_only_without_rewriting_source(tmp_path: Path) -> None:
    root = _legacy_copy(tmp_path)
    before = _snapshot(root)
    manager = ProjectManager()
    metadata = manager.open_project(root)
    assert (metadata.project_id, metadata.revision, metadata.schema_version) == (
        LEGACY_ID,
        1,
        "1.0",
    )
    manager.close()
    assert _snapshot(root) == before
    assert not (root / "working" / "authority.json").exists()


def test_first_edit_migrates_to_authority_layout_deterministically(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(project_module, "_now", lambda: "2026-11-10T17:00:00Z")
    results = []
    for run in ("a", "b"):
        root = _legacy_copy(tmp_path / run)
        manager = ProjectManager()
        manager.open_project(root)
        state = {"notes": "edited by pre-authority app", "units": "mm", "migrated": True}
        manager.commit_edit(state, expected_revision=1)
        manager.close()
        authority = json.loads((root / "working" / "authority.json").read_text(encoding="utf-8"))
        assert authority["schema_version"] == AUTHORITY_SCHEMA_VERSION
        assert authority["metadata"]["project_id"] == LEGACY_ID
        assert authority["metadata"]["created_at"] == "2026-11-10T16:28:24Z"
        assert authority["metadata"]["revision"] == 2 and authority["state"] == state
        reopened = ProjectManager()
        assert reopened.open_project(root).revision == 2
        reopened.close()
        results.append(_snapshot(root))
    assert results[0] == results[1]


@pytest.mark.parametrize(
    ("target", "content"),
    [
        ("working/project.json", None),  # future project schema
        ("working/project.json", b'{"schema_version":'),
        ("working/state.json", b"[1, 2]"),
        ("working/authority.json", b'{"schema_version": 99, "metadata": {}, "state": {}}'),
    ],
)
def test_future_or_malformed_legacy_inputs_fail_closed_without_overwrite(
    tmp_path: Path, target: str, content: bytes | None
) -> None:
    root = _legacy_copy(tmp_path)
    path = root / target
    if content is None:
        value = json.loads(path.read_text(encoding="utf-8"))
        value["schema_version"] = "2.0"
        content = json.dumps(value).encode("utf-8")
    path.write_bytes(content)
    before = _snapshot(root)
    with pytest.raises(ProjectError):
        ProjectManager().open_project(root)
    assert _snapshot(root) == before
