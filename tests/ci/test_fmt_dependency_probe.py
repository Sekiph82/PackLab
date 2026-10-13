from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from tools.packaging import probe_fmt_dependency as probe

ROOT = Path(__file__).resolve().parents[2]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fake_prefix(
    tmp_path: Path, *, source_record: bool = True
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    prefix = tmp_path / "env"
    dll = prefix / "Library" / "bin" / "fmt.dll"
    dll.parent.mkdir(parents=True)
    dll.write_bytes(b"controlled-fmt-dll-fixture")
    package_sha = "a" * 64
    record = {
        "name": "fmt",
        "version": "12.1.0",
        "build": "h1ced75a_1",
        "url": "https://conda.anaconda.org/conda-forge/win-64/fmt-12.1.0-h1ced75a_1.conda",
        "sha256": package_sha,
        "files": ["Library/bin/fmt.dll"],
        "paths_data": {"paths": [{"_path": "Library/bin/fmt.dll", "sha256": _sha(dll)}]},
    }
    meta = prefix / "conda-meta" / "fmt-12.1.0-h1ced75a_1.json"
    meta.parent.mkdir()
    meta.write_text(json.dumps(record), encoding="utf-8")
    lock = {
        "fmt": {
            "name": "fmt",
            "version": "12.1.0",
            "build": "h1ced75a_1",
            "url": record["url"],
            "hash": {"sha256": package_sha},
        }
    }
    sources = (
        {
            "fmt-source-12.1.0": {
                "id": "fmt-source-12.1.0",
                "binary_package": {"name": "fmt", "sha256": package_sha},
            }
        }
        if source_record
        else {}
    )
    return prefix, lock, sources


def test_fmt_probe_accepts_hash_bound_locked_native_owner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prefix, lock, sources = _fake_prefix(tmp_path)
    dll = prefix / "Library" / "bin" / "fmt.dll"
    monkeypatch.setattr(probe, "_import_names", lambda _path: [])

    closure = probe.inspect_import_closure(dll, prefix, lock, sources)

    assert closure == [
        {
            "name": "fmt.dll",
            "path": "library/bin/fmt.dll",
            "package": {
                "name": "fmt",
                "version": "12.1.0",
                "build": "h1ced75a_1",
                "url": lock["fmt"]["url"],
                "sha256": "a" * 64,
            },
            "source_record_id": "fmt-source-12.1.0",
            "owner": "fmt package",
            "sha256": _sha(dll),
            "status": "PASS",
        }
    ]


def test_fmt_probe_blocks_native_package_without_source_license_owner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prefix, lock, _ = _fake_prefix(tmp_path, source_record=False)
    dll = prefix / "Library" / "bin" / "fmt.dll"
    monkeypatch.setattr(probe, "_import_names", lambda _path: [])

    closure = probe.inspect_import_closure(dll, prefix, lock, {})

    assert closure[0]["status"] == "BLOCKED"
    assert closure[0]["owner"] == "SOURCE_OR_LICENSE_UNRESOLVED"


def test_fmt_probe_blocks_unknown_transitive_import(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prefix, lock, sources = _fake_prefix(tmp_path)
    dll = prefix / "Library" / "bin" / "fmt.dll"
    monkeypatch.setattr(probe, "_import_names", lambda _path: ["unknown-native.dll"])

    closure = probe.inspect_import_closure(dll, prefix, lock, sources)

    assert closure[0]["owner"] == "fmt package"
    assert closure[1:] == [
        {
            "name": "unknown-native.dll",
            "parent": "fmt.dll",
            "owner": "UNKNOWN",
            "status": "BLOCKED",
        }
    ]


def test_fmt_probe_does_not_treat_prefix_copy_as_windows_system_dll(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prefix, lock, sources = _fake_prefix(tmp_path)
    system_root = tmp_path / "Windows"
    system_dll = system_root / "System32" / "kernel32.dll"
    system_dll.parent.mkdir(parents=True)
    system_dll.write_bytes(b"system-fixture")
    fake_prefix_copy = prefix / "Library" / "bin" / "kernel32.dll"
    fake_prefix_copy.write_bytes(b"untrusted-shadow")
    monkeypatch.setenv("SystemRoot", str(system_root))
    monkeypatch.setattr(
        probe,
        "_import_names",
        lambda path: ["kernel32.dll"] if path.name == "fmt.dll" else [],
    )

    closure = probe.inspect_import_closure(prefix / "Library/bin/fmt.dll", prefix, lock, sources)

    assert closure[1]["owner"] == "UNKNOWN_PACKAGE"
    assert closure[1]["path"] == "library/bin/kernel32.dll"
    assert closure[1]["status"] == "BLOCKED"


def test_fmt_probe_accepts_system_dll_only_when_resolved_under_system_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prefix, lock, sources = _fake_prefix(tmp_path)
    system_root = tmp_path / "Windows"
    system_dll = system_root / "System32" / "kernel32.dll"
    system_dll.parent.mkdir(parents=True)
    system_dll.write_bytes(b"system-fixture")
    monkeypatch.setenv("SystemRoot", str(system_root))
    monkeypatch.setattr(
        probe,
        "_import_names",
        lambda path: ["kernel32.dll"] if path.name == "fmt.dll" else [],
    )

    closure = probe.inspect_import_closure(prefix / "Library/bin/fmt.dll", prefix, lock, sources)

    assert closure[1]["owner"] == "Windows system"
    assert closure[1]["path"] == "System32/kernel32.dll"
    assert closure[1]["status"] == "PASS"


def test_fmt_probe_rejects_installed_binary_hash_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prefix, lock, sources = _fake_prefix(tmp_path)
    dll = prefix / "Library" / "bin" / "fmt.dll"
    data = json.loads((prefix / "conda-meta/fmt-12.1.0-h1ced75a_1.json").read_text())
    data["paths_data"]["paths"][0]["sha256"] = "0" * 64
    (prefix / "conda-meta/fmt-12.1.0-h1ced75a_1.json").write_text(json.dumps(data))
    monkeypatch.setattr(probe, "_import_names", lambda _path: [])

    with pytest.raises(ValueError, match="file manifest"):
        probe.inspect_import_closure(dll, prefix, lock, sources)


def test_fmt_probe_rejects_changed_package_lock() -> None:
    contract = json.loads(probe.CONTRACT.read_text(encoding="utf-8"))
    contract["package"]["sha256"] = "0" * 64

    with pytest.raises(ValueError, match="exact Windows conda lock"):
        probe.verify_pinned_identity(contract, probe.CONDA_LOCK)


def test_hosted_fmt_probe_is_manual_only_and_never_compiles_occt_or_ocp() -> None:
    workflow = (ROOT / ".github/workflows/pl0350-fmt-dependency-probe.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_dispatch:" in workflow
    assert "push:" not in workflow
    assert "pull_request:" not in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "inputs.confirm_noncompiling_probe == 'YES'" in workflow
    assert "cmake --build" not in workflow
    assert "build_controlled_occt_sdk" not in workflow
    assert "build_controlled_ocp_from_generated_sources" not in workflow
    assert "probe_fmt_dependency" in workflow
    assert "Fail closed when any native owner is unresolved" in workflow
