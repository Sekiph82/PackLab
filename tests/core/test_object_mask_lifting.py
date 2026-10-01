from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from packlab_core.manual_mask_correction import (
    ManualMaskCorrectionService,
    ManualMaskEdit,
    ManualMaskEditAction,
)
from packlab_core.mask_revisions import MaskRevisionService, StaleMaskGeometryError
from packlab_core.object_mask_lifting import (
    PACKLAB_CAMERA_AXES,
    PACKSCAN_CAMERA_TO_WORLD,
    WORLD_TO_CAMERA,
    CameraConventionError,
    LiftCamera,
    LiftVisibilityPolicy,
    ObjectCaptureGeometry,
    ObjectMaskLiftError,
    ObjectMaskLiftingService,
    ObjectMaskLiftRequest,
    WorldPoint,
    validate_camera_convention,
)
from packlab_core.reconstruction import PACKSCAN_CAMERA_CONVENTION, ScaleState
from packlab_core.segmentation import (
    CoordinateTransform,
    InvalidMaskArtifact,
    MaskArtifact,
    MaskRaster,
    PromptEvidence,
    PromptKind,
    SegmentationProvenance,
)

WIDTH = 7
HEIGHT = 5
CREATED_AT = "2026-10-02T00:00:00Z"
RAW_SOURCE = b"synthetic raw capture bytes remain immutable"
SOURCE_INPUT_DIGEST = hashlib.sha256(RAW_SOURCE).hexdigest()
IDENTITY: tuple[float, ...] = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


def _mask(index: int, *, center_foreground: bool) -> MaskArtifact:
    values = [False] * (WIDTH * HEIGHT)
    if center_foreground:
        values[2 * WIDTH + 3] = True
    raster = MaskRaster(WIDTH, HEIGHT, tuple(values))
    source_id = f"raw/images/view-{index:02d}.png"
    source_digest = hashlib.sha256(f"public synthetic image {index}".encode()).hexdigest()
    return MaskArtifact(
        artifact_id=f"mask-artifact-{index:02d}",
        source_image_asset_id=source_id,
        source_digest=source_digest,
        source_width=WIDTH,
        source_height=HEIGHT,
        mask_asset_id=f"working/masks/view-{index:02d}.mask",
        mask_digest=raster.digest,
        mask_width=WIDTH,
        mask_height=HEIGHT,
        transform=CoordinateTransform(WIDTH, HEIGHT, WIDTH, HEIGHT),
        provenance=SegmentationProvenance(
            "synthetic-backend",
            "1",
            "synthetic-model",
            "1",
            "synthetic-checkpoint",
            hashlib.sha256(b"synthetic-checkpoint").hexdigest(),
            "synthetic-runtime",
            "1",
            "tests/fixtures/licenses/synthetic.txt",
        ),
        prompt=PromptEvidence(PromptKind.AUTOMATIC),
        mask_revision=f"mask-revision-{index:02d}",
        created_at=CREATED_AT,
        post_processing_version="fixture:raw",
        raster=raster,
    )


def _fixture(
    *,
    reverse: bool = False,
    cameras: tuple[LiftCamera, ...] | None = None,
    points: tuple[WorldPoint, ...] | None = None,
    scale_state: ScaleState = ScaleState.RELATIVE,
) -> tuple[ObjectMaskLiftRequest, tuple[MaskArtifact, ...], bytearray]:
    masks = tuple(_mask(index, center_foreground=index < 7) for index in range(10))
    revision = MaskRevisionService().publish_initial(
        project_id="project-1",
        source_revision="source-rev-1",
        masks=masks,
        created_at=CREATED_AT,
    )
    camera_values = tuple(
        LiftCamera(
            camera_id=f"camera-{index:02d}",
            source_image_asset_id=mask.source_image_asset_id,
            source_digest=mask.source_digest,
            image_width=WIDTH,
            image_height=HEIGHT,
            intrinsics=(1.0, 1.0, 3.0, 2.0),
            pose_matrix=IDENTITY,
            pose_convention=WORLD_TO_CAMERA,
            camera_axis_convention=PACKLAB_CAMERA_AXES,
            mask_artifact_id=mask.artifact_id,
        )
        for index, mask in enumerate(masks)
    )
    point_values = (
        WorldPoint("front", (0.0, 0.0, 2.0)),
        WorldPoint("outside-mask", (2.0, 0.0, 2.0)),
        WorldPoint("rear-occluded", (0.0, 0.0, 4.0)),
        WorldPoint("behind", (0.0, 0.0, -2.0)),
        WorldPoint("outside-frame", (100.0, 0.0, 2.0)),
    )
    source_bytes = bytearray(RAW_SOURCE)
    request = ObjectMaskLiftRequest(
        project_id="project-1",
        source_revision="source-rev-1",
        source_input_digest=SOURCE_INPUT_DIGEST,
        reconstruction_revision="reconstruction-r1",
        camera_solution_revision="camera-solution-r1",
        mask_set=revision,
        cameras=cameras if cameras is not None else camera_values,
        points=points if points is not None else point_values,
        scale_state=scale_state,
        created_at=CREATED_AT,
    )
    if reverse:
        request = replace(
            request,
            cameras=tuple(reversed(request.cameras)),
            points=tuple(reversed(request.points)),
        )
    return request, masks, source_bytes


def _lift(request: ObjectMaskLiftRequest) -> ObjectCaptureGeometry:
    return ObjectMaskLiftingService().lift(request)


def test_known_point_camera_gate_supports_only_explicit_conventions() -> None:
    for axes in (PACKLAB_CAMERA_AXES, PACKSCAN_CAMERA_CONVENTION):
        for pose in (WORLD_TO_CAMERA, PACKSCAN_CAMERA_TO_WORLD):
            validate_camera_convention(axes, pose)
    with pytest.raises(CameraConventionError, match="no guessing"):
        validate_camera_convention("unknown-camera-axes", WORLD_TO_CAMERA)


def test_duplicate_source_view_rejected_as_ambiguous() -> None:
    request, _masks, _source = _fixture()
    cameras = list(request.cameras)
    cameras[1] = replace(
        cameras[1],
        source_image_asset_id=cameras[0].source_image_asset_id,
        source_digest=cameras[0].source_digest,
    )
    with pytest.raises(ObjectMaskLiftError, match="unique source image"):
        replace(request, cameras=tuple(cameras))


def test_multiview_votes_visibility_and_bounded_output_are_deterministic() -> None:
    request, _masks, source_bytes = _fixture()
    before = bytes(source_bytes)
    first = _lift(request)
    second = _lift(
        replace(
            request,
            cameras=tuple(reversed(request.cameras)),
            points=tuple(reversed(request.points)),
        )
    )
    later = _lift(replace(request, created_at="2026-10-03T00:00:00Z"))
    votes = {item.point_id: item for item in first.point_votes}

    assert first.geometry_id == second.geometry_id
    assert first.geometry_id == later.geometry_id
    assert first.as_dict() == second.as_dict()
    assert votes["front"].support_views == 7
    assert votes["front"].reject_views == 3
    assert votes["front"].support_ratio == 0.7
    assert votes["front"].selected is True
    assert votes["outside-mask"].reject_views == 10
    assert votes["outside-mask"].selected is False
    assert votes["rear-occluded"].observed_views == 0
    assert votes["rear-occluded"].occluded_views == 10
    assert votes["rear-occluded"].reject_views == 0
    assert votes["behind"].behind_camera_views == 10
    assert votes["outside-frame"].out_of_frame_views == 10
    assert first.candidate_count == 5
    assert first.point_count == 1
    assert first.unfiltered_points == first.filtered_points == ((0.0, 0.0, 2.0),)
    assert first.generated is False
    assert first.authority_class == "OBJECT_CAPTURE_GEOMETRY"
    assert first.scale_state is ScaleState.RELATIVE
    assert first.obb is not None and first.obb.method == "pca-preliminary-qa-only"
    assert first.as_dict()["parents"]["mask_set_revision_id"] == request.mask_set.revision_id  # type: ignore[index]
    assert len(first.source_mask_artifacts) == 10
    assert bytes(source_bytes) == before == RAW_SOURCE


def test_camera_to_world_translation_normalizes_to_same_visible_projection() -> None:
    request, _masks, _source = _fixture()
    translated = tuple(1 if index == 3 else value for index, value in enumerate(IDENTITY))
    cameras = tuple(
        replace(
            camera,
            pose_matrix=translated,
            pose_convention=PACKSCAN_CAMERA_TO_WORLD,
            camera_axis_convention=PACKSCAN_CAMERA_CONVENTION,
        )
        for camera in request.cameras
    )
    point = WorldPoint("translated-camera-center", (1.0, 0.0, -2.0))
    translated_request = replace(request, cameras=cameras, points=(point,))
    output = _lift(translated_request)
    assert output.point_count == 1
    assert output.camera_conventions[0][1:] == (
        PACKSCAN_CAMERA_TO_WORLD,
        PACKSCAN_CAMERA_CONVENTION,
    )


def test_threshold_boundary_is_inclusive_and_profile_change_invalidates() -> None:
    request, _masks, _source = _fixture()
    geometry = _lift(request)
    vote = next(item for item in geometry.point_votes if item.point_id == "front")
    assert vote.support_ratio == geometry.threshold_profile.minimum_support_ratio
    assert vote.selected

    stricter = replace(geometry.threshold_profile, minimum_support_ratio=0.700001)
    with pytest.raises(StaleMaskGeometryError, match="stale"):
        geometry.require_current_dependencies(
            current_reconstruction_revision=geometry.reconstruction_revision,
            current_camera_solution_revision=geometry.camera_solution_revision,
            current_source_revision=geometry.source_revision,
            current_source_input_digest=geometry.source_input_digest,
            current_source_images=geometry.source_images,
            current_source_mask_artifacts=geometry.source_mask_artifacts,
            current_camera_conventions=geometry.camera_conventions,
            current_camera_evidence=geometry.camera_evidence,
            current_mask_set=request.mask_set,
            current_projection_convention=geometry.projection_convention,
            current_projection_version=geometry.projection_version,
            current_threshold_profile=stricter,
            current_visibility_policy=geometry.visibility_policy,
        )


def test_mask_reconstruction_camera_and_source_changes_invalidate_geometry() -> None:
    request, masks, _source = _fixture()
    geometry = _lift(request)
    common = {
        "current_reconstruction_revision": geometry.reconstruction_revision,
        "current_camera_solution_revision": geometry.camera_solution_revision,
        "current_source_revision": geometry.source_revision,
        "current_source_input_digest": geometry.source_input_digest,
        "current_source_images": geometry.source_images,
        "current_source_mask_artifacts": geometry.source_mask_artifacts,
        "current_camera_conventions": geometry.camera_conventions,
        "current_camera_evidence": geometry.camera_evidence,
        "current_mask_set": request.mask_set,
        "current_projection_convention": geometry.projection_convention,
        "current_projection_version": geometry.projection_version,
        "current_threshold_profile": geometry.threshold_profile,
        "current_visibility_policy": geometry.visibility_policy,
    }
    geometry.require_current_dependencies(**common)
    changed_camera_matrix = list(geometry.camera_evidence[0].normalized_world_to_camera)
    changed_camera_matrix[3] = 1.0
    changed_camera_evidence = (
        replace(
            geometry.camera_evidence[0],
            normalized_world_to_camera=tuple(changed_camera_matrix),
        ),
        *geometry.camera_evidence[1:],
    )
    for change in (
        {"current_reconstruction_revision": "reconstruction-r2"},
        {"current_camera_solution_revision": "camera-solution-r2"},
        {"current_source_revision": "source-rev-2"},
        {"current_source_input_digest": "0" * 64},
        {"current_source_images": ()},
        {"current_source_mask_artifacts": ()},
        {"current_camera_conventions": ()},
        {"current_camera_evidence": changed_camera_evidence},
        {"current_projection_convention": "other-projection"},
        {"current_projection_version": "2.0.0"},
        {"current_visibility_policy": LiftVisibilityPolicy(tolerance=0.2)},
    ):
        with pytest.raises(StaleMaskGeometryError, match="stale"):
            geometry.require_current_dependencies(**(common | change))

    revision_service = MaskRevisionService()
    parent_set = revision_service.publish_initial(
        project_id="project-1",
        source_revision="source-rev-1",
        masks=masks,
        created_at=CREATED_AT,
    )
    corrected = ManualMaskCorrectionService().correct(
        masks[0],
        editor_id="operator:fixture",
        operations=(ManualMaskEdit(0, 0, ManualMaskEditAction.PAINT),),
        created_at=CREATED_AT,
    )
    new_set = revision_service.publish_child(
        parent_set,
        replacements={masks[0].artifact_id: corrected},
        created_at=CREATED_AT,
    )
    with pytest.raises(StaleMaskGeometryError, match="stale"):
        geometry.require_current_dependencies(**(common | {"current_mask_set": new_set}))


def test_invalid_mask_digest_and_pre_m09_metric_claim_fail_closed() -> None:
    request, _masks, _source = _fixture()
    with pytest.raises(ObjectMaskLiftError, match="METRIC_VERIFIED"):
        replace(request, scale_state=ScaleState.METRIC_VERIFIED)
    masks = list(request.mask_set.masks)
    masks[0] = replace(masks[0], raster=MaskRaster(WIDTH, HEIGHT, tuple([True] * (WIDTH * HEIGHT))))
    bad_set = replace(request.mask_set, masks=tuple(masks), revision_digest="")
    with pytest.raises(InvalidMaskArtifact, match="digest"):
        _lift(replace(request, mask_set=bad_set))


@pytest.mark.parametrize(
    "coordinate",
    [
        pytest.param((True, 0.0, 1.0), id="bool-coordinate"),
        pytest.param((0.0, 0.0, float("nan")), id="non-finite-coordinate"),
    ],
)
def test_malformed_world_point_rejected(coordinate) -> None:
    with pytest.raises(ObjectMaskLiftError, match="finite 3D"):
        WorldPoint("bad-point", coordinate)
