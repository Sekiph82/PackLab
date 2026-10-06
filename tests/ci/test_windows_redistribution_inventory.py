from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.packaging import windows_redistribution_inventory as inventory


def test_safe_posix_path_rejects_absolute_and_parent_paths() -> None:
    assert (
        inventory.safe_posix_path("_internal/PySide6/QtCore.dll") == "_internal/PySide6/QtCore.dll"
    )
    assert inventory.safe_posix_path("../private/file.dll") is None
    assert inventory.safe_posix_path(r"C:\private\file.dll") is None


def test_hooks_contrib_runtime_hook_classification_is_path_and_name_bounded() -> None:
    assert inventory.is_pyinstaller_hooks_contrib_runtime_hook(
        Path("_pyinstaller_hooks_contrib/rthooks/pyi_rth_cryptography_openssl.py")
    )
    assert not inventory.is_pyinstaller_hooks_contrib_runtime_hook(
        Path("_pyinstaller_hooks_contrib/hooks/hook-cryptography.py")
    )
    assert not inventory.is_pyinstaller_hooks_contrib_runtime_hook(
        Path("_pyinstaller_hooks_contrib/rthooks/pyi_rth_unknown.txt")
    )


def test_toc_maps_exact_stage_layout_and_rejects_traversal(tmp_path: Path) -> None:
    stage = tmp_path / "PackLabStudio"
    (stage / "_internal").mkdir(parents=True)
    (stage / "_internal" / "QtCore.dll").write_bytes(b"qt")
    rows = [("QtCore.dll", str(tmp_path / "QtCore.dll"), "BINARY")]
    assert inventory.toc_destinations(rows, "_internal", stage) == {
        "_internal/QtCore.dll": (str(tmp_path / "QtCore.dll"), "BINARY")
    }
    with pytest.raises(ValueError, match="unsafe destination"):
        inventory.toc_destinations([("../escape.dll", "x", "BINARY")], "_internal", stage)


def test_extensionless_declared_license_file_is_collected(tmp_path: Path) -> None:
    license_path = tmp_path / "LICENSE"
    license_path.write_text("MIT License\n", encoding="utf-8")

    class Distribution:
        files = [Path("example-1.dist-info/licenses/LICENSE")]

        @staticmethod
        def locate_file(_path: Path) -> Path:
            return license_path

    assert inventory.distribution_license_files(Distribution()) == [
        ("example-1.dist-info/licenses/LICENSE", license_path)
    ]


def test_inventory_records_path_free_per_file_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "repo"
    stage = project / "build" / "windows-studio" / "PackLabStudio"
    evidence = tmp_path / "evidence"
    project.mkdir()
    stage.mkdir(parents=True)
    source = project / "PackLabStudio.exe"
    source.write_bytes(b"packlab executable")
    (stage / "PackLabStudio.exe").write_bytes(source.read_bytes())
    provenance = {
        "schema_version": 1,
        "PACKLAB_BUILD_REVISION": "a" * 40,
        "studio_version": "1.2.3",
    }
    provenance_source = project / "packlab-build-provenance.json"
    provenance_bytes = json.dumps(provenance).encode()
    provenance_source.write_bytes(provenance_bytes)
    (stage / "packlab-build-provenance.json").write_bytes(provenance_bytes)
    toc = tmp_path / "COLLECT-00.toc"
    toc.write_text(
        repr(
            [
                ("PackLabStudio.exe", str(source), "EXECUTABLE"),
                ("packlab-build-provenance.json", str(provenance_source), "DATA"),
            ]
        ),
        encoding="utf-8",
    )
    analysis = tmp_path / "Analysis-00.toc"
    analysis.write_text("()", encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text('{"schema_version":1}', encoding="utf-8")
    monkeypatch.setattr(inventory, "analysis_source_paths", lambda _path: [])
    monkeypatch.setattr(inventory.importlib.metadata, "distributions", lambda: [])

    files, components, output = inventory.build_inventory(
        stage,
        toc,
        analysis,
        "_internal",
        project,
        "a" * 40,
        "1.2.3",
        registry,
        evidence,
    )
    validation = output[0]
    executable = next(row for row in files["files"] if row["relative_path"] == "PackLabStudio.exe")
    assert executable["sha256"] == inventory.sha256_file(stage / "PackLabStudio.exe")
    assert executable["byte_length"] == len(b"packlab executable")
    assert executable["component_ids"]
    assert executable["mapping_method"] == "pyinstaller_analysis_and_collect_toc_composite"
    assert validation["unresolved_count"] > 0
    serialized = json.dumps([files, components, output])
    assert str(tmp_path).replace("\\", "\\\\") not in serialized
    assert str(tmp_path) not in serialized


def test_license_digest_mismatch_remains_unresolved(tmp_path: Path) -> None:
    source = tmp_path / "LICENSE.txt"
    source.write_text("license evidence", encoding="utf-8")
    registry = {
        "supplemental_evidence": {
            "example": {
                "license_identifier": "MIT",
                "license_file": str(source),
                "license_sha256": "0" * 64,
                "upstream_reference": "https://example.invalid/repo/commit",
            }
        }
    }
    components, _notices, unresolved = inventory.license_rows(
        {"example"}, {}, registry, tmp_path / "out"
    )
    assert components[0]["license_status"] == "UNRESOLVED"
    assert "component:example" in unresolved


def test_metadata_only_supplement_uses_exact_distribution_license_file(
    tmp_path: Path,
) -> None:
    license_path = tmp_path / "LICENSE.txt"
    license_path.write_text("BSD license evidence\n", encoding="utf-8")

    class Distribution:
        version = "1.2.3"
        metadata = {"Name": "Example", "License": ""}
        files = [Path("example-1.2.3.dist-info/licenses/LICENSE.txt")]

        @staticmethod
        def locate_file(_path: Path) -> Path:
            return license_path

    registry = {
        "supplemental_evidence": {
            "example": {
                "license_identifier": "BSD-3-Clause",
                "license_mapping_evidence": "exact_locked_distribution_and_staged_license_file",
                "upstream_reference": "https://example.invalid/example/1.2.3",
                "reason": "Exact release license text is packaged; metadata lacks SPDX.",
            }
        }
    }
    components, notices, unresolved = inventory.license_rows(
        {"example"}, {"example": Distribution()}, registry, tmp_path / "evidence"
    )

    assert unresolved == set()
    assert components[0]["license_identifier"] == "BSD-3-Clause"
    assert components[0]["license_mapping_evidence"] == (
        "exact_locked_distribution_and_staged_license_file"
    )
    assert len(notices) == 1
    assert (tmp_path / "evidence" / notices[0]["path"]).read_text(encoding="utf-8") == (
        "BSD license evidence\n"
    )


def test_generated_runtime_json_must_match_build_revision_and_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "repo"
    stage = project / "build" / "PackLabStudio"
    evidence = tmp_path / "evidence"
    stage.mkdir(parents=True)
    revision = "b" * 40
    version = "1.2.3"
    provenance = {
        "schema_version": 1,
        "PACKLAB_BUILD_REVISION": revision,
        "studio_version": version,
    }
    (stage / "packlab-build-provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
    for name in ("qt-staged-surface.json", "windows-runtime-capabilities.json"):
        (stage / name).write_text(
            json.dumps(
                {
                    "PACKLAB_BUILD_REVISION": revision,
                    "studio_version": version,
                    "status": "PASS",
                }
            ),
            encoding="utf-8",
        )
    toc = tmp_path / "COLLECT-00.toc"
    toc.write_text(repr([("packlab-build-provenance.json", "source", "DATA")]), encoding="utf-8")
    analysis = tmp_path / "Analysis-00.toc"
    analysis.write_text("()", encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text('{"schema_version":1}', encoding="utf-8")
    monkeypatch.setattr(inventory, "analysis_source_paths", lambda _path: [])
    monkeypatch.setattr(inventory.importlib.metadata, "distributions", lambda: [])

    files, _components, output = inventory.build_inventory(
        stage,
        toc,
        analysis,
        "_internal",
        project,
        revision,
        version,
        registry,
        evidence,
    )

    generated = [
        row
        for row in files["files"]
        if row["relative_path"] in {"qt-staged-surface.json", "windows-runtime-capabilities.json"}
    ]
    assert len(generated) == 2
    assert all(row["component_ids"] == ["packlab-generated-runtime-evidence"] for row in generated)
    assert all(row["license_status"] == "EVIDENCE_PRESENT" for row in generated)
    assert output[0]["unresolved_count"] == 0
