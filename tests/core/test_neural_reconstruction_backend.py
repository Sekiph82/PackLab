from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from packlab_core.neural_reconstruction import (
    VGGT_COMMERCIAL_CHECKPOINT_SHA256,
    VGGT_COMMERCIAL_REPOSITORY_REVISION,
    VGGTActivationRecord,
    VGGTReconstructionBackend,
    VGGTWorkspaceCamera,
    VGGTWorkspaceInference,
    VGGTWorkspaceRuntime,
)
from packlab_core.neural_reconstruction_io import (
    VGGTImagePreprocessTransform,
    VGGTOutputArtifact,
)
from packlab_core.reconstruction import (
    CancelToken,
    ReconstructionBackend,
    ReconstructionBackendId,
    ReconstructionCapability,
    ReconstructionInputSet,
    ReconstructionJobSpec,
    ReconstructionOutputManifest,
    RunStatus,
    ScaleState,
)


def _activation() -> VGGTActivationRecord:
    """Synthetic evidence; the public pin is real, but no local file is verified."""
    return VGGTActivationRecord(
        "facebook/VGGT-1B-Commercial",
        VGGT_COMMERCIAL_REPOSITORY_REVISION,
        VGGT_COMMERCIAL_CHECKPOINT_SHA256,
        "synthetic-vggt-license",
        True,
        "synthetic-owner-acceptance",
        "synthetic-acceptable-use-review",
        "synthetic-runtime-license-review",
        "synthetic-deployment-review",
    )


def _job(backend_id: ReconstructionBackendId = ReconstructionBackendId.NEURAL_EXPERIMENTAL):
    inputs = ReconstructionInputSet(
        "project-1",
        "raw/capture.packscan",
        "revision-1",
        hashlib.sha256(b"source").hexdigest(),
        ("working/images/one.jpg", "working/images/two.jpg"),
    )
    return ReconstructionJobSpec("job-1", "project-1", 0, inputs, backend_id)


class SyntheticVGGT:
    def __init__(self) -> None:
        self.calls = 0

    def available(self) -> bool:
        return True

    def execute(self, prepared, cancel):
        self.calls += 1
        return ReconstructionOutputManifest(
            prepared.spec.project_id,
            "synthetic-output-1",
            ReconstructionBackendId.NEURAL_EXPERIMENTAL,
            "synthetic-vggt",
            "in-memory-test-double",
            "synthetic-only",
            prepared.spec.configuration_digest,
            prepared.spec.inputs.source_digest,
            "packscan-camera-to-world",
            point_count=2,
            scale_state=ScaleState.RELATIVE,
        )


class UntrustedMetadataVGGT(SyntheticVGGT):
    def execute(self, prepared, cancel):
        output = super().execute(prepared, cancel)
        return replace(
            output,
            backend_version=r"C:\private\runtime",
            backend_build="token=must-not-be-portable",
            backend_license="C:/private/license.txt",
            authority_class="SCAN_MASTER",
        )


class SyntheticWorkspaceEngine:
    def __init__(
        self, output_root, *, omit_last_camera=False, cancel=None, scale_state=ScaleState.RELATIVE
    ) -> None:
        self.output_root = output_root
        self.omit_last_camera = omit_last_camera
        self.cancel = cancel
        self.scale_state = scale_state
        self.calls = 0
        self.image_ids = ()

    def available(self) -> bool:
        return True

    def infer(self, images, cancel):
        self.calls += 1
        self.image_ids = tuple(image.asset_id for image in images)
        cloud = self.output_root / "cloud.ply"
        cloud.write_bytes(b"synthetic-point-cloud")
        cameras = tuple(
            VGGTWorkspaceCamera(
                image.asset_id,
                (1, 0, 0, index, 0, 1, 0, 0, 0, 0, 1, 3),
                (20, 0, 16, 0, 20, 16, 0, 0, 1),
                VGGTImagePreprocessTransform(32, 32, 0, 0, 1),
            )
            for index, image in enumerate(images)
        )
        if self.omit_last_camera:
            cameras = cameras[:-1]
        result = VGGTWorkspaceInference(
            "revision-v4",
            cameras,
            (VGGTOutputArtifact("point_cloud", "cloud.ply", cloud),),
            point_count=4,
            scale_state=self.scale_state,
            limitations=("synthetic injected engine",),
        )
        if self.cancel is not None:
            self.cancel.cancel()
        return result


def test_vggt_backend_satisfies_protocol_and_defaults_to_unavailable() -> None:
    backend = VGGTReconstructionBackend()
    assert isinstance(backend, ReconstructionBackend)
    report = backend.probe()
    assert not report.available
    assert report.backend_id is ReconstructionBackendId.NEURAL_EXPERIMENTAL
    assert "activation record incomplete" in report.limitations[0]
    run = backend.execute(backend.prepare(_job()), CancelToken())
    assert run.status is RunStatus.FAILED
    assert "activation record incomplete" in run.stage_results[0].failure_reason


def test_vggt_backend_uses_only_synthetic_injected_runtime_and_portable_identity() -> None:
    source = _job()
    runtime = SyntheticVGGT()
    backend = VGGTReconstructionBackend(_activation(), runtime)
    report = backend.probe()
    assert report.available
    assert report.capabilities == (
        ReconstructionCapability.SPARSE,
        ReconstructionCapability.DENSE,
    )

    prepared = backend.prepare(source)
    run = backend.execute(prepared, CancelToken())
    output = backend.collect(run)

    assert run.status is RunStatus.SUCCEEDED
    assert output.scale_state is ScaleState.RELATIVE
    assert output.source_input_digest == source.inputs.source_digest
    assert source.inputs.image_asset_ids == ("working/images/one.jpg", "working/images/two.jpg")
    assert runtime.calls == 1
    provenance = backend.provenance()
    assert provenance.build == (
        f"facebook/VGGT-1B-Commercial@{VGGT_COMMERCIAL_REPOSITORY_REVISION}"
        f"#sha256:{VGGT_COMMERCIAL_CHECKPOINT_SHA256}"
    )
    assert provenance.executable_hashes == {"checkpoint": VGGT_COMMERCIAL_CHECKPOINT_SHA256}
    assert "synthetic" not in provenance.build
    assert "C:\\" not in provenance.build


def test_vggt_backend_normalizes_runtime_metadata_and_authority() -> None:
    backend = VGGTReconstructionBackend(_activation(), UntrustedMetadataVGGT())
    output = backend.collect(backend.execute(backend.prepare(_job()), CancelToken()))

    assert output.backend_version == "vggt-adapter-contract-v1"
    assert output.backend_build == (
        f"facebook/VGGT-1B-Commercial@{VGGT_COMMERCIAL_REPOSITORY_REVISION}"
        f"#sha256:{VGGT_COMMERCIAL_CHECKPOINT_SHA256}"
    )
    assert output.backend_license == "synthetic-vggt-license"
    assert output.authority_class == "RECONSTRUCTION_OBSERVATION"
    assert "private" not in output.backend_build
    assert "token=" not in output.backend_build


def test_vggt_activation_rejects_path_as_license_identifier() -> None:
    activation = replace(_activation(), checkpoint_license_id="C:/private/license.txt")
    backend = VGGTReconstructionBackend(activation, SyntheticVGGT())

    assert not activation.complete
    assert not backend.probe().available


def test_vggt_activation_fails_closed_for_each_missing_review_gate() -> None:
    incomplete_records = (
        replace(_activation(), owner_terms_accepted=False),
        replace(_activation(), owner_acceptance_ref=""),
        replace(_activation(), acceptable_use_review_ref=""),
        replace(_activation(), runtime_license_review_ref=""),
        replace(_activation(), deployment_review_ref=""),
    )

    for activation in incomplete_records:
        runtime = SyntheticVGGT()
        backend = VGGTReconstructionBackend(activation, runtime)
        assert not activation.complete
        assert not backend.probe().available
        run = backend.execute(backend.prepare(_job()), CancelToken())
        assert run.status is RunStatus.FAILED
        assert runtime.calls == 0


@pytest.mark.parametrize("owner_terms_accepted", [1, "false", None])
def test_vggt_activation_requires_boolean_owner_acceptance(owner_terms_accepted) -> None:
    activation = replace(_activation(), owner_terms_accepted=owner_terms_accepted)

    assert not activation.complete
    assert not VGGTReconstructionBackend(activation, SyntheticVGGT()).probe().available


def test_vggt_backend_rejects_other_job_and_invalid_checkpoint_record() -> None:
    backend = VGGTReconstructionBackend(_activation(), SyntheticVGGT())
    with pytest.raises(ValueError, match="another backend"):
        backend.prepare(_job(ReconstructionBackendId.COLMAP_OPENMVS))

    invalid = VGGTActivationRecord(
        "facebook/VGGT-1B",
        VGGT_COMMERCIAL_REPOSITORY_REVISION,
        "bad-hash",
        "license",
        True,
        "owner",
        "aup",
        "runtime",
        "deploy",
    )
    assert not invalid.complete
    assert not VGGTReconstructionBackend(invalid, SyntheticVGGT()).probe().available

    wrong_pin = replace(_activation(), checkpoint_sha256="a" * 64)
    assert not wrong_pin.complete
    assert not VGGTReconstructionBackend(wrong_pin, SyntheticVGGT()).probe().available


def test_vggt_backend_obeys_cancellation_before_inference() -> None:
    runtime = SyntheticVGGT()
    backend = VGGTReconstructionBackend(_activation(), runtime)
    cancel = CancelToken()
    cancel.cancel()
    run = backend.execute(backend.prepare(_job()), cancel)
    assert run.status is RunStatus.CANCELLED
    assert runtime.calls == 0


def _workspace(tmp_path):
    project = tmp_path / "project"
    runtime_output = tmp_path / "runtime-output"
    project.mkdir(parents=True)
    runtime_output.mkdir(parents=True)
    image_ids = _job().inputs.image_asset_ids
    digests = {}
    for image_id in image_ids:
        image_path = project / Path(image_id)
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(image_id.encode("ascii"))
        digests[image_id] = hashlib.sha256(image_id.encode("ascii")).hexdigest()
    return project, runtime_output, digests


def test_vggt_workspace_runtime_wires_verified_inputs_cameras_and_derived_outputs(
    tmp_path,
) -> None:
    project, runtime_output, digests = _workspace(tmp_path)
    engine = SyntheticWorkspaceEngine(runtime_output)
    runtime = VGGTWorkspaceRuntime(project, digests, runtime_output, engine)
    backend = VGGTReconstructionBackend(_activation(), runtime)

    output = backend.collect(backend.execute(backend.prepare(_job()), CancelToken()))

    assert engine.calls == 1
    assert engine.image_ids == _job().inputs.image_asset_ids
    assert output.source_input_digest == _job().inputs.source_digest
    assert output.project_id == "project-1"
    assert output.camera_convention.startswith("packscan_right_handed")
    assert tuple(camera.image_asset_id for camera in output.cameras) == engine.image_ids
    assert output.cameras[0].translation == pytest.approx((0, 0, 3))
    assert output.scale_state is ScaleState.RELATIVE
    assert output.authority_class == "RECONSTRUCTION_OBSERVATION"
    assert output.asset_paths == {
        "camera_parameters": "derived/reconstruction/revision-v4/cameras.json",
        "point_cloud": "derived/reconstruction/revision-v4/cloud.ply",
    }
    camera_file = project / output.asset_paths["camera_parameters"]
    camera_metadata = camera_file.read_text(encoding="ascii")
    assert "intrinsics" in camera_metadata
    assert str(runtime_output) not in camera_metadata
    assert (project / output.asset_paths["point_cloud"]).read_bytes() == b"synthetic-point-cloud"
    assert list(runtime_output.glob(".packlab-vggt-cameras-*.json")) == []


def test_vggt_workspace_runtime_fails_closed_before_engine_on_digest_mismatch(tmp_path) -> None:
    project, runtime_output, digests = _workspace(tmp_path)
    first_asset = _job().inputs.image_asset_ids[0]
    digests[first_asset] = "0" * 64
    engine = SyntheticWorkspaceEngine(runtime_output)
    runtime = VGGTWorkspaceRuntime(project, digests, runtime_output, engine)
    backend = VGGTReconstructionBackend(_activation(), runtime)

    run = backend.execute(backend.prepare(_job()), CancelToken())

    assert run.status is RunStatus.FAILED
    assert "NeuralReconstructionIOError" in run.stage_results[0].failure_reason
    assert engine.calls == 0
    assert not (project / "derived").exists()


def test_vggt_workspace_runtime_rejects_incomplete_cameras_and_honors_cancel(tmp_path) -> None:
    project, runtime_output, digests = _workspace(tmp_path)
    engine = SyntheticWorkspaceEngine(runtime_output, omit_last_camera=True)
    runtime = VGGTWorkspaceRuntime(project, digests, runtime_output, engine)
    backend = VGGTReconstructionBackend(_activation(), runtime)
    failed = backend.execute(backend.prepare(_job()), CancelToken())
    assert failed.status is RunStatus.FAILED
    assert "NeuralReconstructionIOError" in failed.stage_results[0].failure_reason
    assert not (project / "derived").exists()

    cancelled_project, cancelled_runtime, cancelled_digests = _workspace(tmp_path / "cancelled")
    cancel = CancelToken()
    cancel_engine = SyntheticWorkspaceEngine(cancelled_runtime, cancel=cancel)
    cancel_runtime = VGGTWorkspaceRuntime(
        cancelled_project,
        cancelled_digests,
        cancelled_runtime,
        cancel_engine,
    )
    cancelled_backend = VGGTReconstructionBackend(_activation(), cancel_runtime)
    cancelled = cancelled_backend.execute(cancelled_backend.prepare(_job()), cancel)
    assert cancelled.status is RunStatus.CANCELLED
    assert cancel_engine.calls == 1
    assert not (cancelled_project / "derived").exists()
    assert list(cancelled_runtime.glob(".packlab-vggt-cameras-*.json")) == []


def test_vggt_workspace_runtime_rejects_metric_or_untyped_scale(tmp_path) -> None:
    project, runtime_output, digests = _workspace(tmp_path)
    engine = SyntheticWorkspaceEngine(runtime_output, scale_state="metric-verified")
    runtime = VGGTWorkspaceRuntime(project, digests, runtime_output, engine)
    backend = VGGTReconstructionBackend(_activation(), runtime)

    run = backend.execute(backend.prepare(_job()), CancelToken())

    assert run.status is RunStatus.FAILED
    assert "NeuralReconstructionIOError" in run.stage_results[0].failure_reason
    assert not (project / "derived").exists()
    assert list(runtime_output.glob(".packlab-vggt-cameras-*.json")) == []


def test_published_manifest_file_carries_the_activation_identity(tmp_path) -> None:
    # Review P2 (PL-0436): the saved manifest.json used placeholder build/licence values.
    import json

    project, runtime_output, digests = _workspace(tmp_path)
    activation = _activation()
    runtime = VGGTWorkspaceRuntime(
        project,
        digests,
        runtime_output,
        SyntheticWorkspaceEngine(runtime_output),
        activation=activation,
    )
    backend = VGGTReconstructionBackend(activation, runtime)
    output = backend.collect(backend.execute(backend.prepare(_job()), CancelToken()))
    manifest_file = next((project / "derived" / "reconstruction").rglob("manifest.json"))
    saved = json.loads(manifest_file.read_text(encoding="utf-8"))
    text = json.dumps(saved)
    assert activation.checkpoint_sha256 in text
    assert activation.checkpoint_license_id in text
    assert "injected-runtime" not in text and "configured-vggt-checkpoint" not in text
    assert output.backend_build.endswith(activation.checkpoint_sha256)
    assert output.backend_license == activation.checkpoint_license_id


def test_workspace_runtime_rejects_an_incomplete_activation(tmp_path) -> None:
    from dataclasses import replace

    project, runtime_output, digests = _workspace(tmp_path)
    with pytest.raises(ValueError, match="activation record is incomplete"):
        VGGTWorkspaceRuntime(
            project,
            digests,
            runtime_output,
            SyntheticWorkspaceEngine(runtime_output),
            activation=replace(_activation(), checkpoint_id="facebook/VGGT-1B"),
        )


def test_non_commercial_checkpoint_id_alone_is_rejected() -> None:
    # Review mutant N2: the only previous test changed the ID and the hash together.
    from dataclasses import replace

    record = replace(_activation(), checkpoint_id="facebook/VGGT-1B")
    assert record.checkpoint_sha256 == _activation().checkpoint_sha256  # only the ID differs
    assert record.complete is False
    assert VGGTReconstructionBackend(record).probe().available is False
