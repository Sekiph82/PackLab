from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from tools.packaging.build_controlled_ocp_runtime import windows_sdk_gl_include_dir
from tools.packaging.validate_windows_native_source_lock import (
    SourceLockError,
    validate_source_lock,
    verify_conda_lock,
)

ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "tools" / "packaging" / "windows_native_source_lock.json"


@pytest.fixture
def valid_lock() -> dict[str, object]:
    return json.loads(LOCK_PATH.read_text(encoding="utf-8"))


def test_checked_in_windows_native_source_lock_is_exact() -> None:
    from tools.packaging.validate_windows_native_source_lock import load_source_lock

    lock = load_source_lock(LOCK_PATH)
    assert lock["build_environment_lock"]["platform"] == "win-64"


def test_controlled_ocp_lock_binds_exact_pywrap_submodule() -> None:
    from tools.packaging.validate_windows_native_source_lock import load_source_lock

    lock = load_source_lock(LOCK_PATH)
    pywrap = next(
        record for record in lock["records"] if record["id"] == "ocp-pywrap-source-9251940"
    )
    assert pywrap["revision"] == "92519409a57f9ec3f2c005b8057006fdb4752c23"
    assert pywrap["sha256"] == "b88b0f2b9c7d2ae72a7399efc44951659fb1a28ea607d962ba1f507ce754ba48"
    assert pywrap["id"] in lock["required_source_ids"]
    assert pywrap["id"] in lock["production_components"]["controlled-ocp-occt-runtime"]


def test_windows_sdk_gl_include_dir_requires_exact_sdk_header(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sdk_include = tmp_path / "Include" / "10.0.26100.0" / "um"
    gl_header = sdk_include / "gl" / "GL.h"
    gl_header.parent.mkdir(parents=True)
    gl_header.write_text("// test header", encoding="utf-8")
    monkeypatch.setenv("WindowsSdkDir", str(tmp_path))
    monkeypatch.setenv("WindowsSDKVersion", "10.0.26100.0\\")

    include_dir, version = windows_sdk_gl_include_dir()

    assert include_dir == sdk_include
    assert version == "10.0.26100.0"


def test_windows_sdk_gl_include_dir_fails_closed_without_gl_header(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("WindowsSdkDir", str(tmp_path))
    monkeypatch.setenv("WindowsSDKVersion", "10.0.26100.0")

    with pytest.raises(RuntimeError, match="GL.h"):
        windows_sdk_gl_include_dir()


def test_source_record_requires_sha256(valid_lock: dict[str, object]) -> None:
    data = copy.deepcopy(valid_lock)
    data["records"][0]["sha256"] = "missing"  # type: ignore[index]
    with pytest.raises(SourceLockError, match="sha256"):
        validate_source_lock(data)


def test_source_record_rejects_mutable_url(valid_lock: dict[str, object]) -> None:
    data = copy.deepcopy(valid_lock)
    data["records"][0]["url"] = "https://example.org/project/archive/refs/heads/main.tar.gz"  # type: ignore[index]
    with pytest.raises(SourceLockError, match="mutable"):
        validate_source_lock(data)


def test_source_record_rejects_non_authoritative_host(valid_lock: dict[str, object]) -> None:
    data = copy.deepcopy(valid_lock)
    data["records"][0]["url"] = "https://example.org/OCP/archive.tar.gz"  # type: ignore[index]
    with pytest.raises(SourceLockError, match="unapproved source host"):
        validate_source_lock(data)


def test_source_record_rejects_wildcard_build_selector(valid_lock: dict[str, object]) -> None:
    data = copy.deepcopy(valid_lock)
    data["records"][0]["build"] = "all*"  # type: ignore[index]
    with pytest.raises(SourceLockError, match="wildcard"):
        validate_source_lock(data)


def test_source_record_requires_retained_runtime_coverage(valid_lock: dict[str, object]) -> None:
    data = copy.deepcopy(valid_lock)
    del data["records"][0]["retained_runtime_surface"]  # type: ignore[index]
    with pytest.raises(SourceLockError, match="retained_runtime_surface"):
        validate_source_lock(data)


def test_source_lock_rejects_duplicate_ids(valid_lock: dict[str, object]) -> None:
    data = copy.deepcopy(valid_lock)
    data["records"].append(copy.deepcopy(data["records"][0]))  # type: ignore[union-attr]
    with pytest.raises(SourceLockError, match="duplicate"):
        validate_source_lock(data)


def test_source_lock_rejects_unreferenced_required_source(valid_lock: dict[str, object]) -> None:
    data = copy.deepcopy(valid_lock)
    data["required_source_ids"].append("required-but-absent")  # type: ignore[union-attr]
    with pytest.raises(SourceLockError, match="unreferenced or missing"):
        validate_source_lock(data)


def test_checked_in_conda_lock_binds_exact_package_artifacts() -> None:
    verify_conda_lock(ROOT / "tools" / "packaging" / "packlab-ocp-bindings-win.lock")


def test_conda_lock_rejects_wildcard_package_filename(tmp_path: Path) -> None:
    path = tmp_path / "conda-lock.yml"
    path.write_text(
        """version: 1
metadata:
  platforms:
  - win-64
package:
- name: sample
  version: 1.0
  manager: conda
  platform: win-64
  url: https://example.org/win-64/sample-1.0-build*.conda
  hash:
    sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
""",
        encoding="utf-8",
    )
    with pytest.raises(SourceLockError, match="exact package/build filename"):
        verify_conda_lock(path)
