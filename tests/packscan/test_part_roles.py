"""PL-0482/PL-0489: optional manifest part_role, absent = assembled."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from packlab_core.packscan import PackScanError
from packlab_core.packscan.container import _validate_manifest
from packlab_core.packscan.part_roles import (
    PART_ROLES,
    manifest_part_role,
    parts_summary,
)


def _fixture(repo_root: Path, name: str) -> dict[str, object]:
    path = repo_root / "tests" / "fixtures" / "packscan" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_enum_matches_core_roles(repo_root: Path) -> None:
    schema = json.loads(
        (repo_root / "schemas/packscan/manifest.schema.json").read_text(encoding="utf-8")
    )
    assert tuple(schema["properties"]["part_role"]["enum"]) == PART_ROLES
    assert "part_role" not in schema["required"]


@pytest.mark.parametrize("role", PART_ROLES)
def test_every_role_is_accepted(repo_root: Path, role: str) -> None:
    manifest = _fixture(repo_root, "manifest-valid.json") | {"part_role": role}
    _validate_manifest(manifest)
    assert manifest_part_role(manifest) == role


def test_role_fixture_accepted_and_absent_role_is_assembled(repo_root: Path) -> None:
    flipped = _fixture(repo_root, "manifest-valid-part-role-body-flipped.json")
    _validate_manifest(flipped)
    assert manifest_part_role(flipped) == "body_flipped"
    legacy = _fixture(repo_root, "manifest-valid.json")
    _validate_manifest(legacy)
    assert manifest_part_role(legacy) == "assembled"


@pytest.mark.parametrize("value", ["lid", "Body", "", None, 3])
def test_invalid_role_is_rejected(repo_root: Path, value: object) -> None:
    manifest = _fixture(repo_root, "manifest-valid.json") | {"part_role": value}
    with pytest.raises(PackScanError) as error:
        _validate_manifest(manifest)
    assert error.value.code == "schema_invalid"
    with pytest.raises(ValueError):
        manifest_part_role(manifest)


def test_invalid_role_fixture_is_rejected(repo_root: Path) -> None:
    with pytest.raises(PackScanError):
        _validate_manifest(_fixture(repo_root, "manifest-invalid-part-role.json"))


def test_parts_summary_reports_missing_views() -> None:
    summary = parts_summary(["body", "body_interior", "closure_flipped", "assembled"])
    assert summary == {
        "closure": {"upright": False, "flipped": True},
        "body": {"upright": True, "flipped": False, "interior": True},
        "assembled": {"upright": True, "flipped": False},
    }
    complete = parts_summary(PART_ROLES)
    assert all(all(views.values()) for views in complete.values())
