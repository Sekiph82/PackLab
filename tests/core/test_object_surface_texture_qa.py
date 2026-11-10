"""PL-0375 / PL-0376: object-surface low-texture QA on provenance-bearing synthetic renders.

Fixtures are PackLab-generated Blender renders from the public M17 golden subset
(``tests/fixtures/m17_golden_subset``; generator, seed, camera, lighting and material
recorded in its manifest). Sensor noise and the printed-label negative case are
seeded test-time simulations. Nothing here is a factory photo or a physical
measurement; the thresholds are calibrated on synthetic renders only.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest
from test_pre_reconstruction_qa import _report
from tools.datasets.calibrate_object_texture import (
    load_render,
    simulated_printed_label,
    simulated_sensor_noise,
    simulated_specular_streaks,
)

from packlab_core.pre_reconstruction_qa import (
    OBJECT_TEXTURE_MIN_FRACTION,
    GrayImageSamples,
    ObjectMaskSamples,
    PreReconstructionQAError,
    build_pre_reconstruction_qa,
)
from packlab_studio.pre_reconstruction_qa import build_packscan_pre_reconstruction_qa

SUBSET = Path(__file__).resolve().parents[1] / "fixtures" / "m17_golden_subset"
PATH = "images/000.jpg"
HDPE_MATTE = ("syn_jerrycan_hdpe_matte_v01", "syn_trigger_spray_hdpe_matte_v03")
PET_GLOSS = ("syn_bottle_pet_gloss_v01", "syn_tube_pet_gloss_v03")


def _manifest_sample(sample_id: str) -> dict[str, object]:
    manifest = json.loads((SUBSET / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["fully_synthetic"] is True
    assert manifest["physical_measurements_present"] is False
    return next(item for item in manifest["samples"] if item["id"] == sample_id)


def _render(sample_id: str) -> tuple[bytes, GrayImageSamples, ObjectMaskSamples]:
    return load_render(SUBSET, sample_id)


_with_sensor_noise = simulated_sensor_noise
_with_printed_label = simulated_printed_label


def _qa(png: bytes, samples: GrayImageSamples, mask: object) -> dict:
    report = _report(image_bytes=png, width=samples.source_width, height=samples.source_height)
    return build_pre_reconstruction_qa(report, {PATH: samples}, {PATH: mask}).as_dict()


@pytest.mark.parametrize("sample_id", HDPE_MATTE)
def test_pl0375_white_hdpe_render_is_low_texture_under_simulated_sensor_noise(
    sample_id: str,
) -> None:
    sample = _manifest_sample(sample_id)
    assert sample["material_appearance"]["finish"] == "hdpe_matte"
    assert sample["synthetic"] is True
    png, samples, mask = _render(sample_id)
    for sigma in (0.0, 10.0):
        result = _qa(png, _with_sensor_noise(samples, sigma, seed=1), mask)
        texture = result["photos"][0]["object_surface_texture"]
        assert texture["status"] == "warning", (sigma, texture)
        assert texture["reason_code"] == "low_object_surface_texture"
        assert texture["textured_cell_fraction"] < OBJECT_TEXTURE_MIN_FRACTION
        assert result["components"]["object_surface_texture"]["status"] == "warning"
        assert result["overall"]["status"] == "review_required"
        assert result["claim_limit"] == "diagnostic_evidence_only_not_geometry_or_physical_accuracy"
        assert (
            result["components"]["object_surface_texture"]["evidence"]["claim_limit"]
            == "texture_evidence_only_not_reconstruction_quality"
        )


def test_pl0375_reviewer_noise_probe_no_longer_hides_low_texture() -> None:
    # Review probe: a white surface with +/-5 DN noise passed the Laplacian sharpness
    # metric. Pixel-scale noise must not count as surface texture.
    rng = random.Random(0)
    size = 64
    pixels = bytes(rng.randint(215, 225) for _ in range(size * size))
    samples = GrayImageSamples(size, size, pixels, "test-decoder", "1", size, size)
    mask = ObjectMaskSamples(size, size, bytes([1]) * (size * size), "full-frame", "1")
    result = _qa(b"synthetic-image", samples, mask)
    photo = result["photos"][0]
    assert photo["sharpness"]["status"] == "pass"  # documented: noise inflates sharpness
    assert photo["object_surface_texture"]["status"] == "warning"
    assert photo["object_surface_texture"]["textured_cell_fraction"] == 0.0
    assert result["overall"]["status"] == "review_required"


@pytest.mark.parametrize("sigma", [0.0, 10.0])
def test_pl0375_printed_label_negative_case_is_not_flagged(sigma: float) -> None:
    png, samples, mask = _render("syn_jerrycan_hdpe_matte_v01")
    labelled = _with_sensor_noise(_with_printed_label(samples, mask), sigma, seed=1)
    texture = _qa(png, labelled, mask)["photos"][0]["object_surface_texture"]
    assert texture["status"] == "pass", texture
    assert texture["textured_cell_fraction"] >= OBJECT_TEXTURE_MIN_FRACTION


@pytest.mark.parametrize("sample_id", PET_GLOSS)
def test_pl0376_glossy_pet_render_is_review_required_not_pass(sample_id: str) -> None:
    sample = _manifest_sample(sample_id)
    assert sample["material_appearance"]["finish"] == "pet_gloss"
    assert sample["render"]["controlled_sensor_noise"] == "not applied"
    png, samples, mask = _render(sample_id)
    for sigma in (0.0, 6.0):
        result = _qa(png, _with_sensor_noise(samples, sigma, seed=2), mask)
        photo = result["photos"][0]
        assert photo["object_surface_texture"]["status"] == "warning", sigma
        assert result["overall"]["status"] == "review_required"
        assert result["overall"]["next_action"] == "human_review"
    # Documented limitation: the AgX-tone-mapped renders barely clip highlights, so
    # these fixtures cannot calibrate a specular-clipping detector.
    clean = _qa(png, samples, mask)["photos"][0]["pixel_exposure"]["value"]
    assert clean["overexposed_pixel_fraction_above_239"] < 0.05


def test_studio_adapter_passes_object_masks_through_real_decode_path() -> None:
    png, samples, mask = _render("syn_jerrycan_hdpe_matte_v01")
    report = _report(image_bytes=png, width=samples.width, height=samples.height)
    without = build_packscan_pre_reconstruction_qa(report).as_dict()
    assert without["components"]["object_surface_texture"]["status"] == "not_requested"
    with_mask = build_packscan_pre_reconstruction_qa(report, {PATH: mask}).as_dict()
    assert with_mask["photos"][0]["object_surface_texture"]["status"] == "warning"
    assert with_mask == _qa(png, _studio_samples(with_mask, samples), mask)


def _studio_samples(result: dict, samples: GrayImageSamples) -> GrayImageSamples:
    decoder = result["photos"][0]["pixel_exposure"]["value"]["decoder"]
    return GrayImageSamples(
        samples.width,
        samples.height,
        samples.pixels,
        decoder["id"],
        decoder["version"],
        samples.width,
        samples.height,
    )


def test_object_texture_fails_closed_for_missing_misaligned_or_tiny_masks() -> None:
    size = 64
    samples = GrayImageSamples(
        size, size, bytes([200]) * (size * size), "test-decoder", "1", size, size
    )
    report = _report(width=size, height=size)
    not_requested = build_pre_reconstruction_qa(report, {PATH: samples}).as_dict()
    assert not_requested["components"]["object_surface_texture"]["status"] == "not_requested"
    missing = build_pre_reconstruction_qa(report, {PATH: samples}, {}).as_dict()
    assert missing["photos"][0]["object_surface_texture"]["reason_code"] == "object_mask_missing"
    assert missing["components"]["object_surface_texture"]["status"] == "unavailable"
    wrong = ObjectMaskSamples(32, 32, bytes([1]) * 1024, "mask", "1")
    mismatch = build_pre_reconstruction_qa(report, {PATH: samples}, {PATH: wrong}).as_dict()
    assert (
        mismatch["photos"][0]["object_surface_texture"]["reason_code"]
        == "object_mask_dimension_mismatch"
    )
    tiny_flags = bytearray(size * size)
    for row in range(8, 24):
        tiny_flags[row * size + 8 : row * size + 24] = bytes([1]) * 16
    tiny = ObjectMaskSamples(size, size, bytes(tiny_flags), "mask", "1")
    small = build_pre_reconstruction_qa(report, {PATH: samples}, {PATH: tiny}).as_dict()
    assert small["photos"][0]["object_surface_texture"]["reason_code"] == "object_area_too_small"
    with pytest.raises(PreReconstructionQAError):
        ObjectMaskSamples(4, 4, b"\x01" * 15, "mask", "1")
    with pytest.raises(PreReconstructionQAError):
        build_pre_reconstruction_qa(report, {PATH: samples}, [mask for mask in ()])  # type: ignore[arg-type]


@pytest.mark.parametrize("sample_id", PET_GLOSS)
@pytest.mark.parametrize(
    ("count", "width_px", "soft_px"),
    [(1, 1, 0), (2, 2, 0), (1, 6, 0), (2, 6, 0), (2, 4, 4), (2, 12, 8)],
)
def test_pl0376_simulated_specular_streaks_never_count_as_texture(
    sample_id: str, count: int, width_px: int, soft_px: int
) -> None:
    # Review P2-7: clipped glossy-PET highlight streaks used to turn the warning into a pass.
    png, samples, mask = _render(sample_id)
    glossy = simulated_specular_streaks(samples, mask, count, width_px, soft_px)
    for sigma in (0.0, 3.0):
        result = _qa(png, _with_sensor_noise(glossy, sigma, seed=3), mask)
        texture = result["photos"][0]["object_surface_texture"]
        assert texture["status"] == "warning", (count, width_px, soft_px, sigma, texture)
        assert texture["specular_cell_fraction"] > 0
        assert result["overall"]["status"] == "review_required"


def test_pl0376_printed_label_still_passes_beside_a_specular_highlight() -> None:
    png, samples, mask = _render("syn_bottle_pet_gloss_v01")
    labelled = simulated_specular_streaks(_with_printed_label(samples, mask), mask, 1, 6)
    texture = _qa(png, _with_sensor_noise(labelled, 3.0, seed=3), mask)["photos"][0][
        "object_surface_texture"
    ]
    assert texture["status"] == "pass"
    assert texture["specular_cell_fraction"] > 0


def test_calibration_keeps_a_margin_on_both_sides_of_the_threshold() -> None:
    # Pins the PL-0375 calibration in CI: a shifted threshold or a removed exclusion fails.
    plain: list[float] = []
    labelled: list[float] = []
    for sample_id in (*HDPE_MATTE, *PET_GLOSS, "syn_closure_pp_translucent_v01"):
        _png, samples, mask = _render(sample_id)
        label = _with_printed_label(samples, mask)
        for sigma in (0.0, 10.0):
            plain.append(_texture_fraction(_with_sensor_noise(samples, sigma, seed=1), mask))
            labelled.append(_texture_fraction(_with_sensor_noise(label, sigma, seed=1), mask))
    assert max(plain) <= OBJECT_TEXTURE_MIN_FRACTION - 0.04, max(plain)
    assert min(labelled) >= OBJECT_TEXTURE_MIN_FRACTION + 0.04, min(labelled)


def _texture_fraction(samples: GrayImageSamples, mask: ObjectMaskSamples) -> float:
    texture = _qa(b"synthetic-image", samples, mask)["photos"][0]["object_surface_texture"]
    return float(texture["textured_cell_fraction"])
