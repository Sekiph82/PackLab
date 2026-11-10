"""Reproduce the PL-0375 object-surface texture calibration table on synthetic renders.

Runs the production QA texture check over the public M17 golden-subset renders, plain and
with a simulated printed label, at several simulated sensor-noise levels. Every input is
synthetic; the output is software calibration evidence, not physical validation.

Usage: python -m tools.datasets.calibrate_object_texture [--subset DIR]
Requires PySide6 (grayscale decode identical to the Studio QA adapter).
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from tools.datasets.run_benchmark_regression import read_mask_png

from packlab_core.pre_reconstruction_qa import (
    GrayImageSamples,
    ObjectMaskSamples,
    _object_texture,
)

DEFAULT_SUBSET = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "m17_golden_subset"
NOISE_SIGMAS_DN = (0.0, 3.0, 6.0, 10.0)


def load_render(subset: Path, sample_id: str) -> tuple[bytes, GrayImageSamples, ObjectMaskSamples]:
    from PySide6.QtGui import QImage

    png = (subset / "rgb" / f"{sample_id}.png").read_bytes()
    image = QImage.fromData(png).convertToFormat(QImage.Format.Format_Grayscale8)
    width, height, stride = image.width(), image.height(), image.bytesPerLine()
    raw = bytes(image.constBits())
    pixels = b"".join(raw[row * stride : row * stride + width] for row in range(height))
    mask_width, mask_height, flags = read_mask_png(subset / "masks" / f"{sample_id}.png")
    if (mask_width, mask_height) != (width, height):
        raise ValueError(f"{sample_id}: mask and render dimensions differ")
    samples = GrayImageSamples(width, height, pixels, "qt-gray8", "1", width, height)
    mask = ObjectMaskSamples(width, height, bytes(flags), "m17-ground-truth-mask", "synthetic-v2")
    return png, samples, mask


def _replace_pixels(samples: GrayImageSamples, pixels: bytes) -> GrayImageSamples:
    return GrayImageSamples(
        samples.width,
        samples.height,
        pixels,
        samples.decoder_id,
        samples.decoder_version,
        samples.source_width,
        samples.source_height,
    )


def simulated_sensor_noise(
    samples: GrayImageSamples, sigma_dn: float, seed: int
) -> GrayImageSamples:
    """SIMULATED additive Gaussian sensor noise in 8-bit DN, clamped to 0..255."""
    rng = random.Random(seed)
    return _replace_pixels(
        samples,
        bytes(max(0, min(255, round(v + rng.gauss(0.0, sigma_dn)))) for v in samples.pixels),
    )


def simulated_printed_label(
    samples: GrayImageSamples, mask: ObjectMaskSamples, seed: int = 7
) -> GrayImageSamples:
    """SIMULATED dark glyph-like print over a band (40-75% of object height) of the mask."""
    rng = random.Random(seed)
    width = samples.width
    pixels = bytearray(samples.pixels)
    inside = [index for index, flag in enumerate(mask.inside) if flag]
    rows = [index // width for index in inside]
    cols = [index % width for index in inside]
    top, bottom, left, right = min(rows), max(rows), min(cols), max(cols)
    band_top = top + (bottom - top) * 2 // 5
    band_bottom = top + (bottom - top) * 3 // 4
    for _ in range(2000):
        glyph_w, glyph_h = rng.randint(3, 8), rng.randint(5, 9)
        x = rng.randint(left, right - glyph_w)
        y = rng.randint(band_top, band_bottom - glyph_h)
        ink = rng.randint(20, 90)
        for row in range(y, y + glyph_h):
            for col in range(x, x + glyph_w):
                index = row * width + col
                if mask.inside[index] and rng.random() < 0.8:
                    pixels[index] = ink
    return _replace_pixels(samples, bytes(pixels))


def calibration_rows(subset: Path) -> list[dict[str, object]]:
    manifest = json.loads((subset / "manifest.json").read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for sample in manifest["samples"]:
        _png, samples, mask = load_render(subset, sample["id"])
        labelled = simulated_printed_label(samples, mask)
        for sigma in NOISE_SIGMAS_DN:
            for variant, source in (("plain", samples), ("printed_label", labelled)):
                noisy = simulated_sensor_noise(source, sigma, seed=1)
                result = _object_texture(noisy, {"p": mask}, "p")
                rows.append(
                    {
                        "sample_id": sample["id"],
                        "finish": sample["material_appearance"]["finish"],
                        "variant": variant,
                        "noise_sigma_dn": sigma,
                        "status": result["status"],
                        "textured_cell_fraction": result.get("textured_cell_fraction"),
                        "assessed_cell_count": result.get("assessed_cell_count"),
                    }
                )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset", type=Path, default=DEFAULT_SUBSET)
    args = parser.parse_args()
    print(json.dumps(calibration_rows(args.subset), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
