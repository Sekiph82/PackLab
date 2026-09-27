from __future__ import annotations

import hashlib
import json

import pytest

from packlab_core.reconstruction import ReconstructionStageResult, StageStatus
from packlab_core.sparse_export import (
    COLMAP_CAMERA_CONVENTION,
    InvalidSparseExportPayload,
    SparseExportCamera,
    SparseExportImage,
    SparseExportOptions,
    SparseExportPayload,
    SparseExportPoint2D,
    SparseExportPoint3D,
    SparseExportTrack,
    UnsupportedSparseExportOption,
    export_sparse_mapping,
)
from packlab_core.sparse_mapping import (
    STAGE_SUMMARY_CONTRACT,
    SparseMappingRequest,
    normalize_sparse_mapping_result,
)

_SOURCE_DIGEST = hashlib.sha256(b"packscan").hexdigest()
_MATCHER_DIGEST = hashlib.sha256(b"matcher").hexdigest()


def _request() -> SparseMappingRequest:
    return SparseMappingRequest(
        ("working/images/001.jpg", "working/images/002.jpg"),
        "working-revision-1",
        _SOURCE_DIGEST,
        _MATCHER_DIGEST,
    )


def _run() -> object:
    request = _request()
    summary = {
        "contract": STAGE_SUMMARY_CONTRACT,
        "total_images": 2,
        "registered_images": 2,
        "unregistered_images": 0,
        "registration_ratio": 1.0,
        "sparse_model_asset_id": "working/reconstruction/sparse",
    }
    stage = ReconstructionStageResult(
        "sparse-mapping",
        StageStatus.SUCCEEDED,
        0,
        0.1,
        stdout="PACKLAB_SPARSE_MAPPING_SUMMARY_V1 " + json.dumps(summary),
    )
    return normalize_sparse_mapping_result(request, stage)


def _payload(**overrides: object) -> SparseExportPayload:
    request = _request()
    point = SparseExportPoint3D(
        point3d_id=2,
        xyz=(1.0, 2.0, 3.0),
        rgb=(255, 1, 0),
        error=0.25,
        track=(SparseExportTrack(1, 0), SparseExportTrack(2, 0)),
    )
    payload: dict[str, object] = {
        "source_revision": request.source_revision,
        "source_digest": request.source_digest,
        "request_digest": request.request_digest(),
        "output_asset_id": "working/reconstruction/sparse",
        "engine_id": "colmap",
        "engine_version": "3.12.6",
        "camera_convention": COLMAP_CAMERA_CONVENTION,
        "cameras": (SparseExportCamera(7, "PINHOLE", 1920, 1080, (1000.0, 1001.0, 960.0, 540.0)),),
        "images": (
            SparseExportImage(
                2,
                7,
                "working/images/002.jpg",
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 0.0, 2.0),
                (SparseExportPoint2D(20.0, 30.0, 2),),
            ),
            SparseExportImage(
                1,
                7,
                "working/images/001.jpg",
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
                (SparseExportPoint2D(10.0, 15.0, 2),),
            ),
        ),
        "points3d": (point,),
    }
    payload.update(overrides)
    return SparseExportPayload(**payload)  # type: ignore[arg-type]


def test_valid_export_is_deterministic_sorted_and_utf8() -> None:
    run = _run()
    payload = _payload()

    first = export_sparse_mapping(run, payload)
    second = export_sparse_mapping(run, payload)

    assert first.files == second.files
    assert first.names == ("cameras.txt", "images.txt", "points3D.txt", "debug_manifest.json")
    assert "7 PINHOLE 1920 1080 1000 1001 960 540" in first.content("cameras.txt")
    images = first.content("images.txt")
    assert "1 1 0 0 0 0 0 1 7 working/images/001.jpg" in images
    assert "2 1 0 0 0 0 0 2 7 working/images/002.jpg" in images
    assert images.index("working/images/001.jpg") < images.index("working/images/002.jpg")
    assert "2 1 2 3 255 1 0 0.25 1 0 2 0" in first.content("points3D.txt")
    assert all(content.encode("utf-8") for content in first.files.values())


def test_manifest_is_machine_readable_and_does_not_claim_authority() -> None:
    manifest = json.loads(export_sparse_mapping(_run(), _payload()).content("debug_manifest.json"))

    assert manifest["contract"] == "packlab.sparse-export-debug-manifest.v1"
    assert manifest["export_contract"] == "packlab.sparse-export.v1"
    assert manifest["engine"] == {"id": "colmap", "version": "3.12.6"}
    assert manifest["camera_convention"] == COLMAP_CAMERA_CONVENTION
    assert manifest["record_counts"] == {"cameras": 1, "images": 2, "points3d": 1, "tracks": 2}
    limitations = " ".join(manifest["limitations"])
    assert "filesystem materialization" in limitations
    assert "metric calibration" in limitations
    assert "OpenMVS conversion" in limitations
    assert "CAD authority" in limitations
    assert "stdout" not in json.dumps(manifest)
    assert "stderr" not in json.dumps(manifest)


def test_payload_and_bundle_are_immutable_and_export_does_not_mutate_run() -> None:
    run = _run()
    payload = _payload()
    before = run.as_dict()
    bundle = export_sparse_mapping(run, payload)

    assert run.as_dict() == before
    with pytest.raises((AttributeError, TypeError)):
        payload.output_asset_id = "other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        bundle.files["extra.txt"] = "unsafe"  # type: ignore[index]


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_digest", "not-a-digest"),
        ("source_revision", "../private"),
        ("output_asset_id", "C:/private/sparse"),
        ("camera_convention", "unknown-third-party-convention"),
    ],
)
def test_provenance_and_convention_are_explicitly_bound(field: str, value: object) -> None:
    if field == "camera_convention":
        payload = _payload(camera_convention=value)
        with pytest.raises(UnsupportedSparseExportOption):
            export_sparse_mapping(_run(), payload)
        return
    with pytest.raises(InvalidSparseExportPayload):
        _payload(**{field: value})


@pytest.mark.parametrize(
    "override",
    [
        {"source_revision": "other-revision"},
        {"source_digest": hashlib.sha256(b"other").hexdigest()},
        {"request_digest": hashlib.sha256(b"other-request").hexdigest()},
        {"output_asset_id": "working/reconstruction/other"},
        {"engine_id": "openmvs"},
        {"engine_version": "2.4.0"},
    ],
)
def test_payload_provenance_mismatch_fails_closed(override: dict[str, object]) -> None:
    with pytest.raises(InvalidSparseExportPayload):
        export_sparse_mapping(_run(), _payload(**override))


def test_failed_run_and_unsupported_options_never_export() -> None:
    request = _request()
    failed = normalize_sparse_mapping_result(
        request,
        ReconstructionStageResult("sparse-mapping", StageStatus.FAILED, 7, 0.1),
    )

    with pytest.raises(ValueError, match="successful"):
        export_sparse_mapping(failed, _payload())  # type: ignore[arg-type]
    with pytest.raises(UnsupportedSparseExportOption):
        export_sparse_mapping(_run(), _payload(), SparseExportOptions(include_debug_manifest=False))
    with pytest.raises(UnsupportedSparseExportOption):
        export_sparse_mapping(_run(), _payload(), object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "factory",
    [
        lambda: SparseExportCamera(1, "UNKNOWN", 1, 1, (1.0,)),
        lambda: SparseExportCamera(1, "PINHOLE", 1, 1, (1.0, 1.0, 0.0)),
        lambda: SparseExportCamera(1, "PINHOLE", 1, 1, (1.0, 1.0, 0.0, float("inf"))),
        lambda: SparseExportImage(1, 1, "../private.jpg", (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        lambda: SparseExportPoint2D(float("nan"), 1.0),
        lambda: SparseExportPoint3D(
            1, (0.0, 0.0, 0.0), (0, 256, 0), 0.0, (SparseExportTrack(1, 0),)
        ),
        lambda: SparseExportPoint3D(
            1, (0.0, 0.0, 0.0), (0, 0, 0), -1.0, (SparseExportTrack(1, 0),)
        ),
    ],
)
def test_records_reject_invalid_numeric_models_and_names(factory: object) -> None:
    with pytest.raises(ValueError):
        factory()  # type: ignore[operator]


@pytest.mark.parametrize(
    "override",
    [
        {"images": (_payload().images[0], _payload().images[0])},
        {
            "images": (
                SparseExportImage(
                    1,
                    999,
                    "working/images/001.jpg",
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0),
                    (SparseExportPoint2D(1.0, 1.0, 2),),
                ),
            )
        },
        {
            "points3d": (
                SparseExportPoint3D(
                    2, (1.0, 2.0, 3.0), (255, 1, 0), 0.25, (SparseExportTrack(1, 1),)
                ),
            )
        },
        {
            "points3d": (
                SparseExportPoint3D(
                    2, (1.0, 2.0, 3.0), (255, 1, 0), 0.25, (SparseExportTrack(1, 0),)
                ),
            )
        },
    ],
)
def test_payload_rejects_duplicate_or_dangling_cross_references(
    override: dict[str, object],
) -> None:
    payload = _payload(**override)
    with pytest.raises(InvalidSparseExportPayload):
        export_sparse_mapping(_run(), payload)


def test_image_records_always_have_the_required_two_line_shape() -> None:
    payload = _payload(
        images=(
            SparseExportImage(
                1,
                7,
                "working/images/001.jpg",
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (),
            ),
            SparseExportImage(
                2,
                7,
                "working/images/002.jpg",
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (),
            ),
        ),
        points3d=(),
    )
    lines = payload  # construction itself is explicit; empty sparse points are allowed
    assert len(export_sparse_mapping(_run(), lines).content("images.txt").splitlines()) == 7
