from __future__ import annotations

import hashlib

import pytest

from packlab_core.reconstruction import (
    BackendProvenance,
    CameraPrior,
    CameraPriorUse,
    CancelToken,
    CapabilityReport,
    PreparedJob,
    ReconstructionBackend,
    ReconstructionBackendId,
    ReconstructionCapability,
    ReconstructionInputSet,
    ReconstructionJobSpec,
    ReconstructionOutputManifest,
    ReconstructionRun,
    ReconstructionStageResult,
    RunStatus,
    ScaleState,
    StageStatus,
    assess_camera_priors,
)


def _inputs() -> ReconstructionInputSet:
    return ReconstructionInputSet(
        "project-1",
        "raw/capture.packscan",
        "raw-revision-1",
        hashlib.sha256(b"raw").hexdigest(),
        ("working/images/001.jpg", "working/images/002.jpg"),
    )


class FakeBackend:
    def probe(self) -> CapabilityReport:
        return CapabilityReport(ReconstructionBackendId.COLMAP_OPENMVS, True, (ReconstructionCapability.SPARSE,))

    def prepare(self, job: ReconstructionJobSpec) -> PreparedJob:
        return PreparedJob(job, job.assess_camera_priors())

    def execute(self, prepared: PreparedJob, cancel: CancelToken) -> ReconstructionRun:
        status = RunStatus.CANCELLED if cancel.cancelled else RunStatus.SUCCEEDED
        stage = ReconstructionStageResult(
            "sparse",
            StageStatus.CANCELLED if cancel.cancelled else StageStatus.SUCCEEDED,
            None if cancel.cancelled else 0,
            0.01,
            cancelled=cancel.cancelled,
        )
        return ReconstructionRun(prepared, status, (stage,))

    def collect(self, run: ReconstructionRun) -> ReconstructionOutputManifest:
        return ReconstructionOutputManifest(
            run.prepared.spec.project_id,
            "reconstruction-1",
            ReconstructionBackendId.COLMAP_OPENMVS,
            "3.12.6/2.4.0",
            "fixture",
            "external",
            run.prepared.spec.configuration_digest,
            run.prepared.spec.inputs.source_digest,
            "world-to-camera",
            asset_paths={"sparse": "working/reconstruction-1/sparse/points.ply"},
            stage_results=run.stage_results,
        )

    def provenance(self) -> BackendProvenance:
        return BackendProvenance(ReconstructionBackendId.COLMAP_OPENMVS, "fixture", "fixture", "external")


class AlternateBackend(FakeBackend):
    def probe(self) -> CapabilityReport:
        return CapabilityReport(ReconstructionBackendId.COLMAP_OPENMVS, True, (ReconstructionCapability.MESH,))


def test_two_backend_implementations_satisfy_the_same_contract() -> None:
    assert isinstance(FakeBackend(), ReconstructionBackend)
    assert isinstance(AlternateBackend(), ReconstructionBackend)


def test_fake_backend_completes_normalized_job_and_missing_prior_degrades() -> None:
    spec = ReconstructionJobSpec("job-1", "project-1", 0, _inputs(), ReconstructionBackendId.COLMAP_OPENMVS)
    backend = FakeBackend()
    prepared = backend.prepare(spec)
    assert prepared.camera_priors.warnings == (
        "missing camera prior: working/images/001.jpg",
        "missing camera prior: working/images/002.jpg",
    )
    run = backend.execute(prepared, CancelToken())
    manifest = backend.collect(run)
    assert run.status is RunStatus.SUCCEEDED
    assert manifest.scale_state is ScaleState.RELATIVE
    assert manifest.as_dict()["asset_paths"] == {"sparse": "working/reconstruction-1/sparse/points.ply"}


def test_invalid_prior_is_rejected_explicitly() -> None:
    prior = CameraPrior("working/images/001.jpg", width=0, use=CameraPriorUse.FIXED)
    spec = ReconstructionJobSpec("job-1", "project-1", 0, _inputs(), ReconstructionBackendId.COLMAP_OPENMVS, camera_priors=(prior,))
    assessment = spec.assess_camera_priors()
    assert assessment.priors[0].use is CameraPriorUse.REJECTED
    assert "invalid" in assessment.warnings[0]


def test_unbound_prior_is_rejected_at_generic_assessment_boundary() -> None:
    inputs = _inputs()
    prior = CameraPrior(
        inputs.image_asset_ids[0],
        width=1,
        height=1,
        intrinsics=(1.0, 0.0, 0.5, 0.0, 1.0, 0.5, 0.0, 0.0, 1.0),
    )
    assert prior.valid

    assessment = assess_camera_priors(inputs, (prior,))

    assert assessment.priors[0].use is CameraPriorUse.REJECTED
    assert "source binding is incomplete" in assessment.priors[0].reason
    assert "source binding incomplete" in assessment.warnings[0]


def test_cancellation_does_not_change_input_identity() -> None:
    inputs = _inputs()
    spec = ReconstructionJobSpec("job-1", "project-1", 0, inputs, ReconstructionBackendId.COLMAP_OPENMVS)
    token = CancelToken()
    token.cancel()
    run = FakeBackend().execute(FakeBackend().prepare(spec), token)
    assert run.status is RunStatus.CANCELLED
    assert spec.inputs == inputs
    assert spec.inputs.source_digest == hashlib.sha256(b"raw").hexdigest()


def test_m07_manifest_rejects_metric_verified_and_absolute_paths() -> None:
    kwargs = dict(
        project_id="project-1",
        reconstruction_revision="r1",
        backend_id=ReconstructionBackendId.COLMAP_OPENMVS,
        backend_version="fixture",
        backend_build="fixture",
        backend_license="external",
        configuration_digest="config",
        source_input_digest=hashlib.sha256(b"raw").hexdigest(),
        camera_convention="world-to-camera",
    )
    with pytest.raises(ValueError, match="METRIC_VERIFIED"):
        ReconstructionOutputManifest(**kwargs, scale_state=ScaleState.METRIC_VERIFIED)
    with pytest.raises(ValueError, match="relative"):
        ReconstructionOutputManifest(**kwargs, asset_paths={"mesh": "C:/private/mesh.ply"})


def test_changing_source_revision_changes_job_identity() -> None:
    first = _inputs()
    second = ReconstructionInputSet(
        first.project_id,
        first.raw_capture_asset_id,
        "raw-revision-2",
        hashlib.sha256(b"new raw").hexdigest(),
        first.image_asset_ids,
    )
    first_job = ReconstructionJobSpec("job-1", "project-1", 0, first, ReconstructionBackendId.COLMAP_OPENMVS)
    second_job = ReconstructionJobSpec("job-2", "project-1", 0, second, ReconstructionBackendId.COLMAP_OPENMVS)
    assert first_job.inputs.source_digest != second_job.inputs.source_digest
