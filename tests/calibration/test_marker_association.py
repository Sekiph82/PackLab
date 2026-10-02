from __future__ import annotations

import hashlib
import json

import pytest

from packlab_core.calibration import (
    CameraImageBinding,
    MarkerAssociationError,
    associate_marker_detections,
    associated_observations_digest,
    detect_markers,
    serialize_associated_observations,
)
from packlab_core.calibration.marker_detection import DetectionBatch, MarkerObservation

IMAGE_ID = "raw/images/synthetic-view.png"
IMAGE_BYTES = b"synthetic immutable image bytes"
IMAGE_DIGEST = hashlib.sha256(IMAGE_BYTES).hexdigest()
REVISION = "camera-solution-r17"
WIDTH = 640
HEIGHT = 480


def _binding(**changes: object) -> CameraImageBinding:
    values: dict[str, object] = {
        "camera_id": "camera-17",
        "source_image_asset_id": IMAGE_ID,
        "source_digest": IMAGE_DIGEST,
        "image_width": WIDTH,
        "image_height": HEIGHT,
        "camera_solution_revision": REVISION,
    }
    values.update(changes)
    return CameraImageBinding(**values)  # type: ignore[arg-type]


def _batch() -> DetectionBatch:
    observation = MarkerObservation(
        marker_id=4,
        corners_px=((11.5, 12.0), (32.0, 12.5), (31.0, 33.0), (10.0, 32.0)),
        quality={"quality_label": "detected_geometry", "quality_score": 0.75},
        provenance={"detector": "opencv.aruco", "coordinate_unit": "image_pixels"},
    )
    return DetectionBatch("detected", (observation,), (), {"detector": "opencv.aruco"})


def _associate(cameras: tuple[CameraImageBinding, ...] | None = None):
    return associate_marker_detections(
        _batch(),
        source_image_asset_id=IMAGE_ID,
        source_digest=IMAGE_DIGEST,
        image_width=WIDTH,
        image_height=HEIGHT,
        camera_solution_revision=REVISION,
        cameras=(_binding(),) if cameras is None else cameras,
    )


def test_synthetic_marker_binds_to_exact_source_camera_without_scale_claim() -> None:
    result = _associate()
    assert len(result) == 1
    item = result[0]
    assert (item.camera_id, item.camera_solution_revision) == ("camera-17", REVISION)
    assert item.source_image_asset_id == IMAGE_ID
    assert item.source_digest == IMAGE_DIGEST
    assert item.corners_px == _batch().observations[0].corners_px
    assert item.detector_provenance == _batch().observations[0].provenance
    assert "mm" not in json.dumps(item.as_dict()).lower()


def test_duplicate_or_missing_camera_identity_fails_closed() -> None:
    with pytest.raises(MarkerAssociationError, match="duplicate_camera_identity"):
        _associate((_binding(), _binding()))
    with pytest.raises(MarkerAssociationError, match="missing_for_source_image"):
        _associate((_binding(source_image_asset_id="raw/images/other.png"),))


def test_ambiguous_source_binding_stale_revision_and_dimensions_fail_closed() -> None:
    with pytest.raises(MarkerAssociationError, match="ambiguous_camera_identity"):
        _associate((_binding(), _binding(camera_id="camera-18")))
    with pytest.raises(MarkerAssociationError, match="stale_camera_solution_revision"):
        _associate((_binding(camera_solution_revision="camera-solution-old"),))
    with pytest.raises(MarkerAssociationError, match="dimensions_mismatch"):
        _associate((_binding(image_width=WIDTH + 1),))


def test_source_digest_mismatch_is_rejected() -> None:
    with pytest.raises(MarkerAssociationError, match="source_digest_mismatch"):
        _associate((_binding(source_digest="0" * 64),))


def test_duplicate_detector_observation_ids_are_rejected() -> None:
    batch = _batch()
    duplicate = DetectionBatch("detected", batch.observations * 2, (), batch.provenance)
    with pytest.raises(MarkerAssociationError, match="duplicate_marker_id"):
        associate_marker_detections(
            duplicate,
            source_image_asset_id=IMAGE_ID,
            source_digest=IMAGE_DIGEST,
            image_width=WIDTH,
            image_height=HEIGHT,
            camera_solution_revision=REVISION,
            cameras=(_binding(),),
        )


def test_corner_order_coordinates_and_detector_provenance_are_preserved() -> None:
    item = _associate()[0]
    assert item.corners_px == ((11.5, 12.0), (32.0, 12.5), (31.0, 33.0), (10.0, 32.0))
    assert item.detector_provenance["coordinate_unit"] == "image_pixels"


def test_association_serialization_and_digest_are_deterministic() -> None:
    first = _associate()
    second = _associate()
    assert serialize_associated_observations(first) == serialize_associated_observations(second)
    assert associated_observations_digest(first) == associated_observations_digest(second)


def test_unavailable_opencv_detection_is_not_promoted_to_an_observation() -> None:
    import builtins

    original_import = builtins.__import__

    def unavailable_import(name: str, *args: object, **kwargs: object):
        if name == "cv2":
            raise ImportError("synthetic OpenCV unavailable")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = unavailable_import
    try:

        class FakeImage:
            shape = (8, 8)
            dtype = "uint8"

        unavailable = detect_markers(FakeImage())
    finally:
        builtins.__import__ = original_import

    assert unavailable.status == "unavailable"
    assert unavailable.errors == ("opencv_unavailable",)
    assert (
        associate_marker_detections(
            unavailable,
            source_image_asset_id=IMAGE_ID,
            source_digest=IMAGE_DIGEST,
            image_width=WIDTH,
            image_height=HEIGHT,
            camera_solution_revision=REVISION,
            cameras=(_binding(),),
        )
        == ()
    )


def test_source_bytes_are_unchanged_by_detection_and_association() -> None:
    np = pytest.importorskip("numpy")
    before = IMAGE_BYTES
    image = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    image_before = image.copy()

    batch = detect_markers(image)
    if batch.status == "detected":
        associate_marker_detections(
            batch,
            source_image_asset_id=IMAGE_ID,
            source_digest=IMAGE_DIGEST,
            image_width=WIDTH,
            image_height=HEIGHT,
            camera_solution_revision=REVISION,
            cameras=(_binding(),),
        )
    assert IMAGE_BYTES == before
    assert np.array_equal(image, image_before)
