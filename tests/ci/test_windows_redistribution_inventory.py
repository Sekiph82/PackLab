from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.packaging import windows_redistribution_inventory as inventory
from tools.packaging.validate_controlled_ocp_manifest import validate_staged_tree


def test_safe_posix_path_rejects_absolute_and_parent_paths() -> None:
    assert (
        inventory.safe_posix_path("_internal/PySide6/QtCore.dll") == "_internal/PySide6/QtCore.dll"
    )
    assert inventory.safe_posix_path("../private/file.dll") is None
    assert inventory.safe_posix_path(r"C:\private\file.dll") is None


def test_corresponding_source_delivery_fails_closed_when_missing(tmp_path: Path) -> None:
    stage = tmp_path / "PackLabStudio"
    stage.mkdir()
    by_path, delivered, valid = inventory._validate_source_delivery(
        stage, Path(__file__).resolve().parents[2], "a" * 40, "1.2.3"
    )
    assert by_path == {}
    assert delivered == set()
    assert not valid


def test_corresponding_source_manifest_metadata_is_pinned() -> None:
    pinned = {
        "component": "Open3D",
        "version": "0.20.0",
        "revision": "d32b4fce639b3cde284184072796480ef9b528d1",
        "url": "https://github.com/isl-org/Open3D/archive/d32b4fce639b3cde284184072796480ef9b528d1.tar.gz",
        "sha256": "a" * 64,
        "license_identifier": "MIT",
        "source_availability_role": "CORRESPONDING_SOURCE_AND_THIRD_PARTY_INVENTORY",
    }
    row = {
        **pinned,
        "id": "open3d-attested-source-d32b4fce",
        "source_filename": "d32b4fce639b3cde284184072796480ef9b528d1.tar.gz",
    }

    assert inventory._source_record_matches(pinned, row)
    assert not inventory._source_record_matches(pinned, {**row, "version": "0.20.1"})
    assert not inventory._source_record_matches(pinned, {**row, "license_identifier": "Other"})


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
    rows = [("qtcore.DLL", str(tmp_path / "QtCore.dll"), "BINARY")]
    assert inventory.toc_destinations(rows, "_internal", stage) == {
        "_internal/qtcore.dll": (str(tmp_path / "QtCore.dll"), "BINARY")
    }
    with pytest.raises(ValueError, match="unsafe destination"):
        inventory.toc_destinations([("../escape.dll", "x", "BINARY")], "_internal", stage)


def test_toc_rejects_case_insensitive_duplicate_stage_destinations(tmp_path: Path) -> None:
    stage = tmp_path / "PackLabStudio"
    (stage / "_internal").mkdir(parents=True)
    (stage / "_internal" / "QtCore.dll").write_bytes(b"qt")

    with pytest.raises(ValueError, match="duplicate staged destinations"):
        inventory.toc_destinations(
            [
                ("_internal/QtCore.dll", "source-a", "BINARY"),
                ("_internal/qtcore.DLL", "source-b", "BINARY"),
            ],
            "_internal",
            stage,
        )


def test_inventory_reuses_case_insensitive_controlled_ocp_stage_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    stage = project / "build" / "PackLabStudio"
    staged = stage / "_internal" / "OCP" / "TKBin.dll"
    staged.parent.mkdir(parents=True)
    staged.write_bytes(b"controlled native binary")
    revision = "a" * 40
    version = "7.9.3"
    license_id = "LGPL-2.1-only WITH OCCT-exception"
    notice_source = "tools/packaging/windows_licenses/OCCT-7.9.3/LGPL-2.1.txt"
    source_record = {
        "id": "occt-source-7.9.3",
        "version": version,
        "revision": revision,
        "license_identifier": license_id,
        "license_notice_source": notice_source,
    }
    source_lock = project / "tools" / "packaging" / "windows_native_source_lock.json"
    source_lock.parent.mkdir(parents=True)
    source_lock.write_text(json.dumps({"records": [source_record]}), encoding="utf-8")
    manifest = {
        "files": [
            {
                "relative_path": "OCP/tkbin.dll",
                "sha256": inventory.sha256_file(staged),
                "source_package_id": source_record["id"],
                "version": version,
                "build_revision": revision,
                "license_identifier": license_id,
                "license_notice_source": notice_source,
            }
        ]
    }
    monkeypatch.setattr(inventory, "load_and_validate_manifest", lambda *_args: manifest)
    monkeypatch.setattr(inventory, "validate_staged_tree", lambda *_args: None)
    toc = tmp_path / "COLLECT-00.toc"
    source = tmp_path / "tkbin.dll"
    source.write_bytes(staged.read_bytes())
    toc.write_text(repr([("_internal/OCP/TKBin.dll", str(source), "BINARY")]), encoding="utf-8")
    analysis = tmp_path / "Analysis-00.toc"
    analysis.write_text("()", encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text('{"schema_version":1}', encoding="utf-8")
    monkeypatch.setattr(inventory, "analysis_source_paths", lambda _path: [])
    monkeypatch.setattr(inventory.importlib.metadata, "distributions", lambda: [])

    files, _summary, _evidence = inventory.build_inventory(
        stage,
        toc,
        analysis,
        "_internal",
        project,
        revision,
        "1.2.3",
        registry,
        tmp_path / "evidence",
        tmp_path / "controlled-manifest.json",
    )

    row = next(record for record in files["files"] if record["relative_path"].endswith("TKBin.dll"))
    assert row["component_ids"] == ["occt-7.9.3"]
    assert row["mapping_method"] == "controlled_ocp_manifest_and_exact_staged_sha256"
    assert not any(item.startswith("toc:") for item in _evidence[0]["unresolved_items"])


def test_case_insensitive_controlled_ocp_validator_is_used_for_manifest_parity(
    tmp_path: Path,
) -> None:
    stage = tmp_path / "PackLabStudio"
    staged = stage / "_internal" / "OCP" / "TKBin.dll"
    staged.parent.mkdir(parents=True)
    staged.write_bytes(b"controlled native binary")
    manifest = {
        "files": [
            {
                "relative_path": "OCP/tkbin.dll",
                "sha256": inventory.sha256_file(staged),
            }
        ]
    }

    validate_staged_tree(stage, manifest)


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


def test_locked_openssl_runtime_has_explicit_third_party_provenance(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    registry = json.loads(
        (project_root / "tools/packaging/windows_component_license_registry.json").read_text(
            encoding="utf-8"
        )
    )
    record = registry["supplemental_evidence"]["openssl-runtime-3.0.16"]
    license_bytes = (project_root / record["license_file"]).read_bytes()
    local_license = tmp_path / "OpenSSL-LICENSE.txt"
    local_license.write_bytes(license_bytes)
    record["license_file"] = str(local_license)

    components, notices, unresolved = inventory.license_rows(
        {"openssl-runtime-3.0.16"}, {}, registry, tmp_path / "evidence"
    )

    assert components[0]["license_status"] == "EVIDENCE_PRESENT"
    assert components[0]["provenance_class"] == "APP_SHIPPED_THIRD_PARTY"
    assert components[0]["source_evidence_required"] is True
    assert components[0]["source_evidence"]["sha256"] == (
        "57e03c50feab5d31b152af2b764f10379aecd8ee92f16c985983ce4a99f7ef86"
    )
    assert notices[0]["sha256"] == record["license_sha256"]
    assert not unresolved


def test_packlab_application_notice_is_generated_for_project_owned_files(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    registry = json.loads(
        (project_root / "tools/packaging/windows_component_license_registry.json").read_text(
            encoding="utf-8"
        )
    )
    record = registry["supplemental_evidence"]["packlab-application"]
    license_path = project_root / record["license_file"]
    assert inventory.sha256_file(license_path) == record["license_sha256"]

    components, notices, unresolved = inventory.license_rows(
        {"packlab-application"}, {}, registry, tmp_path / "evidence"
    )

    assert not unresolved
    assert components[0]["license_identifier"] == "LicenseRef-PackLab-Proprietary-Internal-Use"
    assert components[0]["provenance_class"] == "PACKLAB_OWNED"
    assert components[0]["source_evidence_required"] is False
    assert len(notices) == 1
    copied_notice = tmp_path / "evidence" / notices[0]["path"]
    assert copied_notice.read_bytes() == license_path.read_bytes()


def test_open3d_native_third_party_license_corpus_is_hashed_and_fail_closed(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    registry = json.loads(
        (project_root / "tools/packaging/windows_component_license_registry.json").read_text(
            encoding="utf-8"
        )
    )
    record = registry["supplemental_evidence"]["open3d"]
    mit_license = tmp_path / "open3d-wheel-LICENSE.txt"
    mit_license.write_text("MIT license from the exact wheel\n", encoding="utf-8")

    class Distribution:
        version = "0.20.0"
        metadata = {"Name": "open3d", "License": "MIT"}
        files = [Path("open3d-0.20.0.dist-info/licenses/LICENSE.txt")]

        @staticmethod
        def locate_file(_path: Path) -> Path:
            return mit_license

    components, notices, unresolved = inventory.license_rows(
        {"open3d"}, {"open3d": Distribution()}, registry, tmp_path / "evidence"
    )

    assert "component:open3d" in unresolved
    assert components[0]["license_status"] == "UNRESOLVED"
    assert components[0]["source_evidence_required"] is True
    additional_notice = next(
        row for row in notices if row["sha256"] == record["additional_license_files"][0]["sha256"]
    )
    copied_notice = tmp_path / "evidence" / additional_notice["path"]
    source_notice = project_root / record["additional_license_files"][0]["path"]
    assert copied_notice.read_bytes() == source_notice.read_bytes()


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
