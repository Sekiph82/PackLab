from __future__ import annotations

import hashlib
import io
import json
import struct
import tarfile
import zlib
from pathlib import Path

import pytest
from tools.datasets.dataset_root import resolve_dataset_root
from tools.datasets.extract_ycb_subset import (
    _copy_or_verify,
    _resolve_dataset_root,
    _safe_name,
    _verified_archive,
    _write_manifest,
)
from tools.datasets.validate_packaging_dataset import validate_manifest
from tools.datasets.validate_ycb_manifest import _regular_file as _regular_ycb_file
from tools.datasets.validate_ycb_manifest import _verify_archive_members
from tools.datasets.ycb_source_identity import YCB_ARCHIVE_IDENTITIES

from packlab_core.benchmark_metrics import (
    compare_synthetic_packaging_sample,
    synthetic_packaging_metric_bands,
)

FAMILIES = ("bottle", "jerrycan", "jar", "closure", "trigger_spray", "pump", "tube", "sachet")
MATERIALS = ("hdpe_matte", "pet_gloss", "pet_clear", "pp_translucent")
TERMS = "PackLab development/CI and owner-controlled design-office and future Kenya-factory use; no external reuse, sublicense, sale or marketing permission"


def _chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def _png(mask: bool = False) -> bytes:
    width, height, color_type = 640, 480, 6
    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    pixel_row = b"".join(
        bytes((255, 255, 255, 255 if not mask or 100 <= x < 540 else 0)) for x in range(width)
    )
    row = b"\x00" + pixel_row
    pixels = zlib.compress(row * height, level=1)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", pixels)
        + _chunk(b"IEND", b"")
    )


@pytest.fixture
def dataset_manifest(tmp_path: Path) -> Path:
    image = _png()
    mask_image = _png(mask=True)
    ply = b"ply\nformat ascii 1.0\ncomment units meters; generated geometry; not physical CAD\nelement vertex 3\nproperty float x\nproperty float y\nproperty float z\nelement face 1\nproperty list uchar int vertex_indices\nend_header\n0 0 0\n0.1 0 0\n0 0.09 0.18\n3 0 1 2\n"
    samples = []
    for family in FAMILIES:
        for material in MATERIALS:
            for view in range(3):
                sample_id = f"syn_{family}_{material}_v{view + 1:02d}"
                metric_bands = synthetic_packaging_metric_bands(
                    nominal_dimensions_mm=(100, 90, 180),
                    mesh_extent_mm=(100, 90, 180),
                    scenario_tolerances_mm=(0.3, 0.6),
                )
                files = {}
                for role in ("rgb", "mask"):
                    rel = f"synthetic/{role}/{sample_id}.png"
                    path = tmp_path / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    payload = image if role == "rgb" else mask_image
                    path.write_bytes(payload)
                    files[role] = {
                        "path": rel,
                        "bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "format": "PNG",
                    }
                geometry_rel = f"synthetic/ground_truth/{sample_id}.ply"
                geometry_path = tmp_path / geometry_rel
                geometry_path.parent.mkdir(parents=True, exist_ok=True)
                geometry_path.write_bytes(ply)
                files["geometry"] = {
                    "path": geometry_rel,
                    "bytes": len(ply),
                    "sha256": hashlib.sha256(ply).hexdigest(),
                    "format": "PLY",
                    "vertices": 3,
                    "faces": 1,
                }
                samples.append(
                    {
                        "id": sample_id,
                        "family": family,
                        "synthetic": True,
                        "source": {"kind": "procedural_blender", "seed": 3692026},
                        "material_appearance": {"finish": material},
                        "dimensions_mm_nominal_simulated": [100, 90, 180],
                        "expected_geometry_extent_mm": [100.0, 90.0, 180.0],
                        "expected_software_metric_bands": {
                            key: {
                                "lower": band.lower,
                                "upper": band.upper,
                                "unit": band.unit,
                                "provenance": band.provenance,
                                "authority": band.authority,
                            }
                            for key, band in metric_bands.items()
                        },
                        "manufacturing_tolerance_mm_simulated": {
                            "each_axis_plus_minus": [0.3, 0.6]
                        },
                        "camera": {
                            "model": "pinhole plus Blender compositor lens distortion",
                            "resolution_px": [640, 480],
                            "focal_length_mm": 50.0,
                            "sensor_mm": [36.0, 27.0],
                            "sensor_fit": "HORIZONTAL",
                            "fx_px": 888.888889,
                            "fy_px": 888.888889,
                            "cx_px": 320,
                            "cy_px": 240,
                            "camera_to_world_row_major": [
                                1,
                                0,
                                0,
                                0,
                                0,
                                1,
                                0,
                                0,
                                0,
                                0,
                                1,
                                0,
                                0,
                                0,
                                0,
                                1,
                            ],
                            "blender_lens_distortion_factor_simulated": 0.0,
                        },
                        "measurement_authority": "synthetic generator inputs only; no physical or Kenya ground truth",
                        "files": files,
                    }
                )
    manifest = {
        "schema_version": "1.0",
        "dataset_id": "packlab-m17-synthetic-packaging-v2",
        "fully_synthetic": True,
        "physical_measurements_present": False,
        "owner_internal_use_scope": TERMS,
        "samples": samples,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_accepts_complete_hash_bound_synthetic_fixture(dataset_manifest: Path) -> None:
    result = validate_manifest(dataset_manifest)
    assert result["sample_count"] == 96
    assert result["families"] == sorted(FAMILIES)
    assert result["materials"] == sorted(MATERIALS)


def test_rejects_truthy_non_boolean_authority(dataset_manifest: Path) -> None:
    document = json.loads(dataset_manifest.read_text(encoding="utf-8"))
    document["fully_synthetic"] = 1
    dataset_manifest.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="exact booleans"):
        validate_manifest(dataset_manifest)


def test_rejects_parent_path_even_if_target_exists(dataset_manifest: Path) -> None:
    document = json.loads(dataset_manifest.read_text(encoding="utf-8"))
    document["samples"][0]["files"]["rgb"]["path"] = "../manifest.json"
    dataset_manifest.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="unsafe sample path"):
        validate_manifest(dataset_manifest)


def test_rejects_file_hash_or_length_drift(dataset_manifest: Path) -> None:
    document = json.loads(dataset_manifest.read_text(encoding="utf-8"))
    document["samples"][0]["files"]["rgb"]["sha256"] = "0" * 64
    dataset_manifest.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        validate_manifest(dataset_manifest)


def test_rejects_incomplete_family_and_ambiguous_json(dataset_manifest: Path) -> None:
    original = dataset_manifest.read_text(encoding="utf-8")
    document = json.loads(original)
    document["samples"].pop()
    dataset_manifest.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected sample count"):
        validate_manifest(dataset_manifest)
    dataset_manifest.write_text('{"schema_version":"1.0","schema_version":"1.0"}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        validate_manifest(dataset_manifest)


def test_rejects_metric_band_drift(dataset_manifest: Path) -> None:
    document = json.loads(dataset_manifest.read_text(encoding="utf-8"))
    document["samples"][0]["expected_software_metric_bands"]["reconstruction_extent_x_mm"][
        "authority"
    ] = "PHYSICAL_MEASUREMENT"
    dataset_manifest.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="authority/provenance"):
        validate_manifest(dataset_manifest)


def test_synthetic_metric_harness_accepts_inclusive_edges(dataset_manifest: Path) -> None:
    document = json.loads(dataset_manifest.read_text(encoding="utf-8"))
    sample = document["samples"][0]
    bands = sample["expected_software_metric_bands"]
    observed = {key: record["lower"] for key, record in bands.items()}
    result = compare_synthetic_packaging_sample(sample, observed)
    assert result.outcome == "PASS"
    assert all(item.authority == "NONPHYSICAL_SOFTWARE_TEST_ONLY" for item in result.results)


def test_synthetic_metric_harness_rejects_missing_unexpected_and_nonfinite(
    dataset_manifest: Path,
) -> None:
    document = json.loads(dataset_manifest.read_text(encoding="utf-8"))
    sample = document["samples"][0]
    bands = sample["expected_software_metric_bands"]
    observed = {key: record["lower"] for key, record in bands.items()}
    with pytest.raises(ValueError, match="metric set mismatch"):
        compare_synthetic_packaging_sample(
            sample, {key: value for key, value in observed.items() if key != "segmentation_iou"}
        )
    with pytest.raises(ValueError, match="metric set mismatch"):
        compare_synthetic_packaging_sample(sample, {**observed, "extra": 0.0})
    observed["segmentation_iou"] = float("nan")
    with pytest.raises(ValueError, match="finite real number"):
        compare_synthetic_packaging_sample(sample, observed)


def test_synthetic_metric_harness_rejects_real_or_ambiguous_authority(
    dataset_manifest: Path,
) -> None:
    document = json.loads(dataset_manifest.read_text(encoding="utf-8"))
    sample = document["samples"][0]
    bands = sample["expected_software_metric_bands"]
    observed = {key: record["lower"] for key, record in bands.items()}
    sample["synthetic"] = False
    with pytest.raises(ValueError, match="only explicitly synthetic"):
        compare_synthetic_packaging_sample(sample, observed)


def test_archive_member_paths_reject_cross_platform_escape_forms() -> None:
    for path in (
        "../escape",
        "pkg/../../escape",
        "..\\escape",
        "C:\\outside",
        "\\\\server\\share\\file",
        "/absolute",
        "pkg/drive:evil",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            _safe_name(path)
    assert _safe_name("006_mustard_bottle/N1_000.jpg").as_posix() == "006_mustard_bottle/N1_000.jpg"


def test_ycb_manifest_paths_reject_cross_platform_escape_forms(tmp_path: Path) -> None:
    for path in (
        "../outside",
        "..\\outside",
        "C:\\outside",
        "\\\\server\\share\\file",
        "pkg/drive:evil",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            _regular_ycb_file(tmp_path, path)


def test_ycb_archive_symlink_is_rejected_before_reading(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    source = root / "source" / "ycb"
    source.mkdir(parents=True)
    outside = tmp_path / "outside.tgz"
    outside.write_bytes(b"outside archive")
    link = source / "006_mustard_bottle_google_16k.tgz"
    try:
        link.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"symlink fixture is unavailable: {error}")

    with pytest.raises(ValueError, match="symlink or junction"):
        _verified_archive(link, root)
    assert outside.read_bytes() == b"outside archive"


def test_ycb_dataset_root_symlink_is_rejected_before_resolution(tmp_path: Path) -> None:
    localappdata = tmp_path / "LocalAppData"
    parent = localappdata / "PackLab" / "datasets"
    parent.mkdir(parents=True)
    outside = tmp_path / "outside-dataset"
    outside.mkdir()
    linked_root = parent / "M17"
    try:
        linked_root.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlink fixture is unavailable: {error}")

    with pytest.raises(ValueError, match="dataset root traverses a symlink or junction"):
        _resolve_dataset_root(linked_root, localappdata)
    with pytest.raises(ValueError, match="dataset root traverses a symlink or junction"):
        resolve_dataset_root(linked_root, localappdata)

    linked_root.unlink()
    linked_root.mkdir()
    intermediate_link = parent / "outside-link"
    try:
        intermediate_link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"intermediate directory symlink fixture is unavailable: {error}")
    aliased = parent / "outside-link" / ".." / "M17"
    with pytest.raises(ValueError, match="dot segments"):
        resolve_dataset_root(aliased, localappdata)


def test_ycb_manifest_symlink_is_never_followed_or_overwritten(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    target = root / "derived" / "ycb"
    target.mkdir(parents=True)
    outside = tmp_path / "owner-file.json"
    outside.write_text("owner bytes", encoding="utf-8")
    manifest = target / "manifest.json"
    try:
        manifest.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"symlink fixture is unavailable: {error}")

    with pytest.raises(ValueError, match="manifest through a link"):
        _write_manifest(manifest, root, '{"dataset_id":"packlab-m17-ycb-real-reference-v1"}\n')
    assert outside.read_text(encoding="utf-8") == "owner bytes"


def test_interrupted_ycb_member_copy_leaves_no_partial_destination(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    destination_root = root / "derived" / "ycb"
    destination_root.mkdir(parents=True)
    destination = destination_root / "frame.jpg"

    class InterruptedReader:
        calls = 0

        def read(self, _size: int) -> bytes:
            self.calls += 1
            if self.calls == 1:
                return b"first chunk"
            raise OSError("simulated interrupted extraction")

    with pytest.raises(OSError, match="simulated interrupted extraction"):
        _copy_or_verify(InterruptedReader(), destination, 99, root)
    assert not destination.exists()
    assert not list(destination_root.glob(".ycb-extract-*.tmp"))


def test_ycb_extracted_record_must_match_the_pinned_archive_member(tmp_path: Path) -> None:
    archive_path = tmp_path / "fixture.tgz"
    member_name = "006_mustard_bottle/google_16k/textured.ply"
    payload = b"fixture mesh bytes"
    with tarfile.open(archive_path, mode="w:gz") as archive:
        info = tarfile.TarInfo(member_name)
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    valid_record = {
        "archive_member": member_name,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }

    _verify_archive_members(archive_path, [valid_record], "archive_member")
    changed = {**valid_record, "sha256": "0" * 64}
    with pytest.raises(ValueError, match="not bound to its archive member"):
        _verify_archive_members(archive_path, [changed], "archive_member")


def test_ycb_source_archive_identity_is_pinned_to_reviewed_bytes() -> None:
    assert YCB_ARCHIVE_IDENTITIES["006_mustard_bottle_google_16k.tgz"]["bytes"] == 10_703_139
    assert YCB_ARCHIVE_IDENTITIES["021_bleach_cleanser_google_16k.tgz"]["sha256"] == (
        "2d71162158f5b51089a08ea12180d47a6480f4ba986af0c887a93ad5fc867588"
    )


def _all_in_band(manifest: Path) -> dict[str, dict[str, float]]:
    samples = json.loads(manifest.read_text(encoding="utf-8"))["samples"]
    return {
        s["id"]: {k: b["lower"] for k, b in s["expected_software_metric_bands"].items()}
        for s in samples
    }


def test_regression_harness_passes_engine_results_inside_bands(dataset_manifest: Path) -> None:
    from tools.datasets.run_benchmark_regression import run_regression

    report = run_regression(dataset_manifest, _all_in_band(dataset_manifest))
    assert report["outcome"] == "PASS"
    assert report["counts"] == {"PASS": 96 * 8, "FAIL": 0, "NOT_EVALUATED": 0}


def test_regression_harness_fails_out_of_band_and_never_passes_unevaluated(
    dataset_manifest: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tools.datasets.run_benchmark_regression as harness
    from tools.datasets.run_benchmark_regression import run_regression

    # Full manifest validation is exercised by the in-band test; skip repeats here.
    monkeypatch.setattr(harness, "validate_manifest", lambda _path: None)

    observed = _all_in_band(dataset_manifest)
    first = next(iter(observed))
    observed[first]["reconstruction_extent_x_mm"] = 100.7
    report = run_regression(dataset_manifest, observed)
    assert report["outcome"] == "FAIL" and report["counts"]["FAIL"] == 1

    partial = {first: {"segmentation_iou": 0.95}}
    report = run_regression(dataset_manifest, partial)
    assert report["outcome"] == "PARTIAL_PASS"
    assert report["counts"] == {"PASS": 1, "FAIL": 0, "NOT_EVALUATED": 96 * 8 - 1}

    assert run_regression(dataset_manifest, {})["outcome"] == "FAIL"


def test_regression_harness_rejects_unknown_samples_and_unbanded_metrics(
    dataset_manifest: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tools.datasets.run_benchmark_regression as harness
    from tools.datasets.run_benchmark_regression import run_regression

    monkeypatch.setattr(harness, "validate_manifest", lambda _path: None)

    with pytest.raises(ValueError, match="unknown samples"):
        run_regression(dataset_manifest, {"real_kenya_bottle": {"segmentation_iou": 1.0}})
    first = next(iter(_all_in_band(dataset_manifest)))
    with pytest.raises(ValueError, match="no band"):
        run_regression(dataset_manifest, {first: {"volume_ml": 1000.0}})
    with pytest.raises(ValueError, match="finite"):
        run_regression(dataset_manifest, {first: {"segmentation_iou": float("nan")}})


def test_builtin_segmentation_engine_scores_ground_truth_masks(dataset_manifest: Path) -> None:
    from tools.datasets.run_benchmark_regression import builtin_segmentation, read_mask_png

    width, height, values = read_mask_png(
        dataset_manifest.parent / "synthetic/mask/syn_bottle_hdpe_matte_v01.png"
    )
    assert (width, height) == (640, 480) and sum(values) == 440 * 480
    sample = json.loads(dataset_manifest.read_text(encoding="utf-8"))["samples"][0]
    metrics = builtin_segmentation(sample, dataset_manifest.parent)
    assert metrics == {"segmentation_iou": 1.0, "segmentation_dice": 1.0}


GOLDEN_SUBSET = (
    Path(__file__).resolve().parents[1] / "fixtures" / "m17_golden_subset" / "manifest.json"
)
FULL_M17_MANIFEST_SHA256 = "3a37b55d8b93affdba73d23a39ba299c12053f433000a5911ac7f6e71ea3601b"


def test_committed_golden_subset_is_real_generated_data_pinned_to_full_dataset() -> None:
    result = validate_manifest(GOLDEN_SUBSET)
    assert result["golden_subset"] is True and result["sample_count"] == 8
    assert result["families"] == sorted(FAMILIES) and result["materials"] == sorted(MATERIALS)
    manifest = json.loads(GOLDEN_SUBSET.read_text(encoding="utf-8"))
    assert manifest["golden_subset_of"]["manifest_sha256"] == FULL_M17_MANIFEST_SHA256
    decision = (
        Path(__file__).resolve().parents[2]
        / manifest["golden_subset_of"]["public_redistribution_decision"]
    )
    assert decision.is_file()
    assert all(sample["source"]["kind"] == "procedural_blender" for sample in manifest["samples"])


def test_regression_harness_runs_segmentation_engine_on_committed_golden_subset() -> None:
    from tools.datasets.run_benchmark_regression import builtin_segmentation, run_regression

    report = run_regression(GOLDEN_SUBSET, observers=(builtin_segmentation,))
    assert report["counts"] == {"PASS": 16, "FAIL": 0, "NOT_EVALUATED": 8 * 6}
    assert report["outcome"] == "PARTIAL_PASS"


@pytest.mark.parametrize(
    "mutation",
    ["drop_family", "wrong_decision", "bad_parent_sha", "unbalanced_materials", "extra_parent_key"],
)
def test_golden_subset_parent_record_and_coverage_fail_closed(
    tmp_path: Path, mutation: str
) -> None:
    import shutil

    root = tmp_path / "subset"
    shutil.copytree(GOLDEN_SUBSET.parent, root)
    path = root / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    parent = manifest["golden_subset_of"]
    if mutation == "drop_family":
        manifest["samples"] = manifest["samples"][1:]
    elif mutation == "wrong_decision":
        parent["public_redistribution_decision"] = "README.md"
    elif mutation == "bad_parent_sha":
        parent["manifest_sha256"] = "not-a-digest"
    elif mutation == "extra_parent_key":
        parent["note"] = "x"
    else:
        manifest["samples"][0]["material_appearance"]["finish"] = manifest["samples"][1][
            "material_appearance"
        ]["finish"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError):
        validate_manifest(path)
