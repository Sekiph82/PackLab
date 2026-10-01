"""Qt decoder adapter for PackLab's source-bound photo duplicate detector."""

from __future__ import annotations

import hashlib

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize, qVersion
from PySide6.QtGui import QImage, QImageReader

from packlab_core.packscan import PackScanReport
from packlab_core.photo_duplicates import (
    MAX_PHOTO_BYTES,
    PerceptualSamples,
    PhotoDuplicateError,
    PhotoDuplicateReport,
    build_photo_duplicate_report,
)
from packlab_core.pre_reconstruction_qa import (
    MAX_IMAGE_DIMENSION,
    MAX_QA_IMAGES,
    MAX_SAMPLES_PER_IMAGE,
    MAX_TOTAL_QA_SAMPLES,
    GrayImageSamples,
    ImageDecodeFailure,
)

_DECODER_ID = "qt-qimagereader-grayscale8/duplicate-sample-fit-512x512-v1"


def build_packscan_photo_duplicate_report(
    report: PackScanReport, *, max_hamming_distance: int = 4
) -> PhotoDuplicateReport:
    """Decode bounded grayscale samples and run the core duplicate profile."""
    if not isinstance(report, PackScanReport):
        raise PhotoDuplicateError("a validated PackScanReport is required")
    declarations = report.manifest.get("payloads")
    if not isinstance(declarations, list):
        raise PhotoDuplicateError("manifest payload declarations are missing")
    image_declarations = [
        item for item in declarations if isinstance(item, dict) and item.get("kind") == "image"
    ]
    if len(image_declarations) > MAX_QA_IMAGES:
        raise PhotoDuplicateError(f"duplicate review is limited to {MAX_QA_IMAGES} images")
    decoded: dict[str, PerceptualSamples | ImageDecodeFailure] = {}
    total_samples = 0
    for declaration in image_declarations:
        path = declaration.get("path")
        digest = declaration.get("sha256")
        if not isinstance(path, str):
            continue
        data = report.payloads.get(path)
        if (
            not isinstance(data, bytes)
            or not isinstance(digest, str)
            or hashlib.sha256(data).hexdigest() != digest
        ):
            # The core verifies all authoritative payload identities and raises
            # before it accepts results; never decode bytes that failed here.
            continue
        if len(data) > MAX_PHOTO_BYTES:
            decoded[path] = ImageDecodeFailure("decode_failed")
            continue
        buffer = QBuffer()
        buffer.setData(QByteArray(data))
        if not buffer.open(QIODevice.OpenModeFlag.ReadOnly):
            decoded[path] = ImageDecodeFailure("decode_failed")
            continue
        reader = QImageReader(buffer)
        reader.setDecideFormatFromContent(True)
        reader.setAutoTransform(False)
        source_size = reader.size()
        source_width, source_height = source_size.width(), source_size.height()
        if source_width < 1 or source_height < 1:
            reason = "unsupported_image_format" if reader.format().isEmpty() else "decode_failed"
            decoded[path] = ImageDecodeFailure(reason)
            continue
        if source_width > MAX_IMAGE_DIMENSION or source_height > MAX_IMAGE_DIMENSION:
            decoded[path] = ImageDecodeFailure("decode_failed")
            continue
        scale = min(1.0, 512 / source_width, 512 / source_height)
        requested_width = max(1, round(source_width * scale))
        requested_height = max(1, round(source_height * scale))
        if requested_width * requested_height > MAX_SAMPLES_PER_IMAGE:
            decoded[path] = ImageDecodeFailure("decode_failed")
            continue
        if total_samples + requested_width * requested_height > MAX_TOTAL_QA_SAMPLES:
            decoded[path] = ImageDecodeFailure("decode_failed")
            continue
        reader.setScaledSize(QSize(requested_width, requested_height))
        image = reader.read()
        if image.isNull():
            decoded[path] = ImageDecodeFailure("decode_failed")
            continue
        gray = image.convertToFormat(QImage.Format.Format_Grayscale8)
        actual_samples = gray.width() * gray.height()
        if (
            gray.width() < 1
            or gray.height() < 1
            or actual_samples > MAX_SAMPLES_PER_IMAGE
            or total_samples + actual_samples > MAX_TOTAL_QA_SAMPLES
            or gray.width() > source_width
            or gray.height() > source_height
        ):
            decoded[path] = ImageDecodeFailure("decode_failed")
            continue
        stride = gray.bytesPerLine()
        raw = bytes(gray.constBits())
        pixels = b"".join(
            raw[row * stride : row * stride + gray.width()] for row in range(gray.height())
        )
        decoded[path] = PerceptualSamples(
            GrayImageSamples(
                width=gray.width(),
                height=gray.height(),
                pixels=pixels,
                decoder_id=_DECODER_ID,
                decoder_version=qVersion(),
                source_width=source_width,
                source_height=source_height,
            ),
            digest,
        )
        total_samples += actual_samples
    return build_photo_duplicate_report(report, decoded, max_hamming_distance=max_hamming_distance)
