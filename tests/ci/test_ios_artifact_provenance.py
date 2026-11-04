from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.ci.ios_artifact_provenance import (
    ProvenanceError,
    build_manifest,
    verify_manifest,
)


def _metadata(**overrides: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "artifact_type": "ios_simulator_app",
        "signing_state": "UNSIGNED",
        "product_name": "PackLabCapture.app",
        "capture_version": "0.1.0",
        "capture_build": "1",
        "packscan_schema_version": "1.0.0",
        "source_commit": "a" * 40,
        "xcode_version": "16.2",
        "xcode_build": "16C5032a",
        "sdk_name": "iphonesimulator",
        "sdk_version": "18.2",
        "bundle_identifier": "com.packlab.capture",
        "package_resolved_sha256": "b" * 64,
        "repository": "Sekiph82/PackLab",
        "workflow_name": "PackLab Capture macOS CI",
        "workflow_run_id": 123456,
        "workflow_run_number": 42,
        "workflow_run_attempt": 1,
        "event_name": "push",
    }
    metadata.update(overrides)
    return metadata


def _artifact(root: Path) -> Path:
    artifact = root / "PackLabCapture.app"
    (artifact / "Contents").mkdir(parents=True)
    (artifact / "Info.plist").write_bytes(b"plist-data")
    (artifact / "Contents" / "executable").write_bytes(b"capture-binary")
    return artifact


def test_manifest_is_deterministic_and_binds_tree_contents(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    first = build_manifest(artifact, _metadata())
    second = build_manifest(artifact, _metadata())

    assert first == second
    assert first["artifact_byte_length"] == len(b"plist-data") + len(b"capture-binary")
    assert first["artifact_file_count"] == 2

    sidecar = tmp_path / "provenance.json"
    sidecar.write_text(json.dumps(first), encoding="utf-8")
    assert verify_manifest(artifact, sidecar) == first

    (artifact / "Info.plist").write_bytes(b"tampered")
    with pytest.raises(ProvenanceError, match="PROVENANCE_ARTIFACT_DIGEST_MISMATCH"):
        verify_manifest(artifact, sidecar)


def test_artifact_type_and_signing_state_must_agree(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    with pytest.raises(ProvenanceError, match="PROVENANCE_SIGNING_STATE_INVALID"):
        build_manifest(artifact, _metadata(signing_state="SIGNED"))

    with pytest.raises(ProvenanceError, match="PROVENANCE_ARTIFACT_TYPE_INVALID"):
        build_manifest(
            artifact,
            _metadata(artifact_type="ios_signed_ipa", signing_state="SIGNED"),
        )


def test_unknown_or_secret_like_fields_are_rejected(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    metadata = _metadata()
    metadata["certificate_private_key"] = "must-not-be-serialized"
    with pytest.raises(ProvenanceError, match="PROVENANCE_METADATA_FIELDS_INVALID"):
        build_manifest(artifact, metadata)

    with pytest.raises(ProvenanceError, match="PROVENANCE_WORKFLOW_INVALID"):
        build_manifest(artifact, _metadata(workflow_name="PackLab\nTOKEN=secret"))


def test_verifier_rejects_sidecar_with_extra_fields_or_invalid_counts(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    manifest = build_manifest(artifact, _metadata())
    sidecar = tmp_path / "provenance.json"

    manifest["artifact_byte_length"] = True
    sidecar.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ProvenanceError, match="PROVENANCE_ARTIFACT_SIZE_INVALID"):
        verify_manifest(artifact, sidecar)

    manifest = build_manifest(artifact, _metadata())
    manifest["unexpected"] = "value"
    sidecar.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ProvenanceError, match="PROVENANCE_SIDECAR_FIELDS_INVALID"):
        verify_manifest(artifact, sidecar)

    for field in ("artifact_byte_length", "artifact_file_count"):
        manifest = build_manifest(artifact, _metadata())
        manifest[field] += 1
        sidecar.write_text(json.dumps(manifest), encoding="utf-8")
        error_code = (
            "PROVENANCE_ARTIFACT_LENGTH_MISMATCH"
            if field == "artifact_byte_length"
            else "PROVENANCE_ARTIFACT_INVENTORY_MISMATCH"
        )
        with pytest.raises(ProvenanceError, match=error_code):
            verify_manifest(artifact, sidecar)


def test_empty_artifact_is_rejected(tmp_path: Path) -> None:
    artifact = tmp_path / "empty.app"
    artifact.mkdir()
    with pytest.raises(ProvenanceError, match="ARTIFACT_EMPTY"):
        build_manifest(artifact, _metadata())


def test_symlink_artifact_entry_is_rejected_when_supported(tmp_path: Path) -> None:
    artifact = tmp_path / "PackLabCapture.app"
    artifact.mkdir()
    target = tmp_path / "outside.bin"
    target.write_bytes(b"external")
    try:
        (artifact / "linked.bin").symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("This Windows environment does not permit creating symlinks.")

    with pytest.raises(ProvenanceError, match="ARTIFACT_LINK_BLOCKED"):
        build_manifest(artifact, _metadata())


def test_junction_artifact_entry_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = _artifact(tmp_path)
    junction_marker = artifact / "junction-marker"
    junction_marker.write_bytes(b"would-represent-junction")

    def is_junction(path: Path) -> bool:
        return path == junction_marker

    monkeypatch.setattr(Path, "is_junction", is_junction, raising=False)
    with pytest.raises(ProvenanceError, match="ARTIFACT_LINK_BLOCKED"):
        build_manifest(artifact, _metadata())
