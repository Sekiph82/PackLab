from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest
from tools.packaging.controlled_ocp_runtime_bundle import (
    MANIFEST_NAME,
    METADATA_NAME,
    SOURCE_EVIDENCE_NAME,
    install_bundle,
    seal_bundle,
    validate_bundle,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LOCK = ROOT / "tools/packaging/windows_native_source_lock.json"
CONDA_LOCK = ROOT / "tools/packaging/packlab-ocp-bindings-win.lock"
BUILD_CONTRACT = ROOT / "tools/packaging/controlled_ocp_runtime_contract.json"


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@pytest.fixture
def sealed_bundle(tmp_path: Path) -> tuple[Path, str, Path]:
    lock = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    records = {row["id"]: row for row in lock["records"]}
    package = tmp_path / "build-env" / "OCP"
    package.mkdir(parents=True)
    files = {
        "OCP.cp312-win_amd64.pyd": b"controlled binding fixture",
        "TKBRep.dll": b"controlled OCCT fixture",
        "BRepPrimAPI.py": b"# controlled python wrapper fixture\n",
    }
    for name, content in files.items():
        (package / name).write_bytes(content)

    manifest_files = []
    for name in ("OCP.cp312-win_amd64.pyd", "TKBRep.dll"):
        source_id = "ocp-source-7.9.3.1.1" if name.endswith(".pyd") else "occt-source-7.9.3"
        record = records[source_id]
        manifest_files.append(
            {
                "relative_path": f"OCP/{name}",
                "sha256": digest(files[name]),
                "owning_component": record["component"],
                "source_package_id": source_id,
                "version": record["version"],
                "build_revision": record["revision"],
                "license_identifier": record["license_identifier"],
                "license_notice_source": record["license_notice_source"],
                "production_purpose": "controlled-runtime bundle test",
            }
        )
    revisions = {
        "ocp_source_revision": records["ocp-source-7.9.3.1.1"]["revision"],
        "ocp_pywrap_source_revision": records["ocp-pywrap-source-9251940"]["revision"],
        "occt_source_revision": records["occt-source-7.9.3"]["revision"],
    }
    manifest = {
        "schema_version": 1,
        "status": "PASS",
        "input_lock_sha256": digest(SOURCE_LOCK.read_bytes()),
        **revisions,
        "toolchain": {
            "python": "3.12.15",
            "cmake": "cmake version 3.31.8",
            "compiler": "MSVC 19.44.35229.0",
            "windows_sdk": "10.0.26100.0",
            "ocp_bindgen_workers": 4,
            "cmake_parallel": 4,
            "cmake_generator": "Visual Studio 17 2022",
        },
        "build_timings": [
            {
                "phase": phase,
                "started_utc": "2026-10-09T00:00:00+00:00",
                "ended_utc": "2026-10-09T00:00:01+00:00",
                "duration_seconds": 1.0,
                "worker_count": 4,
            }
            for phase in (
                "occt_native_build",
                "pywrap_generation",
                "ocp_native_compile_link",
            )
        ],
        "files": manifest_files,
    }
    manifest_path = tmp_path / "controlled-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    source_records = []
    for record in lock["records"]:
        if record["source_availability_role"] == "PROJECT_OFFICIAL_BINARY":
            continue
        filename = Path(urlparse(record["url"]).path).name
        source_records.append(
            {
                "record_id": record["id"],
                "filename": filename,
                "expected_sha256": record["sha256"],
                "observed_sha256": record["sha256"],
                "byte_length": 1,
                "status": "PASS",
            }
        )
    source_evidence_path = tmp_path / "source-evidence.json"
    source_evidence_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_lock_sha256": digest(SOURCE_LOCK.read_bytes()),
                "status": "PASS",
                "verified_source_count": len(source_records),
                "records": source_records,
            }
        ),
        encoding="utf-8",
    )

    cache_key = "controlled-ocp-windows-x64-py3.12-v1-test"
    bundle = tmp_path / "controlled-ocp-runtime"
    metadata = seal_bundle(
        SimpleNamespace(
            build_contract=BUILD_CONTRACT,
            bundle=bundle,
            cache_key=cache_key,
            conda_lock=CONDA_LOCK,
            manifest=manifest_path,
            site_packages=package.parent,
            source_evidence=source_evidence_path,
            source_lock=SOURCE_LOCK,
        )
    )
    assert metadata["runtime_file_count"] == 3
    assert {MANIFEST_NAME, METADATA_NAME, SOURCE_EVIDENCE_NAME} <= {
        path.name for path in bundle.iterdir()
    }
    return bundle, cache_key, tmp_path


def test_controlled_runtime_bundle_validates_every_runtime_file(sealed_bundle) -> None:
    bundle, cache_key, _ = sealed_bundle

    metadata = validate_bundle(bundle, SOURCE_LOCK, CONDA_LOCK, BUILD_CONTRACT, cache_key)

    assert metadata["runtime_file_count"] == 3
    assert metadata["ocp_bindgen_workers"] == 4
    assert metadata["source_revisions"]["ocp"] == "d69b064a3a604ebf245b1f3b14fb54c835a3a571"


def test_controlled_runtime_bundle_rejects_different_cache_key(sealed_bundle) -> None:
    bundle, _, _ = sealed_bundle

    with pytest.raises(ValueError, match="metadata does not match"):
        validate_bundle(bundle, SOURCE_LOCK, CONDA_LOCK, BUILD_CONTRACT, "different-cache-key")


def test_controlled_runtime_bundle_rejects_mutated_runtime_bytes(sealed_bundle) -> None:
    bundle, cache_key, _ = sealed_bundle
    (bundle / "OCP" / "TKBRep.dll").write_bytes(b"changed")

    with pytest.raises(ValueError, match="file hash, size, or inventory"):
        validate_bundle(bundle, SOURCE_LOCK, CONDA_LOCK, BUILD_CONTRACT, cache_key)


def test_controlled_runtime_bundle_rejects_unexpected_file(sealed_bundle) -> None:
    bundle, cache_key, _ = sealed_bundle
    (bundle / "OCP" / "unexpected.dll").write_bytes(b"unowned")

    with pytest.raises(ValueError, match="file hash, size, or inventory"):
        validate_bundle(bundle, SOURCE_LOCK, CONDA_LOCK, BUILD_CONTRACT, cache_key)


def test_controlled_runtime_bundle_rejects_metadata_lock_mismatch(sealed_bundle) -> None:
    bundle, cache_key, _ = sealed_bundle
    metadata_path = bundle / METADATA_NAME
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["source_lock_sha256"] = "0" * 64
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="metadata mismatch: source_lock_sha256"):
        validate_bundle(bundle, SOURCE_LOCK, CONDA_LOCK, BUILD_CONTRACT, cache_key)


def test_controlled_runtime_install_removes_opaque_wheel_runtime(sealed_bundle) -> None:
    bundle, cache_key, tmp_path = sealed_bundle
    target_site = tmp_path / "target-site-packages"
    target_site.mkdir()
    (target_site / "cadquery_ocp_novtk.libs").mkdir()
    (target_site / "cadquery_ocp_novtk").mkdir()
    (target_site / "OCP").mkdir()

    install_bundle(
        SimpleNamespace(
            bundle=bundle,
            build_contract=BUILD_CONTRACT,
            cache_key=cache_key,
            conda_lock=CONDA_LOCK,
            site_packages=target_site,
            source_lock=SOURCE_LOCK,
        )
    )

    assert not (target_site / "cadquery_ocp_novtk.libs").exists()
    assert not (target_site / "cadquery_ocp_novtk").exists()
    assert (target_site / "OCP" / "OCP.cp312-win_amd64.pyd").is_file()
