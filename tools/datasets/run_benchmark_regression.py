"""Compare engine results with the M17 synthetic benchmark metric bands.

Usage:
  python tools/datasets/run_benchmark_regression.py <manifest.json> \
      [--observed results.json] [--builtin-segmentation] [--report out.json]

`results.json` maps sample id -> {metric key -> value}, produced by an engine run
(COLMAP/OpenMVS, fitting, SAM 2.1, ...). `--builtin-segmentation` runs PackLab's
mask post-processing engine on each ground-truth mask. Metrics no source covers
are reported NOT_EVALUATED, never PASS. Bands are synthetic software ranges, not
physical or Kenya acceptance.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from collections.abc import Callable, Mapping
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_packaging_dataset import validate_manifest

from packlab_core.benchmark_metrics import MetricOutcome, compare_synthetic_packaging_sample

Observer = Callable[[Mapping[str, object], Path], Mapping[str, float]]


def read_mask_png(path: Path) -> tuple[int, int, tuple[bool, ...]]:
    """Decode a non-interlaced 8-bit grayscale/RGB(A) PNG into a boolean mask."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path.name}")
    pos, idat, header = 8, b"", None
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos : pos + 8])
        chunk = data[pos + 8 : pos + 8 + length]
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"IDAT":
            idat += chunk
        pos += 12 + length
    if header is None:
        raise ValueError(f"PNG missing IHDR: {path.name}")
    width, height, depth, color, _, _, interlace = header
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color)
    if depth != 8 or channels is None or interlace:
        raise ValueError(f"unsupported mask PNG format: {path.name}")
    raw = zlib.decompress(idat)
    stride = width * channels
    rows: list[bytearray] = []
    prev = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        ftype, line = raw[start], bytearray(raw[start + 1 : start + 1 + stride])
        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            if ftype == 1:
                line[i] = (line[i] + a) & 0xFF
            elif ftype == 2:
                line[i] = (line[i] + b) & 0xFF
            elif ftype == 3:
                line[i] = (line[i] + (a + b) // 2) & 0xFF
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 0xFF
            elif ftype != 0:
                raise ValueError(f"invalid PNG filter: {path.name}")
        rows.append(line)
        prev = line
    # Coverage lives in alpha when present, matching validate_packaging_dataset.
    offset = channels - 1 if color in (4, 6) else 0
    values = tuple(row[x * channels + offset] >= 128 for row in rows for x in range(width))
    return width, height, values


def builtin_segmentation(sample: Mapping[str, object], root: Path) -> dict[str, float]:
    from packlab_core.mask_postprocessing import MaskPostProcessingParameters, post_process_mask
    from packlab_core.segmentation import (
        CoordinateTransform,
        MaskArtifact,
        MaskRaster,
        PromptEvidence,
        PromptKind,
        SegmentationProvenance,
    )
    from packlab_core.segmentation_benchmark import mask_quality_metrics

    files = sample["files"]
    assert isinstance(files, Mapping)
    width, height, values = read_mask_png(root / files["mask"]["path"])
    truth = MaskRaster(width, height, values)
    parent = MaskArtifact(
        artifact_id=f"{sample['id']}-gt-mask",
        source_image_asset_id=files["rgb"]["path"],
        source_digest=files["rgb"]["sha256"],
        source_width=width,
        source_height=height,
        mask_asset_id=f"working/{files['mask']['path']}",
        mask_digest=truth.digest,
        mask_width=width,
        mask_height=height,
        transform=CoordinateTransform(width, height, width, height),
        provenance=SegmentationProvenance(
            "m17-synthetic-ground-truth", "1.0", "none", "1.0", "none",
            files["mask"]["sha256"], "python", "3.12", "docs/datasets/M17_DATASET_CATALOG.md",
        ),
        prompt=PromptEvidence(PromptKind.AUTOMATIC),
        mask_revision="m17-gt",
        created_at="2026-11-10T00:00:00Z",
        post_processing_version="none:raw-model-output",
        raster=truth,
    )
    child = post_process_mask(
        parent,
        MaskPostProcessingParameters(max_hole_area=16, max_component_area_to_remove=16, fill_single_pixel_notches=True),
    ).child
    metrics = mask_quality_metrics(truth, child.raster)
    return {"segmentation_iou": metrics.intersection_over_union, "segmentation_dice": metrics.dice}


def run_regression(
    manifest_path: Path,
    observed: Mapping[str, Mapping[str, float]] | None = None,
    observers: tuple[Observer, ...] = (),
) -> dict[str, object]:
    validate_manifest(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    samples = manifest["samples"]
    known = {sample["id"] for sample in samples}
    unknown = sorted(set(observed or {}) - known)
    if unknown:
        raise ValueError(f"observed results reference unknown samples: {unknown}")

    rows, counts = [], {"PASS": 0, "FAIL": 0, "NOT_EVALUATED": 0}
    for sample in samples:
        values: dict[str, float] = dict((observed or {}).get(sample["id"], {}))
        for observer in observers:
            values.update(observer(sample, root))
        bands = sample["expected_software_metric_bands"]
        extra = sorted(set(values) - set(bands))
        if extra:
            raise ValueError(f"{sample['id']}: observed metrics have no band: {extra}")
        not_evaluated = sorted(set(bands) - set(values))
        counts["NOT_EVALUATED"] += len(not_evaluated)
        if values:
            subset = {**sample, "expected_software_metric_bands": {k: bands[k] for k in values}}
            comparison = compare_synthetic_packaging_sample(subset, values)
            for result in comparison.results:
                counts[result.outcome.value] += 1
                rows.append({"sample": sample["id"], "metric": result.key, "observed": result.observed,
                             "lower": result.lower, "upper": result.upper, "unit": result.unit,
                             "outcome": result.outcome.value})
        rows.extend({"sample": sample["id"], "metric": k, "outcome": "NOT_EVALUATED"} for k in not_evaluated)

    evaluated = counts["PASS"] + counts["FAIL"]
    outcome = "FAIL" if counts["FAIL"] or not evaluated else MetricOutcome.PASS.value
    return {
        "dataset_id": manifest["dataset_id"],
        "outcome": outcome,
        "counts": counts,
        "authority": "NONPHYSICAL_SOFTWARE_TEST_ONLY; synthetic ranges, not physical or Kenya acceptance",
        "results": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--observed", type=Path)
    parser.add_argument("--builtin-segmentation", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    observed = json.loads(args.observed.read_text(encoding="utf-8")) if args.observed else None
    observers: tuple[Observer, ...] = (builtin_segmentation,) if args.builtin_segmentation else ()
    report = run_regression(args.manifest, observed, observers)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.write_text(text + "\n", encoding="utf-8")
    print(json.dumps({"outcome": report["outcome"], "counts": report["counts"]}, sort_keys=True))
    return 0 if report["outcome"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
