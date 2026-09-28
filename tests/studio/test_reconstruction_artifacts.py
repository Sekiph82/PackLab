from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from packlab_core.reconstruction import ReconstructionStageResult, StageStatus
from packlab_studio import reconstruction_artifacts as artifacts
from packlab_studio.reconstruction_artifacts import (
    MAX_RETAINED_LOG_CHARS,
    ReconstructionEvidenceCollisionError,
    ReconstructionEvidenceError,
    retain_reconstruction_stage_evidence,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fixture(tmp_path: Path, *, status: StageStatus = StageStatus.SUCCEEDED):
    workspace = tmp_path / "working" / "reconstruction" / "rev-001"
    output = workspace / "outputs" / "partial.mesh"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"mesh bytes; opaque to retention")
    result = ReconstructionStageResult(
        "dense",
        status,
        0 if status is StageStatus.SUCCEEDED else 7,
        1.25,
        stdout="C:\\private\\capture\\frame.jpg token=<PACKLAB_TEST_TOKEN_REDACTED>\n"
        + "x" * 20_000,
        stderr="password=<PACKLAB_TEST_PASSWORD_REDACTED>",
        cancelled=status is StageStatus.CANCELLED,
        failure_reason=None if status is StageStatus.SUCCEEDED else "stage stopped",
    )
    kwargs = {
        "source_revision": "rev-001",
        "source_digest": _digest("source"),
        "reconstruction_request_digest": _digest("request"),
        "stage_digest": _digest("stage"),
        "output_identities": {"mesh": "working/reconstruction/openmvs/dense-mesh"},
    }
    return workspace, output, result, kwargs


def _retain(workspace: Path, output: Path, result: ReconstructionStageResult, kwargs):
    return retain_reconstruction_stage_evidence(
        workspace,
        "dense",
        "run-001",
        result,
        {"mesh": "outputs/partial.mesh"},
        **kwargs,
    )


@pytest.mark.unit
def test_success_retains_opaque_output_logs_and_manifest(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)

    retained = _retain(workspace, output, result, kwargs)
    manifest = json.loads(retained.manifest_path.read_text(encoding="utf-8"))

    assert retained.idempotent is False
    assert (retained.evidence_path / "outputs/mesh.mesh").read_bytes() == output.read_bytes()
    assert manifest["contract"] == "packlab.reconstruction-stage-evidence.v1"
    assert manifest["stage_id"] == "dense"
    assert manifest["run_id"] == "run-001"
    assert manifest["stage_status"] == "succeeded"
    assert manifest["source_revision"] == "rev-001"
    assert manifest["source_digest"] == kwargs["source_digest"]
    assert (
        manifest["provenance"]["reconstruction_request_digest"]
        == kwargs["reconstruction_request_digest"]
    )
    assert manifest["provenance"]["stage_digest"] == kwargs["stage_digest"]
    assert manifest["outputs"][0]["sha256"] == _digest("mesh bytes; opaque to retention")
    assert manifest["outputs"][0]["byte_size"] == len(output.read_bytes())
    assert "<PACKLAB_TEST_TOKEN_REDACTED>" not in manifest["stdout"]
    assert "private" not in manifest["stdout"].lower()
    assert len(manifest["stdout"]) <= MAX_RETAINED_LOG_CHARS
    assert manifest["outputs"][0]["output_identity"] == kwargs["output_identities"]["mesh"]


@pytest.mark.unit
@pytest.mark.parametrize("status", [StageStatus.FAILED, StageStatus.CANCELLED])
def test_failed_and_cancelled_runs_retain_partial_outputs(
    tmp_path: Path, status: StageStatus
) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path, status=status)

    retained = _retain(workspace, output, result, kwargs)
    manifest = json.loads(retained.manifest_path.read_text(encoding="utf-8"))

    assert manifest["status"] == status.value
    assert (retained.evidence_path / "outputs/mesh.mesh").read_bytes() == output.read_bytes()
    assert (retained.evidence_path / "logs/stdout.txt").is_file()
    assert (retained.evidence_path / "logs/stderr.txt").is_file()


@pytest.mark.unit
def test_identical_repeat_is_idempotent(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)

    first = _retain(workspace, output, result, kwargs)
    before = first.manifest_path.read_bytes()
    second = _retain(workspace, output, result, kwargs)

    assert second.idempotent is True
    assert second.manifest_path.read_bytes() == before


@pytest.mark.unit
def test_same_identity_byte_mismatch_preserves_prior_evidence(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)
    first = _retain(workspace, output, result, kwargs)
    prior = (first.evidence_path / "outputs/mesh.mesh").read_bytes()
    output.write_bytes(b"different bytes")

    with pytest.raises(ReconstructionEvidenceCollisionError):
        _retain(workspace, output, result, kwargs)

    assert (first.evidence_path / "outputs/mesh.mesh").read_bytes() == prior
    assert first.manifest_path.is_file()


@pytest.mark.unit
def test_same_identity_provenance_mismatch_fails_closed(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)
    first = _retain(workspace, output, result, kwargs)
    changed = dict(kwargs)
    changed["stage_digest"] = _digest("different stage")

    with pytest.raises(ReconstructionEvidenceCollisionError):
        _retain(workspace, output, result, changed)

    assert first.manifest_path.is_file()


@pytest.mark.unit
def test_case_insensitive_output_identity_collision_fails_closed(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)
    second = workspace / "outputs" / "other.mesh"
    second.write_bytes(b"other bytes")

    with pytest.raises(ReconstructionEvidenceCollisionError):
        retain_reconstruction_stage_evidence(
            workspace,
            "dense",
            "run-001",
            result,
            {"mesh": "outputs/partial.mesh", "MESH": "outputs/other.mesh"},
            output_identities={
                "mesh": kwargs["output_identities"]["mesh"],
                "MESH": "working/reconstruction/openmvs/other-mesh",
            },
            source_revision=kwargs["source_revision"],
            source_digest=kwargs["source_digest"],
            reconstruction_request_digest=kwargs["reconstruction_request_digest"],
            stage_digest=kwargs["stage_digest"],
        )


@pytest.mark.unit
def test_case_insensitive_stage_run_collision_fails_closed(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)
    first = _retain(workspace, output, result, kwargs)
    variant = ReconstructionStageResult(
        "DENSE",
        result.status,
        result.exit_code,
        result.duration_seconds,
        stdout=result.stdout,
        stderr=result.stderr,
        cancelled=result.cancelled,
        failure_reason=result.failure_reason,
    )

    with pytest.raises(ReconstructionEvidenceCollisionError):
        retain_reconstruction_stage_evidence(
            workspace,
            "DENSE",
            "RUN-001",
            variant,
            {"mesh": "outputs/partial.mesh"},
            **kwargs,
        )

    assert first.manifest_path.is_file()


@pytest.mark.unit
def test_sequence_duplicate_basenames_fail_before_conversion(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)
    other = workspace / "alternate" / output.name
    other.parent.mkdir()
    other.write_bytes(b"other bytes")

    with pytest.raises(ReconstructionEvidenceCollisionError):
        retain_reconstruction_stage_evidence(
            workspace,
            "dense",
            "run-001",
            result,
            ["outputs/partial.mesh", "alternate/partial.mesh"],
            output_identities={
                "partial.mesh": kwargs["output_identities"]["mesh"],
            },
            source_revision=kwargs["source_revision"],
            source_digest=kwargs["source_digest"],
            reconstruction_request_digest=kwargs["reconstruction_request_digest"],
            stage_digest=kwargs["stage_digest"],
        )


@pytest.mark.unit
def test_case_insensitive_source_path_collision_fails_before_publication(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)

    with pytest.raises(ReconstructionEvidenceCollisionError):
        retain_reconstruction_stage_evidence(
            workspace,
            "dense",
            "run-001",
            result,
            {"mesh": "outputs/partial.mesh", "other": "Outputs/PARTIAL.mesh"},
            output_identities={
                "mesh": kwargs["output_identities"]["mesh"],
                "other": "working/reconstruction/openmvs/other-mesh",
            },
            source_revision=kwargs["source_revision"],
            source_digest=kwargs["source_digest"],
            reconstruction_request_digest=kwargs["reconstruction_request_digest"],
            stage_digest=kwargs["stage_digest"],
        )

    assert not (workspace / "evidence").exists()


@pytest.mark.unit
@pytest.mark.parametrize(
    "path",
    [
        "../outside.bin",
        "/absolute.bin",
        "C:/absolute.bin",
        "outputs/../outside.bin",
        "raw/capture.packscan",
        "private/scan.bin",
        "supplier/drawing.step",
    ],
)
def test_unsafe_and_source_paths_fail_closed(tmp_path: Path, path: str) -> None:
    workspace, _, result, kwargs = _fixture(tmp_path)
    with pytest.raises(ReconstructionEvidenceError):
        retain_reconstruction_stage_evidence(
            workspace,
            "dense",
            "run-001",
            result,
            {"mesh": path},
            **kwargs,
        )


@pytest.mark.unit
def test_unsafe_stage_and_run_identities_are_rejected(tmp_path: Path) -> None:
    workspace, _, result, kwargs = _fixture(tmp_path)
    for stage_id, run_id in [("../dense", "run-001"), ("dense", "run/001")]:
        with pytest.raises(ReconstructionEvidenceError):
            retain_reconstruction_stage_evidence(
                workspace,
                stage_id,
                run_id,
                result,
                {"mesh": "outputs/partial.mesh"},
                **kwargs,
            )


@pytest.mark.unit
def test_symlink_escape_is_rejected_when_supported(tmp_path: Path) -> None:
    workspace, _, result, kwargs = _fixture(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = workspace / "outputs" / "link.bin"
    try:
        link.symlink_to(outside / "not-inside.bin")
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"symlink creation unavailable: {type(error).__name__}")
    with pytest.raises(ReconstructionEvidenceError):
        retain_reconstruction_stage_evidence(
            workspace,
            "dense",
            "run-001",
            result,
            {"mesh": "outputs/link.bin"},
            **kwargs,
        )


@pytest.mark.unit
def test_missing_output_is_a_bounded_retention_failure(tmp_path: Path) -> None:
    workspace, _, result, kwargs = _fixture(tmp_path)
    retained = retain_reconstruction_stage_evidence(
        workspace,
        "dense",
        "run-001",
        result,
        {"mesh": "outputs/missing.mesh"},
        **kwargs,
    )
    manifest = json.loads(retained.manifest_path.read_text(encoding="utf-8"))

    assert manifest["retention_status"] == "bounded_failure"
    assert manifest["retention_failures"] == ["mesh:outputs/missing.mesh:missing_or_unreadable"]
    assert manifest["outputs"] == []
    assert (retained.evidence_path / "logs/stdout.txt").is_file()


@pytest.mark.unit
def test_atomic_failure_leaves_no_partial_evidence(tmp_path: Path, monkeypatch) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)

    def fail_atomic_json(target: Path, value: object) -> None:
        raise OSError("simulated manifest write failure")

    monkeypatch.setattr(artifacts, "_atomic_json", fail_atomic_json)
    with pytest.raises(OSError, match="simulated manifest"):
        _retain(workspace, output, result, kwargs)

    assert not (workspace / "evidence/dense/run-001").exists()
    assert not list(workspace.glob(".stage-evidence-*"))


@pytest.mark.unit
def test_mid_publication_failure_removes_final_identity(tmp_path: Path, monkeypatch) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)
    original_replace = artifacts.os.replace
    final_path = workspace / "evidence" / "dense" / "run-001"
    moved = False

    def fail_after_first_final_move(source: str | bytes, target: str | bytes) -> None:
        nonlocal moved
        target_path = Path(target)
        original_replace(source, target)
        if target_path.parent == final_path and not moved:
            moved = True
            raise OSError("simulated mid-publication failure")

    monkeypatch.setattr(artifacts.os, "replace", fail_after_first_final_move)
    with pytest.raises(OSError, match="simulated mid-publication"):
        _retain(workspace, output, result, kwargs)

    assert moved
    assert not final_path.exists()
    assert not list(workspace.glob(".stage-evidence-*"))


@pytest.mark.unit
def test_idempotent_retry_detects_tampered_retained_bytes(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)
    first = _retain(workspace, output, result, kwargs)
    retained_output = first.evidence_path / "outputs/mesh.mesh"
    retained_output.write_bytes(b"tampered retained bytes")

    with pytest.raises(ReconstructionEvidenceCollisionError):
        _retain(workspace, output, result, kwargs)

    assert retained_output.read_bytes() == b"tampered retained bytes"
    assert first.manifest_path.is_file()


@pytest.mark.unit
def test_stage_result_contract_is_validated_at_public_boundary(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)
    malformed = ReconstructionStageResult("other-stage", StageStatus.SUCCEEDED, 0, 1.0, stdout="ok")

    with pytest.raises(ReconstructionEvidenceError):
        _retain(workspace, output, malformed, kwargs)


@pytest.mark.unit
def test_provenance_links_are_preserved_without_parsing_outputs(tmp_path: Path) -> None:
    workspace, output, result, kwargs = _fixture(tmp_path)
    kwargs = dict(kwargs, provenance={"producer": "openmvs.TextureMesh:2.4.0"})

    retained = _retain(workspace, output, result, kwargs)
    manifest = json.loads(retained.manifest_path.read_text(encoding="utf-8"))

    assert manifest["provenance"]["producer"] == "openmvs.TextureMesh:2.4.0"
    assert manifest["outputs"][0]["byte_size"] == len(b"mesh bytes; opaque to retention")
