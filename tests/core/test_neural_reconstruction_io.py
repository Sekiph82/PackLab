from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import packlab_core.neural_reconstruction_io as neural_io
from packlab_core.neural_reconstruction_io import (
    NeuralReconstructionIOError,
    VGGTImagePreprocessTransform,
    VGGTOutputArtifact,
    normalize_vggt_camera,
    normalize_vggt_world_point,
    publish_vggt_artifacts,
    resolve_vggt_image_assets,
)
from packlab_core.reconstruction import (
    PACKSCAN_CAMERA_CONVENTION,
    ReconstructionBackendId,
    ReconstructionInputSet,
    ReconstructionOutputManifest,
    ScaleState,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inputs(image_ids: tuple[str, ...]) -> ReconstructionInputSet:
    return ReconstructionInputSet(
        "project-1",
        "raw/capture.packscan",
        "revision-1",
        _sha(b"capture-index"),
        image_ids,
    )


def _manifest(
    scale: ScaleState = ScaleState.RELATIVE, revision: str = "r1"
) -> ReconstructionOutputManifest:
    return ReconstructionOutputManifest(
        project_id="project-1",
        reconstruction_revision=revision,
        backend_id=ReconstructionBackendId.NEURAL_EXPERIMENTAL,
        backend_version="vggt-adapter-contract-v1",
        backend_build="facebook/VGGT-1B-Commercial@pinned#sha256:pin",
        backend_license="VGGT-AUP",
        configuration_digest=_sha(b"configuration"),
        source_input_digest=_sha(b"capture-index"),
        camera_convention=PACKSCAN_CAMERA_CONVENTION,
        point_count=0,
        scale_state=scale,
        limitations=("synthetic output fixture",),
        authority_class="RECONSTRUCTION_OBSERVATION",
    )


def test_image_resolver_verifies_exact_manifest_digests_and_preserves_order(tmp_path: Path) -> None:
    root = tmp_path / "project"
    first = root / "working/images/first.jpg"
    second = root / "working/images/second.jpg"
    first.parent.mkdir(parents=True)
    first.write_bytes(b"synthetic-image-one")
    second.write_bytes(b"synthetic-image-two")
    before = (first.read_bytes(), second.read_bytes())
    inputs = _inputs(("working/images/second.jpg", "working/images/first.jpg"))

    resolved = resolve_vggt_image_assets(
        inputs,
        root,
        {
            "working/images/first.jpg": _sha(before[0]),
            "working/images/second.jpg": _sha(before[1]),
        },
    )

    assert tuple(item.asset_id for item in resolved) == inputs.image_asset_ids
    assert tuple(item.sha256 for item in resolved) == (_sha(before[1]), _sha(before[0]))
    assert "path" not in resolved[0].portable_record()
    assert (first.read_bytes(), second.read_bytes()) == before


def test_image_resolver_rejects_incomplete_index_missing_file_and_digest_mismatch(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    image = root / "working/image.jpg"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"expected-image")
    inputs = _inputs(("working/image.jpg",))

    with pytest.raises(NeuralReconstructionIOError, match="exactly match"):
        resolve_vggt_image_assets(inputs, root, {})
    with pytest.raises(NeuralReconstructionIOError, match="duplicate normalized IDs"):
        resolve_vggt_image_assets(
            inputs,
            root,
            {
                "working/image.jpg": _sha(b"expected-image"),
                "working\\image.jpg": _sha(b"expected-image"),
            },
        )
    with pytest.raises(NeuralReconstructionIOError, match="does not match"):
        resolve_vggt_image_assets(inputs, root, {"working/image.jpg": _sha(b"different")})
    with pytest.raises(NeuralReconstructionIOError, match="unavailable"):
        resolve_vggt_image_assets(
            _inputs(("working/missing.jpg",)),
            root,
            {"working/missing.jpg": _sha(b"missing")},
        )


def test_image_resolver_rejects_file_changed_during_digest_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "project"
    image = root / "working/image.jpg"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"original")
    inputs = _inputs(("working/image.jpg",))
    original_hash = neural_io._file_sha256

    def hash_then_mutate(path: Path) -> str:
        digest = original_hash(path)
        # Change the size: a same-size rewrite within one filesystem timestamp tick is not
        # observable by the size/mtime/inode guard (it flaked on hosted CI). Same-size,
        # same-tick swaps are caught later by the worker's own image re-hash.
        path.write_bytes(b"mutated and longer")
        return digest

    monkeypatch.setattr(neural_io, "_file_sha256", hash_then_mutate)
    with pytest.raises(NeuralReconstructionIOError, match="changed while"):
        resolve_vggt_image_assets(
            inputs,
            root,
            {"working/image.jpg": _sha(b"original")},
        )


def test_image_resolver_rejects_reparse_escape_when_platform_allows_it(tmp_path: Path) -> None:
    root = tmp_path / "project"
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"outside")
    images = root / "working/images"
    images.mkdir(parents=True)
    link = images / "linked.jpg"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable in this Windows environment")

    with pytest.raises(NeuralReconstructionIOError, match="reparse"):
        resolve_vggt_image_assets(
            _inputs(("working/images/linked.jpg",)),
            root,
            {"working/images/linked.jpg": _sha(b"outside")},
        )


def test_camera_conversion_maps_opencv_axes_and_processed_intrinsics() -> None:
    transform = VGGTImagePreprocessTransform(
        source_width=800,
        source_height=400,
        pad_left=0,
        pad_top=200,
        scale=518 / 800,
    )
    camera = normalize_vggt_camera(
        "working/images/a.jpg",
        (1, 0, 0, 1, 0, 1, 0, 2, 0, 0, 1, 3),
        (300, 0, 259, 0, 250, 259, 0, 0, 1),
        transform,
    )

    assert camera.camera_to_world == pytest.approx(
        (1, 0, 0, -1, 0, 1, 0, 2, 0, 0, 1, 3, 0, 0, 0, 1)
    )
    assert camera.intrinsics == pytest.approx(
        (300 / (518 / 800), 0, 399.5, 0, 250 / (518 / 800), 199.5, 0, 0, 1)
    )
    assert normalize_vggt_world_point((1, 2, 3)) == (1, -2, -3)


def test_camera_conversion_rejects_non_rotation_and_invalid_intrinsics() -> None:
    transform = VGGTImagePreprocessTransform(100, 100, 0, 0, 1)
    with pytest.raises(NeuralReconstructionIOError, match="orthonormal"):
        normalize_vggt_camera(
            "working/a.jpg",
            (2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0),
            (50, 0, 50, 0, 50, 50, 0, 0, 1),
            transform,
        )
    with pytest.raises(NeuralReconstructionIOError, match="focal lengths"):
        normalize_vggt_camera(
            "working/a.jpg",
            (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0),
            (0, 0, 50, 0, 50, 50, 0, 0, 1),
            transform,
        )
    with pytest.raises(NeuralReconstructionIOError, match="transform is invalid"):
        VGGTImagePreprocessTransform(100, 100, 0, 0, float("nan"))
    with pytest.raises(NeuralReconstructionIOError, match="three finite values"):
        normalize_vggt_world_point((1, float("inf"), 3))


def test_publish_vggt_artifacts_is_atomic_derived_and_non_authoritative(tmp_path: Path) -> None:
    project = tmp_path / "project"
    runtime = tmp_path / "runtime-output"
    project.mkdir()
    runtime.mkdir()
    source_artifact = runtime / "cloud.ply"
    source_artifact.write_bytes(b"synthetic point cloud")

    published = publish_vggt_artifacts(
        project,
        "r2",
        _manifest(revision="r2"),
        runtime,
        (VGGTOutputArtifact("point_cloud", "point_cloud.ply", source_artifact),),
    )

    assert published.manifest.asset_paths == {
        "point_cloud": "derived/reconstruction/r2/point_cloud.ply"
    }
    assert published.manifest.scale_state is ScaleState.RELATIVE
    assert published.manifest.authority_class == "RECONSTRUCTION_OBSERVATION"
    assert published.manifest.source_input_digest == _sha(b"capture-index")
    assert published.artifact_sha256 == {"point_cloud": _sha(b"synthetic point cloud")}
    assert (published.directory / "point_cloud.ply").read_bytes() == b"synthetic point cloud"
    stored = json.loads(published.manifest_path.read_text(encoding="ascii"))
    assert stored["source_input_digest"] == _sha(b"capture-index")
    assert stored["authority_class"] == "RECONSTRUCTION_OBSERVATION"
    assert str(runtime) not in published.manifest_path.read_text(encoding="ascii")

    with pytest.raises(NeuralReconstructionIOError, match="already exists"):
        publish_vggt_artifacts(
            project,
            "r2",
            _manifest(revision="r2"),
            runtime,
            (VGGTOutputArtifact("point_cloud", "point_cloud.ply", source_artifact),),
        )


def test_publish_removes_only_explicitly_owned_runtime_artifact(tmp_path: Path) -> None:
    project = tmp_path / "project"
    runtime = tmp_path / "runtime-output"
    project.mkdir()
    runtime.mkdir()
    generated = runtime / "generated.ply"
    retained = runtime / "owner-reference.ply"
    generated.write_bytes(b"generated")
    retained.write_bytes(b"owner data")

    publish_vggt_artifacts(
        project,
        "r-owned",
        _manifest(revision="r-owned"),
        runtime,
        (
            VGGTOutputArtifact("generated", "generated.ply", generated, cleanup_after_publish=True),
            VGGTOutputArtifact("reference", "reference.ply", retained),
        ),
    )

    assert not generated.exists()
    assert retained.read_bytes() == b"owner data"


def test_failed_publish_still_removes_explicitly_owned_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    runtime = tmp_path / "runtime-output"
    project.mkdir()
    runtime.mkdir()
    generated = runtime / "generated.ply"
    generated.write_bytes(b"generated")

    def fail_rename(source: Path, destination: Path) -> None:
        raise OSError("synthetic atomic-rename failure")

    monkeypatch.setattr(neural_io.os, "rename", fail_rename)

    with pytest.raises(NeuralReconstructionIOError, match="atomic VGGT output"):
        publish_vggt_artifacts(
            project,
            "r-fail",
            _manifest(revision="r-fail"),
            runtime,
            (
                VGGTOutputArtifact(
                    "generated", "generated.ply", generated, cleanup_after_publish=True
                ),
            ),
        )

    assert not generated.exists()


def test_publish_vggt_artifacts_rejects_unsafe_revision_and_metric_claim(tmp_path: Path) -> None:
    project = tmp_path / "project"
    runtime = tmp_path / "runtime-output"
    project.mkdir()
    runtime.mkdir()
    artifact = runtime / "cloud.ply"
    artifact.write_bytes(b"synthetic")
    item = (VGGTOutputArtifact("cloud", "cloud.ply", artifact),)

    with pytest.raises(NeuralReconstructionIOError, match="revision ID"):
        publish_vggt_artifacts(project, "../escape", _manifest(), runtime, item)
    with pytest.raises(NeuralReconstructionIOError, match="does not match its destination"):
        publish_vggt_artifacts(project, "r3", _manifest(), runtime, item)
    with pytest.raises(NeuralReconstructionIOError, match="portable tokens"):
        publish_vggt_artifacts(
            project,
            "r3",
            _manifest(revision="r3"),
            runtime,
            (VGGTOutputArtifact("cloud", "nested\\cloud.ply", artifact),),
        )
    invalid_manifest = object.__new__(ReconstructionOutputManifest)
    object.__setattr__(invalid_manifest, "backend_id", ReconstructionBackendId.NEURAL_EXPERIMENTAL)
    object.__setattr__(invalid_manifest, "authority_class", "RECONSTRUCTION_OBSERVATION")
    object.__setattr__(invalid_manifest, "scale_state", ScaleState.METRIC_VERIFIED)
    object.__setattr__(invalid_manifest, "asset_paths", {})
    with pytest.raises(NeuralReconstructionIOError, match="authority or scale"):
        publish_vggt_artifacts(project, "r3", invalid_manifest, runtime, item)


def test_publish_vggt_artifacts_cleans_only_its_staging_directory_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    runtime = tmp_path / "runtime-output"
    project.mkdir()
    runtime.mkdir()
    artifact = runtime / "cloud.ply"
    artifact.write_bytes(b"synthetic")

    def fail_rename(source: Path, destination: Path) -> None:
        raise OSError("synthetic atomic-rename failure")

    monkeypatch.setattr(neural_io.os, "rename", fail_rename)
    with pytest.raises(NeuralReconstructionIOError, match="atomic VGGT output"):
        publish_vggt_artifacts(
            project,
            "r4",
            _manifest(revision="r4"),
            runtime,
            (VGGTOutputArtifact("cloud", "cloud.ply", artifact),),
        )

    assert artifact.read_bytes() == b"synthetic"
    assert list((project / "derived/reconstruction").iterdir()) == []
