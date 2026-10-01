"""Bounded exact and perceptual duplicate candidates for PackScan photos."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from .packscan.container import PackScanReport
from .pre_reconstruction_qa import (
    MAX_QA_IMAGES,
    MAX_TOTAL_QA_SAMPLES,
    GrayImageSamples,
    ImageDecodeFailure,
)

DUPLICATE_PROFILE_ID: Final = "packlab.photo-duplicate-review.v1"
DIFFERENCE_HASH_ALGORITHM: Final = "difference_hash_9x8_luma_v1"
DEFAULT_MAX_HAMMING_DISTANCE: Final = 4
MAX_HAMMING_DISTANCE: Final = 16
MIN_LUMA_RANGE: Final = 8
MAX_PHOTO_BYTES: Final = 256 * 1024 * 1024
MAX_TOTAL_PHOTO_BYTES: Final = 2 * 1024 * 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PhotoDuplicateError(ValueError):
    """Raised when duplicate analysis inputs are ambiguous or unsafe."""


@dataclass(frozen=True, slots=True)
class PerceptualSamples:
    """Decoded luma samples explicitly bound to one source image digest."""

    samples: GrayImageSamples
    source_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.samples, GrayImageSamples):
            raise PhotoDuplicateError("perceptual samples must use the bounded luma contract")
        if not isinstance(self.source_sha256, str) or _SHA256.fullmatch(self.source_sha256) is None:
            raise PhotoDuplicateError("perceptual samples need a lowercase source SHA-256")


@dataclass(frozen=True, slots=True)
class PhotoDuplicateReport:
    """Canonical non-destructive duplicate candidates and provenance."""

    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return json.loads(json.dumps(self.payload, sort_keys=True, allow_nan=False))

    @property
    def canonical_json(self) -> bytes:
        return json.dumps(
            self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json).hexdigest()


def _difference_hash(samples: GrayImageSamples) -> tuple[int | None, str | None]:
    if samples.width < 9 or samples.height < 8:
        return None, "insufficient_sample_resolution"
    pixels = samples.pixels
    if max(pixels) - min(pixels) < MIN_LUMA_RANGE:
        return None, "low_contrast_image"
    grid: list[list[int]] = []
    for output_y in range(8):
        source_y = min(samples.height - 1, ((2 * output_y + 1) * samples.height) // 16)
        row: list[int] = []
        for output_x in range(9):
            source_x = min(samples.width - 1, ((2 * output_x + 1) * samples.width) // 18)
            row.append(pixels[source_y * samples.width + source_x])
        grid.append(row)
    signature = 0
    for row in grid:
        for left, right in zip(row[:-1], row[1:], strict=True):
            signature = (signature << 1) | int(left > right)
    return signature, None


def _photo_metadata(report: PackScanReport) -> dict[str, object] | None:
    metadata_bytes = report.payloads.get("metadata/photos.json")
    if isinstance(metadata_bytes, bytes):
        try:
            metadata = json.loads(metadata_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            metadata = None
        if isinstance(metadata, dict) and isinstance(metadata.get("photos"), list):
            return metadata
    return None


def _canonical_order(
    report: PackScanReport, image_paths: list[str]
) -> tuple[list[str], dict[str, object]]:
    metadata = _photo_metadata(report)
    if metadata is not None:
        photos = metadata["photos"]
        assert isinstance(photos, list)
        records = [item for item in photos if isinstance(item, dict)]
        sequences = [item.get("sequence") for item in records]
        paths = [item.get("image_path") for item in records]
        if (
            len(records) == len(photos) == len(image_paths)
            and all(isinstance(value, int) and not isinstance(value, bool) for value in sequences)
            and sequences == list(range(len(records)))
            and paths == image_paths
        ):
            return [path for path in paths if isinstance(path, str)], {
                "policy": "photo_metadata_zero_based_sequence",
                "status": "verified",
            }
        return sorted(image_paths), {
            "policy": "manifest_path_ascending_fallback",
            "status": "metadata_order_unavailable",
            "reason_code": "photo_metadata_order_does_not_match_manifest",
        }
    return sorted(image_paths), {
        "policy": "manifest_path_ascending_fallback",
        "status": "metadata_order_unavailable",
        "reason_code": "photo_metadata_missing_or_malformed",
    }


def build_photo_duplicate_report(
    report: PackScanReport,
    decoded_images: Mapping[str, PerceptualSamples | ImageDecodeFailure],
    *,
    max_hamming_distance: int = DEFAULT_MAX_HAMMING_DISTANCE,
) -> PhotoDuplicateReport:
    """Return exact duplicate groups and perceptual near-duplicate candidates.

    Exact identity is source-byte SHA-256. Perceptual candidates use a 64-bit
    horizontal difference hash and an inclusive Hamming-distance threshold.
    All output is review-only: no photo is removed, rewritten, or hidden.
    """
    if not isinstance(report, PackScanReport):
        raise PhotoDuplicateError("a validated PackScanReport is required")
    if not isinstance(decoded_images, Mapping):
        raise PhotoDuplicateError("decoded_images must be a path-keyed mapping")
    if (
        not isinstance(max_hamming_distance, int)
        or isinstance(max_hamming_distance, bool)
        or not 0 <= max_hamming_distance <= MAX_HAMMING_DISTANCE
    ):
        raise PhotoDuplicateError(f"max_hamming_distance must be in 0..{MAX_HAMMING_DISTANCE}")
    if any(
        not isinstance(path, str)
        or not isinstance(decoded, (PerceptualSamples, ImageDecodeFailure))
        for path, decoded in decoded_images.items()
    ):
        raise PhotoDuplicateError(
            "decoded image entries must use the declared path and result contracts"
        )
    declarations = report.manifest.get("payloads")
    if not isinstance(declarations, list):
        raise PhotoDuplicateError("manifest payload declarations are missing")
    images = [
        item for item in declarations if isinstance(item, dict) and item.get("kind") == "image"
    ]
    if not images:
        raise PhotoDuplicateError("duplicate review requires at least one image")
    if len(images) > MAX_QA_IMAGES:
        raise PhotoDuplicateError(f"duplicate review is limited to {MAX_QA_IMAGES} images")
    by_path: dict[str, dict[str, object]] = {}
    folded_paths: set[str] = set()
    exact_groups: dict[str, list[str]] = defaultdict(list)
    total_photo_bytes = 0
    for declaration in images:
        path = declaration.get("path")
        digest = declaration.get("sha256")
        size = declaration.get("size_bytes")
        data = report.payloads.get(path) if isinstance(path, str) else None
        if (
            not isinstance(path, str)
            or not path
            or path in by_path
            or path.casefold() in folded_paths
            or not isinstance(digest, str)
            or _SHA256.fullmatch(digest) is None
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or size > MAX_PHOTO_BYTES
            or not isinstance(data, bytes)
            or len(data) != size
            or hashlib.sha256(data).hexdigest() != digest
            or report.checksums.get(path) != digest
        ):
            raise PhotoDuplicateError("manifest image identity or payload integrity check failed")
        by_path[path] = {"sha256": digest, "size_bytes": size}
        folded_paths.add(path.casefold())
        total_photo_bytes += size
        if total_photo_bytes > MAX_TOTAL_PHOTO_BYTES:
            raise PhotoDuplicateError("source image payload total exceeds the profile limit")
        exact_groups[digest].append(path)
    if set(decoded_images) - set(by_path):
        raise PhotoDuplicateError("decoded image mapping contains undeclared source paths")
    metadata_bytes = report.payloads.get("metadata/photos.json")
    metadata_declaration = next(
        (
            item
            for item in declarations
            if isinstance(item, dict) and item.get("path") == "metadata/photos.json"
        ),
        None,
    )
    if metadata_declaration is None:
        raise PhotoDuplicateError("photo metadata declaration is missing")
    metadata_sha = metadata_declaration.get("sha256")
    metadata_size = metadata_declaration.get("size_bytes")
    if (
        not isinstance(metadata_bytes, bytes)
        or not isinstance(metadata_sha, str)
        or _SHA256.fullmatch(metadata_sha) is None
        or not isinstance(metadata_size, int)
        or isinstance(metadata_size, bool)
        or metadata_size < 0
        or len(metadata_bytes) != metadata_size
        or hashlib.sha256(metadata_bytes).hexdigest() != metadata_sha
        or report.checksums.get("metadata/photos.json") != metadata_sha
    ):
        raise PhotoDuplicateError("photo metadata payload integrity check failed")
    declared_paths = [item.get("path") for item in images]
    if not all(isinstance(path, str) for path in declared_paths):
        raise PhotoDuplicateError("manifest image paths are invalid")
    manifest_order = [path for path in declared_paths if isinstance(path, str)]
    ordered_paths, ordering = _canonical_order(report, manifest_order)
    metadata = _photo_metadata(report)
    dimensions_by_path: dict[str, tuple[int, int]] = {}
    metadata_photos = metadata.get("photos") if metadata is not None else None
    if isinstance(metadata_photos, list):
        for photo in metadata_photos:
            if not isinstance(photo, dict):
                continue
            path = photo.get("image_path")
            dimensions = photo.get("pixel_dimensions")
            if (
                isinstance(path, str)
                and isinstance(dimensions, dict)
                and isinstance(dimensions.get("width"), int)
                and not isinstance(dimensions.get("width"), bool)
                and isinstance(dimensions.get("height"), int)
                and not isinstance(dimensions.get("height"), bool)
                and dimensions["width"] > 0
                and dimensions["height"] > 0
            ):
                dimensions_by_path[path] = (dimensions["width"], dimensions["height"])
    source_evidence = [{"image_path": path, **by_path[path]} for path in ordered_paths]
    exact = [
        {"source_sha256": digest, "image_paths": sorted(paths)}
        for digest, paths in sorted(exact_groups.items())
        if len(paths) > 1
    ]
    sample_total = sum(
        image.samples.width * image.samples.height
        for image in decoded_images.values()
        if isinstance(image, PerceptualSamples)
    )
    if sample_total > MAX_TOTAL_QA_SAMPLES:
        raise PhotoDuplicateError("decoded perceptual sample total exceeds the profile limit")
    signatures: dict[str, int] = {}
    unavailable: list[dict[str, str]] = []
    image_signature_records: list[dict[str, object]] = []
    for path in ordered_paths:
        digest = by_path[path]["sha256"]
        assert isinstance(digest, str)
        decoded = decoded_images.get(path)
        if isinstance(decoded, PerceptualSamples):
            if decoded.source_sha256 != digest:
                raise PhotoDuplicateError(
                    "perceptual samples are bound to a different source digest"
                )
            if path not in dimensions_by_path:
                reason = "photo_dimensions_unavailable"
                unavailable.append(
                    {"image_path": path, "source_sha256": digest, "reason_code": reason}
                )
                image_signature_records.append(
                    {
                        "image_path": path,
                        "source_sha256": digest,
                        "algorithm": DIFFERENCE_HASH_ALGORITHM,
                        "status": "unavailable",
                        "reason_code": reason,
                    }
                )
                continue
            if (
                decoded.samples.source_width,
                decoded.samples.source_height,
            ) != dimensions_by_path[path]:
                reason = "dimension_mismatch"
                unavailable.append(
                    {"image_path": path, "source_sha256": digest, "reason_code": reason}
                )
                image_signature_records.append(
                    {
                        "image_path": path,
                        "source_sha256": digest,
                        "algorithm": DIFFERENCE_HASH_ALGORITHM,
                        "status": "unavailable",
                        "reason_code": reason,
                    }
                )
                continue
            signature, failure = _difference_hash(decoded.samples)
            if failure is None:
                assert signature is not None
                signatures[path] = signature
                image_signature_records.append(
                    {
                        "image_path": path,
                        "source_sha256": digest,
                        "algorithm": DIFFERENCE_HASH_ALGORITHM,
                        "hash_hex": f"{signature:016x}",
                        "source_dimensions": {
                            "width": decoded.samples.source_width,
                            "height": decoded.samples.source_height,
                        },
                        "sample_dimensions": {
                            "width": decoded.samples.width,
                            "height": decoded.samples.height,
                        },
                        "decoder_id": decoded.samples.decoder_id,
                        "decoder_version": decoded.samples.decoder_version,
                    }
                )
                continue
            reason = failure if isinstance(failure, str) else "perceptual_hash_unavailable"
        elif isinstance(decoded, ImageDecodeFailure):
            reason = decoded.reason_code
        else:
            reason = "decoded_samples_missing"
        unavailable.append({"image_path": path, "source_sha256": digest, "reason_code": reason})
        image_signature_records.append(
            {
                "image_path": path,
                "source_sha256": digest,
                "algorithm": DIFFERENCE_HASH_ALGORITHM,
                "status": "unavailable",
                "reason_code": reason,
            }
        )
    near_pairs: list[dict[str, object]] = []
    for index, path_a in enumerate(ordered_paths):
        hash_a = signatures.get(path_a)
        if hash_a is None:
            continue
        for path_b in ordered_paths[index + 1 :]:
            if by_path[path_a]["sha256"] == by_path[path_b]["sha256"]:
                continue
            hash_b = signatures.get(path_b)
            if hash_b is None:
                continue
            distance = (hash_a ^ hash_b).bit_count()
            if distance <= max_hamming_distance:
                near_pairs.append(
                    {
                        "image_path_a": path_a,
                        "source_sha256_a": by_path[path_a]["sha256"],
                        "image_path_b": path_b,
                        "source_sha256_b": by_path[path_b]["sha256"],
                        "hamming_distance": distance,
                        "max_hamming_distance_inclusive": max_hamming_distance,
                    }
                )
    payload: dict[str, object] = {
        "schema": "packlab.photo-duplicate-review.v1",
        "profile_id": DUPLICATE_PROFILE_ID,
        "authority": "non_authoritative_duplicate_candidates",
        "claim_limit": "review_candidates_only_no_automatic_photo_deletion_or_rescan_policy",
        "capture_id": report.manifest.get("capture_id"),
        "photo_metadata_sha256": metadata_sha,
        "exact_identity": "sha256_of_verified_source_image_bytes",
        "perceptual": {
            "algorithm": DIFFERENCE_HASH_ALGORITHM,
            "hamming_distance_max_inclusive": max_hamming_distance,
            "hash_bits": 64,
            "minimum_luma_range": MIN_LUMA_RANGE,
            "image_ordering": ordering,
        },
        "source_images": source_evidence,
        "perceptual_signatures": image_signature_records,
        "exact_duplicate_groups": exact,
        "near_duplicate_pairs": near_pairs,
        "perceptual_unavailable_images": unavailable,
        "summary": {
            "image_count": len(ordered_paths),
            "exact_duplicate_group_count": len(exact),
            "near_duplicate_pair_count": len(near_pairs),
            "perceptual_unavailable_count": len(unavailable),
        },
    }
    return PhotoDuplicateReport(payload)
