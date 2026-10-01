"""Qt image-decoding adapter for the backend-neutral capture QA service."""

from __future__ import annotations

import hashlib

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize, qVersion
from PySide6.QtGui import QImage, QImageReader

from packlab_core.packscan import PackScanReport
from packlab_core.pre_reconstruction_qa import (
    MAX_IMAGE_DIMENSION,
    MAX_QA_IMAGES,
    MAX_SAMPLES_PER_IMAGE,
    MAX_TOTAL_QA_SAMPLES,
    GrayImageSamples,
    ImageDecodeFailure,
    PreReconstructionQAReport,
    build_pre_reconstruction_qa,
)

_MAX_IMAGE_BYTES = 256 * 1024 * 1024
_DECODER_ID = "qt-qimagereader-grayscale8"
_SAMPLE_PROFILE = "nearest-scale-fit-1024x1024-v1"


def build_packscan_pre_reconstruction_qa(report: PackScanReport) -> PreReconstructionQAReport:
    """Decode verified PackScan image bytes and invoke the core QA profile.

    Decoding is read-only. Each source payload is hash-checked against its
    manifest declaration before Qt receives it; decode failures are recorded as
    normalized missing-data codes in the core report.
    """
    declarations = report.manifest.get("payloads")
    if not isinstance(declarations, list):
        raise ValueError("PackScan manifest payload declarations are unavailable")
    image_declarations = [
        item for item in declarations if isinstance(item, dict) and item.get("kind") == "image"
    ]
    if len(image_declarations) > MAX_QA_IMAGES:
        raise ValueError("image count exceeds the QA profile limit")
    decoded: dict[str, GrayImageSamples | ImageDecodeFailure] = {}
    total_samples = 0
    for declaration in image_declarations:
        path = declaration.get("path")
        if not isinstance(path, str):
            continue
        data = report.payloads.get(path)
        expected_digest = declaration.get("sha256")
        if (
            not isinstance(data, bytes)
            or not isinstance(expected_digest, str)
            or hashlib.sha256(data).hexdigest() != expected_digest
        ):
            # The core boundary raises for this same mismatch; keep the path out
            # of the decoder so no unverified bytes are interpreted.
            continue
        if len(data) > _MAX_IMAGE_BYTES:
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
        scale = min(1.0, 1024 / source_width, 1024 / source_height)
        sample_width = max(1, round(source_width * scale))
        sample_height = max(1, round(source_height * scale))
        if sample_width * sample_height > MAX_SAMPLES_PER_IMAGE:
            decoded[path] = ImageDecodeFailure("decode_failed")
            continue
        if total_samples + sample_width * sample_height > MAX_TOTAL_QA_SAMPLES:
            decoded[path] = ImageDecodeFailure("decode_failed")
            continue
        reader.setScaledSize(QSize(sample_width, sample_height))
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
        decoded[path] = GrayImageSamples(
            width=gray.width(),
            height=gray.height(),
            pixels=pixels,
            decoder_id=f"{_DECODER_ID}/{_SAMPLE_PROFILE}",
            decoder_version=qVersion(),
            source_width=source_width,
            source_height=source_height,
        )
        total_samples += actual_samples
    return build_pre_reconstruction_qa(report, decoded)
