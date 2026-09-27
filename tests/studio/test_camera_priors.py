from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from packlab_core.packscan import write_packscan
from packlab_core.reconstruction import (
    CameraPriorUse,
    ReconstructionInputSet,
    assess_camera_priors,
)
from packlab_studio.project import ProjectManager
from packlab_studio.reconstruction_workspace import ReconstructionWorkspaceError

MODEL = "iPhone 16 Standard"
LENS = "main-wide"
CONVENTION = "packscan_right_handed_x_right_y_up_z_out_of_screen_camera_forward_neg_z_v3"


def _photos(dimensions: tuple[int, int] = (4032, 3024)) -> bytes:
    records = []
    for index in range(1, 3):
        records.append(
            {
                "photo_id": f"photo-{index:04d}",
                "image_path": f"images/{index:04d}.jpg",
                "sequence": index - 1,
                "original_filename": f"IMG_{index:04d}.JPG",
                "pixel_dimensions": {"width": dimensions[0], "height": dimensions[1]},
                "orientation": {"value": "landscape", "rotation_degrees": 0, "source": "exif"},
                "focal_length_mm": {"status": "unavailable"},
                "exposure": {"status": "unavailable"},
                "iso": {"status": "unavailable"},
                "white_balance_kelvin": {"status": "unavailable"},
            }
        )
    return json.dumps({"schema_version": "1.0.0", "photos": records}, separators=(",", ":")).encode()


def _intrinsics(
    *,
    dimensions: tuple[int, int] = (4032, 3024),
    reference: tuple[int, int] = (4032, 3024),
    policy: str = "exact_reference_only",
    lens: str = LENS,
    model: str = MODEL,
) -> bytes:
    return json.dumps(
        {
            "schema_version": "1.0.0",
            "status": "measured",
            "lens": {"device_model": model, "lens_identity": lens, "source": "device_api"},
            "reference_dimensions": {"width": reference[0], "height": reference[1]},
            "target_dimensions": {"width": dimensions[0], "height": dimensions[1]},
            "pixel_coordinate_origin": "top_left_pixel_center",
            "matrix_convention": "row_major_3x3_homogeneous",
            "dimension_policy": policy,
            "intrinsic_matrix": [[2000.0, 0.0, reference[0] / 2], [0.0, 2000.0, reference[1] / 2], [0.0, 0.0, 1.0]],
            "distortion": {
                "model": "none",
                "coefficient_order_version": "none_v1",
                "coefficient_order": [],
                "coefficients": [],
            },
            "provenance": {
                "source": "dedicated_calibration",
                "recorded_at": "2026-09-22T09:00:00Z",
                "calibration_id": "calibration/test-0001",
            },
        },
        separators=(",", ":"),
    ).encode()


def _pose(*, convention: str = CONVENTION, translation_unit: str = "metres") -> bytes:
    return json.dumps(
        {
            "schema_version": "1.0.0",
            "timestamp": "2026-09-22T09:00:00Z",
            "timestamp_domain": "utc",
            "status": "available",
            "tracking_state": "normal",
            "confidence": 0.98,
            "camera_to_world_matrix": [[1, 0, 0, 1], [0, 1, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]],
            "world_to_camera_matrix": [[1, 0, 0, -1], [0, 1, 0, -2], [0, 0, 1, -3], [0, 0, 0, 1]],
            "camera_to_world_quaternion": {"order": "xyzw", "x": 0, "y": 0, "z": 0, "w": 1},
            "coordinate_convention": convention,
            "basis_conversion": "arkit_to_packscan_identity_shared_right_handed_basis_v1",
            "translation_unit": translation_unit,
            "provenance": {"source": "ARKit", "source_version": "6.0"},
        },
        separators=(",", ":"),
    ).encode()


def _package(
    repo_root: Path,
    destination: Path,
    *,
    dimensions: tuple[int, int] = (4032, 3024),
    reference: tuple[int, int] = (4032, 3024),
    policy: str = "exact_reference_only",
    include_intrinsics: bool = True,
    intrinsic_bytes: bytes | None = None,
    pose_bytes: bytes | None = None,
) -> Path:
    manifest = json.loads(
        (repo_root / "tests" / "fixtures" / "packscan" / "manifest-valid.json").read_text(
            encoding="utf-8"
        )
    )
    manifest["capture_id"] = "camera-prior-capture"
    manifest["device"]["lens"] = LENS
    payloads = {
        "images/0001.jpg": b"IMAGE-0001",
        "images/0002.jpg": b"IMAGE-0002",
        "metadata/photos.json": _photos(dimensions),
    }
    if include_intrinsics:
        payloads["metadata/intrinsics/photo-0001.json"] = intrinsic_bytes or _intrinsics(
            dimensions=dimensions, reference=reference, policy=policy
        )
        payloads["metadata/intrinsics/photo-0002.json"] = _intrinsics(
            dimensions=dimensions, reference=reference, policy=policy
        )
    if pose_bytes is not None:
        payloads["metadata/poses/photo-0001.json"] = pose_bytes
    manifest["payloads"] = [
        {
            "path": path,
            "kind": "photo_metadata" if path == "metadata/photos.json" else "image" if path.startswith("images/") else "calibration",
            "required": True,
            "authority": "source",
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "media_type": "application/json" if path.startswith("metadata/") else "image/jpeg",
        }
        for path, data in payloads.items()
    ]
    return write_packscan(destination, manifest, payloads)


def _prepared(tmp_path: Path, repo_root: Path, **kwargs):
    package = _package(repo_root, tmp_path / "capture.packscan", **kwargs)
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Camera Priors")
    assert manager.layout is not None
    raw = manager.layout.path("raw", "capture.packscan")
    raw.write_bytes(package.read_bytes())
    source_id = "raw/capture.packscan"
    workspace = manager.create_reconstruction_workspace(
        source_id, hashlib.sha256(raw.read_bytes()).hexdigest(), revision_id="prior-r1"
    )
    working_set = manager.materialize_reconstruction_working_set(workspace)
    return manager, workspace, working_set, raw.read_bytes()


def test_import_camera_priors_maps_metadata_to_exact_working_images_and_preserves_raw(
    tmp_path: Path, repo_root: Path
) -> None:
    manager, workspace, working_set, raw_before = _prepared(
        tmp_path, repo_root, pose_bytes=_pose()
    )

    assessment = manager.import_reconstruction_camera_priors(workspace)

    first, second = assessment.priors
    assert first.valid
    assert first.image_asset_id == working_set.images[0].working_asset_id
    assert first.source_image_asset_id == "images/0001.jpg"
    assert first.source_digest == working_set.inputs.source_digest
    assert first.source_revision == "prior-r1"
    assert first.intrinsics == (2000.0, 0.0, 2016.0, 0.0, 2000.0, 1512.0, 0.0, 0.0, 1.0)
    assert first.pose == (1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 2.0, 0.0, 0.0, 1.0, 3.0, 0.0, 0.0, 0.0, 1.0)
    assert first.camera_convention == CONVENTION
    assert first.pose_unit == "metres"
    assert first.policy_version == "packlab_camera_prior_policy_v1"
    assert second.pose is None
    assert second.valid
    assert manager.layout.path("raw", "capture.packscan").read_bytes() == raw_before
    assert all(
        (manager.layout.root / image.working_asset_id).read_bytes()
        == (b"IMAGE-0001" if image.order == 0 else b"IMAGE-0002")
        for image in working_set.images
    )


def test_uniform_dimension_policy_normalizes_intrinsics_to_working_image(tmp_path: Path, repo_root: Path) -> None:
    manager, workspace, _working_set, _raw_before = _prepared(
        tmp_path,
        repo_root,
        dimensions=(2016, 1512),
        reference=(4032, 3024),
        policy="uniform_scale_about_origin",
    )

    assessment = manager.import_reconstruction_camera_priors(workspace)

    assert assessment.priors[0].intrinsics == (1000.0, 0.0, 1008.0, 0.0, 1000.0, 756.0, 0.0, 0.0, 1.0)
    assert all(prior.valid for prior in assessment.priors)


@pytest.mark.parametrize(
    "mode",
    list(CameraPriorUse),
)
def test_every_explicit_prior_use_mode_is_preserved(tmp_path: Path, repo_root: Path, mode: CameraPriorUse) -> None:
    manager, workspace, _working_set, _raw_before = _prepared(tmp_path, repo_root)

    assessment = manager.import_reconstruction_camera_priors(workspace, use=mode.value)

    assert assessment.priors[0].use is mode
    if mode is CameraPriorUse.REJECTED:
        assert not assessment.priors[0].valid


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"intrinsic_bytes": _intrinsics(lens="other-lens")}, "lens identity"),
        ({"intrinsic_bytes": _intrinsics(dimensions=(1920, 1080), policy="exact_reference_only")}, "dimensions"),
        ({"intrinsic_bytes": b"not-json"}, "metadata JSON"),
        ({"pose_bytes": _pose(convention="ambiguous")}, "metadata is invalid"),
        ({"pose_bytes": _pose(translation_unit="millimetres")}, "metadata is invalid"),
    ],
)
def test_inconsistent_or_malformed_metadata_is_explicitly_rejected(
    tmp_path: Path, repo_root: Path, kwargs: dict[str, object], reason: str
) -> None:
    parameters = dict(kwargs)
    pose_bytes = parameters.pop("pose_bytes", None)
    manager, workspace, _working_set, _raw_before = _prepared(
        tmp_path, repo_root, pose_bytes=pose_bytes, **parameters
    )

    assessment = manager.import_reconstruction_camera_priors(workspace)

    assert assessment.priors[0].use is CameraPriorUse.REJECTED
    assert any(reason.lower() in warning.lower() for warning in assessment.warnings)


def test_missing_intrinsics_and_changed_working_bytes_fail_closed(tmp_path: Path, repo_root: Path) -> None:
    manager, workspace, working_set, raw_before = _prepared(tmp_path, repo_root, include_intrinsics=False)
    missing = manager.import_reconstruction_camera_priors(workspace)
    assert all(prior.use is CameraPriorUse.REJECTED for prior in missing.priors)

    working_path = manager.layout.root / working_set.images[0].working_asset_id
    working_path.write_bytes(b"changed-owner-bytes")
    with pytest.raises(ReconstructionWorkspaceError, match="working-set image bytes changed"):
        manager.import_reconstruction_camera_priors(workspace)
    assert manager.layout.path("raw", "capture.packscan").read_bytes() == raw_before


def test_prior_revision_and_source_digest_binding_rejects_reuse() -> None:
    inputs = ReconstructionInputSet(
        "project-1",
        "raw/capture.packscan",
        "revision-2",
        hashlib.sha256(b"capture").hexdigest(),
        ("working/revision-2/inputs/images/0001.jpg",),
    )
    prior = _prior_for_binding()
    assessment = assess_camera_priors(inputs, (prior,))
    assert assessment.priors[0].use is CameraPriorUse.REJECTED
    assert "revision mismatch" in assessment.warnings[0]


def _prior_for_binding():
    from packlab_core.reconstruction import CameraPrior

    return CameraPrior(
        "working/revision-2/inputs/images/0001.jpg",
        width=1,
        height=1,
        intrinsics=(1.0, 0.0, 0.5, 0.0, 1.0, 0.5, 0.0, 0.0, 1.0),
        source_digest=hashlib.sha256(b"capture").hexdigest(),
        source_revision="revision-1",
    )
