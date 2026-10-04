from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

import pytest

from packlab_core.trigger_pump_library import (
    TriggerPumpLibraryError,
    import_local_trigger_pump_component,
)


def _fixture(root: Path) -> tuple[Path, dict[str, object]]:
    root.mkdir(parents=True, exist_ok=True)
    geometry = {
        "contract": "packlab.trigger-pump-geometry-reference.v1",
        "authority_class": "LIBRARY_DESIGN_COMPONENT",
        "component_id": "synthetic-trigger-pump",
        "coordinate_unit": "mm_unverified",
        "parameters": {"overall_length": 72.0, "body_width": 24.0, "body_depth": 19.0},
        "attachment_reference": {
            "role": "closure_actuator_interface",
            "semantic_key": "actuator-mount-v1",
        },
    }
    geometry_bytes = json.dumps(geometry, sort_keys=True, separators=(",", ":")).encode()
    (root / "geometry.json").write_bytes(geometry_bytes)
    license_bytes = b"TEST ONLY synthetic fixture evidence; this is not a license grant.\n"
    (root / "license-evidence.txt").write_bytes(license_bytes)
    manifest: dict[str, object] = {
        "contract": "packlab.trigger-pump-library-component.v1",
        "component_id": "synthetic-trigger-pump",
        "component_version": "1.2.0",
        "source": {"kind": "packlab_authored", "reference": "packlab:test-fixture"},
        "provenance": {"provenance_id": "fixture-provenance-r1", "source_revision": "fixture-r1"},
        "license": {
            "identifier": "TEST-ONLY",
            "review_status": "reviewed",
            "reviewed_by": "fixture-reviewer",
            "reviewed_at_utc": "2026-10-04T14:00:00Z",
            "evidence_path": "license-evidence.txt",
            "evidence_sha256": hashlib.sha256(license_bytes).hexdigest(),
        },
        "geometry_asset": {
            "path": "geometry.json",
            "format": "json",
            "sha256": hashlib.sha256(geometry_bytes).hexdigest(),
        },
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return manifest_path, manifest


def _write_manifest(root: Path, manifest: dict[str, object]) -> None:
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")


def test_verified_local_import_is_deterministic_and_library_authority(tmp_path: Path) -> None:
    _fixture(tmp_path)
    first = import_local_trigger_pump_component(tmp_path, "manifest.json")
    second = import_local_trigger_pump_component(tmp_path, "manifest.json")

    assert first == second
    assert first.import_id == second.import_id
    assert first.component_version == "1.2.0"
    assert first.license_identifier == "TEST-ONLY"
    assert first.geometry_asset_sha256
    assert dict(first.geometry_parameters)["overall_length"] == 72.0
    payload = first.as_dict()
    assert payload["geometry"]["authority_class"] == "LIBRARY_DESIGN_COMPONENT"  # type: ignore[index]
    assert payload["scan_master_revision_id"] is None
    assert payload["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert payload["mold_use_authorized"] is False
    assert payload["downloaded"] is False
    assert payload["network_accessed"] is False


def test_geometry_digest_tamper_rejects(tmp_path: Path) -> None:
    _fixture(tmp_path)
    (tmp_path / "geometry.json").write_text('{"tampered":true}', encoding="utf-8")
    with pytest.raises(TriggerPumpLibraryError, match="geometry_digest_mismatch"):
        import_local_trigger_pump_component(tmp_path, "manifest.json")


@pytest.mark.parametrize("field", ["license", "provenance"])
def test_missing_license_or_provenance_rejects(tmp_path: Path, field: str) -> None:
    _, manifest = _fixture(tmp_path)
    del manifest[field]
    _write_manifest(tmp_path, manifest)
    with pytest.raises(TriggerPumpLibraryError, match=f"{field}_must_be_object"):
        import_local_trigger_pump_component(tmp_path, "manifest.json")


def test_unreviewed_license_and_missing_license_evidence_reject(tmp_path: Path) -> None:
    _, manifest = _fixture(tmp_path)
    license_record = manifest["license"]
    assert isinstance(license_record, dict)
    license_record["review_status"] = "pending"
    _write_manifest(tmp_path, manifest)
    with pytest.raises(TriggerPumpLibraryError, match="license_not_reviewed"):
        import_local_trigger_pump_component(tmp_path, "manifest.json")

    license_record["review_status"] = "reviewed"
    license_record["evidence_path"] = "private/license.txt"
    _write_manifest(tmp_path, manifest)
    with pytest.raises(TriggerPumpLibraryError, match="license_path_private_or_raw"):
        import_local_trigger_pump_component(tmp_path, "manifest.json")


def test_unsupported_contract_and_component_version_reject(tmp_path: Path) -> None:
    _, manifest = _fixture(tmp_path)
    manifest["contract"] = "packlab.trigger-pump-library-component.v2"
    _write_manifest(tmp_path, manifest)
    with pytest.raises(TriggerPumpLibraryError, match="contract_unsupported"):
        import_local_trigger_pump_component(tmp_path, "manifest.json")

    manifest["contract"] = "packlab.trigger-pump-library-component.v1"
    manifest["component_version"] = "latest"
    _write_manifest(tmp_path, manifest)
    with pytest.raises(TriggerPumpLibraryError, match="component_version_invalid"):
        import_local_trigger_pump_component(tmp_path, "manifest.json")


@pytest.mark.parametrize(
    "path",
    [
        "private/manifest.json",
        "raw/manifest.json",
        "../outside.json",
        "https://example.test/asset.json",
    ],
)
def test_private_raw_escape_and_network_manifest_paths_reject(tmp_path: Path, path: str) -> None:
    _fixture(tmp_path)
    with pytest.raises(TriggerPumpLibraryError, match="path_(private_or_raw|invalid)"):
        import_local_trigger_pump_component(tmp_path, path)


def test_private_raw_geometry_asset_paths_reject(tmp_path: Path) -> None:
    _, manifest = _fixture(tmp_path)
    geometry_asset = manifest["geometry_asset"]
    assert isinstance(geometry_asset, dict)
    for unsafe_path in ("raw/geometry.json", "geometry_raw_scan.json"):
        geometry_asset["path"] = unsafe_path
        _write_manifest(tmp_path, manifest)
        with pytest.raises(TriggerPumpLibraryError, match="geometry_path_private_or_raw"):
            import_local_trigger_pump_component(tmp_path, "manifest.json")


def test_import_never_opens_network_urls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fixture(tmp_path)

    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("library import attempted network access")

    monkeypatch.setattr(urllib.request, "urlopen", reject_network)
    imported = import_local_trigger_pump_component(tmp_path, "manifest.json")
    assert imported.as_dict()["network_accessed"] is False
